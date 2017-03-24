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
Flask Keystone Auth Middleware.

Flask Extension to allow Flasky user and role handling for Keystone.

This Extension wraps :keystonemiddleware: to provide authentication and
role access via the OpenStack Keystone project, by parsing the headers
returned from :class`keystomemiddleware.auth_token` and creating a User
object to be attached to the request.

This user object is governed with the concept of "configured roles" which
are roles specific to this application that map to lists of upstream
Keystone roles.

Configured roles are established in the :mod:`oslo.config` configuration
file, and can then be accessed in code within your application.

Example Configuration File:
.. code-block:: ini
   :linenos:

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

    [flask_keystone]
    roles = your_keystone_role:your_flask_role,another_role:your_flask_role2

Once the User object is created and attached to the request object,
it works much in the same way as Flask-Login. The user itself is exposed
via :object:`flask_keystone.current_user`, and several helper
function and decorators exist (most useful of which are
:func:`RaxKeystone.requires_role` and :func:`User.has_role`).

:param app: `flask.Flask` application to which to connect.
:type app: `flask.Flask`
:param str config_group: :class:`oslo_config.cfg.OptGroup` to which
                         to attach.

Note that consistent with the Application Factory method of `flask.Flask`
instantiation, it is possible to pass these parameters either during
__init__, or via an init_app function after instantiation.
"""

import io
import re
import ast
import sys

from os import path

from setuptools import find_packages, setup
from setuptools.command.test import test

here = path.abspath(path.dirname(__file__))

_version_re = re.compile(r'__version__\s+=\s+(.*)')

with open('flask_keystone/__init__.py', 'rb') as f:
    version = str(ast.literal_eval(_version_re.search(
        f.read().decode('utf-8')).group(1)))


class Tox(test):
    """
    TestCommand to run ``tox`` via setup.py.

    Allows running of tox tests via `python setup.py test`.
    """

    def finalize_options(self):
        """
        Finalize options from args.

        Standard Tox args can be passed to `setup.py` test
        as if it were the tox executable.
        """
        test.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        """
        Pass test running off to the Tox `cmdline` construct.

        args can be passed in on the command line as they would to
        the standard Tox executable, like so:

        .. code-block:: bash
            python setup.py test --version

        """
        # import here, cause outside the eggs aren't loaded
        import tox
        errcode = tox.cmdline(self.test_args)
        sys.exit(errcode)


def read(*filenames, **kwargs):
    """
    Read file contents into string.

    Used by setup.py to concatenate long_description.

    :param string filenames: Files to be read and concatenated.
    :rtype: string

    """
    encoding = kwargs.get('encoding', 'utf-8')
    sep = kwargs.get('sep', '\n')
    buf = []
    for filename in filenames:
        if path.splitext(filename)[1] == ".md":
            try:
                import pypandoc
                buf.append(pypandoc.convert_file(filename, 'rst'))
                continue
            except:
                with io.open(filename, encoding=encoding) as f:
                    buf.append(f.read())
        with io.open(filename, encoding=encoding) as f:
            buf.append(f.read())
    return sep.join(buf)


setup(
    name='flask_keystone',
    version=version,
    description=(
        'This project wraps the existing keystone middleware to provide'
        ' courtesy user functions within an API.'
    ),
    long_description=read("README.md"),

    # The project's main homepage.
    url='https://github.com/Rackspace-DOT/flask_keystone',

    # Author details
    author='Rackspace Developers for Operational Tooling',
    author_email='dot@rackspace.com',
    platforms="any",
    install_requires=[
        'Flask',
        'oslo.config',
        'oslo.log',
        'keystonemiddleware',
        'keystoneauth1'
    ],
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',

        'Intended Audience :: Developers',

        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Middleware',
        'Topic :: Software Development :: Libraries :: Python Modules'

        'License :: OSI Approved :: Apache Software License',

        'Operating System :: Unix',
        'Operating System :: POSIX',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.4'
    ],

    keywords=['flask', 'identity', 'auth'],
    tests_require=['tox', 'virtualenv'],
    cmdclass={'test': Tox},

    packages=find_packages(
        exclude=["*.tests", "*.tests.*", "tests.*", "tests"]
    ),
    entry_points={
        'console_scripts': [],
    }
)
