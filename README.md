
Privex's Custom Admin for Django
=================================

[![PyPi Version](https://img.shields.io/pypi/v/privex-adminplus.svg)](https://pypi.org/project/privex-adminplus/)
![License Button](https://img.shields.io/pypi/l/privex-adminplus) 
![PyPI - Downloads](https://img.shields.io/pypi/dm/privex-adminplus)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/privex-adminplus) 
![PyPI - Django Version](https://img.shields.io/pypi/djversions/privex-adminplus)
![GitHub last commit](https://img.shields.io/github/last-commit/Privex/adminplus)

This is a custom admin views extension for the [Django Web Framework](https://www.djangoproject.com/), which has been
designed as an alternative to [Django AdminPlus](https://github.com/jsocol/django-adminplus).

**Despite the name, neither this project, nor ourselves have any affiliation with the original
[Django AdminPlus](https://github.com/jsocol/django-adminplus), nor is this project designed to be a 1:1 exact
re-implementation of Django AdminPlus - it may in some cases work as a drop-in replacement, but is not guaranteed
to work like that.**

```
+===================================================+
|                 © 2020 Privex Inc.                |
|               https://www.privex.io               |
+===================================================+
|                                                   |
|        Privex Django Admin Plus                   |
|        License: X11/MIT                           |
|                                                   |
|        Core Developer(s):                         |
|                                                   |
|          (+)  Chris (@someguy123) [Privex]        |
|                                                   |
+===================================================+

Privex Django Admin Plus - An extension for Django so you can add custom views to the admin panel
Copyright (c) 2020    Privex Inc. ( https://www.privex.io )
```

# Install with pip

We recommend at least Python 3.6 - we cannot guarantee compatibility with older versions.

```
pip3 install privex-adminplus
```

# Quickstart

### Install the `privex-adminplus` package from PyPi using `pip3` / `pipenv`

```shell script
# Using the standard 'pip3' package manager
pip3 install -U privex-adminplus

# Using 'pipenv' - third party package manager + virtualenv manager + interpreter version manager
pipenv install privex-adminplus
```

### Add to `INSTALLED_APPS` in `YourProject/yourapp/settings.py`

Open `settings.py` in your Django project. 

Remove the default `django.contrib.admin` from INSTALLED_APPS. Then add `privex.adminplus` followed by
`privex.adminplus.apps.PVXAdmin` to the **START** / **TOP** of `INSTALLED_APPS`.

```python
INSTALLED_APPS = [
    # You must delete / comment out the line for the default admin (django.contrib.admin)   
    # 'django.contrib.admin',

    # NOTE: If you are running a version of Django older than 3.1 (3.0.9, 2.2.15 etc.), then you should 
    #       add 'privex.adminplus.backports' BEFORE the 'privex.adminplus' and PVXAdmin apps.
    #       The backports app is auto-loaded if it's not in INSTALLED_APPS and adminplus detects you need it, but the
    #       auto-loading will slow down your app's startup, and may cause issues with apps that should only be loaded ONCE.

    # 'privex.adminplus.backports',

    'privex.adminplus',
    'privex.adminplus.apps.PVXAdmin',
    # ...
    'django.contrib.auth',
    'django.contrib.contenttypes',
    # ...
]   
```

### Register the custom admin in your master `urls.py` file

In your project's main Django application (generally the folder containing `settings.py` and `wsgi.py`), you'll
need to comment out any previous `admin.site` statements, and add `setup_admin(admin)` before you define any urls.

```python
from django.contrib import admin
from django.urls import path
from privex.adminplus.admin import setup_admin

# Register Privex AdminPlus to replace the default Django admin system
# This will automatically run admin.autodiscover(), so you don't need to call both setup_admin() and admin.autodiscover() 
setup_admin(admin)

# If admin.autodiscover() shouldn't be ran yet, pass discover=False to disable running autodiscover
# setup_admin(admin, discover=False)

##### Ensure any previous admin.xxx statements are deleted / commented out to avoid conflict.
# admin.site = something
# admin.sites.site = admin.site
# admin.autodiscover()

urlpatterns = [   # Mount admin.site.urls as normal, no changes needed here
    path('admin/', admin.site.urls),
    # your app URLs...
]

```


# Notice about AdminPlus Django Back-ports!

## Why do you include the `backports` module, containing code ripped from the official Django project?

While Django is well known for their effort towards ensuring backwards compatibility, the Django admin panel is quite
complex, and frequently has potentially breaking updates such as new template files, layout changes, along with use of
newer Django functions such as new template tags.

These types of changes can cause Django Admin plugins/wrappers/replacements such as Privex AdminPlus to either stop working,
or may simply cause bugs such as the custom pages admin panel list not rendering correctly, custom views won't load etc.

Often, to deal these regressions caused by new Django releases, we have to update Privex AdminPlus to work with the newer
Django version. However, by updating the code to support a newer Django version, it may break AdminPlus on older versions
of Django.

To allow Privex AdminPlus to support newer versions of Django, while retaining support for older versions, we include an
additional Django application: `privex.adminplus.backports`

## What is the `backports` module?

The **backports** application is a Django app which contains backported views, admin panel templates, template tags, and
other parts of the [official Django admin panel code](https://github.com/django/django/tree/master/django/contrib/admin)
which have been copied from a newer version of Django such as **3.1**, **3.2** or even from the latest development code.

The backported code is lightly tested using the included `exampleapp` project, by running the project using a development
server, and then browsing through the admin panel - hand testing both Privex AdminPlus custom views, as well as the
standard `ModelAdmin` views (e.g. creating, editing, viewing and deleting database objects).

Note that the `backports` app is only tested against "older" versions of Django, which are missing at least one critical feature
from the latest stable version of Django that had to be backported.

## Should I add the backports app to INSTALLED_APPS? / How can I disable backports?

### Automatic loading of the backports app

As of Privex AdminPlus 1.0.0 - the oldest Django framework version which **does not require backports** to be able
to use AdminPlus is Django `3.1.0`

To keep the installation process simple, and to ensure compatibility with those upgrading from `privex-adminplus < 1.0.0`,
the `privex.adminplus.apps.PVXAdmin` class contains a Django version check within it's `ready()` method.

If it detects that you're running a Django version which requires backported features, and `privex.adminplus.backports`
isn't in your `INSTALLED_APPS`, then it will dynamically inject `privex.adminplus.backports` into `INSTALLED_APPS`,
and attempt to trigger a re-initialisation of all `INSTALLED_APPS` to ensure backports gets loaded.

If your Django app is configured to log messages which are `WARNING` or higher, you may see the automatic backport app loader
in your logs when you first start your app:

```
PrivexAdminPlusConfig.ready :: Django version is < 3.1 :: Ver is: 2.2.15
'privex.adminplus.backports' not in INSTALLED_APPS... adding to apps and re-initialising!
Re-initialising all Django Apps...
Finished re-initialising.
```

### Do not rely on the backports auto-loader

While the backports app is auto-loaded if it's not in INSTALLED_APPS and adminplus detects you need it, 
**auto-loading will slow down your app's startup, and may cause issues with apps that should only be loaded ONCE.**

To prevent the risk of strange issues related to the backports auto-loader, if you are running a version of Django older 
than 3.1.0 (3.0.9, 2.2.15 etc.), then you should add `'privex.adminplus.backports'` BEFORE the `'privex.adminplus'` 
and PVXAdmin apps in your `INSTALLED_APPS`

```python
INSTALLED_APPS = [
    'privex.adminplus.backports',
    'privex.adminplus',
    'privex.adminplus.apps.PVXAdmin',
    # ...
]
```

### Force disabling the backports auto-loader

If you are running on an older version of Django which normally requires our `privex.adminplus.backports` Django app,
but you don't want to / can't use our backports app, it's possible to disable the backports auto-loader.

Reason Examples:

- Because of another Django app / Python package which conflicts with our backports
- Because you've made your own backports/modifications to views/templates/classes etc. which conflicts with our backports app.

**NOTE:** The backports auto-loader only loads `backports` if it's **not already loaded** (listed in INSTALLED_APPS),
AND **you're running an older version of Django** which requires our `backports` app to make pvx-adminplus work at all.

To force disable automatic loading of `privex.adminplus.backports`, set `AUTO_BACKPORT` to `False` in your `settings.py`
file for your project.

```python
# Disable privex.adminplus's automatic loading of privex.adminplus.backports
AUTO_BACKPORT = False

INSTALLED_APPS = [
    'privex.adminplus',
    'privex.adminplus.apps.PVXAdmin',
    # ...
]

```



# Replace the default admin with Privex AdminPlus

First you need to comment out `django.contrib.admin` at the start of your `INSTALLED_APPS`.

Below the commented out `django.contrib.admin`, you'll need to add `privex.adminplus` to register the base Django app itself,
followed by `privex.adminplus.apps.PVXAdmin` to register the admin panel.

```python
INSTALLED_APPS = [
    # 'django.contrib.admin',

    # NOTE: If you are running a version of Django older than 3.1 (3.0.9, 2.2.15 etc.), then you should 
    #       add 'privex.adminplus.backports' BEFORE the 'privex.adminplus' and PVXAdmin apps.
    #       The backports app is auto-loaded if it's not in INSTALLED_APPS and adminplus detects you need it, but the
    #       auto-loading will slow down your app's startup, and may cause issues with apps that should only be loaded ONCE.

    # 'privex.adminplus.backports',

    'privex.adminplus',
    'privex.adminplus.apps.PVXAdmin',
    # ...
    'django.contrib.auth',
    'django.contrib.contenttypes',
    # ...
]   
```

# Remove any old admin.site statements from your `urls.py` file

In your project's main Django application (generally the folder containing `settings.py` and `wsgi.py`), you'll
need to comment out any previous `admin.site` statements, or `admin.autodiscovery()` if they're present.

You do NOT need to remove the admin URL mount `path('admin/', admin.site.urls)`

```python
from django.contrib import admin
from django.urls import path

#####
# Ensure any previous admin.xxx statements are comment out to avoid conflict.
#####
# admin.site = something
# admin.sites.site = admin.site
# admin.autodiscover()

urlpatterns = [
    # Mount admin.site.urls as normal, no changes needed here
    path('admin/', admin.site.urls),
    # your app URLs...
]

```

# Usage

## Registering standard ModelView's

Register your ModelViews as normal in your `admin.py`

```python
from django.contrib import admin
from myapp.models import SomeModel

@admin.register(SomeModel)
class SomeModelAdmin(admin.ModelAdmin):
    pass

```

## Registering custom admin views

You can register custom views using the `privex.adminplus.admin.register_url`, including both function-based and class-based
views. You don't even need to specify a name or URL, it can be automatically inferred from the class/function name.



```python
from privex.adminplus.admin import register_url
from django.http import HttpResponse
from django.views import View

# This would result in the url '{admin_prefix}/hello/' and the human name 'Testing Admin'
@register_url(url='hello/')
def testing_admin(request):
    return HttpResponse(b"hello world")

# This would result in the url '{admin_prefix}/another_test' and the human name 'Another Test'
@register_url()
def another_test(request):
    return HttpResponse(b"another test view")

# This would result in the url '{admin_prefix}/class_view_test' and the human name 'Class View Test'
@register_url()
class ClassViewTest(View):
    def get(self, *args, **kwargs):
        return HttpResponse(b"this is a class view")

# You can also hide views from the auto-generated custom admin views list, and you can override their "human friendly name" 
# which is shown on the custom admin views list on the admin index page::

# This would result in the url '{admin_prefix}/lorem' and the human name 'Lorem Ipsum Dolor Generator'
@register_url(human="Lorem Ipsum Dolor Generator")
def lorem(request):
    return HttpResponse(b"lorem ipsum dolor")
# This would result in the url '{admin_prefix}/some_internal_view' - and the human name doesn't matter, 
# as it's hidden - thus does not show up in the custom admin views list

@register_url(hidden=True)
def some_internal_view(request):
    return HttpResponse(b"this is an internal view, not for just browsing!")

```

## Admin views with multiple URLs and route parameters

Below are two examples: multiple URLs for one view by specifying them as a list - and multiple URLs by specifying them
as a dictionary (dicts allow you to set a static `admin:` prefixed name for each URL)

```python
from django.contrib.auth.models import User
from django.http import HttpResponse, JsonResponse, HttpRequest
from privex.adminplus.admin import register_url

# You can specify multiple URLs as a list.
# By default, all URLs other than the first one specified will be set as hidden=False - to avoid duplicate
# custom view entries in the admin panel
@register_url(['user_info/', 'user_info/<str:username>'])
def user_info(request, username=None):
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
def user_info(request, username=None):
    if username:
        u = User.objects.filter(username=username).first()
        return JsonResponse(dict(id=u.id, username=u.username, first_name=u.first_name, last_name=u.last_name))
    return JsonResponse(dict(error=True, message="no username in URL"))

```

When more than one URL is specified in ``url`` using a list/dict, if hide_extra is True, then only the first URL
in the list/dict of URLs will use the user-specified ``hidden`` parameter.
The rest of the URLs will have `hidden=True`

To disable automatically hiding "extra" URLs, pass hide_extra=False like so:

```python
@register_url(hide_extra=False)
```

If hide_params is True, URLs which contain route parameters (e.g. ``<str:username>``) will be hidden by default, to prevent
errors caused by trying to reverse their URL in the admin panel custom view list.

To disable automatically hiding URLs which contain route parameters, pass hide_params=False like so:

```python
@register_url(hide_params=False)
```


# Included Example App

For development and testing purposes, the folder `exampleapp` contains a basic Django project which tries to use
most features of `privex-adminplus`, so that they can be tested by hand in an actual Django application.

To use exampleapp:

```sh
git clone https://github.com/Privex/adminplus
cd adminplus
# install requirements
pip3 install -r requirements.txt

# For exampleapp to be able to resolve the 'privex/adminplus' module, you must set the PYTHONPATH
# to the base folder of the privex-adminplus project.
export PYTHONPATH="$PWD"

# Enter exampleapp and migrate the Django DB (auto-creates an sqlite3 database at exampleapp/db.sqlite3)
cd exampleapp
./manage.py migrate

# Create an admin user
./manage.py createsuperuser

# Start the dev server and then navigate to http://127.0.0.1:8000/admin
./manage.py runserver
```

