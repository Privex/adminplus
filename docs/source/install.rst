.. _Installation:

Installation
============

Download/Install the package
----------------------------

Download and install from PyPi using pip (recommended)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Using the standard ``pip3`` package manager

.. code-block:: bash
    
    pip3 install -U privex-adminplus


Using ``pipenv`` - third party package manager + virtualenv manager + interpreter version manager

.. code-block:: bash

    pipenv install privex-adminplus


(Alternative) Manual install from Git
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Option 1 - Use pip to install straight from Github**

.. code-block:: bash

    pip3 install git+https://github.com/Privex/adminplus.git


**Option 2 - Clone and install manually**

.. code-block:: bash

    # Clone the repository from Github
    git clone https://github.com/Privex/adminplus.git
    cd adminplus

    # RECOMMENDED MANUAL INSTALL METHOD
    # Use pip to install the source code
    pip3 install .

    # ALTERNATIVE MANUAL INSTALL METHOD
    # If you don't have pip, or have issues with installing using it, then you can use setuptools instead.
    python3 setup.py install

Add to INSTALLED_APPS
---------------------

Open ``settings.py`` in your Django project (e.g. ``YourProject/yourapp/settings.py``)

Locate the ``INSTALLED_APPS`` list.

Remove the default ``django.contrib.admin`` from INSTALLED_APPS.

Then add `privex.adminplus` followed by `privex.adminplus.apps.PVXAdmin` to the **START** / **TOP** of `INSTALLED_APPS`.

.. code-block:: python

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


Comment out any existing admin statements in ``urls.py``
--------------------------------------------------------

Open the ``urls.py`` file - in your project's main Django application (generally the folder containing `settings.py` and `wsgi.py`).

Comment out any previous ``admin.site`` statements in that file, including ``admin.autodiscover()`` if it's present.

.. code-block:: python

    from django.contrib import admin
    from django.urls import path

    ##### Ensure any previous admin.xxx statements are deleted / commented out to avoid conflict.
    # admin.site = something
    # admin.sites.site = admin.site
    # admin.autodiscover()

    urlpatterns = [   # Mount admin.site.urls as normal, no changes needed here
        path('admin/', admin.site.urls),
        # your app URLs...
    ]



Start using Privex AdminPlus :)
-------------------------------

Privex AdminPlus should now be fully installed, registered, and configured :)

It's time to start adding some custom admin views. Continue on to the :ref:`Example Usages`



(Troubleshooting) Manually register the custom admin
----------------------------------------------------

As of privex-adminplus ``1.0.0``, :func:`.setup_admin` is automatically called when the :mod:`privex.adminplus` app is loaded.

For some projects, this may cause issues, especially if you're using other Django admin plugins alongside ``privex-adminplus``.

If the automatic setup does not work, or causes issues e.g. the Django application crashes on startup, you can disable automatic setup,
and register it manually.

To do this, first open your project's ``settings.py`` and set ``AUTO_SETUP_ADMIN = False``

.. code-block:: python

    # Disable automatic registration with setup_admin(admin) when the privex.adminplus app is loaded
    AUTO_SETUP_ADMIN = False


Next, open the ``urls.py`` file - in your project's main Django application (generally the folder containing `settings.py` and `wsgi.py`).

Add an import for ``setup_admin``: ``from privex.adminplus.admin import setup_admin``

Then, add ``setup_admin(admin)`` to the body of the file - generally below your imports, or above your ``urlpatterns``.


.. code-block:: python

    from django.contrib import admin
    from django.urls import path
    from privex.adminplus.admin import setup_admin

    # Register Privex AdminPlus to replace the default Django admin system
    # This will automatically run admin.autodiscover(), so you don't need to call both setup_admin() and admin.autodiscover()
    setup_admin(admin)

    # If admin.autodiscover() shouldn't be ran yet, pass discover=False to disable running autodiscover
    # setup_admin(admin, discover=False)

    urlpatterns = [   # Mount admin.site.urls as normal, no changes needed here
        path('admin/', admin.site.urls),
        # your app URLs...
    ]

