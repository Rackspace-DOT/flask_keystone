Getting Started with Flask Keystone
===================================

Flask Keystone is a Flask Extension which adds the ability to control
users and role-base access control in a :mod:`Flask` like way. Once the
extension is installed, initialized, and configured, it exposes some fairly
standard Flask constructs to interact with Keystone Users and application
specific roles.


Configuring the Extension
-------------------------

Just add some basic configuration items to your :mod:`oslo_config`
configuration file, like so:

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
    roles = lnx-CloudServer-Admin:admin

Initializing the Extension
--------------------------

Simply wrap the application object during instantiation:

.. code-block:: python

   from flask import Flask

   from flask_keystone import Keystone

   app = Keystone(Flask(__name__))

   if __name__ == "__main__":  # pragma: nocover
       app = create_app(app_name=__name__)
       app.run(host="0.0.0.0", port=5000

Accessing the application
-------------------------

Once the application is instantiated, you will automatically be requiring
a valid token for *all* requests to the application. These tokens should be
passed in the `X-Auth-Token` header, as is consistent with Openstack.

You can see this behavior here:

.. code-block:: none

   ~ [ curl -i localhost:5000/
   HTTP/1.0 401 UNAUTHORIZED
   Content-Type: application/json
   Content-Length: 114
   WWW-Authenticate: Keystone uri='https://identity.api.rackspacecloud.com'
   Server: Werkzeug/0.11.11 Python/3.5.2
   Date: Thu, 15 Dec 2016 21:56:53 GMT

   {
     "code": 401,
     "message": "The request you have made requires authentication.",
     "title": "Unauthorized"
   }

   ~ [ curl -i localhost:5000/v1/accounts/ -H "X-Auth-Token: $A_VALID_TOKEN"
   HTTP/1.0 200 OK
   Content-Type: application/json
   Content-Length: 63
   Server: Werkzeug/0.11.11 Python/3.5.2
   Date: Thu, 15 Dec 2016 21:56:43 GMT

   {
     "message": "Looks like access was successfully granted."
   }

Restricting Endpoints
---------------------

Once we have our roles configured, we can start restricting endpoints to only
be accessible by users with certain configured roles. In the following Example
assume an "admin" role was configured as shown in the "Configuring the
Extension" section of this guide.

.. code-block:: python

   from flask import Blueprint

   blueprint = Blueprint('blueprint', __name__)

   @blueprint.route("/test")
   @key.requires_role("admin")
   def test_endpoint():
       return jsonify(message="Looks like access was successfully granted.")

And now, you'll see that even a good token, when it does not have the required
role, will receive a 403 response:

.. code-block:: json

   {
     "code": 403,
     "message": "The provided credentials were accepted, but were not sufficient to access this resource.",
     "title": "Forbidden"
   }

Allowing Anonymous Access in your application
---------------------------------------------
By default, flask_keystone protects all endpoints exposed in the application,
by enforcing a token during a `before_request` function. If you would like anonymous
access to be available in your application, you will need to add the "allow_anonymous_access"
key to your configuration file:

.. warning::

    Once this configuration option is applied, **No** endpoints will be automatically
    protected. You will need to use the `@login_required` decorator to protect them.

.. code-block:: ini

    [flask_keystone]
    roles = your_keystone_role:your_flask_role
    allow_anonyomous_access = True

Once this configuration option is present, you will be able to use the `@login_required`
decorator to token-protect endpoints.

.. code-block:: python

    from flask import Blueprint

    blueprint = Blueprint('blueprint', __name__)

    @blueprint.route("/scary_admin_endpoint")
    @key.requires_role("admin")
    @key.login_required
    def test_endpoint():
        return jsonify(message="This will return a 403 if not admin, and a 401 wihtout a valid token.")

    @blueprint.route("/regular_protected_endpoint)
    @key.login_required
    def test_endpoint_two():
        return jsonify(message="This endpoint will return a 401 without a valid token.")

    @blueprint.route("/anonymous_endpoint")
    def test_endpoint_three():
        return jsonify(message="This endpoint is accessible with or without a token.")

Initializing the Extension in an Application Factory app
--------------------------------------------------------

As with all flask extensions, it is also accessible in an application Factory
setting by initializing the extension separately from it's instantiation:

.. code-block:: python

   from flask import Flask

   from flask_keystone import Keystone

   key = Keystone()

   def create_app(app_name):
       app = Flask(app_name)
       key.init_app(app)

       return app


   if __name__ == "__main__":  # pragma: nocover
       app = create_app(app_name=__name__)
       app.run(host="0.0.0.0", port=5000)
