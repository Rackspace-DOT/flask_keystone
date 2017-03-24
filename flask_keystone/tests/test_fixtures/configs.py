def test_roles_dict():
    """
    A dictionary of roles for use in testing the dynamic User class.

    This dictionary represents the roles that will be in RaxKeystone.roles.
    """
    return {
        "admin": ["admin_role_1", "admin_role_2"],
        "support": ["support_role_1"]
    }
