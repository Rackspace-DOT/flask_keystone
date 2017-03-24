"""
Faked Flask Application for use in testing.

This application is has a simple stub route, and is wrapped with the
flask_rax_keystone extension.
"""

from flask import Flask, Blueprint

from flask_keystone import FlaskKeystone

key = FlaskKeystone()

test = Blueprint("test", __name__)


@test.route("/")
def a_route():
    """
    Simple stub route to determine successful access to the application.
    """
    return "Success."


def create_app(app_name="test_app"):
    """
    Create the flask app.

    This function is intended to be used with the app factory
    style of Flask deployment.

    :param str app_name: Name to be used internally within flask.
    :param blueprints: Blueprints to be registered.
    :type blueprints: list(:py:class:`flask.Blueprint`)
    :returns: The created app.
    :rtype: :py:class:`flask.Flask`
    """

    app = Flask(app_name)
    key.init_app(app)

    return app
