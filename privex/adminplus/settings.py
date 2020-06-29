"""
Settings file used for unit tests
"""
from privex.loghelper import LogHelper
import os
from os import getenv as env
import logging

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEBUG = False
SECRET_KEY = 'NotApplicable'

LOG_FORMATTER = logging.Formatter('[%(asctime)s]: %(name)-55s -> %(funcName)-20s : %(levelname)-8s:: %(message)s')

LOG_LEVEL = logging.WARNING

_lh = LogHelper('adminplus', formatter=LOG_FORMATTER, handler_level=LOG_LEVEL)

_lh.add_console_handler()

INSTALLED_APPS = ['django_nose', 'adminplus']

DATABASES = {}

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

if env('DB_BACKEND', 'sqlite') in ['sqlite', 'sqlite3']:
    DATABASES = dict(default=dict(
        ENGINE='django.db.backends.sqlite3',
        NAME=os.path.join(BASE_DIR, env('DB_PATH', 'db.sqlite3'))
    ))
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.' + env('DB_BACKEND'),
            'NAME': env('DB_NAME', 'adminplus'),
            'USER': env('DB_USER', 'adminplus'),
            'PASSWORD': env('DB_PASS', ''),
            'HOST': env('DB_HOST', 'localhost'),
        }
    }
