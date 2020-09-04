from django.apps import AppConfig
from privex.adminplus import VERSION


class PrivexBackportsConfig(AppConfig):
    name = 'privex.adminplus.backports'
    version = VERSION
    verbose_name = 'Privex AdminPlus Django Backports'

