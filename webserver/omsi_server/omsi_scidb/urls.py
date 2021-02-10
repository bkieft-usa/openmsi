from django.conf.urls import patterns, url, include

urlpatterns = patterns('',
    (r'^$', 'omsi_scidb.views.index'),
)