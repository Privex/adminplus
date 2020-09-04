import copy
import re
import threading
from inspect import isclass
from typing import List, Optional, Union, Dict
from django.contrib import admin
from django.db.models import Model
from django.http import HttpRequest
from django.urls import URLResolver, URLPattern, path, reverse
from django.views import View
from privex.helpers import camel_to_snake, empty, human_name, empty_if, DictObject
import logging

log = logging.getLogger(__name__)

STORE = DictObject(is_setup=False)

_RE_ANGLE_PARAMS = re.compile(r'<[a-zA-Z0-9_:-]+>')
_RE_BRACKET_PARAMS = re.compile(r'\(\?P.*\)')

URL_TYPES = Optional[Union[str, List[str], Dict[str, str]]]

PATH_TYPES = Union[URLResolver, URLPattern]


class CustomAdmin(admin.AdminSite):
    """
    To allow for custom admin views, we override AdminSite, so we can add custom URLs, among other things.
    """
    custom_urls: List[PATH_TYPES] = []
    custom_url_map: Dict[str, DictObject] = DictObject()
    
    _ct_admins = {}
    _sngl_lock = threading.Lock()
    
    def __init__(self, name='custom_admin'):
        # self.custom_urls = []
        # self.custom_url_map = DictObject()
        super().__init__(name)
    
    @classmethod
    def admin_singleton(cls, singleton_name='default', *args, **kwargs):
        with cls._sngl_lock:
            n = singleton_name
            if empty(cls._ct_admins.get(n, None)):
                log.debug("Creating new CustomAdmin singleton '%s'... args: %s | kwargs: %s", n, args, kwargs)
                cls._ct_admins[n] = cls(*args, **kwargs)
        return cls._ct_admins[n]
    
    def get_urls(self) -> List[PATH_TYPES]:
        """Returns a list of merged URLs by combining :meth:`.get_urls` via superclass with :attr:`.custom_urls`"""
        _urls = super(CustomAdmin, self).get_urls()
        urls = self.custom_urls
        return _urls + urls
    
    @property
    def custom_urls_reverse(self):
        """
        Iterates over :attr:`.custom_url_map` and ensures all URL dictionaries have a ``url`` field, which
        points to their reversed URL based on their ``name``
        """
        for _, obj in self.custom_url_map.items():
            if obj.hidden:
                continue
            if 'url' not in obj:
                obj['url'] = reverse(f"admin:{obj.name}")
        
        return self.custom_url_map
    
    # def each_context(self, request):
    #     ctx = super().each_context(request)
    #     ctx['custom_urls'] = self.custom_urls_reverse
    #     return ctx
    
    def url_is_registered(self, url: str, fail=False) -> bool:
        """Returns ``True`` if the URL ``url`` exists within :attr:`.custom_urls` otherwise ``False``"""
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
    def detect_human(obj: Union[callable, View, object, type]) -> Optional[str]:
        """
        Extract a humanised name from an object::
        
            >>> class ExampleView:
            ...     pass
            >>> CustomAdmin.detect_human(ExampleView)
            'Example View'
            >>> CustomAdmin.detect_human(ExampleView())
            'Example View'
            
            >>> def another_example():
            ...     pass
            >>> CustomAdmin.detect_human(another_example)
            'Another Example'
            
            >>> class HasAName:
            ...     pvx_human_name = 'This class has a name'
            >>> CustomAdmin.detect_human(HasAName)
            'This class has a name'
        
        
        :param obj: The object to extract the human name from
        :return str|None name: The human name of the object, or ``None`` if failed to detect it.
        """
        if hasattr(obj, 'pvx_human_name') and not empty(obj.pvx_human_name):
            return obj.pvx_human_name
        return human_name(obj)
    
    @staticmethod
    def detect_name(obj: Union[callable, View, object, type]) -> Optional[str]:
        """
        Extract a snake-case name from a given object (class, instance, function or other type)::
        
            >>> class ExampleView: pass
            >>> CustomAdmin.detect_name(ExampleView)
            'example_view'
            >>> CustomAdmin.detect_name(ExampleView())
            'example_view'
            
            >>> def anotherExample(): pass
            >>> CustomAdmin.detect_name(anotherExample)
            'another_example'
            
            >>> class HasAName:
            ...     pvx_name = 'hello_world'
            >>> CustomAdmin.detect_name(HasAName)
            'hello_world'
        
        :param obj: The object to extract the snake-case name from
        :return str|None name: The snake-case name of the object, or ``None`` if failed to detect it.
        """
        if hasattr(obj, 'pvx_name') and not empty(obj.pvx_name):
            return obj.pvx_name
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
    
    def add_url(self, view_obj, url: URL_TYPES, human: str = None, hidden: bool = False, name: str = None, **kwargs) \
            -> Optional[List[PATH_TYPES]]:
        """
        Register a custom admin view with :class:`.CustomAdmin`
        
        **URL Types**:
            
            With :class:`.str` form, a single URL will be registered under ``/admin/`` with that URL.
            
            **In str form**::
                
                >>> CustomAdmin().add_url(View(), 'someview/')
            
            With :class:`.list` form, simply specify a list of string URLs. Each URL will be given a name with
            a number appended to the end (based on URL position). For the below example, assuming this was a function
            view named ``my_view``, then the first URL would get the name ``my_view_1``, and the second ``my_view_2``.
            
            **In list form**::
                
                >>> CustomAdmin().add_url(View(), ['myview/', 'myview/<int:id>/'])
            
            With :class:`.dict` form, URLs are specified as keys, mapped to a unique name for the URL. This allows you
            to specify arbitrary names for each URL, which will be stable (under the ``admin:`` prefix), allowing you
            to safely reference them from within templates, e.g. ``{% url 'admin:user_info_by_username' user.username %}``
            
            **In dict form**::
            
                >>> CustomAdmin().add_url(View(), {
                ...     'user_info/': 'user_info_index',
                ...     'user_info/<str:username>': 'user_info_by_username'
                ... })
            
            
        
        :param callable|View view_obj: A Django view (function-based or class-based) to register a URL for
        
        :param str url: An individual URL as a string to register the view under
        
        :param List[str] url: With :class:`.list` form, simply specify a list of string URLs. Each URL will be given a name with
                              a number appended to the end (based on URL position). For the below example, assuming this was a function
                              view named ``my_view``, then the first URL would get the name ``my_view_1``, and the second ``my_view_2``.
                              
                              In list form: ``['myview/', 'myview/<int:id>/']``
        
        :param dict url: With :class:`.dict` form, URLs are specified as keys, mapped to a unique name for the URL. This allows you
                         to specify arbitrary names for each URL, which will be stable (under the ``admin:`` prefix), allowing you
                         to safely reference them from within templates, e.g. ``{% url 'admin:user_info_by_username' user.username %}``
                        
                         In dict form: ``{'user_info/': 'user_info_index', 'user_info/<str:username>': 'user_info_by_username'}``
        
        :param str human: A human readable link name/title for the page - which would be shown in the admin panel
        :param bool hidden: (Default: ``False``) Whether or not to hide this URL from the admin page list
        :param str name: A unique URL name for referencing with Django URL name lookups
        :param kwargs: Additional options
        
        :keyword bool hide_extras: (Default: ``True``) When more than one URL is specified in ``url`` using a list/dict, if
                                    hide_extra is True, then only the first URL in the list/dict of URLs will use the
                                    user-specified ``hidden`` parameter. The rest of the URLs will have ``hidden=True``
        
        :keyword bool hide_params: If hide_params is True, URLs which contain route parameters (e.g. ``<str:username>``) will be hidden
                                   by default, to prevent errors caused by trying to reverse their URL in the admin panel custom view list.
        
        :return List[PATH_TYPES] custom_urls: If successful, returns the current list of URLs from :attr:`.custom_urls`
        """
        if empty(view_obj):
            log.error(
                f"view_obj is empty, cannot register! url: {url} | human: {human} | hidden: {hidden} | name: {name} | kwargs: {kwargs}"
            )
            return None
        url = camel_to_snake(view_obj.__name__) + '/' if empty(url) else url
        # When more than one URL is specified in ``url`` using a list/dict, if hide_extra is True, then only the first URL
        # in the list/dict of URLs will use the user-specified ``hidden`` parameter.
        # The rest of the URLs will have hidden=True
        hide_extra = kwargs.get('hide_extra', True)
        # If hide_params is True, URLs which contain route parameters (e.g. ``<str:username>``) will be hidden by default, to prevent
        # errors caused by trying to reverse their URL in the admin panel custom view list.
        hide_params = kwargs.get('hide_params', True)
        
        name = name if not empty(name) else self.detect_name(view_obj)
        human = human if not empty(human) else self.detect_human(empty_if(view_obj, name))
        
        ####
        # Handle URLs specified as a list
        ####
        if isinstance(url, list):
            url = [u for u in list(url) if not self.url_is_registered(u)]
            name_number = 1
            orig_name = name
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
            # if hasattr(view_obj, '__name__'):
            #     name = camel_to_snake(view_obj.__name__)
            # else:
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
        """
        This is a wrapper method which routes calls from :func:`.register_url` / :func:`.ct_register` to the correct
        method, depending on whether a Django :class:`.ModelAdmin` view is being registered, or whether
        a custom user function/class admin view is being registered.
        
        See :meth:`.add_url` for full docs. Most params are just passed through to :meth:`.add_url`.
        
        :param callable|type|Type[View]|View view: The function/class view to register, or a :class:`.ModelAdmin`
        :param Model model: Only applicable when registering :class:`.ModelAdmin`'s
        :param str|list|dict url: The URL or multiple URLs to register ``view`` under
        :param str human: The human friendly name for the view - displayed on the admin index list of custom views
        :param bool hidden: (Default: ``False``) Whether or not to hide this URL from the admin page list
        :param str name: A unique URL name for referencing with Django URL name lookups
        :param kwargs:
        :return:
        """
        if url is None:
            if isclass(view) and issubclass(view, admin.ModelAdmin):
                if empty(model):
                    raise ValueError(f"Wrapped ModelAdmin {view.__name__} but no model passed to ct_register...")
                # log.debug("Registering ModelAdmin view: %s", view.__name__)
                self.register(model, view)
                return
            raise ValueError("Wrapped classes without url's must subclass admin.ModelAdmin.")
        
        self.add_url(view_obj=view, url=url, human=human, hidden=hidden, name=name, **kwargs)


