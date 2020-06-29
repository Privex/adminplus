import copy
from inspect import isclass
from typing import List, Union, Dict
from django.contrib import admin
from django.db.models import Model
from django.urls import URLResolver, URLPattern, path, reverse
from privex.helpers import camel_to_snake, empty, human_name, empty_if, DictObject
import logging

log = logging.getLogger(__name__)


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
        log.debug("Parent URLs: %s || Custom URLs: %s", _urls, urls)
        return _urls + urls
    
    @property
    def custom_urls_reverse(self):
        for name, obj in self.custom_url_map.items():
            if 'url' not in obj:
                obj['url'] = reverse(f"admin:{name}")
        
        return self.custom_url_map
    
    def each_context(self, request):
        ctx = super().each_context(request)
        ctx['custom_urls'] = self.custom_urls_reverse
        return ctx
    
    def add_url(self, view_obj, url: str, human: str = None, hidden: bool = False, name: str = None, **kwargs):
        for u in self.custom_urls:
            if url is None: break
            # noinspection PyProtectedMember
            if u.pattern._route == url:
                log.warning("URL %s is already registered with CustomAdmin... Not registering!", url)
                return self.custom_urls
        
        name = camel_to_snake(view_obj.__name__) if empty(name) else name
        view_obj = view_obj.as_view() if isclass(view_obj) else view_obj
        
        self.custom_urls.append(
            path(url, view_obj, name=name)
        )
        self.custom_url_map[name] = DictObject(
            name=name,
            route=url,
            human=empty_if(human, human_name(name)),
            hidden=hidden
        )
        return self.custom_urls
    
    def wrap_register(self, view, model: Model = None, url: str = None, human: str = None, hidden: bool = False, name: str = None,
                      **kwargs):
        if url is None:
            if isclass(view) and issubclass(view, admin.ModelAdmin):
                if empty(model):
                    raise ValueError(f"Wrapped ModelAdmin {view.__name__} but no model passed to ct_register...")
                log.debug("Registering ModelAdmin view: %s", view.__name__)
                self.register(model, view)
                return
            raise ValueError("Wrapped classes without url's must subclass admin.ModelAdmin.")
        
        self.add_url(view_obj=view, url=url, human=human, hidden=hidden, name=name, **kwargs)


ctadmin = CustomAdmin()


def ct_register(model: Model = None, url: str = None, human: str = None, hidden: bool = False, name: str = None, **kwargs):
    """
    Generally not needed, as :func:`django.contrib.admin.decorators.register` should still work.
    
    Works the same as ``@admin.register(MyModel)`` but registers the view + model onto :attr:`.ctadmin`
    """
    def _decorator(cls):
        ctadmin.wrap_register(
            cls, model=model, url=url, human=human, hidden=hidden, name=name, **kwargs
        )
    
    return _decorator


def register_url(url: str = None, human: str = None, hidden: bool = False, name: str = None, **kwargs):
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
            url=camel_to_snake(cls.__name__) if empty(url) else url,
            human=human, hidden=hidden, name=name, **kwargs
        )
    
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
    admin.register = ct_register
    admin.sites.site = admin.site
    if discover:
        admin.autodiscover()
    
    return admin.site

