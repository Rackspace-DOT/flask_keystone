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

import json
from oslo_config import fixture

from testtools import TestCase

from keystoneauth1 import fixture as ksa_fixture
from keystonemiddleware import fixture as ksm_fixture

from flask import jsonify

from flask_keystone import (current_user, FlaskKeystone)
from flask_keystone.exceptions import (FlaskKeystoneUnauthorized,
                                       FlaskKeystoneForbidden)

from flask_keystone.tests.test_fixtures.fake_app import create_app


class TestFlaskKeystone(TestCase):
    """
    TODO(rtrox): Add a docstring here.
    """
    def setUp(self):
        """
        Setup the Test Environment for the Flask Keystone Extension.

        This setup function creates a flask app, and initializes the ksm
        fixture to intercept auth requests. It also generates a token
        for use in testing, and configures the extension.
        """
        super(TestFlaskKeystone, self).setUp()
        self.conf = self.useFixture(fixture.Config())
        self.conf.config(
            group="keystone_authtoken",
            delay_auth_decision=True
        )
        self.app = create_app()

        self.key = FlaskKeystone()
        self.conf.config(
            group="flask_keystone",
            roles={
                "admin_role_1": "admin",
                "admin_role_2": "admin",
                "support_role_1": "support"
            }
        )

        self.key.init_app(self.app)

        self.c = self.app.test_client()

        self.auth_token_fixture = self.useFixture(
            ksm_fixture.AuthTokenFixture()
        )

        self.token = self.create_token(["admin_role_1"])
        self.token_id = self.auth_token_fixture.add_token(self.token)

        @self.app.route("/user_id")
        def user_id():
            """
            Simple test route to return the id of the current user.

            Requires authentication token, but no role check.
            """
            return current_user.user_id

        @self.app.route("/requires_admin")
        @self.key.requires_role("admin")
        def requires_admin_role():
            """
            Test that a good token without role raises FlaskKeystoneForbidden.

            A token that does not have the correct keystone roles for a
            specified configured role should raise a FlaskKeystoneForbidden
            and therefore a 403.
            """
            return str(current_user.is_admin())

        @self.app.route("/requires_admin_or_unconfigured")
        @self.key.requires_role(["admin", "unconfiguredrole"])
        def requires_admin_or_unconfigured_role():
            """
            Simple test route to test role based access control.

            This should return successful as at least one role is valid.
            """
            return str(current_user.is_admin())

        @self.app.route("/requires_admin_or_support")
        @self.key.requires_role(["admin", "support"])
        def requires_admin_or_support_role():
            """
            Simple test route to test role based access control.

            This should return successful as at least one role is present.
            """
            return str(current_user.is_admin())

        @self.app.route("/requires_support_or_unconfigured")
        @self.key.requires_role(["support", "unconfiguredrole"])
        def requires_support_or_unconfigured_role():
            """
            Simple test route to test role based access control.

            This should return successful as at least one role is valid.
            """
            return str(current_user.is_admin())

        @self.app.route("/requires_unconfigured")
        @self.key.requires_role("unconfiguredrole")
        def requires_unconfigured_role():
            """
            Simple test route to test role based access control.

            This endpoint should always return a 403.
            """
            return "This shouldn't succeed."

        @self.app.route("/requires_support")
        @self.key.requires_role("support")
        def requires_support_role():
            """
            Simple test route to test role based access control.

            Returns a boolean value whether the user has the "support" role.
            """
            return "This shouldn't succeed."

        @self.app.route("/bad_type")
        @self.key.requires_role(12)
        def requires_bad_type():
            """
            Simple test route to ensure a TypeError is thrown for a bad type.

            Should raise a TypeError when accessed.
            """
            return "This shouldn't succeed."

    def tearDown(self):
        """
        TODO(russ7612): add docstring.
        """
        super(TestFlaskKeystone, self).tearDown()

    @staticmethod
    def create_token(roles=["admin_role_1"]):
        """
        Create a fake token that will be used in testing.

        :param roles: List of keystone roles to apply to token.
        :type roles: list(str)
        :returns: Testing Token.
        :rtype: `kestoneauth1.fixture.v2.Token`

        This token allows configuration of the roles assigned to it
        for rapid testing of RBAC.
        """

        # Creates a project scoped V3 token, with 1 entry in the catalog
        token = ksa_fixture.v2.Token(
            user_id="auser",
            tenant_id="atenant",
            tenant_name="atenantname"
        )
        for role in roles:
            token.add_role(name=role, id=role)
        return token

    def assert_json_equal(self, actual, expected):
        message = ("JSON did not match expected response. expected: %s,"
                   "actual: %s" % (json.dumps(expected), json.dumps(actual)))
        self.assertEqual(expected, actual, message)

    def test_instantiation(self):
        """
        Test initialization of the FlaskKeystone extension.

        A successful test should prove that roles are properly parsed,
        and that the User model is correctly generated.
        """

        expected = {
            "admin": set([
                "admin_role_2",
                "admin_role_1"
            ]),
            "support": set([
                "support_role_1"
            ])
        }
        self.assertEqual(self.key.roles, expected, "Roles should set at"
                                                   "key.roles.")
        assert hasattr(self.key.User, "is_admin")
        assert callable(self.key.User.is_admin)

    def test_get_user(self):
        """
        Test retrieval of the current_user when inside request scope.

        This test utilizes a test flask endpoint to fake a user and ensure
        that it is retrievable via the current_user construct.
        """
        result = self.c.get(
            "/user_id",
            headers={"X-Auth-Token": self.token_id})
        self.assertEqual(result.data.decode('utf-8'), "auser",
                         "Did not receive the expected successful response.")

    def test_bad_token(self):
        """
        Test that a missing token correctly generates a
        `FlaskKeystoneUnauthorized exception`.
        """
        result = self.c.get(
            "/user_id",
        )
        self.assertEqual(result.status_code, 401, "Bad response code. "
                                                  "Expected 401, got %s" %
                                                  result.status_code)
        json_response = json.loads(result.data.decode('utf-8'))

        expected = FlaskKeystoneUnauthorized().to_dict()
        self.assert_json_equal(json_response, expected)

    def test_failed_role_check(self):
        """Test that a failed role check generates a FlaskKeystoneForbidden."""
        result = self.c.get(
            "/requires_support",
            headers={"X-Auth-Token": self.token_id}
        )
        json_response = json.loads(result.data.decode('utf-8'))
        expected = FlaskKeystoneForbidden().to_dict()
        self.assert_json_equal(json_response, expected)

    def test_succesful_role_check(self):
        """
        Test that the same endpoint successful returns when given a good token.
        """
        result = self.c.get(
            "/requires_admin",
            headers={"X-Auth-Token": self.token_id}
        )
        self.assertEqual(result.data.decode('utf-8'), "True",
                         "Did not receive the expected response"
                         "from the server.")

    def test_multiple_roles_with_one_unconfigured(self):
        """
        Test that at least one configured & present role returns successfully.
        """
        result = self.c.get(
            "/requires_admin_or_unconfigured",
            headers={"X-Auth-Token": self.token_id}
        )
        self.assertEqual(result.data.decode('utf-8'), "True",
                         "Did not receive the expected response"
                         "from the server.")

    def test_only_one_role_required(self):
        """
        Requires role should only require one role in list to be present.
        """
        result = self.c.get(
            "/requires_admin_or_support",
            headers={"X-Auth-Token": self.token_id}
        )
        self.assertEqual(result.data.decode('utf-8'), "True",
                         "Did not receive the expected response"
                         "from the server.")

    def test_unconfigured_role_check(self):
        """
        Test that the requires_role decorator will return a 403 when a
        non-existant role is passed.
        """
        result = self.c.get(
            "/requires_unconfigured",
            headers={"X-Auth-Token": self.token_id}
        )
        json_response = json.loads(result.data.decode('utf-8'))
        expected = FlaskKeystoneForbidden().to_dict()
        self.assert_json_equal(json_response, expected)

    def test_requires_role_bad_type(self):
        """
        test that requires_role raises a TypeError when a bad type is passed.
        """
        result = self.c.get(
            "/bad_type",
            headers={"X-Auth-Token": self.token_id}
        )

        json_response = json.loads(result.data.decode('utf-8'))
        expected = FlaskKeystoneForbidden().to_dict()
        self.assert_json_equal(json_response, expected)

    def test_requires_role_multiple_roles_failure(self):
        """
        test that requires_role returns a 403 when multiple roles are
        specified but none are present.
        """
        result = self.c.get(
            "/requires_support_or_unconfigured",
            headers={"X-Auth-Token": self.token_id}
        )

        json_response = json.loads(result.data.decode('utf-8'))
        expected = FlaskKeystoneForbidden().to_dict()
        self.assert_json_equal(json_response, expected)


