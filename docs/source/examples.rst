.. _Example Usages:

##############
Example Usages
##############

.. Attention:: If you haven't installed the ``privex-adminplus`` Python package yet, or if you've blindly installed it
               without knowing you need to **enable it and register it with your app and admin system**...

               Then you should go to the :ref:`Installation` page - which shows you how to install Privex AdminPlus,
               as well as how to correctly register it with your Django application.


Basic usage
===========

The :func:`.register_url` decorator is very easy to use, and very flexible.

Using Privex AdminPlus, you can write custom Django views for the admin panel just like you would write views
in your ``views.py``, but instead of needing to register their URL in ``urls.py``, you can just wrap them
with :func:`.register_url` to add them to the URL routing, and they'll also automatically show up
on the admin index page.

Below are **three basic examples**, showing a very simple function-based view, a class-based view, and a more
powerful / more magical :class:`.TemplateView` generic view which would simply render the template ``admin/static_page.html``


.. code-block:: python

    from privex.adminplus.admin import register_url
    from django.http import HttpResponse
    from django.views.generic import TemplateView
    from django.views import View

    # This would result in the url '{admin_prefix}/another_test' and the human name 'Another Test'
    @register_url()
    def another_test(request):
        return HttpResponse(b"another test view")

    # This would result in the url '{admin_prefix}/class_view_test' and the human name 'Class View Test'
    @register_url()
    class ClassViewTest(View):
        def get(self, *args, **kwargs):
            return HttpResponse(b"this is a class view")

    # This would result in the url '{admin_prefix}/some_static_page' and the human name 'Some Static Page'
    @register_url()
    class SomeStaticPage(TemplateView):
        template_name = "admin/static_page.html"

Customising your view registration (custom url, name, human name)
=================================================================

.. code-block:: python

    # URL: {admin_prefix}/example/    Name: admin:some_static_page     Human: Some Static Page
    @register_url('example/')
    class SomeStaticPage(TemplateView):
        template_name = "admin/static_page.html"

    # URL: {admin_prefix}/other/    Name: admin:other     Human: Other Page
    @register_url('other/', name='other', human='Other Page')
    class SomeOtherPage(TemplateView):
        template_name = "admin/other_page.html"

    # URL: {admin_prefix}/account/<str:username>    Name: admin:view_account     Human: N/A
    # Because the URL has a parameter in it, this view will be hidden by default, meaning it won't be shown
    # in the "Custom Pages" list on the admin panel, since you can't just navigate to it without a username param.
    @register_url('account/<str:username>/', name='view_account')
    def show_account_view(request, username: str):
        u = User.objects.get(username=username)
        return JsonResponse(dict(
            username=u.username, id=u.id, email=u.email,
            first_name=u.first_name, last_name=u.last_name
        ))


Registering views without using decoration
==========================================

.. code-block:: python

    from privex.adminplus.admin import register_url, CustomAdmin
    from django.http import HttpResponse
    from django.views.generic import TemplateView
    from django.contrib import admin

    ct: CustomAdmin = admin.site

    def view_generator(template: str):
        class _GenView(TemplateView):
            template_name = template

        return _GenView

    GV = view_generator('admin/my_view.html')
    # Using admin.site (ct), we can manually register GV to a URL by calling add_url
    ct.add_url(GV, 'some_view/', name='someview', human='Some View')

    # Alternatively just wrap the class using the normal register_url decorator as a function
    # The first call layer takes the decorator arguments for register_url, i.e. url, name, human name etc.
    # The second call layer is the view (class or function) to wrap with the decorator. In this case, we're wrapping the class 'GV'
    GV = register_url('some_view/', name='someview', human='Some View')(GV)


Registering views with multiple URLs / URLs with parameters
===========================================================

.. code-block:: python

    from django.contrib.auth.models import User
    from django.http import JsonResponse, HttpRequest
    from privex.adminplus.admin import register_url
    # You can specify multiple URLs as a list.
    # By default, all URLs other than the first one specified will be set as hidden=False - to avoid duplicate
    # custom view entries in the admin panel
    @register_url(['user_info/', 'user_info/<str:username>'])
    def user_info(request: HttpRequest, username=None):
        if username:
            u = User.objects.filter(username=username).first()
            return JsonResponse(dict(id=u.id, username=u.username, first_name=u.first_name, last_name=u.last_name))
        return JsonResponse(dict(error=True, message="no username in URL"))

    # If you want the URLs to have stable URL names, you can pass the URLs as a dictionary of `url: name` instead,
    # which will register the URLs under the given names.
    # NOTE: Just like when passing a list, only the first item in the dictionary will have hidden=False
    @register_url({
        'user_info/': 'user_info_index',
        'user_info/<str:username>': 'user_info_by_username'
    })
    def user_info(request: HttpRequest, username=None):
        if username:
            u = User.objects.filter(username=username).first()
            return JsonResponse(dict(id=u.id, username=u.username, first_name=u.first_name, last_name=u.last_name))
        return JsonResponse(dict(error=True, message="no username in URL"))


Disable hiding extra URLs
=========================

When more than one URL is specified in ``url`` using a list/dict, if hide_extra is True, then only the first URL
in the list/dict of URLs will use the user-specified ``hidden`` parameter.
The rest of the URLs will have ``hidden=True``

To disable automatically hiding "extra" URLs, pass hide_extra=False like so:

.. code-block:: python

    @register_url(['hello/world/', 'hello/lorem', 'hello/ipsum'], hide_extra=False)
    def multi_urls(request):
        pass


Disable hiding URLs with parameters
===================================

If hide_params is True, URLs which contain route parameters (e.g. ``<str:username>``) will be hidden by default, to prevent
errors caused by trying to reverse their URL in the admin panel custom view list.

To disable automatically hiding URLs which contain route parameters, pass ``hide_params=False`` like so:

.. code-block:: python

    @register_url('account/<str:username>/', name='view_account', hide_params=False)
    def show_account_view(request, username: str):
        u = User.objects.get(username=username)
        return JsonResponse(dict(
            username=u.username, id=u.id, email=u.email,
            first_name=u.first_name, last_name=u.last_name
        ))


