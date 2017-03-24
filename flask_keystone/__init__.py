# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Flask Extension to allow Flasky user and role handling for Keystone.

This Extension wraps :keystonemiddleware: to provide authentication and
role access via the OpenStack Keystone project, by parsing the headers
returned from :class`keystomemiddleware.auth_token` and creating a User
object to be attached to the request.

This user object is governed with the concept of "configured roles" which
are roles specific to this application that map to lists of upstream
Keystone roles.

Configured roles are established in the :mod:`oslo.config` configuration
file, and can then be accessed in code within your application.

Once the User object is created and attached to the request object,
it works much in the same way as Flask-Login. The user itself is exposed
via :obj:`flask_keystone.current_user`, and several helper
function and decorators exist (most useful of which are
:func:`FlaskKeystone.requires_role` and :func:`User.has_role`).
"""

from flask import (_request_ctx_stack,
                   request)

from functools import wraps

from keystonemiddleware import auth_token

from oslo_config import cfg
from oslo_log import log as logging

from werkzeug.local import LocalProxy

from flask_keystone.config import RAX_OPTS
from flask_keystone.exceptions import (FlaskKeystoneException,
                                       FlaskKeystoneForbidden,
                                       FlaskKeystoneUnauthorized,
                                       handle_exception)

from flask_keystone.anonymous import AnonymousBase
from flask_keystone.user import UserBase


__version__ = "0.2"


current_user = LocalProxy(lambda: _get_user())


def _get_user():
    return _request_ctx_stack.top.keystone_user


class FlaskKeystone(object):
    """

    :param app: `flask.Flask` application to which to connect.
    :type app: `flask.Flask`
    :param str config_group: :class:`oslo_config.cfg.OptGroup` to which
                             to attach.

    Note that consistent with the Application Factory method of `flask.Flask`
    instantiation, it is possible to pass these parameters either during
    __init__, or via an init_app function after instantiation.
    """

    def __init__(self, app=None, config_group="flask_keystone"):
        self.app = app
        if app is not None:  # pragma: no cover
            self.init_app(app, config_group)

    def init_app(self, app, config_group="flask_keystone"):
        """
        Iniitialize the Flask_Keystone module in an application factory.

        :param app: `flask.Flask` application to which to connect.
        :type app: `flask.Flask`
        :param str config_group: :class:`oslo_config.cfg.OptGroup` to which
                                 to attach.

        When initialized, the extension will apply the
        :mod:`keystonemiddleware` WSGI middleware to the flask Application,
        attach it's own error handler, and generate a User model based on
        its :mod:`oslo_config` configuration.
        """
        cfg.CONF.register_opts(RAX_OPTS, group=config_group)

        self.logger = logging.getLogger(__name__)
        try:
            logging.register_options(cfg.CONF)
        except cfg.ArgsAlreadyParsedError:  # pragma: no cover
            pass
        logging.setup(cfg.CONF, "flask_keystone")

        self.config = cfg.CONF[config_group]
        self.roles = self._parse_roles()
        self.User = self._make_user_model()
        self.Anonymous = self._make_anonymous_model()
        self.logger.debug("Initialized keystone with roles: %s and "
                          "allow_anonymous: %s" % (
                              self.roles,
                              self.config.allow_anonymous_access
                          ))
        app.wsgi_app = auth_token.AuthProtocol(app.wsgi_app, {})

        self.logger.debug("Adding before_request request handler.")
        app.before_request(self._make_before_request())
        self.logger.debug("Registering Custom Error Handler.")
        app.register_error_handler(FlaskKeystoneException, handle_exception)

    def _set_user(self, request):
        """
        Instantiate a user and attach it to the request context.

        :param request: The request from which to instantiate the User.
        :type request: :class:`flask.Request`

        This function instantiates a :class:`FlaskKeystone.User` and applies
        it to the request context for retrieval and comparison at any point
        during a single request.
        """
        _request_ctx_stack.top.keystone_user = self.User(request)

    def _set_anonymous_user(self):
        """
        Instantiate an anonymous user and attach it to the request context.

        This function should only be called if "allow_anonymous_access is
        set in the configuration for flask_keystone.
        """
        _request_ctx_stack.top.keystone_user = self.Anonymous()

    def _parse_roles(self):
        """
        Generate a dictionary for configured roles from oslo_config.

        Due to limitations in ini format, it's necessary to specify
        roles in a flatter format than a standard dictionary. This
        function serves to transform these roles into a standard
        python dictionary.
        """
        roles = {}
        for keystone_role, flask_role in self.config.roles.items():
            roles.setdefault(flask_role, set()).add(keystone_role)
        return roles

    def _make_before_request(self):
        """
        Generate the before_request function to be added to the app.

        Currently this function is static, however it is very likely we will
        need to programmatically generate this function in the future.
        """
        def before_request():
            """
            Process invalid identity statuses and attach user to request.

            :raises: :exception:`exceptions.FlaskKeystoneUnauthorized`

            This function guarantees that a bad token will return a 401
            when :mod:`keystonemiddleware` is configured to
            defer_auth_decision. Once this is done, it instantiates a user
            from the generated User model and attaches it to the request
            context for later access.
            """
            identity_status = request.headers.get(
                "X-Identity-Status", "Invalid"
            )
            if identity_status != "Confirmed":
                msg = ("Couldn't authenticate user '%s' with "
                       "X-Identity-Status '%s'")
                self.logger.info(msg % (
                    request.headers.get("X-User-Id", "None"),
                    request.headers.get("X-Identity-Status", "None")
                ))
                if not self.config.allow_anonymous_access:
                    msg = "Anonymous Access disabled, rejecting %s"
                    self.logger.debug(
                        msg % request.headers.get("X-User-Id", "None")
                    )
                    raise FlaskKeystoneUnauthorized()
                else:
                    self.logger.debug("Setting Anonymous user.")
                    self._set_anonymous_user()
                    return

            self._set_user(request)

        return before_request

    def _make_user_model(self):
        """
        Dynamically generate a User class for use with FlaskKeystone.

        :returns: a generated User class, inherited from
                  :class:`flask_keystone.UserBase`.
        :rtype: class

        This User model is intended to work somewhat similarly to the User
        class that is created for Flask-Login, however it is Dynamically
        generated based on configuration values in `oslo.config.cfg`, and
        is populated automatically from the request headers added by
        :mod:`keystonemiddleware`.

        This User class has the concept of "roles", which are defined in
        oslo.config, and generates helper functions to quickly Determine
        whether these roles apply to a particular instance.
        """
        class User(UserBase):
            """
            A User as defined by the response from Keystone.

            Note: This class is dynamically generated by :class:`FlaskKeystone`
            from the :class:`flask_keystone.UserBase` class.

            :param request: The incoming `flask.Request` object, after being
                            handled by the :mod:`keystonemiddleware`
            :returns: :class:`flask_keystone.UserBase`
            """
            pass

        User.generate_has_role_function(self.roles)
        User.generate_is_role_functions(self.roles)

        return User

    def _make_anonymous_model(self):
        """
        Dynamically generate an Anonymous class for use with FlaskKeystone.

        :return: a generated Anonymous class, inherited from
                 :class:`flask_keystone.AnonymousBase`.
        :rtype: class

        This Anonymous model will approximate the User class generated for this
        extension, attempting to have all the same attributes (though they will
        all be empty strings other than `Anonymous.roles`), and having the
        same helper functions (though they will always return false).
        """
        class Anonymous(AnonymousBase):
            """
            An Anonymous user, approximating a logged in User.

            Note: This class is dynamically generated by :class:`FlaskKeystone`
            from the :class:`flask_keystone.AnonymousBase` class.

            :returns: :class:`flask_keystone.UserBase`
            """
            pass

        Anonymous.generate_is_role_functions(self.roles)

        return Anonymous

    def requires_role(self, roles):
        """
        Require specific configured roles for access to a :mod:`flask` route.

        :param roles: Role or list of roles to test for access
                      (only one role is required to pass).
        :type roles: str OR list(str)
        :raises: FlaskKeystoneForbidden

        This method will gate a particular endpoint to only be accessed by
        :class:`FlaskKeystone.User`'s with a particular configured role. If the
        role given does not exist, or if the user does not have the requested
        role, a FlaskKeystoneForbidden exception will be thrown, resulting in a
        403 response to the client.
        """
        def wrap(f):
            @wraps(f)
            def wrapped_f(*args, **kwargs):
                if isinstance(roles, list):
                    if any(current_user.has_role(role) for role in roles):
                        return f(*args, **kwargs)

                elif isinstance(roles, str):
                    if current_user.has_role(roles):
                        return f(*args, **kwargs)
                else:
                    msg = ("roles parameter for requires_role on endpoint %s "
                           "should be a list or str, but is type %s.")
                    self.logger.error(msg % (
                        request.path,
                        type(roles)
                    ))

                msg = ("Rejected User '%s' access to '%s' "
                       "due to RBAC. (Requires '%s')")

                self.logger.info(msg % (
                    current_user.user_id,
                    request.path,
                    roles
                ))

                raise FlaskKeystoneForbidden()

            return wrapped_f
        return wrap

    def login_required(self, f):
        """
        Require a user to be validated by Identity to access an endpoint.

        :raises: FlaskKeystoneUnauthorized

        This method will gate a particular endpoint to only be accessed by
        :class:`FlaskKeystone.User`'s. This means that a valid token will need
        to be passed to grant access. If a User is not authenticated,
        a FlaskKeystoneUnauthorized will be thrown, resulting in a 401 response
        to the client.
        """
        @wraps(f)
        def wrapped_f(*args, **kwargs):
            if current_user.anonymous:
                msg = ("Rejected User '%s access to '%s' as user"
                       " could not be authenticated.")
                self.logger.warn(msg % (
                    current_user.user_id,
                    request.path
                ))
                raise FlaskKeystoneUnauthorized()
            return f(*args, **kwargs)
        return wrapped_f
