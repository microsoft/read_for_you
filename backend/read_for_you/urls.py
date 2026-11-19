from django.views.generic import TemplateView
from django.views.static import serve as static_serve
from django.urls import path, re_path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("recognition", views.recognition, name="recognition"),
    path("getStoragedData", views.getStoragedData, name="getStoragedData"),
    path("getBookMetadata", views.getBookMetadata, name="getBookMetadata"),
    path("getImageFromAB2", views.getImageFromAB2, name="getImageFromAB2"),
    path("getBookHistory", views.getBookHistory, name="getBookHistory"),
    path("getResultOfUser", views.getResultOfUser, name="getResultOfUser"),
]

# Serve static files (both development and production for SPA)
dist_root = settings.BASE_DIR / 'read_for_you' / 'static' / 'dist'

# 静态文件路由 - 必须在 catch-all 之前
urlpatterns += [
    re_path(r'^(?P<path>assets/.*)$', static_serve, {'document_root': dist_root}),
    re_path(r'^(?P<path>vite\.svg)$', static_serve, {'document_root': dist_root}),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])

# Catch-all route for SPA - must be AFTER static files
urlpatterns += [
    re_path(r'^.*$', TemplateView.as_view(template_name='index.html'), name='frontend'),
]