class TestFlaskKeystoneAnonymousUser(TestCase):
    """
    TODO(russ7612): Add a docstring here.
    """
    def setUp(self):
        """
        Setup the Test Environment for the Flask Keystone Extension.

        This setup function creates a flask app, and initializes the ksm
        fixture to intercept auth requests. It also generates a token
        for use in testing, and configures the extension.
        """
        super(TestFlaskKeystoneAnonymousUser, self).setUp()
        self.conf = self.useFixture(fixture.Config())
        self.conf.config(
            group="keystone_authtoken",
            delay_auth_decision=True
        )

        self.app = create_app()

        self.key = FlaskKeystone()
        self.conf.config(
            group="flask_keystone",
            allow_anonymous_access=True,
            roles={
                "admin_role_1": "admin",
                "admin_role_2": "admin",
                "support_role_1": "support"
            }
        )
        self.conf.config(
            debug=True
        )

        self.key.init_app(self.app)

        self.c = self.app.test_client()

        self.auth_token_fixture = self.useFixture(
            ksm_fixture.AuthTokenFixture()
        )

        self.token = self.create_token(["admin_role_1"])
        self.token_id = self.auth_token_fixture.add_token(self.token)

        @self.app.route("/anonymous")
        def anonymous_endpoint():
            """
            Test that an anonymous user can access an endpoint.

            An anonymous user should be able to access an endpoint when the
            allow_anonymous_access config option is set.
            """
            return jsonify(admin=current_user.is_admin())

        @self.app.route("/requires_login")
        @self.key.login_required
        def requires_a_login():
            """
            Endpoint that requires a login in an anonymous installation.
            """
            return jsonify(current_user=current_user.user_id)

        @self.app.route("/requires_support")
        @self.key.requires_role("support")
        @self.key.login_required
        def requires_support_user():
            """
            Requires the "support" role, which is not present on the token.
            """
            return jsonify(support=current_user.is_support())

        @self.app.route("/requires_support_two")
        @self.key.requires_role("support")
        def requires_support_user_paranoia():
            """
            Requires the "support" role, which is not present on the token.

            A secondary endpoint for a paranoia test, ensuring that a 403
            is thrown when an Anonymous user is allowed to hit the
            @requires_role decorator.
            """
            return jsonify(support=current_user.is_support())

        @self.app.route("/requires_admin")
        @self.key.requires_role("admin")
        @self.key.login_required
        def requires_admin_user():
            """
            Requires the "admin" role, which is present on the token.
            """
            return jsonify(admin=current_user.is_admin())

        @self.app.route("/anonymous_role_inventory")
        def anonymous_inv():
            return jsonify(
                admin=current_user.is_admin(),
                support=current_user.is_support(),
                has_admin=current_user.has_role("admin"),
                has_support=current_user.has_role("support"),
                has_keystone_role=current_user._has_keystone_role("a_role")
            )

    def tearDown(self):
        """
        TODO(russ7612): add docstring.
        """
        super(TestFlaskKeystoneAnonymousUser, self).tearDown()

    @staticmethod
    def create_token(roles=["admin_role_1"]):
        """
        Create a fake token that will be used in testing.

        :param roles: List of keystone roles to apply to token.
        :type roles: list(str)
        :returns: Testing Token.
        :rtype: `kestoneauth1.fixture.v2.Token`

        This token allows configuration of the roles assigned to it
        for rapid testing of RBAC.
        """

        # Creates a project scoped V3 token, with 1 entry in the catalog
        token = ksa_fixture.v2.Token(
            user_id="auser",
            tenant_id="atenant",
            tenant_name="atenantname"
        )
        for role in roles:
            token.add_role(name=role, id=role)
        return token

    def assert_json_equal(self, actual, expected):
        message = ("JSON did not match expected response. expected: %s,"
                   "actual: %s" % (json.dumps(expected), json.dumps(actual)))
        self.assertEqual(expected, actual, message)

    def test_anonymous_access(self):
        """
        Test that a missing token will allow access to an anonymous endpoint.
        """
        result = self.c.get(
            "/anonymous"
        )
        self.assertEqual(result.status_code, 200, "Bad response code. "
                                                  "Expected 200, got %d" %
                                                  result.status_code)
        json_response = json.loads(result.data.decode('utf-8'))

        expected = {"admin": False}
        self.assert_json_equal(json_response, expected)

    def test_bad_token(self):
        """
        Test that a missing token correctly generates a
        `FlaskKeystoneUnauthorized exception`.
        """
        result = self.c.get(
            "/requires_login",
        )
        self.assertEqual(result.status_code, 401, "Bad response code. "
                                                  "Expected 401, got %d" %
                                                  result.status_code)
        json_response = json.loads(result.data.decode('utf-8'))

        expected = FlaskKeystoneUnauthorized().to_dict()
        self.assert_json_equal(json_response, expected)

    def test_good_token(self):
        """Test that a good token will allow access to a protected endpoint."""
        result = self.c.get(
            "/requires_login",
            headers={"X-Auth-Token": self.token_id}
        )
        self.assertEqual(result.status_code, 200, "Bad response code. "
                                                  "Expected 200, got %d" %
                                                  result.status_code)
        json_response = json.loads(result.data.decode('utf-8'))

        expected = {"current_user": "auser"}
        self.assert_json_equal(json_response, expected)

    def test_failed_role_check(self):
        """
        Test that a role-check functions correctly with a missing role.

        This action should generate a 403 (FlaskKeystoneForbidden).
        """
        result = self.c.get(
            "/requires_support",
            headers={"X-Auth-Token": self.token_id}
        )

        self.assertEqual(result.status_code, 403, "Bad Response code. "
                                                  "Expected 403, got %d" %
                                                  result.status_code)
        json_response = json.loads(result.data.decode('utf-8'))
        expected = FlaskKeystoneForbidden().to_dict()
        self.assert_json_equal(json_response, expected)

    def test_failed_role_check_paranoia(self):
        """
        Test that the @login_required decorator is covered by @requires_role.

        This test is my own paranoia(russ7612), want to ensure that a 403
        is always returned on a role check, even if login_required is not
        present.
        """
        result = self.c.get(
            "/requires_support_two",
            headers={"X-Auth-Token": self.token_id}
        )

        self.assertEqual(result.status_code, 403, "Bad Response code. "
                                                  "Expected 403, got %d" %
                                                  result.status_code)
        json_response = json.loads(result.data.decode('utf-8'))
        expected = FlaskKeystoneForbidden().to_dict()
        self.assert_json_equal(json_response, expected)

    def test_successful_role_check(self):
        """
        Test that a token with the proper roles can get access.

        When a token has the correct role, a 200 should be returned.
        """
        result = self.c.get(
            "/requires_admin",
            headers={"X-Auth-Token": self.token_id}
        )
        self.assertEqual(result.status_code, 200, "Bad Response code. "
                                                  "Expected 200, got %d" %
                                                  result.status_code)
        json_response = json.loads(result.data.decode('utf-8'))
        expected = {"admin": True}
        self.assert_json_equal(json_response, expected)

    def test_all_roles_should_be_false(self):
        """
        Check that all helper functions return False as expected on an Anon.
        """
        result = self.c.get(
            "/anonymous_role_inventory"
        )
        self.assertEqual(result.status_code, 200, "Bad response code. "
                                                  "Expected 200, got %d" %
                                                  result.status_code)
        json_response = json.loads(result.data.decode('utf-8'))
        for k, v in json_response.items():
            self.assertEqual(v, False, "A role check returned True when it "
                                       "shouldn't have. Check: %s, Value: %s" %
                                       (k, v))
