import copy
import re
from inspect import isclass
from typing import List, Optional, Union, Dict
from django.contrib import admin
from django.db.models import Model
from django.urls import URLResolver, URLPattern, path, reverse
from privex.helpers import camel_to_snake, empty, human_name, empty_if, DictObject
import logging

log = logging.getLogger(__name__)

_RE_ANGLE_PARAMS = re.compile(r'<[a-zA-Z0-9_:-]+>')
_RE_BRACKET_PARAMS = re.compile(r'\(\?P.*\)')

URL_TYPES = Optional[Union[str, List[str], Dict[str, str]]]


class CustomAdmin(admin.AdminSite):
    """
    To allow for custom admin views, we override AdminSite, so we can add custom URLs, among other things.
    """
    custom_urls: List[Union[URLResolver, URLPattern]]
    custom_url_map: Dict[str, DictObject]
    
    def __init__(self, name='custom_admin'):
        self.custom_urls = []
        self.custom_url_map = DictObject()
        super().__init__(name)
    
    def get_urls(self):
        _urls = super(CustomAdmin, self).get_urls()
        urls = self.custom_urls
        return _urls + urls
    
    @property
    def custom_urls_reverse(self):
        for _, obj in self.custom_url_map.items():
            if obj.hidden:
                continue
            if 'url' not in obj:
                obj['url'] = reverse(f"admin:{obj.name}")
        
        return self.custom_url_map
    
    def each_context(self, request):
        ctx = super().each_context(request)
        ctx['custom_urls'] = self.custom_urls_reverse
        return ctx
    
    def url_is_registered(self, url: str, fail=False):
        if url is None:
            return False
        for u in self.custom_urls:
            # noinspection PyProtectedMember
            if u.pattern._route == url:
                log.warning("URL %s is already registered with CustomAdmin... Not registering!", url)
                if fail:
                    raise FileExistsError(f"URL '{url}' is already registered with CustomAdmin!")
                return True
        return False
    
    @staticmethod
    def detect_name(obj):
        if hasattr(obj, 'pvx_human_name') and not empty(obj.pvx_human_name):
            return obj.pvx_human_name
        elif hasattr(obj, '__name__'):
            return camel_to_snake(obj.__name__)
        elif hasattr(obj, '__class__') and hasattr(obj.__class__, '__name__'):
            return camel_to_snake(obj.__class__.__name__)
        elif hasattr(obj, 'name') and not empty(obj.name):
            return obj.name

        log.warning("No name specified by user for view, and cannot infer from view_obj.__name__ or other attributes... obj: %s", obj)
        return None
    
    @staticmethod
    def regex_has_params(url: str) -> bool:
        """Check if a URL contains view parameters"""
        if _RE_ANGLE_PARAMS.search(url) is not None:
            # log.debug("URL '%s' contains angle bracket (<str:example>) parameters", url)
            return True
        if _RE_BRACKET_PARAMS.search(url) is not None:
            # log.debug("URL '%s' contains round bracket ( (?P<x>()) ) parameters", url)
            return True
        return False
    
    def add_url(self, view_obj, url: URL_TYPES, human: str = None, hidden: bool = False, name: str = None, **kwargs):
        if empty(view_obj):
            log.error(
                f"view_obj is empty, cannot register! url: {url} | human: {human} | hidden: {hidden} | name: {name} | kwargs: {kwargs}"
            )
            return None
        # When more than one URL is specified in ``url`` using a list/dict, if hide_extra is True, then only the first URL
        # in the list/dict of URLs will use the user-specified ``hidden`` parameter.
        # The rest of the URLs will have hidden=True
        hide_extra = kwargs.get('hide_extra', True)
        # If hide_params is True, URLs which contain route parameters (e.g. ``<str:username>``) will be hidden by default, to prevent
        # errors caused by trying to reverse their URL in the admin panel custom view list.
        hide_params = kwargs.get('hide_params', True)
        
        ####
        # Handle URLs specified as a list
        ####
        if isinstance(url, list):
            url = [u for u in list(url) if not self.url_is_registered(u)]
            name_number = 1
            orig_name = name if not empty(name) else self.detect_name(view_obj)
            orig_hidden = hidden
            for u in url:
                if name_number > 1:
                    name = f"{orig_name}_{name_number}"
                    if hide_extra:
                        hidden = True
                if self.regex_has_params(u) and hide_params:
                    hidden = True

                self.add_url(view_obj, url=u, human=human, hidden=hidden, name=name, **kwargs)
                name_number += 1
                hidden = orig_hidden
            
            return self.custom_urls
        ####
        # Handle URLs specified as a dict of url:name
        ####
        elif isinstance(url, dict):
            # url = {u: n for u, n in dict(url).items() if not self.url_is_registered(u)}
            orig_hidden = hidden
            name_number = 1
            for u, n in url.items():
                if self.url_is_registered(u):
                    continue
                if name_number > 1 and hide_extra:
                    hidden = True
                if self.regex_has_params(u) and hide_params:
                    hidden = True
                self.add_url(view_obj, url=u, human=human, hidden=hidden, name=n, **kwargs)
                name_number += 1
                hidden = orig_hidden
            return self.custom_urls
        ####
        # Handle a plain string URL
        ####
        elif isinstance(url, str):
            if self.url_is_registered(url):
                return self.custom_urls

        ####
        # String URL handling continued
        ####
        if empty(name):
            if hasattr(view_obj, '__name__'):
                name = camel_to_snake(view_obj.__name__)
            else:
                log.warning("No name specified by user for view, and cannot infer from view_obj.__name__ ...")
                name = None
        
        # If a URL contains Django route parameters e.g. ``<str:example>``, it's best to hide them by default, otherwise
        # they'll cause issues when they're reversed in .custom_urls_reverse
        if self.regex_has_params(url) and hide_params:
            hidden = True
        
        # Class-based views need to be registered using .as_view()
        view_obj = view_obj.as_view() if isclass(view_obj) else view_obj
        
        self.custom_urls.append(
            path(url, view_obj, name=name)
        )
        self.custom_url_map[url] = DictObject(
            name=name,
            route=url,
            human=empty_if(human, human_name(empty_if(name, "unknown_custom_view"))),
            hidden=hidden
        )
        return self.custom_urls
    
    def wrap_register(self, view, model: Model = None, url: URL_TYPES = None, human: str = None, hidden: bool = False, name: str = None,
                      **kwargs):
        if url is None:
            if isclass(view) and issubclass(view, admin.ModelAdmin):
                if empty(model):
                    raise ValueError(f"Wrapped ModelAdmin {view.__name__} but no model passed to ct_register...")
                # log.debug("Registering ModelAdmin view: %s", view.__name__)
                self.register(model, view)
                return
            raise ValueError("Wrapped classes without url's must subclass admin.ModelAdmin.")
        
        self.add_url(view_obj=view, url=url, human=human, hidden=hidden, name=name, **kwargs)


