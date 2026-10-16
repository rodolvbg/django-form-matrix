"""The demo in Unfold: ``DJANGO_SETTINGS_MODULE=example.settings_unfold``."""

from .settings import *  # noqa: F403
from .settings import INSTALLED_APPS

INSTALLED_APPS = ["unfold", *INSTALLED_APPS]
