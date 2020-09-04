from django.contrib import admin
from django.contrib.auth.models import User
from django.http import HttpResponse, JsonResponse, HttpRequest
from django.views import View
from privex.adminplus.admin import ct_register, register_url, CustomAdmin
from app.models import Comment, Post
import logging

log = logging.getLogger(__name__)

ctadmin: CustomAdmin = admin.site


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['title', 'user']


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['title', 'user']


@register_url(url='hello/')
def testing_admin(request):
    log.warning("ctadmin.custom_urls: %s", ctadmin.custom_urls)
    log.warning("ctadmin.custom_urls_reverse: %s", ctadmin.custom_urls_reverse)
    log.warning("ctadmin.custom_url_map: %s", ctadmin.custom_url_map)
    return HttpResponse(b"hello world")


@register_url(url='debug_urls/')
def debug_urls(request):
    log.warning("ctadmin.custom_urls: %s", ctadmin.custom_urls)
    log.warning("ctadmin.custom_urls_reverse: %s", ctadmin.custom_urls_reverse)
    log.warning("ctadmin.custom_url_map: %s", ctadmin.custom_url_map)
    return JsonResponse(dict(
        custom_urls=[str(u) for u in ctadmin.custom_urls],
        custom_url_map=ctadmin.custom_url_map,
        custom_urls_reverse=ctadmin.custom_urls_reverse
    ))


@register_url(hidden=True)
def another_test(request):
    return HttpResponse(b"another test view")


@register_url()
class ClassViewTest(View):
    def get(self, *args, **kwargs):
        return HttpResponse(b"this is a class view")


@register_url(['user_info/', 'user_info/<str:username>/'])
def user_info(request, username=None):
    if username:
        u = User.objects.filter(username=username).first()
        return JsonResponse(dict(id=u.id, username=u.username, first_name=u.first_name, last_name=u.last_name))
    return JsonResponse(dict(error=True, message="no username in URL"))


@register_url({
    'post_info/': 'post_info',
    'post_info/<int:post_id>/': 'post_info_byid',
    'post_info/<int:post_id>/comments': 'post_comments'
})
def post_info(request: HttpRequest, post_id=None):
    get_comments = request.path.endswith('/comments')
    
    if post_id:
        p: Post = Post.objects.get(id=post_id)
        post_dict = dict(id=p.id, title=p.title, content=p.content, user=p.user.username)
        res = dict(post_dict)
        if get_comments:
            res = dict(post=post_dict, comments=[])
            for c in p.comments.all():   # type: Comment
                res['comments'].append(
                    dict(id=c.id, title=c.title, content=c.content, user=c.user.username)
                )
        return JsonResponse(res)
    
    return JsonResponse(dict(error=True, message="no post id in URL"))


def yet_another_test_view(request: HttpRequest):
    return JsonResponse(dict(hello='world'))


ctadmin.add_url(yet_another_test_view, 'yet_another_test_view/')


class DecWrappedManual(View):
    def get(self, request):
        return JsonResponse(dict(view_name=self.__class__.__name__))


# ca = admin.site    # type: CustomAdmin
# from privex.adminplus.admin import ctadmin as ctd
# log.error("ctadmin is: %s", ctadmin)
# log.error("ctd is: %s", ctd)


DecWrappedManual = register_url('wrapped_manual_dec/', human='View manually wrapped with decorator')(DecWrappedManual)
