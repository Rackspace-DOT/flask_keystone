The Dynamically Generated `User` class
======================================

Flask Keystone Dynamically Generates a User model based on it's
configuration, which collects the data from the request headers to set
attributes, and creates helper functions to determine role membership.

These Helper Functions include `is_<configured_role>()`, and
has_role(`<configured_role>`).

Additionally, The generated User class automatically attaches all Keystone
header data to itself for easy access. For example, `User.project_id`, and
`User.user_id`. These attributes are dynamically generated from the header
names using the following transformation:

.. code-block: python

   header.strip("X-").replace("-", "_").lower()

Commonly used attributes are:
    - User.user_id
    - User.project_id
    - User.project_name
    - User.roles (Note, this converts automatically to a list)
    - User.service_catalog

Additional attributes (and their latest names), can be found in the auth_token
`documentation <http://docs.openstack.org/developer/keystonemiddleware/api/keystonemiddleware.auth_token.html>`_

**class flask_keystone.user.UserBase(request)**

   Bases: `UserBase <flask_keystone.user>`

   The User Class to which all keystone data is appended.

   :Parameters:
      **request** -- The incoming *flask.Request* object, after being
      handled by the ``keystonemiddleware``

   :Returns:
      ``Keystone.User``

   When this Flask exension is initialized, a *User* class is
   generated programatically, with helper methods for determining
   membership in configurable, application specific roles.

   These methods include *is_{role_name}()* and
   *has_role(*role_name*)*, both of which return a boolean describing
   membership of an instance of User in the configured roles.

   All "X-" Headers added by keystonemiddleware are translated into
   Attributes of this class as well, such that: -
   *request.headers["X-Project-Id"]`* becomes *User.project_id* -
   *request.headers["X-User-Id"]* becomes *User.user_id* and so on.


   **has_role**(*role*)

      Return a boolean whether given user has the defined configured_role.

      :Parameters:
         * **role** (*str*) -- The role to against which to evaluate the `User`.

      :Returns:
         * **bool** -- Whether the given user has the role specified in this
           method.

      This method is intended to be used by an inheriting class to
      generate the has_role method based on the roles provided.

      ``Keystone`` uses this to add these methods to a dynamically
      generated class which inherits from this class.


   **is_<configured_role>()**

      Return a boolean whether given User has the defined configured_role.

      This set of methods serves as a convenience function around
      :func:`has_role`. For example, `is_admin()` is equivalent to
      `has_role("admin")`.

      Commonly this will appear as `User.is_admin()` or `User.is_support()`,
      but any configured roles can be used here.

      :Returns:
         * **bool** -- Whether the given user has the role specified in this
           method.

      This method is programmatically generated from the `UserBase` class,
      and will be present for any roles configured in the configuration file.

Notes on Anonymous Access
=========================

When Anonymous Access is enabled, an "Anonymous" user is also generated. This user
will have all the same helper methods, but they will always return `False`.

For the attributes themselves, a best effort is made to populate these all with
empty strings, but the list is hard-coded based on the `keystonemiddleware.auth_token`
documentation, which means it may not always be equivalent. It is recommended not to
attempt to access attributes outside a token gated endpoint to ensure the attributes
you expect to present are actually present.
