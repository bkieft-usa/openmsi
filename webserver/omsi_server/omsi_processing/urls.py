from django.conf.urls import patterns, url, include

urlpatterns = patterns('',
    url(r'^convert', 'omsi_processing.views.convert', name='omsi_processing.convert'),
    url(r'^update', 'omsi_processing.views.update', name='omsi_processing.update'),
    url(r'^jobs', 'omsi_processing.views.jobs', name='omsi_processing.jobs')
)