from django.conf.urls import patterns, include, url
from django.views.generic import View

urlpatterns = patterns('',
    url(r'^test_view/$', View.as_view(), name="main"),
)
