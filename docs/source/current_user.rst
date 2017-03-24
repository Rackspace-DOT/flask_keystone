The `current_user` object
=========================

The :obj:`current_user` object allows access to the User that connected
to the application. This is accessibly anywhere :mod:`flask` 's
`Request Context <http://flask.pocoo.org/docs/0.11/reqcontext/>`_ is.

This is especially useful inside routes:

.. code-block:: python

   from flask import Blueprint

   from flask_keystone import current_user

   blueprint = Blueprint('blueprint', __name__)

   @blueprint.route("/test")
   def test_endpoint():
       user_name = current_user.user_name
       message = "Hello, %s!" % user_name
       if current_user.is_admin():
           message += "Looks like your an Admin!"
       return jsonify(message=message)
