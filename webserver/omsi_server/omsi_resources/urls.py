from django.conf.urls import patterns, url, include

urlpatterns = patterns('',
    url(r'^$', 'omsi_resources.views.filemanager' , name='omsi_resources.default'),
    url(r'^filemanager', 'omsi_resources.views.filemanager' , name='omsi_resources.filemanager'),
    url(r'^fileProcessor', 'omsi_resources.views.fileProcessor' , name='omsi_resources.fileProcessor'),
    url(r'^hierarchicalFilemanager', 'omsi_resources.views.hierarchicalFilemanager', name='omsi_resources.hierarchicalFilemanager'),
    url(r'^addfile', 'omsi_resources.views.addfile', name='omsi_resources.addfile'),
    url(r'^jobManager', 'omsi_resources.views.jobManager', name='omsi_resources.jobManager'),
)
