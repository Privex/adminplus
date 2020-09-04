# v1.0.0 - BREAKING CHGS - complete overhaul

 - Added full support for Django 3.1 sidebar, while retaining compatibility with 3.0 and 2.2

 - AdminPlus now automatically registers the Django admin site when the `privex.adminplus` app is loaded.
   
   You no longer need to call `setup_admin(admin)` from your `urls.py`, however, existing calls to
   `setup_admin` are fine, they'll simply be ignored if the admin is already registered.
 
 - `adminplus.admin.apps.PVXAdmin` is automatically loaded if you don't specify it in your `INSTALLED_APPS`

 - `CustomAdmin`
     - `CustomAdmin.custom_urls` and `CustomAdmin.custom_url_map` are now class attributes instead of
       instance attributes.
       
       This fixes an issue where `admin.site` would be a different `CustomAdmin` instance from `adminplus.admin.ctadmin`,
       which meant that `admin.site.add_url` would write to a different registered URL maps 
       compared to `adminplus.admin.register_url`
    - Added `admin_singleton` method to get or create a named singleton instance
    - The `ctadmin` global object now uses admin_singleton to avoid duplicates
    - Removed `each_context` method, no longer needed thanks to `privex.adminplus.admin.pvx_context_processor`
    - Small adjustments to `add_url` method
    - Added `detect_human` static method
    - Added PyDoc comment blocks to most methods and some attributes
 
 - Changed `PrivexAdminPlusConfig.name` to `privex.adminplus` instead of just `adminplus`
 
 - Added template context processor `privex.adminplus.admin.pvx_context_processor`, which is added to `settings.TEMPLATE`
   by new helper function `privex.adminplus.admin.inject_context_processors` (called during setup_admin)
 
   The context processor allows us to inject `ctadmin`, `custom_urls` (ref to `custom_urls_reverse`) and `custom_url_map`
   into every template context, which is necessary for Privex AdminPlus to be able to render the list of custom pages
   from any admin view, without having to extend each view, or attempt to hijack their context.
   
   This allows us to do in a template - rendered in any view: `for name, obj in custom_urls.items`
 
 - Added `templates/admin/nav_sidebar.html` for rendering the list of custom pages in the Django 3.1+ sidebar.
 
 - Added `templates/admin/custom_pages_box.html` - refactored "Custom Pages" box into this file, so it can be
   imported into `nav_sidebar.html` and `index.html` consistently.
 
 - Added `backports` module
    - Backported `translate` / `blocktranslate` templatetags from Django 3.1 i18n library into
      `privex.adminplus.backports.templatetags.blocktranslate.py`
    - Backported `admin/app_list.html` into `backports/templates/admin/app_list.html`, adjusted to use
      backported `translate`/`blocktranslate` template tags.
  
  - Added method `adminplus.admin.apps.PrivexAdminPlusConfig.ready`, which handles auto-loading additional apps if needed,
    and automatically registering the Django site via `setup_admin(admin)`.
     
    - Detects the Django version after the app is loaded, and if the Django version is older than `3.1.0`, it will auto-load
     `privex.adminplus.backports` (if it wasn't added by the user to INSTALLED_APPS)
    - Detects whether `adminplus.admin.apps.PVXAdmin` is registered in `INSTALLED_APPS`. If not, then injects it into
      INSTALLED_APPS
    - If we had to inject backports or PVXAdmin, then it re-loads all apps specified in `INSTALLED_APPS`
    - After all apps are re-loaded (or if they didn't have to be), it automatically registers the admin site
      with Django using `setup_admin`
 
 - Much much more :)
 
 - Added documentation under the `docs/` folder.
 


