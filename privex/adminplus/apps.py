from collections import OrderedDict
from typing import Iterable, List, Union

from django.apps import AppConfig
from django.apps.registry import Apps
from django.core.exceptions import ImproperlyConfigured
from privex.helpers.common import empty, is_true, inject_items

from privex.adminplus import VERSION
from django.contrib.admin.apps import AdminConfig
from django.conf import settings
import logging

log = logging.getLogger(__name__)

QUIET = is_true(getattr(settings, 'ADMINPLUS_QUIET', False))

# def ap_quiet():
#     return is_true(getattr(settings, 'ADMINPLUS_QUIET', False))


def _app_installed(entry: str) -> bool:
    return entry in settings.INSTALLED_APPS


def _inject_app(entry: str, index: int = None, after: str = None):
    if index is None:
        if after is None:
            raise ValueError("_inject_app expects either 'index' or 'after' to be specified")
        index = settings.INSTALLED_APPS.index(after)
    x = inject_items(items=[entry], dest_list=settings.INSTALLED_APPS, position=index)
    settings.INSTALLED_APPS = x
    return settings.INSTALLED_APPS


def _append_app(entry: str):
    settings.INSTALLED_APPS += [entry]
    return settings.INSTALLED_APPS


def _prepend_app(entry: str):
    settings.INSTALLED_APPS = [entry] + settings.INSTALLED_APPS
    return settings.INSTALLED_APPS


# def _init_app(entry, app_ins: Apps = None):
#     if not app_ins:
#         from django.apps import apps as app_ins
#     if isinstance(entry, AppConfig):
#         app_config = entry
#     else:
#         app_config = AppConfig.create(entry)
#     if app_config.label in app_ins.app_configs:
#         raise ImproperlyConfigured(
#             "Application labels aren't unique, "
#             "duplicates: %s" % app_config.label)
#
#     app_ins.app_configs[app_config.label] = app_config
#     app_config.apps = app_ins


def _reinit_apps(inst_apps: List[str]):
    """
    Resets :mod:`django.apps.apps` and then loads all Django apps listed in ``inst_apps``.
    
    This allows dynamically adding new apps to ``settings.INSTALLED_APPS``, albeit it's not very efficient,
    since :class:`django.apps.registry.Apps` doesn't allow for initialising a singular app.
    
    Example::
        
        >>> from django.conf import settings
        >>> settings.INSTALLED_APPS += ['privex.adminplus.backports']
        >>> _reinit_apps(settings.INSTALLED_APPS)
    
    Based on this SO answer by Gersón Vizquel: https://stackoverflow.com/a/57897422/2648583
    
    :param List[str] inst_apps: A list of installed applications (from ``settings.INSTALLED_APPS``)
    """
    if not QUIET: log.warning(" [!!!] Re-initialising all Django Apps...")
    from django.apps import apps
    apps.app_configs = OrderedDict()
    apps.apps_ready = apps.models_ready = apps.loading = apps.ready = False
    apps.clear_cache()
    apps.populate(inst_apps)
    if not QUIET: log.warning(" [+++] Finished re-initialising.")


def version_eq_gt(min_version: Union[tuple, list], current_version: Union[tuple, list]) -> bool:
    """
    Check that ``current_version`` is either equal to, or greater than ``min_version``.
    
    Examples::
    
        >>> mv = (3, 1)
        >>> version_eq_gt(mv, (3, 0, 0))
        False
        >>> version_eq_gt(mv, (4, 0, 0))
        True
        >>> version_eq_gt(mv, (3, 1, 0))
        True
        >>> version_eq_gt(mv, (3, 3))
        True
        >>> version_eq_gt(mv, (3,))
        False
        >>> version_eq_gt((3, 0, 0), (3,))
        True
    
    :param tuple|list min_version:      The minimum version to check for, as a list/tuple of version segments, e.g. ``(1, 1, 0)``
    :param tuple|list current_version:  The version to check ``min_version`` against, as a list/tuple of version
                                        segments, e.g. ``(1, 1, 1)``
    :return bool version_eq_or_gt: ``True`` if ``current_version`` is equal to or greater than ``min_version``, otherwise ``False``
    """
    v = current_version
    for i, b in enumerate(min_version):
        # If we've reached the end of current_version but min_version still has values left,
        # then we'll assume they're equal only if the current min_version segment is empty (including value 0)
        if (len(v) - 1) < i: return empty(b, True, True)
        
        if v[i] > b: return True   # If the current version segment is higher than the min segment, we're fine.
        if v[i] == b: continue     # If the current version segment is equal, then we should check the next segment.
        if v[i] < b: return False  # If the segment is lower, this version is older than the minimum.
        
    # If we didn't return True or False by now, the version is equal. So return True.
    return True


