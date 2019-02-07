omsi_access Package
===================


:mod:`views` Module
-------------------

This module is responsible for answering any requests for OMSI HDF5 data from the web. THE URL's for accessing the data are defined in ``omsi_server.urls``. This module provides a series of functions for accessing different types of data. Here a list of the main functions of interest. The first function listed for each group provides access to the data via the URL query-string and take only the ``HTTPRequest`` as input. The query-string-based functions utilize the other functions for the actual data retrieval. The other functions utilize a set of direct function input parameters to fullfill the data requests. All functions return ``HTTPResponse`` objects typically containing either a JSON or PNG object of the data or an HTTP error message.

* **Single Spectra** :

    * ``views.get_spectrum`` :  DJANOG view for requesting either a JSON object or PNG image of a single spectrum or the difference of two spectra based on the query-string of the URL.
    * ``views.get_data_spectrum`` : DJANOG view for requesting a JSON object a single spectrum or the difference of two spectra.
    * ``views.get_image_spectrum`` : DJNAGO view for requesting a PNG image plot of a single spectrum or the differerence of two spectra.

* **m/z Data Slices** :

    * ``views.get_slice`` : "DJANOG view for requesting either a JSON object or PNG image of a single or multiple m/z slices of the data based on the query-string of the URL.
    * ``views.get_data_slice`` : DJANOG view for requesting a JSON object of a single data slice.
    * ``views.get_image_slice`` : "DJANOG view for requesting a PNG gray-scale image of a single data slice.
    * ``views.get_data_slice_range`` : DJANOG view for requesting a JSON object of multiple mz-data slices (with optional reduction operations)
    * ``views.get_image_slice_range`` : DJANOG view for requesting a PNG gray-scale image of multiple mz-data slices reduced to a 2D array by applying a user-defined reduction opeation (e.g. max, mean etc.) along the m/z axis.

* **Generic Data Subcubes** :

    * ``views.get_cube`` : DJANOG view for requesting a JSON object of a general 3D subset of the raw MSI data or derived analysis data based on the URL query-string.
    * ``views.get_data_cube`` : "DJANOG view for requesting a JSON object of a general 3D subset of the data.
    * ``views.get_analysis_data`` : DJANOG view for requesting a JSON object of a general 3D subset of an analysis dataset.

* **Static m/z Axes** :

    * ``views.get_mz`` :  DJANGO view for requesting information about the axes for image slices and spectra. In the case of raw data this would be the m/z values of the intrument.
    * ``views.get_mzaxes``: DJANGO view for requesting information about the axes for image slices and spectra. In the case of raw data this would be the m/z values of the intrument.
    * ``views.get_axes`` : Same a ``views.get_mz`` used to remap the name for URLs to support both qmz and qaxes URL pattern.

* **Metadata Information** :

    * ``views.get_metadata`` :  DJANOG view for requesting a JSON object with metadata from a file, experiment, analysis, instrument or sample based on the URL query string.

* **Helper Functions** : The following functions are not directly mapped to URL requests but provide generally useful functionality required by the other functions:

    * ``views_helper.get_omsi_h5py`` : Helper function used to retrieve the h5py object associated with different parts of an OpenMSI HDF5 data file.
    * ``views_helper.get_omsi_rawdata_numpy`` : Helper function used to retrieve numpy data associated with different parts of an OpenMSI HDF5 data file.
    * ``views_helper.get_real_filename`` : Function used to retrieve the real name of an datafile specified in a DJANOG web request URL. This function also checks whether access to the requested file is allowed.
    * ...

* **Related Analysis Helper Functions** : The following functions are provided by the ``omsi.analysis`` module to enable convenient default slicing and spectra selection behavior for analysis functions.

    * ``omsi.analysis.analysis_views`` : Helper class for interfacing different anlaysis algorithms with the webbased viewer.

        * ``omsi.analysis.analysis_views.get_slice`` : Perform m/z slicing on an analysis.
        * ``omsi.analysis.analysis_views.get_spectra`` : Get spectra for an analysis.
        * ``omsi.analysis.analysis_views.get_axes`` : Get m/z axes and labels for spectra and slices for an analysis.
        * ``omsi.analysis.analysis_views.supports_slice`` : Check wheter a given analysis supports slice selection opertations (see als ``omsi.analysis.analysis_views.get_slice`` )
        * ``omsi.analysis.analysis_views.supports_spectra`` : Check wheter a given analysis supports selection of spectra (see als ``omsi.analysis.analysis_views.get_spectra`` )

|
|
|

.. automodule:: omsi_access.views
    :members:
    :undoc-members:
    :show-inheritance:

:mod:`views_definitions` Module
-------------------------------

Module defining the query parameters and other settings for the omsi_access.views.

.. automodule:: omsi_access.views_definitions
    :members:
    :undoc-members:
    :show-inheritance:

:mod:`views_helper` Module
--------------------------

Module with reusable helper functions for omsi_access.views.

.. automodule:: omsi_access.views_helper
    :members:
    :undoc-members:
    :show-inheritance:

:mod:`models` Module
--------------------

Currently no access to a database are implemented in this module.

.. automodule:: omsi_access.models
    :members:
    :undoc-members:
    :show-inheritance:

:mod:`tests` Module
-------------------

Currently no tests are defined for this module.

.. automodule:: omsi_access.tests
    :members:
    :undoc-members:
    :show-inheritance:

