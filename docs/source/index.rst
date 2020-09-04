.. _Privex Django Admin Plus documentation:



Privex Django AdminPlus (privex-adminplus) documentation
=========================================================

.. image:: https://www.privex.io/static/assets/svg/brand_text_nofont.svg
   :target: https://www.privex.io/
   :width: 400px
   :height: 400px
   :alt: Privex Logo
   :align: center

Welcome to the documentation for `Privex's Django Admin Plus`_ - an open source Python 3 Django App package,
which allows you to add **custom views** to the Django admin panel, and have them appear on the admin index
with a link, so you can easily navigate to your custom views.

The :func:`.register_url` decorator - which is the recommended (and easiest) way to register your custom admin views,
is **extremely flexible**. It can **automatically interpolate a sane URL, route name, and human name** (for the link title in
the admin index) from a class or function-based view, saving you time from having to manually define URLs, route names,
and titles for your custom pages.

If you'd rather define a URL, name, human name etc. for your view, you're able to supply them as arguments / kwargs
to :func:`.register_url` as needed. Anything that isn't specified explicitly will be inferred from the name of the
function/class view.

This project has been confirmed to work with **Django 2.2, 3.0, and 3.1** - using **Python 3.7 and 3.8**. The minimum python
version is **Python 3.6**, while this app may also work on older Django versions.

When new Django versions are released, if there are breaking changes to the admin system, we can update AdminPlus to work
with the newer Django version, while retaining support for older versions through our :mod:`privex.adminplus.backports` module.

For more information about our backports module, please read our :ref:`Django Backports Information` page.

**Despite the name, neither this project, nor ourselves have any affiliation with the original** `Django AdminPlus`_ ,
nor is this project designed to be a 1:1 exact re-implementation of Django AdminPlus - it may in some cases work
as a drop-in replacement, but is not guaranteed to work like that.

This documentation is automatically kept up to date by ReadTheDocs, as it is automatically re-built each time
a new commit is pushed to the `Github Project`_ 

.. _Privex's Django Admin Plus: https://github.com/Privex/adminplus
.. _Github Project: https://github.com/Privex/adminplus
.. _Django AdminPlus: https://github.com/jsocol/django-adminplus

Screenshot
----------

.. image:: https://cdn.privex.io/github/adminplus/privex_adminplus_index.png
   :target: https://cdn.privex.io/github/adminplus/privex_adminplus_index.png
   :alt: Screenshot of Django admin panel index from the example app included with Privex AdminPlus
   :align: center

Simple usage example
--------------------

.. Tip:: For more complex examples, and general usage information such as how to set multiple URLs for one view,
          registering a view dynamically (without using :func:`.register_url` as a decorator), and other
          useful usage information see the :ref:`Example Usages` page.

Privex AdminPlus is very easy to use, thanks to the :func:`.register_url` decorator.

You can wrap both class-based views, and function-based views using :func:`.register_url` - all parameters are optional,
even the URL. AdminPlus will attempt to automatically generate a URL, route name, and/or human name (page title in admin list)
if they aren't specific / are blank.

All views registered with :func:`.register_url` will be shown in the admin panel under **Custom Pages** by default, unless
either the primary URL contains a parameter (``/user/<str:username>``), or you explicitly specify ``hidden=True``
to :func:`.register_url`

.. code-block:: python

    from privex.adminplus.admin import register_url
    from django.http import HttpResponse, JsonResponse
    from django.views.generic import View, TemplateView

    # This would result in the url '{admin_prefix}/another_test' and the human name 'Another Test'
    @register_url()
    def another_test(request):
        return HttpResponse(b"another test view")

    # URL: {admin_prefix}/example/    Name: admin:some_static_page     Human: Some Static Page
    @register_url('example/')
    class SomeStaticPage(TemplateView):
        template_name = "admin/static_page.html"

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

Quick install
-------------

.. Note:: For more in-depth installation instructions, with examples of how each file / section should look when configuring,
          see the :ref:`Installation` page.

**Installing with** `Pipenv`_ **(recommended)**

.. code-block:: bash

    pipenv install privex-adminplus


**Installing with standard** ``pip3``

.. code-block:: bash

    pip3 install privex-adminplus

**Add to INSTALLED_APPS**

 * Open your main settings.py file
 * Delete or comment out ``'django.contrib.admin'`` in your ``INSTALLED_APPS``
 * At the **START / TOP** of your ``INSTALLED_APPS``, insert ``'privex.adminplus'`` followed by ``'privex.adminplus.apps.PVXAdmin'``

**Comment out any old ``admin.site = xxx`` statements in urls.py**

 * In your **master urls.py** (same folder as wsgi.py, asgi.py, and settings.py), comment out / delete any existing
   admin settings / calls e.g. ``admin.site = xxx`` or ``admin.autodiscovery()`` (leave the ``path('admin/', admin.site.urls)`` as-is)

Now you should be good to go :)

For more in-depth installation instructions, with examples of how each file / section should look when configuring,
see the :ref:`Installation` page.

All Documentation
=================

.. toctree::
   :maxdepth: 8
   :caption: Main:

   self
   install
   backports
   examples


.. toctree::
   :maxdepth: 3
   :caption: Code Documentation:

   adminplus/index

.. contents::






.. _Pipenv: https://pipenv.kennethreitz.org/en/latest/




Python Module Overview
----------------------

Privex's Django AdminPlus is organised into various sub-modules to make it easier to find the
functions/classes you want to use, and to avoid having to load the entire module (though it's lightweight).

Below is a listing of the sub-modules available in ``privex-adminplus`` with a short description of what each module
contains.

.. include:: adminplus/index.rst







Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
