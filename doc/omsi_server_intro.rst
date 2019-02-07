Introduction
============

The OMSI web application is based on the DJANGO web framework and consists of the following packages:

 * **Main Project** (``omsi_server``) This package defines the main DJANGO project.
 * **Data Access** (``omsi_access``) This DJANGO application is used to access OMSI HDF5 data files via the web.
 * **Web Client** (``omsi_client``) This DJANGO application defines the web application for the online data viewer. The web client used the ``omsi_access`` module to request data from the server.

Running the DJANGO omsi_server
------------------------------

Using the simple DJANGO webserver the omsi_server can be run locally simply using the following command:

   ``python manage.py runserver``

This starts DJANGO webserver on port 8000. To use a different port simply include it as input parameter, e.g. :

    ``python manage.py runserver 8100``


A Note on Data Security
-----------------------
* User authentication is done via NEWT
* User authorization is done using the omsi_resources app. Currently two modes of file access authorization are available:

    * File authorization based on user permissions managed in a database. This is the primary authorization mechanism.
    * For files that are not in the database, we ensure that not just anyone can directly access data at any path by specifying the a field ALLOWED_DATA_PATHS (i.e., public data locations) and PRIVATE_DATAPATHS (i.e., locations for user-only files) in the local settings of the  DJANOG settings file. Upon request we checks whether the requested file is in fact located at one of the specified locations (or subfolders if ALLOWED_DATAPATHS_EXACT is False).


How are URL's constructed
-------------------------

The exact syntax for the URL's are defined in ``omsi_server/omsi_access/urls``. The basic scheme used for construction URL's is as follows

``<baseURL>/<command>/?querystring`` : The function parameters are encoded in the query-string of the URL *(Recomended)*

  **URL Components**

  * ``<baseURL>`` : The basic URL where the server is running, e.g. https://openmsi.nersc.gov/openmsi/
  * ``<command>`` : Depending on which data/action we are requesting a different command is used:

        * ``client`` : Request client webpages. The specific webpages are requested via, e.g., ...client/viewer
        * ``qslice`` : Request ion-slices (raw or derived) from the data
        * ``qspectrum`` : Request spectra (raw or derived) from the data
        * ``qcube`` : Request arbitrary subsets of the data
        * ``qmz`` : Request information about the m/z axis of the data
        * ``qmetadata`` : Request metadata informatio about a file, experiment, anlysis etc.

  **Common query-string parameters**

  * ``file`` : The filename/path of the OpenMSI HDF5 datafile to be used.
  * ``expIndex`` : The index of the experiment stored in the file.
  * ``dataIndex`` : The index of the MSI dataset to be used.
  * ``anaIndex`` : The index of the analysis dataset to be used (default None). Either andIndex or anaIdentifier must be provided.
  * ``anaIdentifier`` : Identifier string of the analysis dataset (default None). Either andIndex or anaIdentifier must be provided.
  * ``anaDataName``: Name of the analysis dataset that should be retrieved. (default None).
  * ``row`` : Selection string for the row in the image. [row,:,:] in array notation.
  * ``col`` : Selection string for the column in the image. [:,col,:] in array notation.
  * ``format`` : Output format of the returned data, one of: JSON or PNG.
  * ``row2`` : Secondary selection string for the row in the image.
  * ``col2`` : Secondary selection string for the column in the image.
  * ``findPeaks`` : Execute local peak finding for the retrieved data (only used if format==JSON).
  * ``normalize`` : Should the data retireved be normalized by dividing by the maximum value retrieved (1=True , 0=False). This parameter is only used if format==JSON.
  * ``reduction`` : Data reduction to be applied to the slices (axis=2). Reduction operations are defined as strings indicating the numpy function to be used for reduction. Valid reduction operations include e.g.: min, max, mean, median, std, var etc.. The default value is None if format==JSON. The default value is 'max' if format==PNG.
  * ``axis`` : The axis along which the reduction operation should be applied  (default value 2, i.e., the mz axis).
  * ``operations``, ``operations1``, ``operations2`` : Data operations to be applied to the data. JSON string with list of dictionaries or a python list of dictionaries. Each dict specifies a single data transformation or data reduction that are applied in order. See omsi.shared.omsi_data_selection.transform_and_reduce_data(...) for details.
  * ``mtype`` : Type of metadata requested, one of: ``filelist``, ``file``, ``experiment``, ``experimentFull``, ``analysis``, ``instrument``, ``sample`` .
  * ``viewerOption`` : For some analysis, multiple visualization modes are available, i.e., different combinations of data may be viewed in the online viewer.
  * etc. ...


