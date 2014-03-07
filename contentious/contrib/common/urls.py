from django.conf.urls import patterns, include, url


urlpatterns = patterns(
    'contentious.contrib.common.views',
    url(r'^save_content/$', 'save_content', name="contentious_save_content"),
)