class PrivexAdminPlusConfig(AppConfig):
    name = 'privex.adminplus'
    verbose_name = 'Privex Django AdminPlus'
    version = VERSION
    django_min_backport = (3, 1)
    
    # def _check_django_version(self):
    #     import django
    #     v = django.VERSION
    #     for i, b in enumerate(self.django_min_backport):
    #         if v[i] > b:   # If the current version segment is higher than the min segment, we're fine.
    #             return True
    #         if v[i] == b:  # If the current version segment is equal, then we should check the next segment.
    #             continue
    #         if v[i] < b:   # If the segment is lower, this version is older than the minimum.
    #             return False
    #     return True
    
    def lwarn(self, msg, *args, **kwargs):
        if QUIET: return
        log.warning(msg, *args, **kwargs)
    
    def lerror(self, msg, *args, **kwargs):
        if QUIET: return
        log.error(msg, *args, **kwargs)

    def linfo(self, msg, *args, **kwargs):
        if QUIET: return
        log.info(msg, *args, **kwargs)
    
    def _handle_backports(self):
        import django
        if version_eq_gt(self.django_min_backport, django.VERSION):
            return True
    
        auto_backport = is_true(getattr(settings, 'AUTO_BACKPORT', True))
    
        if not auto_backport:
            log.debug(" [!!!] settings.AUTO_BACKPORT is false - not checking if backports loaded...")
            return True
    
        if _app_installed('privex.adminplus.backports'):
            log.debug(" [+++] backports already loaded. skipping auto-backport.")
            return True
        
        self.lwarn(" [...] PrivexAdminPlusConfig.ready :: Django version is < 3.1.0 :: Ver is: %s", django.get_version())
        self.lwarn(" [...] 'privex.adminplus.backports' not in INSTALLED_APPS... Dynamically injecting into INSTALLED_APPS ...")
        # settings.INSTALLED_APPS += ['privex.adminplus.backports']
        _prepend_app('privex.adminplus.backports')
        return False
    
    def _setup_admin(self):
        auto_admin = is_true(getattr(settings, 'AUTO_SETUP_ADMIN', True))
        if not auto_admin:
            self.lwarn(" [!!!] settings.AUTO_SETUP_ADMIN is false - not registering privex-adminplus by calling setup_admin(admin)...")
            return False
        from privex.adminplus.admin import setup_admin
        from django.contrib import admin as dj_admin
        setup_admin(dj_admin)
    
    def ready(self):
        """
        When ``privex.adminplus`` is loaded, we run some verification checks to see if we need to auto-load additional applications,
        and automatically register the admin site with Django once we're all ready.
        
          * If ``privex.adminplus.apps.PVXAdmin`` isn't present in ``INSTALLED_APPS``, then we'll inject it into
            INSTALLED_APPS directly below ``privex.adminplus``
            
          * If we're running on an older Django version that requires our backports, then we'll inject ``privex.adminplus.backports``
            into INSTALLED_APPS
            
          * If we had to inject PVXAdmin or backports, then :func:`._reinit_apps` will be called to re-load all apps in INSTALLED_APPS
          
          * Finally, :meth:`._setup_admin` is called, which auto-registers the admin site using :func:`.setup_admin`, so long as
            the user hasn't disabled automatic registration by setting ``AUTO_SETUP_ADMIN=False``
            
        
        """
        need_reload = False
        # Inject privex.adminplus.apps.PVXAdmin into INSTALLED_APPS if it's not present
        if not _app_installed('privex.adminplus.apps.PVXAdmin'):
            self.lerror(" ------------------------------------------------------------------\n")
            self.lerror(" [!!!] 'privex.adminplus.apps.PVXAdmin' is not in your INSTALLED_APPS.")
            self.lerror(" [!!!] To prevent potential issues, and speedup your app's startup time, add 'privex.adminplus.apps.PVXAdmin' "
                        "to INSTALLED_APPS directly after 'privex.adminplus'\n")
            self.lerror(" ------------------------------------------------------------------\n")
            self.lerror(" [+++] Dynamically injecting apps.PVXAdmin into INSTALLED_APPS ...")
            _inject_app('privex.adminplus.apps.PVXAdmin', after='privex.adminplus')
            need_reload = True
            # _init_app('privex.adminplus.apps.PVXAdmin')
        # If we're on an older Django version, inject privex.adminplus.backports into INSTALLED_APPS if it's not present
        bp = self._handle_backports()
        if not bp:
            log.debug(" [!!!] ready(): backports NOT loaded - waiting for re-init before further setup.")
            need_reload = True
        # If we had to inject the PVXAdmin or backports app, then we need to re-initialise the app registry
        if need_reload:
            _reinit_apps(settings.INSTALLED_APPS)
            return super().ready()
        
        # After the app registry re-initialises, or if we didn't need to, then this code will be executed.
        self.linfo(" [+++] ready(): backports are loaded (or don't need to be), calling setup_admin")
        # Automatically register the admin site using setup_admin
        self._setup_admin()
        
        self.linfo(" [+++] %s is ready!", self.__class__.__name__)
        return super().ready()
        

class PVXAdmin(AdminConfig):
    default_site = 'privex.adminplus.admin.CustomAdmin'
    
    def ready(self):
        
        return super().ready()

