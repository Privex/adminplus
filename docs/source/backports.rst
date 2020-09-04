.. _Django Backports Information:

###############################################
Important info about AdminPlus Django BackPorts
###############################################

.. contents::

Why do you include the ``backports`` module?
--------------------------------------------

(and why does it contain code ripped from the official Django project?)

While Django is well known for their effort towards ensuring backwards compatibility, the Django admin panel is quite
complex, and frequently has potentially breaking updates such as new template files, layout changes, along with use of
newer Django functions such as new template tags.

These types of changes can cause Django Admin plugins/wrappers/replacements such as Privex AdminPlus to either stop working,
or may simply cause bugs such as the custom pages admin panel list not rendering correctly, custom views won't load etc.

Often, to deal these regressions caused by new Django releases, we have to update Privex AdminPlus to work with the newer
Django version. However, by updating the code to support a newer Django version, it may break AdminPlus on older versions
of Django.

To allow Privex AdminPlus to support newer versions of Django, while retaining support for older versions, we include an
additional Django application: :mod:`privex.adminplus.backports`

What is the ``backports`` module?
--------------------------------------------

The **backports** application is a Django app which contains backported views, admin panel templates, template tags, and
other parts of the `official Django admin panel code`_ which have been copied from a newer version of Django such as
**3.1**, **3.2** or even from the latest development code.

The backported code is lightly tested using the included ``exampleapp`` project, by running the project using a development
server, and then browsing through the admin panel - hand testing both Privex AdminPlus custom views, as well as the
standard :class:`.ModelAdmin` views (e.g. creating, editing, viewing and deleting database objects).

Note that the :mod:`privex.adminplus.backports` app is only tested against "older" versions of Django, which are missing at least one critical feature
from the latest stable version of Django that had to be backported.

.. _Official Django Admin Panel code: https://github.com/django/django/tree/master/django/contrib/admin

Should I add the backports app to INSTALLED_APPS?
-------------------------------------------------

Automatic loading of the backports app
--------------------------------------

As of Privex AdminPlus 1.0.0 - the oldest Django framework version which **does not require backports** to be able
to use AdminPlus is Django ``3.1.0``

To keep the installation process simple, and to ensure compatibility with those upgrading from ``privex-adminplus < 1.0.0``,
the :class:`privex.adminplus.apps.PVXAdmin` class contains a Django version check within it's
:meth:`privex.adminplus.apps.PVXAdmin.ready()` method.

If it detects that you're running a Django version which requires backported features, and ``'privex.adminplus.backports'``
isn't in your ``INSTALLED_APPS``, then it will dynamically inject ``'privex.adminplus.backports'`` into ``INSTALLED_APPS``,
and attempt to trigger a re-initialisation of all ``INSTALLED_APPS`` to ensure backports gets loaded.

If your Django app is configured to log messages which are ``WARNING`` or higher, you may see the automatic backport app loader
in your logs when you first start your app::

    PrivexAdminPlusConfig.ready :: Django version is < 3.1 :: Ver is: 2.2.15
    'privex.adminplus.backports' not in INSTALLED_APPS... adding to apps and re-initialising
    Re-initialising all Django Apps...
    Finished re-initialising.


Do not rely on the backports auto-loader
----------------------------------------

While the :mod:`privex.adminplus.backports` app is only auto-loaded if it's not in ``INSTALLED_APPS`` and AdminPlus detects you need it,
**auto-loading will slow down your app's startup, and may cause issues with apps that should only be loaded ONCE.**

To prevent the risk of strange issues related to the backports auto-loader, if you are running a version of Django older than 3.1.0 (3.0.9, 2.2.15 etc.),
then you should add ``'privex.adminplus.backports'`` BEFORE the ``'privex.adminplus'`` and PVXAdmin apps in your ``INSTALLED_APPS``

If you see the message ``'privex.adminplus.backports' not in INSTALLED_APPS... adding to apps and re-initialising`` in the logs for your
application, then it means you need the backports module to use privex-adminplus, thus you should add it to your ``INSTALLED_APPS`` for
best reliability and speed.

.. code-block:: python

    INSTALLED_APPS = [
        'privex.adminplus.backports',
        'privex.adminplus',
        'privex.adminplus.apps.PVXAdmin',
        # ...
    ]


Force disabling the backports auto-loader
-----------------------------------------

.. Caution::    You should **NOT** disable the ``backports`` autoloader unless you're running an old version of Django (thus the autoloader is used),
                AND our :mod:`privex.adminplus.backports` Django app conflicts directly with another Django app, or your own project-level
                Django backport implementations.

                The backports auto-loader only loads ``backports`` if it's **not already loaded** (listed in INSTALLED_APPS), AND **you're running an older**
                **version of Django** which requires our ``backports`` app to make pvx-adminplus work at all.

                This means the auto-loader is **automatically disabled** if :mod:`privex.adminplus.backports` is in your ``INSTALLED_APPS``, or you're running
                on a new enough version of Django that no backports are needed (at the time of writing, ``3.1.0`` or newer does not require backports)


If you are running on an older version of Django which normally requires our :mod:`privex.adminplus.backports` Django app,
but you don't want to / can't use our backports app, it's possible to disable the backports auto-loader.

Reason Examples:

 * Because of another Django app / Python package which conflicts with our backports
 * Because you've made your own backports/modifications to views/templates/classes etc. which conflicts with our backports app.

To force disable automatic loading of :mod:`privex.adminplus.backports`, set ``AUTO_BACKPORT`` to ``False`` in your ``settings.py``
file for your project.

.. code-block:: python

    # Disable privex.adminplus's automatic loading of privex.adminplus.backports
    AUTO_BACKPORT = False

    INSTALLED_APPS = [
        'privex.adminplus',
        'privex.adminplus.apps.PVXAdmin',
        # ...
    ]