ctadmin = CustomAdmin.admin_singleton()


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

CONTEXT_PROCESSORS = (
    'privex.adminplus.admin.pvx_context_processor',
)


def pvx_context_processor(request: HttpRequest) -> dict:
    """
    A simple Django **Template Context Processor** which allows us to ensure that various different
    variables are available from within all views' templates, without having to modify/replace each view
    to inject the context.
    """
    ctx = dict(
        custom_urls=ctadmin.custom_urls_reverse,
        custom_url_map=ctadmin.custom_url_map,
        ctadmin=ctadmin
    )
    # log.debug("pvx_context_processor :: URL = %s", request.get_full_path())
    # log.debug("pvx_context_processor :: PATH = %s ", request.path)
    # log.debug("pvx_context_processor :: HEADERS = %s ", request.headers)
    # log.debug("pvx_context_processor :: Context = %s ", ctx)
    # log.debug(" --------- pvx_context_processor --------- ")
    return ctx
    

_DEFAULT_TEMPLATE = dict(
    BACKEND='django.template.backends.django.DjangoTemplates', DIRS=[], APP_DIRS=True,
    OPTIONS=dict(context_processors=[
        'django.template.context_processors.debug', 'django.template.context_processors.request',
        'django.contrib.auth.context_processors.auth', 'django.contrib.messages.context_processors.messages',
    ])
)
"""
This is the usual :class:`.dict` contained within ``settings.TEMPLATES`` by default.

If something seems wrong with ``settings.TEMPLATES`` when running :func:`.inject_context_processors`,
``_DEFAULT_TEMPLATE`` is used to reset ``settings.TEMPLATES`` back to it's default value.
"""


