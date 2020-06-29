import os
from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "privex.adminplus.settings")


class TestAdminPlus(TestCase):
    pass


if __name__ == "__main__":
    import dotenv
    import unittest
    from django.conf import settings

    dotenv.read_dotenv()
    settings.configure()
    unittest.main()


