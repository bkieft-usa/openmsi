"""The basic scheme used for construction of data/image request URL's is as follows:
    <baseURL>/<command>/"<filename>"/<expIndex>/<dataIndex>/<zval> ...

    **Required**:

    * ``<baseURL>`` : The basic URL where the server is running, e.g. http://localhost:8000/
    * ``<command>`` : Depending on which data/action we are requesting a different command
                is used, e.g., slice, islice, spectrum, filemetadata etc.

    **Optional**:

    * ``<filename>`` : The name of the OMSI HDF5 file to be used. The filename is enclosed
                in "...".
    * ``<expIndex>``   : Number indicating the index of the experiment.
    * ``<dataIndex>``  : Number indicating the index of the dataset.
    * ``<zval>``       : Number indicating the mz-slize value.
    * ``<xmin>``, ``<ymin>``, ``<zmin>``: Number indicating the lower bound of a selection in x,y, or z.
                Array indicies are 0-based and inclusive, i.e., to access data starting
                from the first element set this value to 0.
    * ``<xmax>``, ``<ymax>``, ``<zmax>`` : Number indicating the upper bound of a selection in x,y, or z.
                The upper bound is not included in the selection. Set to -1 in order to
                set the maximum to include everyting starting from xmin to the last element.
    * ``<normalize>``  : Set to 1 in order to normalize the raw data by dividing by the maximum value.
                NOTE: Normalization is applied to the raw data, i.e., data reduction is
                currently performed after the data is normalized, i.e., after the reduction
                operation is applied, the data may no longer be normalized.
    * ``<reduction>``  : Reduction operations are used to reduce, e.g., a 3D array to a 2D array
                by computing, e.g, the mean along a selected axis of the matrix.
                Reduction can be any numpy operations that can be called as follows,
                operation(data,axis). This includes a large range of functions such as,
                min, max, mean, median, std, var and others.
    * ``<findPeaks>``  : Option specific to spectra. Set to 1 in order to execute peak finding for
                the requested spectrum data

    In order to support optional parameters, the same python functin may be mapped to
    multiple URL's consisting of different subsets of optional parameters available
    for the given python function.
"""

from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()
from django.views.generic import RedirectView

urlpatterns = patterns('',
    # Examples:
    url(r'^$', RedirectView.as_view(url='/openmsi/client'), name='home'),
    # url(r'^omsi_server/', include('omsi_server.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),

    # Django account login page
    #url(r'^accounts/login/$', 'django.contrib.auth.views.login'),

    #////////////////////////////////////////////////////////////////////
    #   URL's for requesting different types of data                   //
    #   using the query-string                                         //
    #////////////////////////////////////////////////////////////////////
    #Request JSON object or PNG image of a spectrum or the difference of two spectra via the query-string.
    #See omsi_access.views.get_spectrum for more details on the required and optional query parameters.
    url(r'^qspectrum/$', 'omsi_access.views.get_spectrum', name="omsi_access.qspectrum"),
    #Request JSON object or PNG image of a single or multiple m/z-slices of the data via the query-string.
    #See omsi_access.views.get_slice for more details on the required and optional query parameters.
    url(r'^qslice/$', 'omsi_access.views.get_slice', name="omsi_access.slice"),
    #Request JSON object of subcubes of the original MSI data or derived analysis data based on the query string
    #See omsi_omsi_access.views.get_cube for more details on the required and optional query parameters.
    url(r'^qcube/$', 'omsi_access.views.get_cube', name="omsi_access.qcube"),
    #Request JSON object with metadata for a file, expermiment, analysis or instrument
    #See omsi_access.get_metadata for more details on the required and optional query parameters.
    url(r'^qmetadata/$', 'omsi_access.views.get_metadata' , name="omsi_access.qmetadata"),
    #Request JSON object with the mz data for a given dataset or analysis
    url(r'^qmz/$', 'omsi_access.views.get_mz', name="omsi_access.qmz"),
    #Request JSON object with the mz data for a given dataset or analysis
    url(r'^qaxes/$', 'omsi_access.views.get_axes', name="omsi_access.qaxes"),

    #//////////////////////////////////////////////////
    #   Client URL patterns                         //
    #//////////////////////////////////////////////////

    # This is a quick way to make the dev env (check for openmsi prefix) behave like production
    # without changing client URLs
    url(r'^(openmsi/)?client/', include('omsi_client.urls')),
    url(r'^(openmsi/)?resources/', include('omsi_resources.urls')),

    #//////////////////////////////////////////////////
    #   Data processing URL patterns                 //
    #//////////////////////////////////////////////////
    url(r'^(openmsi/)?processing/', include('omsi_processing.urls')),

    #//////////////////////////////////////////////////
    #    SciDB URL patterns                          //
    #//////////////////////////////////////////////////
    url(r'^(openmsi/)?scidb/', include('omsi_scidb.urls')),



)
