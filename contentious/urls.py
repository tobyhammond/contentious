from django.conf.urls import patterns, url


urlpatterns = patterns(
    'contentious.views',
    url(r'^save_content/$', 'save_content', name="contentious_save_content"),
)

