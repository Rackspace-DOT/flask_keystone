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
Test Cases for user.UserBase, and the generation of a dynamic user class.
"""

from flask_keystone.user import UserBase

from flask_keystone.tests.test_fixtures.configs import test_roles_dict
from flask_keystone.tests.test_fixtures.request import build_mock_request

from unittest import TestCase


class TestUserBase(TestCase):
    """
    Test the UserBase inherited methods, excluding class generation.

    These tests should accurately represent the creation of the user class
    based on configuration in an oslo_config configuration file.
    """

    def setUp(self):
        self.request = build_mock_request(
            headers=[
                (
                    "X-User-Id",
                    "rtrox"
                ),
                (
                    "X-Project-Id",
                    "123456"
                ),
                (
                    "X-Roles",
                    "admin_role_1,support_role_1"
                )
            ]
        )

    def tearDown(self):
        pass

    def test_user_init(self):
        user = UserBase(self.request)
        self.assertEqual(user.user_id, "rtrox",
                         "user.user_id should be rtrox.")
        self.assertEqual(user.project_id, "123456",
                         "user.project_id should be '123456'.")
        self.assertEqual(user.roles, [
            "admin_role_1",
            "support_role_1"
        ], "user.roles does contain the required roles.")

    def test_transform_header(self):
        user = UserBase(self.request)
        self.assertEqual(
            user.transform_header("X-User-Id"),
            "user_id",
            "Transforming 'X-User-Id' header should yield 'user_id'."
        )

    def test_has_keystone_role(self):
        user = UserBase(self.request)
        self.assertTrue(user._has_keystone_role("admin_role_1"),
                        'user does not have the admin_role_1 role.')
        self.assertTrue(user._has_keystone_role("support_role_1"),
                        'user does not have the admin_role_1 role.')
        self.assertFalse(user._has_keystone_role("any_other_role"),
                         'user returned True for a non-existant role.')


class TestUserClassGenerator(TestCase):
    """
    This TestCase should test the dynamic generation of class methods.
    """

    def setUp(self):
        class User(UserBase):
            pass

        self.User = User
        self.request = build_mock_request(
            headers=[
                (
                    "X-Roles",
                    "admin_role_1"
                )
            ]
        )

    def tearDown(self):
        pass

    def test_has_role_generator(self):
        self.User.generate_has_role_function(test_roles_dict())

        self.assertTrue(hasattr(self.User, "has_role"),
                        "has_role method not present on "
                        "generated User class.")
        self.assertTrue(callable(self.User.has_role),
                        "has_role method not callable on "
                        "generated User class.")
        self.assertTrue(self.User(self.request).has_role("admin"),
                        "has_role('admin') should return True on "
                        "generated user.")
        self.assertFalse(self.User(self.request).has_role("support"),
                         "has_role('support') should return False on "
                         "generated user.")

    def test_is_role_generator(self):
        self.User.generate_has_role_function(test_roles_dict())
        self.User.generate_is_role_functions(test_roles_dict())

        self.assertTrue(hasattr(self.User, "is_admin"),
                        "is_admin method not present on "
                        "generated User class.")
        self.assertTrue(hasattr(self.User, "is_support"),
                        "is_support method not present on "
                        "generated User class.")
        self.assertTrue(callable(self.User.is_admin),
                        "is_admin method is not a callable on "
                        "generated User class.")
        self.assertTrue(callable(self.User.is_support),
                        "is_support method is not callable on "
                        "generated User class.")
        self.assertTrue(self.User(self.request).is_admin(),
                        "is_admin() method should return True "
                        "for generated User.")
        self.assertFalse(self.User(self.request).is_support(),
                         "is_support() method should return False "
                         "for generated User.")
