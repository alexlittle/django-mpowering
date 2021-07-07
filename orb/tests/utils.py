"""
Utility functions for enhancing the reusability and readability of test code
"""

from __future__ import unicode_literals

import unicodedata
from functools import wraps
from importlib import import_module

import mock
from django.conf import settings
from django.contrib.auth import SESSION_KEY
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory


def remove_control_characters(text):
    """Removes unicode control characters from a string"""
    return "".join(ch for ch in text if unicodedata.category(ch)[0] != "C")


def clean_and_strip(text):
    """Removes unicode control characters and leading/trailing whitespace"""
    return remove_control_characters(text).strip()


def request_factory(factory=None, user=None, userprofile=None, method='GET', **kwargs):
    """A function that returns a request object configured with a user (either
    a provided user or an anonymous user) as well as a session attribute.
    Useful anywhere testing against user state of any kind is required in a
    view.

    Based on this gist: https://gist.github.com/964472
    """
    if factory is None:
        factory = RequestFactory()
    engine = import_module(settings.SESSION_ENGINE)
    request = factory.request(REQUEST_METHOD=method)
    request.session = engine.SessionStore()
    request.session[SESSION_KEY] = getattr(user, 'id', 12)
    request.features = kwargs.get('features', {})
    request.user = user or AnonymousUser()
    if userprofile:
        request.user.userprofile = userprofile
    for key in kwargs:
        setattr(request, "{0}".format(key), kwargs[key])
    return request


def mocked_model(spec_model):
    """
    Returns a Mock that can be used like a related object

    >>> some_mock = mocked_model(MyRelatedModel)
    >>> some_mock.foo = True
    >>> resource = Resource.objects.create(..)
    >>> resource.bar = some_mock

    Without doing this, you'll get errors like:

    ValueError: Cannot assign "<MagicMock id='4554528976'>":
            "User.userprofile" must be a "UserProfile" instance.

    Args:
        spec_model: a model class

    Returns:
        Mock

    """
    model_state = mock.MagicMock()
    model_state.db = 'default'

    mock_profile = mock.MagicMock(spec=spec_model)
    mock_profile._state = model_state
    return mock_profile


class LoginClient(object):
    """
    A context manager and decorator for test methods that logs in a
    user and logs out for the duration of the block/test method.

    As a decorator, should be used on TestCase test methods.

        class SomeTests(TestCase):

            @LoginClient(username="bob", password="pass")
            def test_api(self):
                self.assertEqual(
                    self.client.get("/admin/").status_code,
                    200,
                )

    As a context manager the TestCase must be passed explicitly

        class SomeTests(TestCase):
            def test_something(self):
                with LoginClient(self, username="bob", password="pass"):
                    self.assertEqual(
                        self.client.get("/admin/").status_code,
                        200,
                    )

    """
    def __init__(self, test_case=None, username=None, password=None):
        self.test_case = test_case
        self.username = username
        self.password = password

    def __enter__(self):
        try:
            self.test_case.client.login(username=self.username, password=self.password)
        except AttributeError:
            self.test_case.login(username=self.username, password=self.password)
        return self

    def __exit__(self, *args):
        try:
            self.test_case.client.logout()
        except AttributeError:
            self.test_case.logout()

    def __call__(self, method):
        @wraps(method)
        def wrapper(*args, **kw):
            if self.test_case is None:
                try:
                    self.test_case = args[0]
                except IndexError:
                    raise TypeError("Missing the TestCase instance argument")
            with self:
                return method(*args, **kw)
        return wrapper

login_client = LoginClient  # friendly alias
