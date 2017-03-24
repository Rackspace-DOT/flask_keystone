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
Configuration Directives for the Flask Rax Keystone Project.

This Extension wraps the :class:`keystonemiddleware.auth_token` WSGI Middleware
to add :mod:`flask` style configuration of users and role-based access control
to a API-Based Flask project.

As such, it is necessary to configure **both** the
:class:`keystonemiddleware.auth_token` middleware **and** the Flask Extension
in your :mod:`oslo_config` configuration file.

Configuring keystonemiddleware.auth_token
-----------------------------------------
Full Configuration options for :class:`keystonemiddleware.auth_token`
can be found in it's documentation, but a basic config set can be seen below.

Configuring Flask Rax Keystone
------------------------------
Currently Flask Rax Keystone only allows configuration via the :mod:oslo_config
module. To configure roles for use in your :class:`flask.Flask` application,
simply use the syntax "keystone_role:configured_role" in the "roles"
configuration directive, like this:

.. code-block:: ini

   [flask_keystone]
   roles = admin_role_1:admin

Note that it is also possible to map multiple keystone roles to the same
configured role, by simply specifying the same configured role in the roles
key:

.. code-block:: ini

   [flask_keystone]
   roles = admin_role_1:admin,admin_role_2:admin

And it is also possible to specify several roles:

.. code-block:: ini

   [flask_keystone]
   roles = admin_role_1:admin,support_role_1:support

Using a Different Configuration Group
-------------------------------------

The default :class:`OptGroup` for Flask Rax Keystone is
"flask_keystone", but this can easily be changed during initialization of the
extension like so:

.. code-block:: python

   from flask import Flask

   from flask_keystone import FlaskKeystone

   app = Flask(__name__)
   key = FlaskKeystone(app, config_group="my_config_group")

   if __name__ == "__main__":  # pragma: nocover
       app = create_app(app_name=__name__)
       app.run(host="0.0.0.0", port=5000

Or alternately, if you are using the Application Factory construct for Flask:

.. code-block:: python

   from flask import Flask

   from flask_keystone import FlaskKeystone

   key = FlaskKeystone()

   def create_app(app_name):
       app = Flask(app_name)

       key.init_app(app, config_group="my_config_group")

       return app


   if __name__ == "__main__":  # pragma: nocover
       app = create_app(app_name=__name__)
       app.run(host="0.0.0.0", port=5000)




Example Configuration File
--------------------------

.. code-block:: ini

    [keystone_authtoken]
    debug=True
    log_level=debug
    identity_uri = https://identity.api.rackspacecloud.com
    auth_uri = https://identity.api.rackspacecloud.com
    admin_tenant_name = 123456
    admin_user = your_admin_user
    admin_password = your_admin_user
    auth_version = 2.0
    auth_protocol = https
    delay_auth_decision = True

    [flask_keystone]
    roles = admin_role_1:admin,support_role_1:support
"""
from oslo_config import cfg

RAX_OPTS = [
    cfg.DictOpt('roles', default={}),
    cfg.BoolOpt('allow_anonymous_access', default=False)
]