ctadmin = CustomAdmin()


def ct_register(model: Model = None, url: URL_TYPES = None, human: str = None, hidden: bool = False, name: str = None, **kwargs):
    """
    Generally not needed, as :func:`django.contrib.admin.decorators.register` should still work.
    
    Works the same as ``@admin.register(MyModel)`` but registers the view + model onto :attr:`.ctadmin`
    """
    def _decorator(cls):
        ctadmin.wrap_register(
            cls, model=model, url=url, human=human, hidden=hidden, name=name, **kwargs
        )
        return cls
    
    return _decorator


def register_url(url: URL_TYPES = None, human: str = None, hidden: bool = False, name: str = None, **kwargs):
    """
    Register a custom admin view with PVXAdmin
    
    **Examples**
    
    First we import some things::
      
        >>> from django.http import HttpResponse
        >>> from django.views import View
        >>> from privex.adminplus.admin import register_url
        
    We'll register this function-based view ``example`` under the admin prefix with the URL ``hello/``::
        
        >>> @register_url('hello/')
        >>> def example(request):
        >>>     return HttpResponse(b"hello world!")
    
    We can also register class-based views - this time we won't specify a URL. The URL will be auto-generated based on the
    class name, which should result in something like ``/admin/my_view`` (assuming the admin is mounted on ``/admin``)::
    
        >>> @register_url()
        >>> class MyView(View):
        ...     def get(self):
        ...         return HttpResponse(b"this is a class based view")
    
    You can also hide views from the auto-generated custom admin views list, and you can override their "human friendly name" which
    is shown on the custom admin views list on the admin index page::
        
        >>> @register_url(human="Lorem Ipsum Dolor Generator")
        >>> def lorem(request):
        >>>     return HttpResponse(b"lorem ipsum dolor")
        
        >>> @register_url(hidden=True)
        >>> def some_internal_view(request):
        ...     return HttpResponse(b"this is an internal view, not for just browsing!")
    
    
    """
    def _decorator(cls):
        ctadmin.wrap_register(
            cls,
            url=camel_to_snake(cls.__name__) + '/' if empty(url) else url,
            human=human, hidden=hidden, name=name, **kwargs
        )
        return cls
    
    return _decorator


# Alias for somewhat basic drop-in compatibility when used as a replacement for django-adminplus
register_view = register_url


def setup_admin(old_admin, discover=True):
    """
    Register Privex AdminPlus to replace the default Django admin site
    
        >>> from django.contrib import admin
        >>> from privex.adminplus.admin import setup_admin
        >>>
        >>> # Register Privex AdminPlus to replace the default Django admin site
        >>> # This will automatically run admin.autodiscover(), so you don't need to call both setup_admin() and admin.autodiscover()
        >>> setup_admin(admin)
    
    :param django.contrib.admin old_admin: This should be a reference to :mod:`django.contrib.admin`
    :param bool discover: If ``True``, runs ``admin.autodiscover()`` after registration is finished
    """
    old = old_admin.site
    
    admin.site = ctadmin
    # noinspection PyProtectedMember
    admin.site._registry = copy.copy(old._registry)
    # admin.register = ct_register
    admin.sites.site = admin.site
    if discover:
        admin.autodiscover()
    
    return admin.site

