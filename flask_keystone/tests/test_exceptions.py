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
Test Cases for flask_keystone specific Exceptions.
"""

import json

from flask_keystone import exceptions
from flask_keystone import FlaskKeystone

from flask_keystone.tests.test_fixtures.fake_app import create_app

from oslo_config import fixture

from testtools import TestCase
from unittest import mock


PATCHER = mock.patch("keystonemiddleware.auth_token.AuthProtocol", mock.Mock())


class TestHandleException(TestCase):
    """
    Test the handle_exception function.

    This test case should prove that an exception passed to handle_exception
    successfully generates a json response suitable for use with Flask.
    """

    def setUp(self):
        super(TestHandleException, self).setUp()
        PATCHER.start()
        self.conf = self.useFixture(fixture.Config())
        key = FlaskKeystone()
        self.app = create_app()
        key.init_app(self.app)
        self.conf.config(
            group="flask_keystone",
            roles="admin_role_1:admin")

    def tearDown(self):
        super(TestHandleException, self).tearDown()
        PATCHER.stop()

    def test_handle_exception(self):
        """
        Generate a Response object using handle_exception and test that it
        matches the expected response.

        TODO(russ7612): expand this docstring.
        """
        err = exceptions.FlaskKeystoneUnauthorized()

        with self.app.test_request_context("/"):
            resp = exceptions.handle_exception(err)

        resp_json = json.loads(resp.data.decode('utf-8'))
        assert resp.status_code == 401
        assert resp_json == {
            "code": 401,
            "message": "The request you have made requires authentication.",
            "title": "Unauthorized"
        }


class TestExceptions(TestCase):
    """
    Test that each exception matches the expected json output.

    Each specified Exception generates a specific error output. These should
    be tested to ensure they do not drift from release to release.
    """

    def setUp(self):
        super(TestExceptions, self).setUp()

    def tearDown(self):
        super(TestExceptions, self).tearDown()

    def test_base_exception(self):
        """
        Test that the base exception allows customization of title & message.
        """
        err = exceptions.FlaskKeystoneException(
            title="AnError",
            message="We encountered an error."
        )
        self.assertEqual(err.status_code, 500,
                         "BaseException should result in 500 Status Code."
                         "got %d" % err.status_code)
        self.assertEqual(err.title, "AnError",
                         "BaseException title not correctly set.")
        self.assertEqual(err.message, "We encountered an error.",
                         "BaseException message not correctly set.")
        self.assertEqual(err.to_dict(), {
            "code": 500,
            "title": "AnError",
            "message": "We encountered an error."
        }, "Error message did not match.")

    def test_custom_status_code(self):
        """
        Test that status_code can be changed on base exception.
        """
        err = exceptions.FlaskKeystoneException(
            title="Bad Request",
            message="Could Not Deserialize JSON.",
            status_code=400
        )
        self.assertEqual(err.to_dict(), {
            "code": 400,
            "title": "Bad Request",
            "message": "Could Not Deserialize JSON."
        }, "Error message did not match.")

    def test_unauthorized_exception(self):
        """Test the response details of the Unauthorized exception."""
        err = exceptions.FlaskKeystoneUnauthorized()
        self.assertEqual(err.to_dict(), {
            "code": 401,
            "message": "The request you have made requires authentication.",
            "title": "Unauthorized"
        }, "Error message did not match.")

    def test_forbidden_exception(self):
        """Test the response details of the Forbidden exception."""
        err = exceptions.FlaskKeystoneForbidden()
        self.assertEqual(err.to_dict(), {
            "code": 403,
            "title": "Forbidden",
            "message": ("The provided credentials were accepted, but were "
                        "not sufficient to access this resource.")
        }, "Error message did not match.")
