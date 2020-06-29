from django.apps import AppConfig
from privex.adminplus import VERSION
from django.contrib.admin.apps import AdminConfig


class PrivexAdminPlusConfig(AppConfig):
    name = 'adminplus'
    version = VERSION


class PVXAdmin(AdminConfig):
    default_site = 'privex.adminplus.admin.CustomAdmin'

