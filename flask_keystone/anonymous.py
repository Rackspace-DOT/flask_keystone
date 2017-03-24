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
Base Anonymous Model for use with the Flask Keystone Extension.

This Model is never accessed directly, but is rather used as a base
class for auto-generation of an Anonymous class based on the provided
configuration.

Once generated, the Anonymous model will have the following attributes:

- An `is_{role_name}()` method, which takes no arguments, and returns a
  boolean if the user has the requested configured role (always `False`).
- A `has_role(*role_name*)` method, which takes the requested configured_roles
  role as an arugment and returns a boolean if the user has the requested
  configured role (always `False`).
- An approximation of all attrs that would be added by `keystonemiddleware`,
  all set to an empty `str`, except roles, which is an emply list.
"""

from oslo_config import cfg
from oslo_log import log as logging


class AnonymousBase(object):
    """
    Base Anonymous class used in autogeneration of an anonymous class.

    :returns: :class:`flask_keystone.AnonymousBase`

    When this Flask extension is initialized with the allow_anonymous_access
    configuration option set, an `Anonymous` class is generated
    programatically, with the same helper methods as
    `flask_keystone.UserBase`. On the anonymous user, all of these methods
    will always return `False`.

    These methods include `is_{role_name}()` and `has_role(*role_name*)`,
    both of which will always return false as an Anonymous user has no
    configured roles.

    The Anonymous User will also make best effort to create all attributes
    that should be present on a User class, though these attributes are
    statically generated based on `keystonemiddleware.auth_token` 's
    documentation (Though all attributes will be set to an empty string).
    """

    def __init__(self):
        """
        Initialize an instance of :class:`flask_keystone.AnonymousBase`.

        This class should approximate the `flask_keystone.UserBase` class,
        with the exception that all attributes will be set to an empty string,
        and all helper methods will return False.
        """
        self.logger = logging.getLogger(__name__)
        try:
            logging.register_options(cfg.CONF)
        except cfg.ArgsAlreadyParsedError:  # pragma: no cover
            pass
        logging.setup(cfg.CONF, "flask_keystone")

        self.anonymous = True
        self.auth_token = ""
        self.service_token = ""
        self.domain_id = ""
        self.service_domain_id = ""
        self.domain_name = ""
        self.service_domain_name = ""
        self.project_id = ""
        self.service_project_id = ""
        self.project_name = ""
        self.service_project_name = ""
        self.project_domain_id = ""
        self.service_project_domain_id = ""
        self.project_domain_name = ""
        self.service_project_domain_name = ""
        self.user_id = ""
        self.service_user_id = ""
        self.user_name = ""
        self.service_user_name = ""
        self.user_domain_id = ""
        self.service_user_domain_id = ""
        self.user_domain_name = ""
        self.service_user_domain_name = ""
        self.service_roles = ""
        self.is_admin_project = ""
        self.service_catalog = ""
        self.tenant_id = ""
        self.tenant_name = ""
        self.tenant = ""
        self.user = ""
        self.role = ""

        self.roles = []

    def _has_keystone_role(self, role):
        """
        Determine whether keystone role is present on this instance.

        :param str role: Role that should be present in `UserBase.roles`.
                         These roles will have been populated from "X-Roles".
        :returns: Whether or not the role is present for this instance.
        :rtype: bool

        Note that as this is an Anonymous user, this function will always
        return `False`.
        """
        return False

    def has_role(self, role):
        """
        Determine if an instance of this class has the configured role.

        :param str role: The role identifier from `oslo.config.cfg` to
                         against which to evaluate this instance for
                         membership.
        :returns: Whether or not the instance has the desired role.
        :rtype: bool

        Note that as this is an Anonymous user, this function will always
        return `False`.
        """
        return False

    @classmethod
    def generate_is_role_functions(cls, roles):
        """
        Generate `class.is_{role}()` methods for a class.

        :param class cls: The python class to be modified.
        :param dict roles: The roles to use for generation.

        This method is intended to be used by an inheriting class to
        generate `is_{role}()` methods based on the roles provided
        during generation.

        :class:`RaxKeystone` uses this to add these methods to a dynamically
        generated class which inherits from this class.

        Note that as this is an Anonymous user, these functions will always
        return `False`.
        """
        for access_role in roles.keys():
            setattr(cls, "is_" + access_role, lambda x: False)