Web Client: Requesting Webpages
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* ``<baseURL>/client/<command>``

  * ``<baseURL>`` : The basic URL where the server is running, e.g. https://openmsi.nersc.gov/openmsi/
  * ``<command>`` : Depending on which page is requested this may be:

     * empty : Same as ``index``.
     * ``index`` : Request main OpenMSI page (e.g., https://openmsi.nersc.gov/openmsi/client/ )
     * ``publications`` : Request the OpenMSI publications page.
     * ``about`` : Request the about OpenMSI page with project information.
     * ``login`` : Login page

        * ``next`` : Query-string parameter indicating where the user should be pointed to after login is complete.

     * ``logout`` : Logout

        * ``next`` : Query-string parameter indicating where the user should be pointed to after login is complete.

     * ``test`` : Simple page for testing access performance.
     * ``news`` : Request the page with OpenMSI news.
     * ``contact`` : Request the page with contact the OpenMSI team.
     * ``examples`` : Request the page with a series of examples illustrating the use of OpenMSI.
     * ``viewer`` : Request the page with the OpenMSI web viewer application. The viewer page supports a number of optional query string parameters to initalize the viewer:

        **Color channel setting query-string parameters:**

        * ``channel1Value`` : Floating point number indicating the m/z value to be used for the red channel
        * ``channel2Value`` : Floating point number indicating the m/z value to be used for the green channel
        * ``channel3Value`` : Floating point number indicating the m/z value to be used for the blue channel
        * ``rangeValue`` : Floating point number indicating the m/z range for the color channels

        **Viewer cursor 1 settings query-string parameters:**

        * ``cursorCol1`` : X position to be used for the first cursor. NOTE: Only used if ``cursorRow1`` is given as well.
        * ``cursorRow1`` : Y position to be used for the first cursor. NOTE: Only used if ``cursorCol1`` is given as well.

        **Viewer cursor 2 settings query-string parameters:**

        * ``cursorCol2`` : X position to be used for the second cursor. NOTE: Only used if ``cursorRow2`` is given as well.
        * ``cursorRow2`` : Y position to be used for the second cursor. NOTE: Only used if ``cursorCol2`` is given as well.

        **Data settings query-string parameters:**

        * ``file`` : The file to be opened in the viewer (if the file is valid)
        * ``expIndex`` : Integer index of the experiment to be loaded. NOTE: Will be ignored in case that no or an invalid ``file`` is given.
        * ``dataIndex`` : Integer index of the dataset to be loaded. NOTE: Will be ignored in case that no or an invalid ``file`` is given.
        * ``anaIndex`` : Integer index of the analysis to be loaded. NOTE: Will be ignored in case that no or an invalid ``file`` is given as well as in case that a ``dataIndex`` has been provided.

        **Example ``viewer`` URL**

            * http://127.0.0.1:8000/openmsi/client/viewer/?&file=/Users/oruebel/Devel/openmsi/data/11042008_NIMS.h5&expIndex=0&dataIndex=0&channel1Value=200&channel2Value=300&channel3Value=400&rangeValue=0.5&cursorCol1=10&cursorRow1=100&cursorCol2=20&cursorRow2=50


Data Server 1: Requesting m/z data ``qmz``, ``qaxes``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* Request static mz axes information:

    * https://openmsi.nersc.gov/openmsi/qmz/?
    * https://openmsi.nersc.gov/openmsi/qaxes/?
    * For details see also omsi_access.views.get_mz
    * Required query string parameters include:

        * ``file`` : The filename/path of the OpenMSI HDF5 datafile to be used
        * ``expIndex`` : The index of the experiment stored in the file

    * Required query parameters when requesting from raw MSI data

        * ``dataIndex`` : The index of the MSI dataset to be used

    * Required query parameters when requesting from analysis data

        * ``anaIndex`` : The index of the analysis dataset to be used. Note, anaIndex or anaIdentifier are redundant and only one should be sepcified.
        * ``anaIdentifier`` : Identifier string of the analysis dataset. Note, andIndex or anaIdentifier are redundant and only one should be sepcified.
        * ``qslice_viewerOption`` : Integer indicating which qslice viewerOption should be used. Some analysis may support multiple different viewer behaviors for the qslice URL pattern. This optional parameter is used to indicate which viewer behavior should be used.
        * ``qspectrum_viewerOption`` : Integer indicating which qspectrum viewerOption should be used. Some analysis may support multiple different viewer behaviors for the qspectrum URL pattern. This optional parameter is used to indicate which viewer behavior should be used.


    *Additional optional query parameters**

       * ``precision`` : Integer value indicating the maximum number of floating point precision to be used for the returned m/z object.
       * ``format``: Output format of the returned data, one of: 'JSON', 'PNG', or 'HDF5' as defined by views_definitions.views_definitions.available_formats. (default=JSON)
       * ``layout``: Specification of the layout to be used for the m/z axis. E.g., default vs. hilbert.


    * Returns error message or JSON object with the following entries:

        * ``values_spectra`` : Axes values for the spectra or null if missing in the data.
        * ``label_spectra`` : Axes label to be used for the spectrum axes.
        * ``values_slice`` : Optional. This entry is only present if different from 'values_spectra'. Values for z axes identfying the different image slices or null if missing in the data.
        * ``label_slice`` : Optional. This entry is only present if different from 'label_spectra'. Label for the z axes of the image slices.
        * ``values_x`` : Optional. This entry is only present if we have a 1D+ image. Values for the x axis of the image identify the different pixel locations.
        * ``label_x`` : Optional. Label for the x-axis of the image.
        * ``values_y`` : Optional. This entry is only present if we have a 2D+ image. Values for the y axis of the image identify the different pixel locations.
        * ``label_y`` : Optional. Label for the y-axis of the image.
        * ``values_z`` : Optional. This entry is only present if we have a 3D+ image. Values for the z axis of the image identify the different pixel locations.
        * ``label_z`` : Optional. Label for the z-axis of the image.

    * Example 1: Raw data

        * URL: https://openmsi.nersc.gov/openmsi/qmz/?file=/project/projectdirs/openmsi/omsi_data/TEST.h5&dataIndex=0
        * Returns:  {"values_spectra": [409.85882568359375, 409.87069702148438, .... 1504.997802734375, 1505.0205078125], "label_spectra": "m/z"}

    * Example 2: Analysis

        * URL: https://openmsi.nersc.gov/openmsi/qmz/?file=/project/projectdirs/openmsi/omsi_data/TEST.h5&anaIndex=1
        * Returns:  {"values_spectra": [1, 2, 3, ....], "label_spectra": "Component Index"}


Data Server 2: Requesting spectra ``qspectrum``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* Request JSON object of a single or multiple spectra or the difference of two or multiple spectra. For PNG images currently only single spectra request (i.e., reduced spectra) is supported.:

    * https://openmsi.nersc.gov/openmsi/qspectrum/?....
    * Required query arguments:

        * ``filename`` : The filename/path of the OpenMSI HDF5 datafile to be used
        * ``expIndex`` : The index of the experiment stored in the file
        * ``format`` : Output format of the returned data, one of: JSON or PNG
        * ``row`` : Selection string for the row in the image. [row,:,:] in array notation. See Section :ref:`server-data-selection`
        * ``col`` : Selection string for the column in the image. [:,col,:] in array notation. See Section :ref:`server-data-selection`

    * Required query arguments when requesting from raw MSI data

        * ``dataIndex`` : The index of the MSI dataset to be used

    * Required query arguments when requesting analysis data

        The following parameters are used to request "spectra" from derived analysis data.

        * ``anaIndex`` : The index of the analysis dataset to be used (default None). Note, anaIndex or anaIdentifier are redundant and only one should be sepcified.
        * ``anaIdentifier`` : Identifier string of the analysis dataset (default None). Note, andIndex or anaIdentifier are redundant and only one should be sepcified.
        * ``anaDataName`` : Name of the analysis dataset that should be retrieved. (default None). If not provided then the function will try and figure out which dataset to be used based on what the analysis specifies as data to be used.
        * ``viewerOption`` : Integer indicating which default behavior should be used for the given analysis (if multiple options are available). (Default=0)

    * Optional query parameters

        * ``findPeaks`` : Execute local peak finding for the retrieved data (only used if format==JSON)
        * ``layout`` : Parameter used to specify the requested data layout. Available options are specified in omsi_access.views_definitions.available_layouts. Currently available options include:

            * ``default`` : Let the server function decide on the default data layout.
            * ``hilbert`` : Use a 2D hilbert data layout. Currently only supported by qspectrum and qmz.

    * Optional query parameters when requesting difference spectra:

        * ``row2`` : Secondary selection string for the row in the image of the second pixel/spectrum to be loaded. If a second location is given, then the difference spectrum will be returned. See Section :ref:`server-data-selection`
        * ``col2`` : Secondary selection string for the column in the image of the second pixel/spectrum to be loaded. If a second location is given, then the difference spectrum will be returned. See Section :ref:`server-data-selection`

    * Optional query parameter for data processing:

        * ``operations`` : Data operations to be applied to the final data. JSON string with list of dictionaries or a python list of dictionaries. Each dict specifies a single data transformation or data reduction that are applied in order. See omsi.shared.omsi_data_selection.transform_and_reduce_data(...) for details.
        * ``operations1`` : Data operations to be applied to primary selection (x,y). JSON string with list of dictionaries or a python list of dictionaries. Each dict specifies a single data transformation or data reduction that are applied in order. See omsi.shared.omsi_data_selection.transform_and_reduce_data(...) for details.
        * ``operations2`` : Data operations to be applied to secondary selection (x2,y2). JSON string with list of dictionaries or a python list of dictionaries.  Each dict specifies a single data transformation or data reduction that  are applied in order. See omsi.shared.omsi_data_selection.transform_and_reduce_data(...) for details.

    * Examples:

        * https://openmsi.nersc.gov/openmsi/qspectrum/?file=/project/projectdirs/openmsi/omsi_data/TEST.h5&expIndex=0&dataIndex=0&x=10&y=11&findPeaks=1&format=JSON


Data Server 3: Requesting ion slices ``qslice``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* Request JSON object of a single or multiple m/z image slices of the data. For PNG images only a single image may be retrieved at a time.

    * https://openmsi.nersc.gov/openmsi/qslice/?....

    * Required query arguments:

        * ``filename`` : The filename/path of the OpenMSI HDF5 datafile to be used
        * ``expIndex`` : The index of the experiment stored in the file
        * ``mz`` : String specifying which image slices should be retrieved. See Section :ref:`server-data-selection`
        * ``format``: Output format of the returned data, one of: JSON or PNG

    * Required query argments when requesting from raw MSI data

        * ``dataIndex`` : The index of the MSI dataset to be used

    * Required query arguments when requesting analysis data

        The following parameters are used to request "spectra" from derived analysis data.

        * ``anaIndex`` : The index of the analysis dataset to be used (default None). Note, anaIndex or anaIdentifier are redundant and only one should be sepcified.
        * ``anaIdentifier`` : Identifier string of the analysis dataset (default None). Note, andIndex or anaIdentifier are redundant and only one should be sepcified.
        * ``anaDataName`` : Name of the analysis dataset that should be retrieved. (default None). If not provided then the function will try and figure out which dataset to be used based on what the analysis specifies as data to be used.
        * ``viewerOption`` : Integer indicating which default behavior should be used for the given analysis (if multiple options are available). (Default=0)

    * Optional query parameters:

        * ``operations`` :  JSON string with list of dictionaries or a python list of dictionaries. Each dict specifies a single data transformation or data reduction that are applied in order.
                           See omsi.shared.omsi_data_selection.transform_and_reduce_data(...)
                           for details. If no operations are specified, then by default a maximum
                           projection will be performed '{"reduction": "max", "axis": 2}'. If
                           format is PNG, then normalization is performed in addition,
                           '{"transformation": "minusMinDivideMax"}',
    * Examples

        * https://openmsi.nersc.gov/openmsi/qslice/?file=/project/projectdirs/openmsi/omsi_data/TEST.h5&expIndex=0&dataIndex=0&z=0:20&reduction=mean&format=PNG

Data Server 4: Requesting general data subsets  ``qcube``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* Request JSON object of general subsets of the original MSI data or derived analysis data

    * https://openmsi.nersc.gov/openmsi/qcube/?....
    * Required query arguments:

       * ``filename`` : The filename/path of the OpenMSI HDF5 datafile to be used
       * ``expIndex`` : The index of the experiment stored in the file

    * Required if original MSI data is requested:

       * ``dataIndex`` : The index of the MSI dataset to be used (Required only  if raw analysis data is requested)

    * Required if analysis data is requested:

       * ``anaIndex`` : The index of the analysis dataset to be used (default None). Either andIndex or anaIdentifier must be provided.
       * ``anaIdentifier`` : Identifier string of the analysis dataset (default None). Either andIndex or anaIdentifier must be provided.
       * ``anaDataName`` : Name of the analysis dataset that should be retrieved.

    * Required for specification of data selections:

       * ``row`` : Selection string for the row in the image. [row,:,:] in array notation. Default value is ":" (i.e. all). See Section :ref:`server-data-selection`
       * ``col`` :  Selection string for the column in the image. [:,col,:] in array notation Default value is ":" (i.e. all). See Section :ref:`server-data-selection`
       * ``mz`` :  Selection string for the data axis dimensions of the image. [:,:,mz] in array notation. Default value is ":" (i.e. all). See Section :ref:`server-data-selection`

    * Optional query arguments:

       * format : The format of the requested return object. This is one of either: \
                  JSON, PNG, or HDF5 as defined in views_definitions.available_formats. \
                  Note, support for PNG is limited for qcube. (Default: 'JSON')
       * operations:  JSON string with list of dictionaries or a python \
                      list of dictionaries. Each dict specifies a single data \
                      transformation or data reduction that are applied in order. \
                      See omsi.shared.omsi_data_selection.transform_and_reduce_data(...) \
                      for details.

    * Example:

        * https://openmsi.nersc.gov/openmsi/qcube/?file=/project/projectdirs/openmsi/omsi_data/TEST.h5&expIndex=0&dataIndex=0&zmin=0&zmax=10&reduction=mean

Data Server 5: Requesting metadata  ``qmetadata``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* **Request JSON object of metadata pertaining to: filelist, file, experiment, analysis, instrument or sample:**

    * https://openmsi.nersc.gov/openmsi/qmetadata/?....
    * Required query arguments:

        * ``mtype`` : Type of metadata requested, one of:

               * ``filelistView`` : Dictionary of all files the current user can view
               * ``filelistEdit`` : Dictionary of all files the current user can edit
               * ``filelistManage`` : Dictionary of all files the current user can manage
               * ``filelistRawData`` : Dictionary of all raw data files the current user owns
               * ``file`` : Basic file metadata describing the complete structure of the file.
               * ``provenance`` : Get the provenance information for the specified object.

    * Required query arguments for any type other than ``filelist*``

        * ``filename`` : The filename/path of the OpenMSI HDF5 datafile to be used

    * Optional query arguments for mtype ``file`` and ``provenance`` :

        The following parameters are used specify specific objects within a file.

        * ``expIndex`` : The index of the experiment stored in the file
        * ``anaIndex`` : The index of the analysis dataset to be used (default None). Either andIndex or anaIdentifier must be provided.
        * ``anaIdentifier`` : Identifier string of the analysis dataset (default None). Either andIndex or anaIdentifier must be provided.
        * ``dataIndex`` : Index of the MSI dataset (only when requesting information for a raw MSI dataset).
        * ``anaDataName`` : Name of the analysis dataset for which metadata information is requested


    *Optional querystring parameters*

        * format : The format of the requested return object. This is one of either:  \
                   JSON or HDF5 as defined in views_definitions.available_formats. Note, \
                   PNG is currently not supported by get_metadata. (Default: 'JSON')
        * `nameKey` : Used to indicate which key name should be used to store object names. (Default: 'name')
        * `childKey` : Used to indcate which key name should be used to store lists of children. (Default: '_children')
        * `depth` : Used by qmetadata mtype==file to indicate until which path depth the \
                    childKey should be used. For path deeper than depth an '_' is prepanded to childKey. \
                    This is used to indcate for D3 which children should be displayed and which one should \
                    be expanded by default.

    * Examples:

        * Request list of available OMSI HDF5 files:

             * https://openmsi.nersc.gov/openmsi/qmetadata/?mtype=filelist

        * Request file metadata:

            * https://openmsi.nersc.gov/openmsi/qmetadata/?file=/project/projectdirs/openmsi/omsi_data/TEST.h5&mtype=file

        * Request experiment metdata:

            * https://openmsi.nersc.gov/openmsi/qmetadata/?file=/project/projectdirs/openmsi/omsi_data/TEST.h5&expIndex=0&mtype=file

        * Request extended experiment metdata inculding information about all datasets, analyses, instrument, sample:

            * https://openmsi.nersc.gov/openmsi/qmetadata/?file=/project/projectdirs/openmsi/omsi_data/TEST.h5&expIndex=0&mtype=experiment

        * Request instrument metdata:

            * https://openmsi.nersc.gov/openmsi/qmetadata/?file=/project/projectdirs/openmsi/omsi_data/TEST.h5&expIndex=0&mtype=instrument

        * Request sample metdata:

            * https://openmsi.nersc.gov/openmsi/qmetadata/?file=/project/projectdirs/openmsi/omsi_data/TEST.h5&expIndex=0&mtype=sample

        * Request experiment metdata:

            * https://openmsi.nersc.gov/openmsi/qmetadata/?file=/project/projectdirs/openmsi/omsi_data/TEST.h5&expIndex=0&anaIndex=0&mtype=analysis


.. _server-data-selection:


Data Selection 1: Basic Slicing
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The data request URL's commonly support data selection parameters, e.g., ``x``, ``y``, or ``z`` , which are used to select the data that should be retrieved. There are several basic ways in which a user may specify data selections:

    * **Range selection:** ``a:b`` indicated that all values in the range of ``a`` and ``b`` should be selected (while the upper bound is not included in the selection). ``1:10`` selects ``1,2,3,4,5,6,7,8,9``.
    * **Index selection:** ``a`` specifies a single index ``a`` that should be selected. NOTE: Specifying a single index usually implies that the dimensionality of the returned array is reduced by 1. E.g., a selection of [1,4,5] usually results in the retrieval of a single scalar corresponding do the item with index 1,4,5. In contrast, the same selection specified via multiple index lists or range-selection may result in the retrieval of a multi-dimensional array containing the scalar.
    * **All:** ``:`` indicates that all values, i.e., the full range for the given dimension, should be selected.
    * **Index list:** ``[a,b,c,d]`` indicates that the indicies ``a,b,c,d`` should be selected.

Data Selection 2: Multi-dimensional Slicing
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Several data URL's supported multiple selection parameters, e.g., ``x`` and ``y`` in qspectrum. These parameters are combines ``[x,y,:]`` to allow retrieval of data from multi-dimensional arrays. The semantic for different combinations follows a the same strategy as numpy (and h5py) :

    * **All-to-all:** Most combinations of selections follow the all-to-all combination principal. That is all elements in the selection specified for ``x`` are combined with the selection specified for ``y``. ``x=1:4`` and ``y=1:3``, hence, results in the retrieval of the elements ``[(1,1), (1,2), (2,1), (2,2) (3,1), (4,2)]``. All-to-all selection, hence, always result in the retrieval of of a single or multiple rectangular regions.
    * **Multiple index lists:** In case that multiple index list selections are specified the lists are matched. This means if multiple lists are specified, then the lists must be of equal lenght and the lists are merged to define specific index-pairs to be selected. E.g, ``x=[1,2]` and ``y=[4,5]`` results in the retrieval of the elements ``[ (1,4), (2,4) ]`` compared to the all-to-all matching, which would retrieve ``[ (1,4), (1,5), (2,4), (2,5) ]``. This allows for selection of arbitrary regions of interest. NOTE: When specifying multipled index lists, the dimensionality of the returned array may be reduced.

Data Selection 3: Limitations
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    * If a single index list is given in a selection then the indicies are expected to be in increasing order. This is due to the use of h5py for data selection on the server side. NOTE: If multiple index lists are given, then this limitation does not apply as the lists are merged on the server side.
    * If multiple index lists are given then the lists must have the same length as the lists are matched and merged on the server side.
    * For PNG images, the server currently supports the retrieval of only singel images at a time (in contrast to JSON for which the server can return multiple data items at a time). Therefore, if a PNG image is requested a default reduction operation is applied (mean spectrum, max image) and a single image is returned. In contrast, if no reduction operation is specified for JSON requests, then the full data will be returned.

Data Operations:
^^^^^^^^^^^^^^^^

Data operations allow a user to specify complex data transformations and reduction operations that should be performed on the data. These operations are specified via JSON objects using the capabilities provided by BASTet as part of the ``omsi.shared.omsi_data_selection`` class.

For a lists of available data operations see:

    * ``omsi.shared.omsi_data_selection.reduction_allowed_numpy_function`` : List of allowed data reduction operations. Reduction operations are any single data operation that may change the shape of the data.
    * ``omsi.shared.omsi_data_selection.transformation_type`` : List of available data transformations.

        * For transformation type is ``singleDataTransform`` or ``scale``, see ``omsi.shared.omsi_data_selection.transformation_allowed_numpy_single_data`` for the list of allowed data transformation that operate on a single input data array that do not change the shape of the data.
        * For transformation type is ``dualDataTransform`` or ``arithmetic``, see ``omsi.shared.omsi_data_selection.transformation_allowed_numpy_dual_data`` for the list of allowed data transformations that operator on two input data arrays but the output assumes the shape of one of the two arrays (in most cases the first array).

The ``omsi.shared.omsi_data_selection`` module also provides a number of helper functions to assist with the construction of specifications for data operations. See:

  * ``omsi.shared.omsi_data_selection.construct_reduce_dict`` : Construct a python dictionary describing a given data reduction.
  * ``omsi.shared.omsi_data_selection.construct_transform_dict`` : Construct a python dictionary describing a given data transformation.
  * ``omsi.shared.omsi_data_selection.construct_transform_reduce_list`` : Merge a series of data operations to a list of operations to be executed one-after-the-other in a pipeline fashion.
  * ``omsi.shared.omsi_data_selection.transform_reduce_description_to_json`` : Convert a python description of a data operations pipeline to a JSON description.
  * ``omsi.shared.omsi_data_selection.json_to_transform_reduce_description`` : Convert a JSON description of a pipeline to python.
  * ``omsi.shared.omsi_data_selection.is_transform_or_reduce``

Some notes on common behavior of data operations:

    * If an input data array (parameter ``x1``, ``x2``) is not specified for a given data operation, then the output of the previous operation is used a input.
    * An input data array (parameter ``x1``, ``x2``) may itself be a description of a data operation that is executed in order to generate the input for that function.
    * Data operations are executed in a pipeline fashion one-after-the-other.
    * Branching and loop operations are currently not yet supported.
    * The output of a given data operation may be assigned a name by setting the ``variable`` parameter to a user-defined name for the data operation. This variable may then be reused as input (``x1``, ``x2``) parameter of subsequent data operations.

.. code-block:: python
    :linenos:

    plow = construct_reduce_dict( reduction_type='percentile' ,
                                  q=lower_percentile ,
                                  x1='reduce_max',
                                  variable='plow')
    minus_plow = construct_transform_dict( trans_type='arithmetic' ,
                                         operation='subtract',
                                         x1='reduce_max',
                                         x2='plow')

Here an example of such a data processing pipeline for the purpose of computing a maximum projection images from a series of ion-images and normalizing the image based on the 5th and 95th percentile.

1.1) Example:
"""""""""""""

Compute normalized maximum projection of data. This type of data operation is used in OpenMSI, e.g, to compute ion-images for visualization. The script defines the following basic operations.

    1) perform maximum projection along the last axis (i.e., the m/z axis) if the input data has 2 or more dimensions.
    2) compute the 5th percentile for all values larger than 0 of the the output of step 1  and subtract the value from the output of step 1
    3) compute the 95th percentile for all values larger than 0 of the output of step 2 and divide the output of step 2 by the computed value
    4) clip the output of step 3 to the range [0,1], i.e., set all values <0 to 0 and all values >1 to 1.


1.2) Constructing a Data Operations Specification
"""""""""""""""""""""""""""""""""""""""""""""""""

The following example shows how we can use the helper functions provided by omsi.share.omsi_data_selection to construct a specification of the data operation.

.. code-block:: python
    :linenos:

    from omsi.shared.omsi_data_selection import construct_reduce_dict, \
                                                construct_transform_dict, \
                                                transform_reduce_description_to_json

    #1) Reduce by max
    reduce_max = construct_reduce_dict(reduction_type='max',
                                       axis=-1,
                                       min_dim=2)

    #1.1) Compute the lower percentile
    select_larger_0 = construct_reduce_dict( reduction_type='select_values',
                                             selection = construct_transform_dict( trans_type='arithmetic',
                                                                            operation = 'greater',
                                                                            x2=0))
    plow = construct_reduce_dict( reduction_type='percentile' ,
                                  q=lower_percentile,
                                  x1=select_larger_0)
    #1.2) Substract the lower percentile
    minus_p5 = construct_transform_dict( trans_type='arithmetic' ,
                                         operation='subtract',
                                         x2=plow )
    #2.1) Compute the upper percentile
    phigh = construct_reduce_dict( reduction_type='percentile',
                                   q=upper_percentile,
                                   x1=select_larger_0)
    #2.2) Convert phigh to float
    phigh_as_float = construct_transform_dict( trans_type='astype' , dtype='float', x1=phigh)
    #2.2) Divide by the upper percentile
    divide_by_p95 = construct_transform_dict( trans_type='arithmetic',
                                              operation='divide',
                                              x2=phigh_as_float )
    #3) Clip the data so that all values >1 are set to 1 and all values smaller than 0 are set to 0
    clip = construct_transform_dict( trans_type='scale',
                                     operation='clip',
                                     a_min=0,
                                     a_max=1 )
    #4) Combine the data operations to a pipeline for: i) maximum projection, ii)-5p, iii) \95p, iv) clip.
    operations_json = transform_reduce_description_to_json(reduce_max, minus_p5, divide_by_p95 , clip)


1.3) Illustration of the calculation performed:
"""""""""""""""""""""""""""""""""""""""""""""""
Illustration::

                   |--select_values( .. , greater(..,0))--|
                   |                                      |
                   |----------------------->percentile(x1=|, q=5)--|
                   |                                               |
    data-->reduce(max)---------------------------------->minus(.., | )----\
                                                                          |
            /------------------------------------------------------------ /
            |
            |
            |      |--select_values( .. , greater(..,0))--|
            |      |                                      |
            |      |----------------------->percentile(x1=|, q=95)-->astype('float')--|
            |      |                                                                  |
            \----- -------------------------------------------------------divide(.. , |)
                                                                                      |
                                                                                      |
                                                                                  clip(0,1)
                                                                                      |
                                                                                      |
                                                                                    output


1.4) JSON description of the above calculation:
"""""""""""""""""""""""""""""""""""""""""""""""

``[{"min_dim": 2, "reduction": "max", "axis": -1}, {"x2": {"q": 5.0, "reduction": "percentile", "x1": {"reduction": "select_values", "selection": {"x2": 0, "operation": "greater", "axes": null, "transformation": "arithmetic"}}}, "operation": "subtract", "axes": null, "transformation": "arithmetic"}, {"x2": {"dtype": "float", "x1": {"q": 95.0, "reduction": "percentile", "x1": {"reduction": "select_values", "selection": {"x2": 0, "operation": "greater", "axes": null, "transformation": "arithmetic"}}}, "axes": null, "transformation": "astype"}, "operation": "divide", "axes": null, "transformation": "arithmetic"}, {"operation": "clip", "axes": null, "a_max": 1, "transformation": "scale", "a_min": 0}]``

.. _dataopeationsjson_figure:

.. figure:: _static/data_operation_json.*
   :scale: 70 %
   :alt: Illustration of the layout of the JSON object specifying a data operations processing pipeline.

   Illustration of the layout of the JSON object specifying the data operation processing pipeline.


