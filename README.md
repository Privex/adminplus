
Privex's Custom Admin for Django
=================================

[![PyPi Version](https://img.shields.io/pypi/v/django-lockmgr.svg)](https://pypi.org/project/privex-adminplus/)
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

# Replace the default admin with Privex AdminPlus

First you need to comment out `django.contrib.admin` at the start of your `INSTALLED_APPS`.

Below the commented out `django.contrib.admin`, you'll need to add `privex.adminplus` to register the base Django app itself,
followed by `privex.adminplus.apps.PVXAdmin` to register the admin panel.

```python
INSTALLED_APPS = [
    # 'django.contrib.admin',
    'privex.adminplus',
    'privex.adminplus.apps.PVXAdmin',
    # ...
    'django.contrib.auth',
    'django.contrib.contenttypes',
    # ...
]   
```

# Register the custom admin in your master `urls.py` file

In your project's main Django application (generally the folder containing `settings.py` and `wsgi.py`), you'll
need to comment out any previous `admin.site` statements, and add `setup_admin(admin)` before you define any urls.

```python
from django.contrib import admin
from django.urls import path
from privex.adminplus.admin import setup_admin

# Register Privex AdminPlus to replace the default Django admin system
# This will automatically run admin.autodiscover(), so you don't need to call both setup_admin() and admin.autodiscover() 
setup_admin(admin)

#### If you have a special app where admin.autodiscover() shouldn't be ran yet, you can run setup_admin
#### with discover=False to disable running autodiscover
# setup_admin(admin, discover=False)

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