def inject_context_processors() -> List[dict]:
    """
    Injects our :attr:`.CONTEXT_PROCESSORS` into each template configuration's ``context_processors`` within ``settings.TEMPLATES``
    
    If ``settings.TEMPLATES`` is empty or otherwise broken/invalid, then this function will automatically reset it's
    value to a list containing the standard default DjangoTemplates config (``[_DEFAULT_TEMPLATE]`` using :attr:`._DEFAULT_TEMPLATE`)
    """
    from django.conf import settings

    settings.TEMPLATES = getattr(settings, 'TEMPLATES', [])
    # If TEMPLATES is empty (whether None, "", (), [], {} etc.), then we need to reset it to the default,
    # which is a list containing just the default Django template dict
    if empty(settings.TEMPLATES, True, True):
        settings.TEMPLATES = [copy.deepcopy(_DEFAULT_TEMPLATE)]
    
    new_templates = []
    
    # We need to iterate over each dict within TEMPLATES, so we can adjust ['OPTIONS']['context_processors'] as needed.
    for t in settings.TEMPLATES:
        t: dict
        log.debug("[inject_context_processors] Checking template setting: %s", t)
        opts = t['OPTIONS'] = t.get('OPTIONS', {})
        opts['context_processors'] = opts.get('context_processors', [])
        # Check whether all processors in CONTEXT_PROCESSORS exist. If any processors are missing, append just the missing processors
        for cp in CONTEXT_PROCESSORS:
            if cp in opts['context_processors']:
                log.debug("[inject_context_processors] SKIP - Processor '%s' already in processors: %s", cp, opts['context_processors'])
                continue
            log.debug("[inject_context_processors] Adding processor '%s' to processors: %s", cp, opts['context_processors'])
            opts['context_processors'].append(cp)
        # To be safe, we append the modified template dict to a new list, which we'll use to overwrite settings.TEMPLATES
        new_templates.append(t)
    # Overwrite settings.TEMPLATES with our updated template dicts, with our context processors injected
    settings.TEMPLATES = new_templates
    
    return settings.TEMPLATES


def setup_admin(old_admin, discover=True, inject_context=True, force=False) -> CustomAdmin:
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
    :param bool inject_context: If ``True``, runs :func:`.inject_context_processors` after registration is finished, which will
                                automatically add any missing :attr:`.CONTEXT_PROCESSORS` to ``settings.TEMPLATE_CONTEXT_PROCESSORS``
    """
    if STORE.is_setup:
        if not force:
            return admin.site
        log.warning("Privex AdminPlus setup_admin was already called and setup successfully - but 'force' is True. "
                    "Setting up admin again, despite STORE.is_setup is True...")
    
    old = old_admin.site
    
    admin.site = ctadmin
    # noinspection PyProtectedMember
    admin.site._registry = copy.copy(old._registry)
    admin.sites.site = admin.site

    if inject_context:
        inject_context_processors()
    
    if discover:
        admin.autodiscover()
    
    STORE.is_setup = True
    
    return admin.site

