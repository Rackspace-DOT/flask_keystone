"""
Helper Fixture to buid a mocked request with a given set of headers.

Allows a mocked request object to be created, which allows testing
of context specific functions outside of the request context.
"""

from werkzeug.test import EnvironBuilder
from werkzeug.wrappers import Request


def build_mock_request(headers):
    """Build a Request based on the given headers."""
    builder = EnvironBuilder(
        path='/',
        method="GET",
        headers=headers
    )
    return Request(builder.get_environ())
