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
Exceptions specific to the Flask Keystone Extension.

Any Exception inherited from :class:`FlaskKeystoneException` will be
automatically handled and transformed to appear as follows to the client:

.. code-block:: json

   {
      "code": "<status_code>",
      "message": "<message>",
      "title": "<title>"
   }
"""

from flask import jsonify


def handle_exception(error):
    """
    Jsonify a :class:`FlaskKeystoneException` for return to the client.

    :param error: Exception to be handled and jsonified.
    :type error: :class:`FlaskKeystoneException`
    :returns: :class:`flask.Response`

    This function is automatically added to the wrapped :class`flask.Flask`
    when the extension is initialized.
    """
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


class FlaskKeystoneException(Exception):
    """
    Generic Exception class for the sake of homogeneity.

    :param str title:       Title of the error to be returned with the
                            exception. In all foreseeable circumstances this
                            should be the name of the HTTP Error Code
                            (Unauthorized, Forbidden, Bad Request, etc.)
    :param str message:     The unique message text for the specific error. In
                            inheriting classes this may either be defined
                            during __init__, or hard coded.
    :param int status_code: The status code to be returned with the Exception.
                            (default: 500)
    :param dict payload:    Payload to be returned to the client. If this param
                            is set, the default response format will be
                            overridden with the dictionary specified.

    FlaskKeystoneException adds a custom handler to the wrapped app for this
    exception, which will cause the response to the client to appear as
    follows:

    .. code-block:: json

      {
         "code": "<status_code>",
         "message": "<message>",
         "title": "<title>"
      }
    """
    status_code = 500

    def __init__(self, title, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.title = title
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['code'] = self.status_code
        rv['title'] = self.title
        rv['message'] = self.message
        return rv


class FlaskKeystoneUnauthorized(FlaskKeystoneException):
    """
    An Unauthorized User has attempted to access the System.

    This Exception will be thrown when the underlying
    :mod:`keystonemiddleware` returns any "X-Identity-Status other than
    "Confirmed". While the keystonemiddleware docs should be consulted for
    the most current definition of this response, a non-"Confirmed" response
    will normally indicate that either no token was sent with the request,
    or the sent token was invalid.

    This exception will be caught by :func:`handle_exceptions` and therefore
    generate the following client response:

    .. code-block:: json

       {
         "code": 401,
         "message": "The request you have made requires authentication.",
         "title": "Unauthorized"
       }
    """
    status_code = 401

    def __init__(self):
        message = "The request you have made requires authentication."
        FlaskKeystoneException.__init__(
            self,
            title="Unauthorized",
            message=message,
        )


class FlaskKeystoneForbidden(FlaskKeystoneException):
    """
    The provided credentials were accepted, but were not sufficient.

    This exception will be thrown when the Token sent with the request
    is present and valid, but the account/user that it signifies does
    not have the roles required to access the resource requested.

    This exception will be caught by :func:`handle_exceptions` and therefore
    generate the following client response:

    .. code-block:: json

       {
         "code": 403,
         "message": "The provided credentials were accepted, but were not sufficient to access this resource.",  # noqa: E501
         "title": "Forbidden"
       }
    """
    status_code = 403

    def __init__(self):
        message = ("The provided credentials were accepted, but were "
                   "not sufficient to access this resource.")
        FlaskKeystoneException.__init__(
            self,
            title="Forbidden",
            message=message
        )
