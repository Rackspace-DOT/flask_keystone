Flask Keystone
==============

[![Build Status](https://travis-ci.org/Rackspace-DOT/flask_keystone.svg?branch=master)](https://travis-ci.org/Rackspace-DOT/flask_keystone)[![Coverage Status](https://coveralls.io/repos/github/Rackspace-DOT/flask_keystone/badge.svg?branch=master)](https://coveralls.io/github/Rackspace-DOT/flask_keystone?branch=master)

Flask Keystone is a flask extension which wraps the [keystonemiddleware](https://github.com/openstack/keystonemiddleware "KeystoneMiddleware's Github Page") project, and provides access to Keystone
users, project, and roles in a familiar, Flask-y manner. During development, you will find that most constructs appear very similar to flask-login.

Documentation
-------------

COMING SOON

Installation
------------
This package can be installed like any other python packages:
1. Clone this Repo
2. ```python setup.py install```

Getting Started with Flask Rax Keystone
=======================================

Flask Keystone is a Flask Extension which adds the ability to control users and role-base access control in a `Flask` like way. Once the extension is installed, initialized, and configured, it exposes some fairly standard Flask constructs to interact with Keystone Users and application specific roles.

Configuring the Extension
-------------------------

Just add some basic configuration items to your `oslo_config` configuration file, like so:

```ini
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

[rax_access]
roles = your_keystone_role:your_flask_role
```

Initializing the Extension
--------------------------

Simply wrap the application object during instantiation:
```python
    from flask import Flask

    from flask_rax_keystone import RaxKeystone

    app = RaxKeystone(Flask(__name__))

    if __name__ == "__main__":  # pragma: nocover
        app = create_app(app_name=__name__)
        app.run(host="0.0.0.0", port=5000
```

Accessing the application
-------------------------

Once the application is instantiated, you will automatically be requiring a valid token for *all* requests to the application. These tokens should be passed in the *X-Auth-Token* header, as is consistent with Openstack.

You can see this behavior here:
```bash
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

~ [ curl -i localhost:5000/ -H "X-Auth-Token: $A_VALID_TOKEN"
HTTP/1.0 200 OK
Content-Type: application/json
Content-Length: 63
Server: Werkzeug/0.11.11 Python/3.5.2
Date: Thu, 15 Dec 2016 21:56:43 GMT

{
  "message": "Looks like access was successfully granted."
}
```

Restricting Endpoints
---------------------

Once we have our roles configured, we can start restricting endpoints to only be accessible by users with certain configured roles. In the following Example assume an "admin" role was configured as shown in the "Configuring the Extension" section of this guide.

```python
from flask import Blueprint

blueprint = Blueprint('blueprint', __name__)

@blueprint.route("/test")
@key.requires_role("admin")
def test_endpoint():
    return jsonify(message="Looks like access was successfully granted.")
```

And now, you'll see that even a good token, when it does not have the required role, will receive a 403 response:

```json
    {
      "code": 403,
      "message": "The provided credentials were accepted, but were not sufficient to access this resource.",
      "title": "Forbidden"
    }
```
Initializing the Extension in an Application Factory app
--------------------------------------------------------

As with all flask extensions, it is also accessible in an application Factory setting by initializing the extension separately from it's instantiation:
```python
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
```
