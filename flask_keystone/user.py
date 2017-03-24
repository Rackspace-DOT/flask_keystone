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
Base User Model for use with the Flask Keystone Extension.

This Model is never accessed directly, but is rather used as a base
class for auto-generation of a User class based on the provided
configuration.

Once generated, the User model will have the following attributes:

- An `is_{role_name}()` method, which takes no arguments, and returns a
  boolean if the user has the requested configured role.
- A `has_role(*role_name*)` method, which takes the requested configured_roles
  role as an arugment and returns a boolean if the user has the requested
  configured role.
- Attributes for all headers added by `keystonemiddleware`. ("X-Project-Id"
  becomes `User.project_id`, etc.)
"""

from oslo_config import cfg
from oslo_log import log as logging


class UserBase(object):
    """
    Base User class used in autogeneration of a user class.

    :param request: The incoming `flask.Request` object, after being handled
                    by the :mod:`keystonemiddleware`
    :returns: :class:`flask_keystone.UserBase`

    When this Flask extension is initialized, a `User` class is generated
    programatically, with helper methods for determining membership in
    configurable, application specific roles.

    These methods include `is_{role_name}()` and `has_role(*role_name*)`,
    both of which return a boolean describing membership of an instance of
    User in the configured roles.

    All "X-" Headers added by keystonemiddleware are translated into Attributes
    of this class as well, such that:
    -  `request.headers["X-Project-Id"]`` becomes `User.project_id`
    -  `request.headers["X-User-Id"]` becomes `User.user_id` and so on.
    """

    def __init__(self, request):
        """
        Initialize an instance of :class:`flask_keystone.UserBase`.

        During initialization, headers are transformed and applied as
        attributes to the object. Keystone Roles are also then added to a
        `UserBase.roles` attribute so that they can be easily transformed to
        a list.
        """
        self.logger = logging.getLogger(__name__)
        try:
            logging.register_options(cfg.CONF)
        except cfg.ArgsAlreadyParsedError:  # pragma: no cover
            pass
        logging.setup(cfg.CONF, "flask_keystone")

        for header in request.headers:
            if header[0].startswith("X-"):
                setattr(self, self.transform_header(header[0]), header[1])
        self.roles = request.headers.get("X-Roles", "").split(",")
        self.anonymous = False

    def transform_header(self, header):
        """
        transforms incoming header names for use as attrs.

        :param str header: header name to be transformed
        :returns: string to be used as an attr for this object.
        :rtype: str

        examples:
                "X-Project-Id" => "project_id"
                "X-User-Id"    => "user_id"
        """
        return header.strip("X-").replace("-", "_").lower()

    def _has_keystone_role(self, role):
        """
        Determine whether keystone role is present on this instance.

        :param str role: Role that should be present in `UserBase.roles`.
                         These roles will have been populated from "X-Roles".
        :returns: Whether or not the role is present for this instance.
        :rtype: bool
        """
        return role in self.roles

    @classmethod
    def generate_has_role_function(cls, roles):
        """
        Generate a `class.has_role('role_name')` method for a class.

        :param class cls: The python class to be modified.
        :param dict roles: The roles to use for generation.

        This method is intended to be used by an inheriting class to
        generate the has_role method based on the roles provided.

        :class:`FlaskKeystone` uses this to add these methods to a dynamically
        generated class which inherits from this class.
        """
        def has_role_func(self, role):
            """
            Determine if an instance of this class has the configured role.

            :param str role: The role identifier from `oslo.config.cfg` to
                             against which to evaluate this instance for
                             membership.
            :returns: Whether or not the instance has the desired role.
            :rtype: bool

            Note that the role passed to this function is the role identifier
            from the :class:`oslo.config.cfg`, rather than a keystone role
            itself.
            """
            if role not in roles:
                msg = "Evaluating has_role('%s'), Role '%s' does not exist."
                self.logger.warn(msg % (role, self.user_id))
                return False
            for group in roles[role]:
                if self._has_keystone_role(group):
                    return True
            return False
        setattr(cls, "has_role", has_role_func)

    @staticmethod
    def generate_is_role_function(access_role):
        """
        Define and return an is_<role> function.

        :param str access_role: The name of the configured role.

        This method is intended to be used by an inheriting class to
        generate `is_{role}()` methods based on the roles provided
        during generation.

        :class:`FlaskKeystone` uses this to add these methods to a dynamically
        generated class which inherits from this class.
        """
        def is_role_func(self):
            """
            Determine whether an instance of a class has this role.

            :returns: Whether or not the instance has this role.
            :rtype: bool

            This method will return a boolean describing whether an
            instance haves the role in the name of this method. This
            is a convenience function which has equivalency to
            :func:`has_role`. For example `user.is_admin()` is equivalent
            to `user.has_role("admin")`.

            Note that this function is dynamically generated.

            Note that the role passed to this function is the role
            identifier from the :class:`oslo.config.cfg`, rather than
            a keystone role itself.
            """
            return self.has_role(access_role)

        return is_role_func

    @classmethod
    def generate_is_role_functions(cls, roles):
        """
        Generate `class.is_{role}()` methods for a class.

        :param class cls: The python class to be modified.
        :param dict roles: The roles to use for generation.

        This method is intended to be used by an inheriting class to
        generate `is_{role}()` methods based on the roles provided
        during generation.

        :class:`FlaskKeystone` uses this to add these methods to a dynamically
        generated class which inherits from this class.
        """

        for access_role in roles.keys():
            is_role_func = cls.generate_is_role_function(access_role)
            setattr(cls, "is_" + access_role, is_role_func)
