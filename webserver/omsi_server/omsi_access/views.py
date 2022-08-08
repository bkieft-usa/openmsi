# TODO: User authorization
#  1) Modify the filelist metadata call to return a list of public, private and group-owned files
# https://docs.djangoproject.com/en/dev/topics/auth/default/#topic-authorization

# TODO: HDF5 download
#  1) Add temporary data location for DJANGO
#  2) Add cronjob for cleaning up the data location. Usually all temporary files are erased automatically
#     but we need to make sure that we not clutter up the system
#  3) Modify the views to use the numpy_to_hdf5... function to create an hdf5 download for specific data requests
#  4) Modify the qcube function to allow retrieval of complete files, experiments, analyses and datasets
#

# Get the DJANGO settings, e.g., to get the default file path
from django.conf import settings
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseForbidden, HttpResponseBadRequest
# Usually we should have the json module in python but in case we don't
# use simplejson as fallback solution
try:
    import json
except ImportError:
    from django.utils import simplejson as json
from django.core.cache import cache
import numpy as np
import sys
import os
import time

from django.views.decorators.csrf import csrf_exempt

from omsi.dataformat.omsi_file.analysis import omsi_file_analysis
from omsi.analysis.findpeaks.omsi_findpeaks_local import omsi_findpeaks_local
from omsi.analysis.analysis_views import analysis_views
from omsi.analysis.base import analysis_base
import omsi.shared.data_selection as omsi_data_selection
from omsi.shared.spectrum_layout import compute_hilbert_spectrum, plot_2d_spectrum_as_image
from omsi_server import *
try:
    from omsi_server.omsi_resources import omsi_file_authorization
except:
    from omsi_resources import omsi_file_authorization
import logging
logger = logging.getLogger(__name__)

import views_definitions
import views_helper


# Additional libraries used
# - from PIL import Image : see get_data_slice( ... )  (only if respFormat=='PNG' in both cases)
# - import matplotlib.pyplot as plt : see  get_data_spectrum(...) (only if respForma=='PNG' in both cases)
#//////////////////////////////////////////////////////////////////
#///             Django MZ axes Views                           ///
#//////////////////////////////////////////////////////////////////
def get_axes(request):
    """
    Helper function to remap qmz to qaxes as well
    """
    return get_mz(request)

def get_mz(request):
    """DJANGO view for requesting information about the axes for image slices and spectra. In the case of
       raw data this would be the m/z values of the intrument.The input parameters are specified in the
       HttpRequest. This function uses get_mzaxes(...) to retrieve the requested data.

       :param request: HttpRequest object. This object needs to specify in the request.GET query dictionary
                       the query parameters listed below.

       :returns: HTTPResponse with the requested data or error message.

       **Required query arguments:**

       * filename : The filename/path of the OpenMSI HDF5 datafile to be used
       * expIndex : The index of the experiment stored in the file

       **Required query argments when requesting from raw MSI data**

       * dataIndex : The index of the MSI dataset to be used

       **Required query arguments when requesting analysis data**

       * anaIndex: The index of the analysis dataset to be used (default None). Note, anaIndex or \
                   anaIdentifier are redundant and only one should be specified.
       * anaIdentifier: Identifier string of the analysis dataset (default None). Note, andIndex or \
                   anaIdentifier are redundant and only one should be specified.
        * qslice_viewerOption: Integer indicating which qslice viewerOption should be used. \
                   Some analysis may support multiple different viewer behaviors for the qslice URL \
                  pattern. This optional parameter is used to indicate which viewer behavior should be used.
        * qspectrum_viewerOption: Integer indicating which qspectrum viewerOption should be used. \
                  Some analysis may support multiple different viewer behaviors for the qspectrum URL \
                  pattern. This optional parameter is used to indicate which viewer behavior should be used.


       **Additional optional query parameters**

       * precision : Integer value indicating the maximum number of floating point precision to be \
                     used for the returned m/z object.
       * format: Output format of the returned data, one of: 'JSON', 'PNG', or 'HDF5' as defined \
                 by views_definitions.views_definitions.available_formats. (default=JSON)
       * layout: Specification of the layout to be used for the m/z axis. E.g., default vs. hilbert.

       :returns: django.http.HttpResponse with JSON object with:

            * with the axes information containing a dictionary with the following entries:

                * 'values_spectra' : Axes values for the spectra.
                * 'label_spectra' : Axes label to be used for the spectrum axes
                * 'values_slice' : Optional. This entry is only present if different \
                                   from 'values_spectra'. Values for z axes identifying \
                                   the different image slices.
                * 'label_slice' : Optional. This entry is only present if different from \
                                  'label_spectra'. Label for the z axes of the image slices.

            * Error message (e.g., HttpResponseNotFound etc. )

    """
    logger.debug("Entering view")

    try:
        filename = request.GET[views_definitions.query_parameters['file']]
        expIndex = int(
            request.GET[views_definitions.query_parameters['expIndex']])
    except:
        if settings.DEBUG:
            raise
        else:
            return HttpResponseNotFound("A required query parameter could not be read.")

    filename, filemodel, filetype = omsi_file_authorization.authorize_fileaccess(
        request=request, infilename=filename)
    if isinstance(filename, HttpResponse):  # Check if an error occured
        return filename

    # Get optional input parameters
    try:
        respFormat = request.GET.get(
            views_definitions.query_parameters['format'],
            views_definitions.available_formats['JSON'])
        if respFormat not in views_definitions.available_formats.values():
            return HttpResponseNotFound(
                "Invalid response format requested. " +
                str(respFormat) + "Valid formats are: " +
                views_definitions.available_formats.values())
        dataIndex = request.GET.get(
            views_definitions.query_parameters['dataIndex'],
            None)
        anaIndex = request.GET.get(
            views_definitions.query_parameters['anaIndex'],
            None)
        anaIdentifier = request.GET.get(
            views_definitions.query_parameters['anaIdentifier'],
            None)
        qslice_viewerOption = int(request.GET.get(
            views_definitions.query_parameters['qslice_viewerOption'], 0))
        qspectrum_viewerOption = int(request.GET.get(
            views_definitions.query_parameters['qspectrum_viewerOption'], 0))
        precision = int(request.GET.get(
            views_definitions.query_parameters['precision'], -1))
        layout = request.GET.get(
            views_definitions.query_parameters['layout'],
            views_definitions.available_layouts['default'])
    except:
        if settings.DEBUG:
            raise
        else:
            return HttpResponseNotFound("An optional query parameter could not be read.")

    return get_mzaxes(request=request,
                      filename=filename,
                      expIndex=expIndex,
                      dataIndex=dataIndex,
                      anaIndex=anaIndex,
                      anaIdentifier=anaIdentifier,
                      qslice_viewerOption=qslice_viewerOption,
                      qspectrum_viewerOption=qspectrum_viewerOption,
                      precision=precision,
                      respFormat=respFormat,
                      layout=layout)


def get_mzaxes(request,
               filename,
               expIndex,
               dataIndex=None,
               anaIndex=None,
               anaIdentifier=None,
               qslice_viewerOption=0,
               qspectrum_viewerOption=0,
               precision=-1,
               respFormat=views_definitions.available_formats['JSON'],
               layout=views_definitions.available_layouts['default']):
    """DJANGO view for requesting information about the axes for image slices and spectra. In the case of
       raw data this would be the m/z values of the intrument.

       :param request: The http request object
       :param filename: The filename/path of the OpenMSI HDF5 datafile to be used
       :param expIndex: The index of the experiment stored in the file
       :param dataIndex: The index of the MSI dataset to be used (default is None)
       :param anaIndex: The index of the analysis dataset to be used (default None). \
                        Note, anaIndex or anaIdentifier are redundant and only one \
                        should be specified. Note, if dataIndex is specified (not None) \
                        that the dataIndex takes presence over the analysis request.
       :param anaIdentifier: Identifier string of the analysis dataset (default None).
                        Note, andIndex or anaIdentifier are redundant and only one
                        should be specified. Note, if dataIndex is specified (not None)
                        that the dataIndex takes presence over the analysis request.
       :param qslice_viewerOption: If multiple default viewer behaviors are available
                        for a given analysis then this option is used to switch between
                        them for the qslice URL pattern. (Default=0)
       :param qspectrum_viewerOption: If multiple default viewer behaviors are available
                        for a given analysis then this option is used to switch between
                        them for the qspectrum URL pattern. (Default=0)
       :param precision: Number of digits to be used in the conversion of the mz axis
                        to JSON. By default the standard JSON float encoding is used (-1)
       :param respFormat: Output format of the returned data, one of: 'JSON', 'PNG', or 'HDF5'
                        as defined by views_definitions.available_formats. (default=JSON)
       :param layout: Specification of the layout to be used for the m/z axis.
                        E.g., default vs. hilbert.

       :returns: django.http.HttpResponse with JSON object with:

            * with the axes information containing a dictionary with the following entries:

                * 'values_spectra' : Axes values for the spectra.
                * 'label_spectra' : Axes label to be used for the spectrum axes
                * 'values_slice' : Optional. This entry is only present if different from 'values_spectra'. \
                                   Values for z axes identfying the different image slices.
                * 'label_slice' : Optional. This entry is only present if different from 'label_spectra'. \
                                  Label for the z axes of the image slices.

            * Error message (e.g., HttpResponseNotFound etc. )
    """
    logger.debug("Entering view")

    valuesSpectra = None
    labelSpectra = "m/z"
    valuesSlice = None
    labelSlice = None
    filenameParam = {}
    # Retrieve mz for a derived analysis
    if dataIndex is None:
        filenameParam = {"anaIndex": anaIndex, "anaIdentifier": anaIdentifier}
        anaObj = views_helper.get_omsi_fileobject(
            request=request,
            filename=filename,
            expIndex=expIndex,
            dataIndex=dataIndex,
            anaIndex=anaIndex,
            anaIdentifier=anaIdentifier)
        if not isinstance(anaObj, omsi_file_analysis):
            return HttpResponseNotFound("Error while retrieving analysis." +
                                        "This is likely because either the" +
                                        "anaIndex or anaIdentifier were missing.")
        valuesSpectra, labelSpectra, valuesSlice, labelSlice, valuesX, labelX, valuesY, labelY, valuesZ, labelZ = \
            analysis_views.get_axes(analysis_object=anaObj,
                                    qslice_viewer_option=qslice_viewerOption,
                                    qspectrum_viewer_option=qspectrum_viewerOption)
    # Retrieve m/z for raw data
    else:
        filenameParam = {"dataIndex": dataIndex}
        omsiData = views_helper.get_omsi_fileobject(
            request=request,
            filename=str(filename),
            expIndex=int(expIndex),
            dataIndex=int(dataIndex))
        if isinstance(omsiData, HttpResponse):
            return omsiData
        valuesSpectra = omsiData.mz
        labelSpectra = "m/z"
        valuesSlice = None
        labelSlice = None
        valuesX = range(0, omsiData.shape[0])
        valuesY = range(0, omsiData.shape[1])
        valuesZ = None if len(omsiData.shape) <= 3 else range(0, omsiData.shape[2])
        labelX = 'pixel index X'
        labelY = 'pixel index Y'
        labelZ = None if len(omsiData.shape) <= 3 else 'pixel index Z'

    # Compute the data layout if necessary
    if layout == views_definitions.available_layouts['default']:
        pass
    elif layout == views_definitions.available_layouts['hilbert']:
        if valuesSpectra is not None:
            valuesSpectra, tempI = compute_hilbert_spectrum(
                original_coords=valuesSpectra,
                original_intensities=valuesSpectra)
        if valuesSlice is not None:
            valuesSlice, tempI = compute_hilbert_spectrum(
                original_coords=valuesSlice,
                original_intensities=valuesSlice)

    # Round the data if needed
    if precision >= 0:
        if valuesSpectra is not None:
            valuesSpectra = np.around(valuesSpectra.astype('float'), precision)
        if valuesSlice is not None:
            valuesSlice = np.around(valuesSlice.astype('float'), precision)

    # Define the output data dictionary
    outdata = {}
    if valuesSpectra is not None:
        outdata['values_spectra'] = valuesSpectra.tolist()
    else:
        outdata['values_spectra'] = None
    outdata['label_spectra'] = labelSpectra
    if valuesSlice is not None:
        outdata['values_slice'] = valuesSlice.tolist()
        outdata['label_slice'] = labelSlice
    if valuesX is not None:
        outdata['label_x'] = labelX
        outdata['values_x'] = valuesX
    if valuesY is not None:
        outdata['label_y'] = labelY
        outdata['values_y'] = valuesY
    if valuesZ is not None:
        outdata['label_z'] = labelZ
        outdata['values_z'] = valuesZ

    # Convert the data to JSON
    if precision >= 0:
        try:
            # Try to temporarily monkey-patch the json encoder to define the
            # requested float precision
            from json import encoder
            encoding = "." + str(precision) + "f"
            tempEncode = encoder.FLOAT_REPR
            encoder.FLOAT_REPR = lambda o: format(o, encoding)
            content = json.dumps(outdata)  # Convert the data to JSON
            # Reset the encoding. This is to avoid left-over state, e.g., when
            # using DJANGO's test webserver
            encoder.FLOAT_REPR = tempEncode
        except:
            content = json.dumps(outdata)
    else:
        content = json.dumps(outdata)

    # Return the requested data
    if respFormat == views_definitions.available_formats['JSON']:
        return HttpResponse(
            content=content,
            content_type='application/json')
    elif respFormat == views_definitions.available_formats['HDF5']:
        returnFilename = views_helper.generate_hdf5_filename(
            request=request,
            basefile=filename,
            parameters=filenameParam,
            comment=None)
        return views_helper.numpy_data_to_httpresponse(
            request=request,
            data=outdata,
            respFormat=respFormat,
            returnFilename=returnFilename)
    elif respFormat == views_definitions.available_formats['PNG']:
        return HttpResponseNotFound("PNG is currently not supported by qmz.")
    else:
        return HttpResponseNotFound("Invalid response format requested. " +
                                    str(respFormat) +
                                    "Valid formats are: " +
                                    views_definitions.available_formats.values())


#//////////////////////////////////////////////////////////////////
#///             Django Spectrum Views                          ///
#//////////////////////////////////////////////////////////////////
@csrf_exempt
def get_spectrum(request):
    """DJANOG view for requesting either a JSON object or PNG image of a:

        1) single spectrum, if only are x,y provided in the query string
        2) the difference of two spectra, if x,y,x2,y2 are provided in the query string
        3) A reduced (e.g., max, min, mean, median) spectrum from a range of spectra, \
           if xmin, xmax, ymin, ymax are provided (and not x,y)
        4) the difference of two spectra ranges where each range is reduced first using \
           the given reduction operation to compute, e.g, the mean spectrum

        :param request: HttpRequest object. This object needs to specify in the request.GET
                        query dictionary the query parameters listed below.

        :returns: HTTPResponse with the requested data or error message.

        **Required query arguments:**

        * filename : The filename/path of the OpenMSI HDF5 datafile to be used
        * expIndex : The index of the experiment stored in the file
        * x : x-index of the pixel/spectrum to be loaded
        * y : y-index of the pixel/spectrum to be loaded

        **Required query argments when requesting from raw MSI data**

        * dataIndex : The index of the MSI dataset to be used

        **Required query arguments when requesting analysis data**

        The following parameters are used to request "spectra" from derived analysis data.

        * anaIndex: The index of the analysis dataset to be used (default None). Note, anaIndex \
                    or anaIdentifier are redundant and only one should be sepcified.
        * anaIdentifier: Identifier string of the analysis dataset (default None). Note, andIndex \
                    or anaIdentifier are redundant and only one should be sepcified.
        * anaDataName: Name of the analysis dataset that should be retrieved. (default None). \
                    If not provided then the function will try and figure out which dataset to \
                    be used based on what the analysis specifies as data to be used.
        * viewerOption : Integer indicating which default behavior should be used for the given \
                    analysis (if multiple options are available). (Default=0) Alternatively also \
                     'qspectrum_viewerOption' may be used instead.

        **Optional query parameters**:

        * format : Output format of the returned data, one of: JSON, PNG, or HDF5 as defined in \
                   views_definitions.available_formats. (Default is JSON)
        * precision : Integer value indicating the maximum number of floating point precision to be \
                     used for the returned m/z object.
        * findPeaks : Execute local peak finding for the retrieved data (only used if format==JSON or format==HDF5)
        * operations : Data operations to be applied to the final data. \
                     JSON string with list of dictionaries or a python list of dictionaries. \
                     Each dict specifies a single data transformation or data reduction that \
                     are applied in order. See omsi.shared.omsi_data_selection.transform_and_reduce_data(...) \
                     for details.
        * operations1 : Data operations to be applied to primary selection (x,y). \
                     JSON string with list of dictionaries or a python list of dictionaries. \
                     Each dict specifies a single data transformation or data reduction that \
                     are applied in order. See omsi.shared.omsi_data_selection.transform_and_reduce_data(...) \
                     for details.
        * layout: Specification of the layout to be used for the m/z axis. E.g., default vs. hilbert.

        **Optional query parameters when requesting difference spectra**:
        * x2 : x-index of the second pixel/spectrum to be loaded. If a second location is given, then \
               the difference spectrum will be returned.
        * y2 : y-index of the second pixel/spectrum to be loaded. If a second location is given, then \
               the difference spectrum will be returned.
        * operations2 : Data operations to be applied to secondary selection (x2,y2). \
                      JSON string with list of dictionaries or a python list of dictionaries. \
                      Each dict specifies a single data transformation or data reduction that \
                      are applied in order. See omsi.shared.omsi_data_selection.transform_and_reduce_data(...) \
                      for details.
        * 'operationsMerge': Data operation to be applied to combine the two spectra. \
                      By default the two spectra are merge by computing the difference spectrum. \
                      The first operation must be one of
                      omsi.shared.data_selection.transformation_allowed_numpy_dual_data data operations!
                      We reference the spectra in the transformation by the names `spectrum1`, `spectrum2`.
                      JSON string with list of dictionaries or a python list of dictionaries. \
                      Each dict specifies a single data transformation or data reduction that \
                      are applied in order. See omsi.shared.omsi_data_selection.transform_and_reduce_data(...) \
                      for details.

        **Uses:**

        This function uses other functions to retrieve and return the requested data:

        * get_data_spectrum(...)

        See the documentation of those function for further details.

    """
    logger.debug("Entering view")
    if request.method == 'GET':
        get_method = request.GET
    elif request.method == 'POST':
        get_method = request.POST

    # Get mandatory input parameters
    try:
        filename = get_method[views_definitions.query_parameters['file']]
        expIndex = int(get_method[views_definitions.query_parameters['expIndex']])
        x = get_method[views_definitions.query_parameters['row']]
        y = get_method[views_definitions.query_parameters['col']]
    except:
        if settings.DEBUG:
            raise
        else:
            return HttpResponseNotFound("A required query parameter could not be read.")

    filename, filemodel, filetype = omsi_file_authorization.authorize_fileaccess(
        request=request, infilename=filename)
    if isinstance(filename, HttpResponse):  # Check if an error occured
        return filename

    # Get optional input parameters
    try:
        respFormat = get_method.get(
            views_definitions.query_parameters['format'],
            views_definitions.available_formats['JSON'])
        if respFormat not in views_definitions.available_formats.values():
            return HttpResponseNotFound(
                "Invalid response format requested. " +
                str(respFormat) + "Valid formats are: " +
                views_definitions.available_formats.values())
        x2 = get_method.get(views_definitions.query_parameters['row2'], None)
        y2 = get_method.get(views_definitions.query_parameters['col2'], None)
        operations = get_method.get(views_definitions.query_parameters['operations'], None)
        operations1 = get_method.get(views_definitions.query_parameters['operations1'], None)
        operations2 = get_method.get(views_definitions.query_parameters['operations2'], None)
        operationsMerge = get_method.get(views_definitions.query_parameters['operationsMerge'], None)
        findPeaks = int(get_method.get(views_definitions.query_parameters['findPeaks'], 0))
        dataIndex = get_method.get(views_definitions.query_parameters['dataIndex'], None)
        anaIndex = get_method.get(views_definitions.query_parameters['anaIndex'], None)
        anaIdentifier = get_method.get(views_definitions.query_parameters['anaIdentifier'], None)
        anaDataName = get_method.get(views_definitions.query_parameters['anaDataName'], None)
        layout = get_method.get(views_definitions.query_parameters['layout'],
                                 views_definitions.available_layouts['default'])
        precision = int(get_method.get(views_definitions.query_parameters['precision'], -1))
        # Try to get the viewerOption, if not available get the
        # qspectrum_viewerOption or set to 0 by default
        try:
            viewerOption = int(get_method[views_definitions.query_parameters['viewerOption']])
        except:
            viewerOption = int(get_method.get(views_definitions.query_parameters['qspectrum_viewerOption'], 0))
    except:
        if settings.DEBUG:
            raise
        else:
            return HttpResponseNotFound("An optional query parameter could not be read.")

    if dataIndex is None and anaIdentifier is None and anaIndex is None:

        return HttpResponseNotFound(
            "Ambiguous request both: i) dataIndex for access of raw data and " +
            "ii) anaIdentifier and/or anaIndex for access of analysis data, have been provided.")

    # Return the JSON or PNG for single spectrum (or difference spectrum)
    return get_data_spectrum(
        request=request,
        filename=filename,
        expIndex=expIndex,
        dataIndex=dataIndex,
        x=x,
        y=y,
        operations1=operations1,
        operationsMerge=operationsMerge,
        x2=x2,
        y2=y2,
        operations2=operations2,
        findPeaks=findPeaks,
        anaIndex=anaIndex,
        anaIdentifier=anaIdentifier,
        anaDataName=anaDataName,
        viewerOption=viewerOption,
        precision=precision,
        respFormat=respFormat,
        operations=operations,
        layout=layout)


def get_data_spectrum(request,
                      filename,
                      expIndex,
                      dataIndex,
                      x,
                      y,
                      operations1=None,
                      x2=None,
                      y2=None,
                      operations2=None,
                      operationsMerge=None,
                      findPeaks=0,
                      anaIndex=None,
                      anaIdentifier=None,
                      anaDataName=None,
                      viewerOption=0,
                      precision=-1,
                      operations=None,
                      respFormat=views_definitions.available_formats['JSON'],
                      layout=views_definitions.available_layouts['default']):
    """DJANGO view for requesting a JSON object of a single spectrum or
       the difference of two spectra. \n

         **Required Keyword arguments:**

        :param request: The http request object
        :param filename: The filename/path of the OpenMSI HDF5 datafile to be used
        :param expIndex: The index of the experiment stored in the file
        :param dataIndex: The index of the MSI dataset to be used
        :param x: x selection string pixel/spectrum to be loaded
        :param y: y selection string pixel/spectrum to be loaded

        **Optional Keyword arguments:**

        :param x2: x selection string of the second pixel/spectrum to be loaded
        :param y2: y selection string of the second pixel/spectrum to be loaded
        :param findPeaks: Execute local peak finding for the retrieved data
        :param respFormat: Output format of the returned data, one of: 'JSON', 'PNG', or 'HDF5'
                           as defined by views_definitions.available_formats. (default=JSON)
        :param layout: Specification of the layout to be used for the m/z axis. E.g., default vs. hilbert.
        :param precision: Number of digits to be used in the conversion of the data.
                          By default the standard float encoding is used (-1)
        :param operations: Operations to be applied to the final spectrum data.
                           JSON string with list of dictionaries or a python
                           list of dictionaries. Each dict specifies a single data
                           transformation or data reduction that are applied in order.
                           See omsi.shared.omsi_data_selection.transform_and_reduce_data(...)
                           for details
        :param operations1: Operations to be applied to the first spectrum defined by (x,y).
                           JSON string with list of dictionaries or a python
                           list of dictionaries. Each dict specifies a single data
                           transformation or data reduction that are applied in order.
                           See omsi.shared.omsi_data_selection.transform_and_reduce_data(...)
                           for details.
        :param operations2: Operations to be applied to the second spectrum defined by (x2,y2).
                           JSON string with list of dictionaries or a python
                           list of dictionaries. Each dict specifies a single data
                           transformation or data reduction that are applied in order.
                           See omsi.shared.omsi_data_selection.transform_and_reduce_data(...)
                           for details.
         :param operationsMerge: Data operation to be applied to combine the two spectra. \
                      By default the two spectra are merge by computing the difference spectrum. \
                      The first operation must be one of
                      omsi.shared.data_selection.transformation_allowed_numpy_dual_data data operations!
                      We reference the spectra in the transformation by the names `spectrum1`, `spectrum2`.
                      JSON string with list of dictionaries or a python list of dictionaries. \
                      Each dict specifies a single data transformation or data reduction that \
                      are applied in order. See omsi.shared.omsi_data_selection.transform_and_reduce_data(...) \
                      for details.

         **Optional analysis data argument:**

        The following parameters are used to request "spectra" from derived analysis data.

        :param anaIndex: The index of the analysis dataset to be used (default None).
                         Note, anaIndex or anaIdentifier are redundant and only one should be specified.
        :param anaIdentifier: Identifier string of the analysis dataset (default None). Note,
                         andIndex or anaIdentifier are redundant and only one should be specified.
        :param anaDataName: Name of the analysis dataset that should be retrieved. (default None)
        :param viewerOption: Option indicating which default behavior should be used in case
                         that multiple different behaviors are available for a given dataset/analysis
                          (Default=0).

        :returns: if format=='JSON' django.http.HttpResponse with:

            * JSON object of the raw spectrum data (or multiple  spectra if no reduciton is applied) , \
              if only one pixel is specified and findPeaks==0.
            * JSON object of the difference spectrum (or spectra if not reduction is applied) , if \
              two pixel are specified and findPeak==0.
            * JSON object of the raw data and additional fields with the results from the local peak \
               finding (spectrum, peak_value, peak_pz)
            * JSON object of the difference spectrum and additional fields with  the results from the \
              local peak finding (spectrum, peak_value, peak_pz)
            * in some cases the function may also return additional 'spectrum_mz' data values if the \
              m/z change dynamically for different spectra requests.
            * Error message (e.g., HttpResponseNotFound etc. )

        :return: if format=='PNG' django.http.HttpResponse with:

            * PNG plot of the raw spectrum data, if only one pixel is specified.
            * PNG plot of the difference spectrum data, if two pixels are specified.
            * Error message (e.g., HttpResponseNotFound etc. )

        :return: if format=='HDF5' django.http.HttpResponse with:

            * HDF5 file download of the raw spectrum data (ormultiple  spectra if no reduciton is applied) , \
              if only one pixel is specified and findPeaks==0.
            * HDF5 file download of the difference spectrum (or spectra if not reduciton is applied) , \
              if two pixel are specfified and findPeak==0.
            * HDF5 file download of the raw data and additional fields with the results from the local \
              peak finding (spectrum, peak_value, peak_pz)
            * HDF5 file download of the difference spectrum and additional fields with  the results from \
              the local peak finding (spectrum, peak_value, peak_pz)
            * in some cases the function may also return additional 'spectrum_mz' data values if the \
              m/z change dynamically for different spectra requests.
            * Error message (e.g., HttpResponseNotFound etc. )

    """
    logger.debug("Entering view")

    #Define the data transformations to be used
    # If a 'PNG' image should be returned then set the default reduction operation
    transformations = operations
    transformations1 = operations1
    transformations2 = operations2
    transformations_merge = operationsMerge

    # Selection type
    selectionTypeX = omsi_data_selection.check_selection_string(x)
    selectionTypeY = omsi_data_selection.check_selection_string(y)
    selectionTypeX2 = omsi_data_selection.check_selection_string(x2)
    selectionTypeY2 = omsi_data_selection.check_selection_string(y2)
    # Double check that the selection string is valid. Checking both <0 and 'invalid'
    # is not needed but it is a safeguard against possible errors in future
    # changes
    if selectionTypeX < 0 or selectionTypeX == omsi_data_selection.selection_type['invalid']:
        return HttpResponseNotFound("Invalid selection string x=" + x)
    if selectionTypeY < 0 or selectionTypeY == omsi_data_selection.selection_type['invalid']:
        return HttpResponseNotFound("Invalid selection string y=" + y)
    if (selectionTypeX2 < 0 or selectionTypeX2 == omsi_data_selection.selection_type['invalid']) and x2 is not None:
        return HttpResponseNotFound("Invalid selection string x2=" + x2)
    if (selectionTypeY2 < 0 or selectionTypeY2 == omsi_data_selection.selection_type['invalid']) and y2 is not None:
        return HttpResponseNotFound("Invalid selection string y2=" + y2)

    customMZ = None
    try:
        if dataIndex is None and anaDataName is None:
            anaObj = views_helper.get_omsi_fileobject(
                request,  filename, expIndex, dataIndex, anaIndex, anaIdentifier, anaDataName)
            if not isinstance(anaObj, omsi_file_analysis):
                return HttpResponseNotFound(
                    "Error while retrieving analysis. This is likely " +
                    "because either the anaIndex or anaIdentifier were missing.")
            data1, customMZ1 = analysis_views.get_spectra(analysis_object=anaObj,
                                                          x=x,
                                                          y=y,
                                                          viewer_option=viewerOption)
            if data1 is None:
                return HttpResponseNotFound("Error while retrieving analysis spectra")
        else:
            data1 = views_helper.get_omsi_rawdata_numpy(request=request,
                                                        filename=filename,
                                                        expIndex=expIndex,
                                                        dataIndex=dataIndex,
                                                        anaIndex=anaIndex,
                                                        anaIdentifier=anaIdentifier,
                                                        anaDataName=anaDataName,
                                                        x=x,
                                                        y=y)
            customMZ1 = None
        if isinstance(data1, HttpResponse):
            return data1
        if transformations1 is not None:
            # if len(data1.shape) == 3:
            #     data1 = omsi_data_selection.transform_and_reduce_data(
            #                 data=data1.reshape((data1.shape[0] * data1.shape[1]), data1.shape[2]),
            #                 operations=transformations1,
            #                 http_error=True)
            #
            # if len(data1.shape) == 2:
            #     data1 = omsi_data_selection.transform_and_reduce_data(data=data1,
            #                                                           operations=transformations1,
            #
            #                                           http_error=True)
            data1 = omsi_data_selection.transform_and_reduce_data(data=data1,
                                                                  operations=transformations1,
                                                                  http_error=True)
            if isinstance(data1, HttpResponse):
                return data1

    except:
        if settings.DEBUG:
            raise
        else:
            return HttpResponseNotFound("Data load failed: " + str(sys.exc_info()))

    # Load the data
    try:
        if (x2 is not None) and (y2 is not None):
            if dataIndex is None and anaDataName is None:
                data2, customMZ2 = analysis_views.get_spectra(analysis_object=anaObj,
                                                              x=x2,
                                                              y=y2,
                                                              viewer_option=viewerOption)
                if data2 is None:
                    return HttpResponseNotFound("Error while retrieving analysis spectra")
            else:
                data2 = views_helper.get_omsi_rawdata_numpy(
                    request=request,
                    filename=filename,
                    expIndex=expIndex,
                    dataIndex=dataIndex,
                    anaIndex=anaIndex,
                    anaIdentifier=anaIdentifier,
                    anaDataName=anaDataName,
                    x=x2,
                    y=y2)
                customMZ2 = None
            if isinstance(data2, HttpResponse):
                return data2
            if transformations2 is not None:
                # if len(data2.shape) == 3:
                #     data2 = omsi_data_selection.transform_and_reduce_data(
                #                 data=data2.reshape((data2.shape[0] * data2.shape[1]), data2.shape[2]),
                #                 operations=transformations2,
                #                 http_error=True)
                #
                # if len(data2.shape) == 2:
                #     data2 = omsi_data_selection.transform_and_reduce_data(data=data2,
                #                                                           operations=transformations2,
                #                                                           http_error=True)
                data2 = omsi_data_selection.transform_and_reduce_data(data=data2,
                                                                      operations=transformations2,
                                                                      http_error=True)
                if isinstance(data2, HttpResponse):
                    return data2

            # If the user did not specify a transformation to combine the two spectra,
            # then compute the difference spectrum
            if transformations_merge is None:
                if customMZ1 is None:
                    data = data1.astype('float') - data2.astype('float')
                else:
                    data = np.hstack(data1, (-1 * data2))
                    customMZ = np.hstack(customMZ1, customMZ2)
            else:
                tempdata = np.zeros(1)  # Create some dummy data. The data will not be processed
                data = omsi_data_selection.transform_and_reduce_data(data=tempdata,  # keep the data transform happy
                                                                     operations=transformations_merge,
                                                                     secondary_data={'spectrum1': data1,
                                                                                     'spectrum2': data2},
                                                                     http_error=True)
        else:
            data = data1
    except:
        if settings.DEBUG:
            raise
        else:
            return HttpResponseNotFound("Data load failed: " + str(sys.exc_info()))

    #Apply the final transformation to the data
    if data.ndim > 1 and respFormat == views_definitions.available_formats['PNG']:
        if transformations is None:
            transformations = [{'reduction': 'max', 'axis': -1}]
        else:
            print transformations
    if transformations is not None:
        data = omsi_data_selection.transform_and_reduce_data(data=data,
                                                             operations=transformations,
                                                             http_error=True)
        if isinstance(data, HttpResponse):
            return data

    #Compute the layout for the spectrum
    # Compute the data layout if necessary
    if layout == views_definitions.available_layouts['default']:
        pass
    elif layout == views_definitions.available_layouts['hilbert']:
        """TODO: We need to deal with the case when multiple spectra are loaded (without reduction).
           dt = data.reshape((data.size / data.shape[len(data.shape) - 1], data.shape[len(data.shape) - 1]))
           We can do by creating a 3D array with the hilbert spectrum per slice.
           TODO: We also need to deal in the peak-finding with this situation
        """
        if customMZ is not None:
            customMZ, data = compute_hilbert_spectrum(
                original_coords=np.squeeze(customMZ),
                original_intensities=np.squeeze(data))
        else:
            tempMZ = np.arange(data.size)
            tempMZ, data = compute_hilbert_spectrum(
                original_coords=np.squeeze(tempMZ),
                original_intensities=np.squeeze(data))
        if respFormat == views_definitions.available_formats['PNG']:
            response = HttpResponse(content_type='image/png')
            imgplot, plt = plot_2d_spectrum_as_image(data, show_plot=False)
            plt.savefig(response, format='png')
            return response

    if precision >= 0:
        data = np.around(data.astype('float'), precision)

    # Execute peak finding and return a JSON object with the peak finding and
    # raw spectrum data
    if (int(findPeaks) > 0) and \
            (respFormat == views_definitions.available_formats['JSON'] or
             respFormat == views_definitions.available_formats['HDF5']):
        # Load the m/z data
        #TODO: Should use customMZ values if available
        omsiInstrument = views_helper.get_omsi_fileobject(
            request=request,
            filename=filename,
            expIndex=expIndex,
            instrumentInfo=True)  # Open file in read only mode
        if isinstance(omsiInstrument, HttpResponse):
            return omsiInstrument
        instMZ = omsiInstrument.get_instrument_mz()
        outdata = {'spectrum': data.tolist()}
        if customMZ is not None:
            outdata['spectrum_mz'] = customMZ.lolist()
        # Excute the local peak finding
        dt = data.reshape(
            (data.size / data.shape[len(data.shape) - 1], data.shape[len(data.shape) - 1]))
        pv = [[]] * dt.shape[0]
        pmz = [[]] * dt.shape[0]
        for i in xrange(0, dt.shape[0]):
            fpl = omsi_findpeaks_local(name_key="omsi_findpeaks_local_" + str(time.ctime()))
            fpl.execute(
                msidata=dt[i].reshape(1, 1, dt[i].size),
                mzdata=instMZ,
                printStatus=False)
            pv[i] = fpl.get_analysis_data_by_name(
                'peak_value')['data'].tolist()
            pmz[i] = fpl['peak_mz'].tolist()
            #outdata['peak_value'] = fpl.get_analysis_data_by_name('peak_value')['data'].tolist()
            #outdata['peak_mz']    = fpl.get_analysis_data_by_name('peak_mz')['data'].tolist()

        if dt.shape[0] == 1:
            outdata['peak_value'] = pv[0]
            outdata['peak_mz'] = pmz[0]
        else:
            outdata['peak_value'] = pv
            outdata['peak_mz'] = pmz
        if respFormat == views_definitions.available_formats['JSON']:
            return HttpResponse(content=json.dumps(outdata), content_type='application/json')
        elif respFormat == views_definitions.available_formats['HDF5']:
            parameters = {views_definitions.query_parameters['row']: x,
                          views_definitions.query_parameters['col']: y}
            if x2 is not None and y2 is not None:
                parameters[views_definitions.query_parameters['row2']] = x2
                parameters[views_definitions.query_parameters['col2']] = y2
            returnFilename = views_helper.generate_hdf5_filename(
                request,
                basefile=filename,
                parameters=parameters,
                comment='withpeakfinding')
            return views_helper.generate_hdf5_httpresponse(
                request=request,
                data=outdata,
                returnFilename=returnFilename)
        else:  # this should never be the case:
            if settings.DEBUG:
                raise ValueError("Invalid format key. " + str(respFormat))
            else:
                return HttpResponseNotFound("Unknown format request error")
    # Return only the raw spectrum as a JSON object
    elif respFormat == views_definitions.available_formats['JSON']:
        outdata = {'spectrum': data.tolist()}
        if customMZ is not None:
            outdata['spectrum_mz'] = customMZ.lolist()
        return HttpResponse(content=json.dumps(outdata), content_type='application/json')
    #Return HDF5
    elif respFormat == views_definitions.available_formats['HDF5']:
        outdata = {'spectrum': data}
        if customMZ is not None:
            outdata['spectrum_mz'] = customMZ
        parameters = {views_definitions.query_parameters['row']: x,
                      views_definitions.query_parameters['col']: y}
        if x2 is not None and y2 is not None:
            parameters[views_definitions.query_parameters['row2']] = x2
            parameters[views_definitions.query_parameters['col2']] = y2
        returnFilename = views_helper.generate_hdf5_filename(
            request=request,
            basefile=filename,
            parameters=parameters,
            comment=None)
        return views_helper.generate_hdf5_httpresponse(
            request=request,
            data=outdata,
            returnFilename=returnFilename)
    # Return a Matplotlib plot of the spectrum
    elif respFormat == views_definitions.available_formats['PNG']:
        try:
            import matplotlib.pyplot as plt
        except:
            if settings.DEBUG:
                raise
            else:
                return HttpResponseNotFound("matplotlib.pyplot library not found")
        response = HttpResponse(content_type='image/png')
        plt.clf()
        if customMZ is None:
            a = plt.plot(data.reshape(data.size))
        else:
            a = plt.plot(customMZ.reshape(customMZ.size),
                         data.reshape(data.size))
        plt.savefig(response, format='png')
        return response

    # Unknown response format
    else:
        return HttpResponseNotFound(
            "Unknown format requested. The query parameter 'format' " +
            "did not match either: JSON, PNG, or HDF5. (" + str(respFormat) + ")")


#//////////////////////////////////////////////////////////////////
#///             Generic Django View for requesting             ///
#///             single and multiple data slices using          ///
#///             the query-string of the URL                    ///
#//////////////////////////////////////////////////////////////////
def get_slice(request):
    """ DJANGO view for requesting either a JSON object or PNG image of a single or multiple m/z slices of the data.

        :param request: HttpRequest object. This object needs to specify in the request.GET query dictionary
                        the following query parameters:

        **Required query arguments:**

        * `filename` : The filename/path of the OpenMSI HDF5 datafile to be used
        * `expIndex` : The index of the experiment stored in the file
        * `mz` : String specifying which image slices should be retrieved.

        **Required query arguments when requesting from raw MSI data**

        * `dataIndex` : The index of the MSI dataset to be used

        **Required query arguments when requesting analysis data**

        The following parameters are used to request "slices" from derived analysis data.

        * `anaIndex`: The index of the analysis dataset to be used (default None). Note, anaIndex or \
                      anaIdentifier are redundant and only one should be sepcified.
        * `anaIdentifier` : Identifier string of the analysis dataset (default None). Note, andIndex \
                      or anaIdentifier are redundant and only one should be sepcified.
        * `anaDataName` : Name of the analysis dataset that should be retrieved. (default None). If not \
                      provided then the function will try and figure out which dataset to be used based \
                      on what the analysis specifies as data to be used.
        * `viewerOption` : Integer indicating which default behavior should be used for the given analysis \
                      (if multiple options are available). (Default=0) Alternatively also 'qslice_viewerOption' \
                      may be used instead.


        **Optional query parameters:**

        * `format`: Output format of the returned data, one of: JSON , PNG or HDF5 (Default is JSON)
        * `operations` :  JSON string with list of dictionaries or a python \
                           list of dictionaries. Each dict specifies a single data \
                           transformation or data reduction that are applied in order. \
                           See omsi.shared.omsi_data_selection.transform_and_reduce_data(...) \
                           for details. If no operations are specified, then by default a maximum \
                           projection will be performed '{"reduction": "max", "axis": 2}'. If \
                           format is PNG, then normalization is performed in addition, \
                           '{"transformation": "minusMinDivideMax"}',
        * precision : Integer value indicating the maximum number of floating point precision to be \
                      used for the returned m/z object.

        :returns: django.http.HttpResponse with:

            * JSON object of the raw image slice data (2D array)
            * HDF5 file download of the raw image slice data
            * PNG image of the raw image slice(s)
            * Error message (e.g., HttpResponseNotFound etc. )

        **Uses:**

        This function uses other views to actually retrieve the data:

        * get_data_slice(...)

        See the documentation of those functions for further details.

    """
    logger.debug("Entering view")

    # Get mandatory input parameters
    try:
        filename = request.GET[views_definitions.query_parameters['file']]
        expIndex = int(
            request.GET[views_definitions.query_parameters['expIndex']])
        z = request.GET.get(views_definitions.query_parameters['mz'], None)
    except:
        if settings.DEBUG:
            raise
        else:
            return HttpResponseNotFound("A required query parameter could not be read.")

    filename, filemodel, filetype = omsi_file_authorization.authorize_fileaccess(
        request=request, infilename=filename)
    if isinstance(filename, HttpResponse):  # Check if an error occured
        return filename

    # Get optional input parameters
    try:
        respFormat = request.GET.get(
            views_definitions.query_parameters['format'], views_definitions.available_formats['JSON'])
        if respFormat not in views_definitions.available_formats.values():
            return HttpResponseNotFound("Invalid response format requested. " +
                                        str(respFormat) + "Valid formats are: " +
                                        views_definitions.available_formats.values())
        operations = request.GET.get(
            views_definitions.query_parameters['operations'], None)
        dataIndex = request.GET.get(
            views_definitions.query_parameters['dataIndex'], None)
        anaIndex = request.GET.get(
            views_definitions.query_parameters['anaIndex'], None)
        anaIdentifier = request.GET.get(
            views_definitions.query_parameters['anaIdentifier'], None)
        anaDataName = request.GET.get(
            views_definitions.query_parameters['anaDataName'], None)
        # Try to get the viewerOption, if not available get the
        # qslice_viewerOption or set to 0 by default
        try:
            viewerOption = int(request.GET[views_definitions.query_parameters['viewerOption']])
        except:
            viewerOption = int(request.GET.get(views_definitions.query_parameters['qslice_viewerOption'], 0))
        precision = int(request.GET.get(
            views_definitions.query_parameters['precision'], -1))


    except:
        if settings.DEBUG:
            raise
        else:
            return HttpResponseNotFound("An optional query parameter could not be read.")

    # Return the JSON object or PNG image for the data slice
    return get_data_slice(request=request,
                          filename=filename,
                          expIndex=expIndex,
                          dataIndex=dataIndex,
                          z=z,
                          anaIndex=anaIndex,
                          anaIdentifier=anaIdentifier,
                          anaDataName=anaDataName,
                          viewerOption=viewerOption,
                          precision=precision,
                          operations=operations,
                          respFormat=respFormat)


#//////////////////////////////////////////////////////////////////
#///             Django Single Slice Views                      ///
#//////////////////////////////////////////////////////////////////
def get_data_slice(request,
                   filename,
                   expIndex,
                   dataIndex,
                   z,
                   anaIndex=None,
                   anaIdentifier=None,
                   anaDataName=None,
                   viewerOption=0,
                   precision=-1,
                   operations=None,
                   respFormat=views_definitions.available_formats['JSON']):
    """DJANOG view for requesting a JSON object of a single data slice \n

        **Required Keyword arguments:**

        :param request: The http request object
        :param filename: The filename/path of the OpenMSI HDF5 datafile to be used
        :param expIndex: The index of the experiment stored in the file
        :param dataIndex: The index of the MSI dataset to be used
        :param z: selection string indicating which m/z slices should be loaded.

        **Optional Keyword arguments:**

        :param respFormat: Output format of the returned data, one of: 'JSON', 'HDF5', 'PNG'. (default=JSON)
        :param operations:  JSON string with list of dictionaries or a python
                           list of dictionaries. Each dict specifies a single data
                           transformation or data reduction that are applied in order.
                           See omsi.shared.omsi_data_selection.transform_and_reduce_data(...)
                           for details.

        **Optional analysis data argument:**

        The following parameters are used to request "spectra" from derived analysis data.

        :param anaIndex: The index of the analysis dataset to be used (default None).
                        Note, anaIndex or anaIdentifier are redundant and only one should be specified.
        :param anaIdentifier: Identifier string of the analysis dataset (default None). Note, andIndex
                        or anaIdentifier are redundant and only one should be specified.
        :param anaDataName: Name of the analysis dataset that should be retrieved. (default None)
        :param viewerOption: Option indicating which default behavior should be used in case that
                        multiple different behaviors are available for a given dataset/analysis (Default=0).

        :returns: django.http.HttpResponse with:

            * JSON object of the raw image slice data (2D array) (if respFormat=='JSON')
            * HDF5 file download of the raw image slice data (if respFormat=='HDF5')
            * PNG gray-scale image of the raw image slice data (2D array) (if respFormat=='PNG')
            * Error message (e.g., HttpResponseNotFound etc. )

    """

    logger.debug("Entering view")

    #Define the data transformation to be applied
    if operations is None:
        transformations = [{'reduction': 'max', 'axis': 2}]
    else:
        transformations = operations
    # Set normalize to True if a 'PNG' image should be returned in order to ensure that the image is not white
    if respFormat == views_definitions.available_formats['PNG']:
        if operations is None:
            transformations = [{'transformation': omsi_data_selection.transformation_type['minusMinDivideMax']},
                               {'reduction': 'max', 'axis': 2}]

    # Selection type
    selectionType = omsi_data_selection.check_selection_string(z)
    # Double check that the selection string is valid. Checking both <0 and 'invalid'
    # is not needed but it is a safeguard against possible errors in future
    # changes
    if selectionType < 0 or selectionType == omsi_data_selection.selection_type['invalid']:
        return HttpResponseNotFound("Invalid selection string")

    # Get the raw data
    if dataIndex is None and anaDataName is None:
        anaObj = views_helper.get_omsi_fileobject(request,
                                                  filename,
                                                  expIndex,
                                                  dataIndex,
                                                  anaIndex,
                                                  anaIdentifier,
                                                  anaDataName)
        if not isinstance(anaObj, omsi_file_analysis):
            return HttpResponseNotFound("Error while retrieving analysis. This is likely because" +
                                        " either the anaIndex or anaIdentifier were missing.")
        data = analysis_views.get_slice(analysis_object=anaObj,
                                        z=z,
                                        operations=transformations,
                                        viewer_option=viewerOption)
        if data is None:
            data = HttpResponseNotFound("Error while retrieving analysis slice. Check whether one" +
                                        " the input parameters (e.g, zmin) is incorrect or out of range.")
        if isinstance(data, HttpResponse):
            return data
    else:
        # If only a single slice is selected, then we don't need to do a
        # reduction as views_helper.get_omsi_rawdata_numpy(...) already returns
        # a 2D array
        if selectionType == omsi_data_selection.selection_type['index']:
            reduction = None
        # Load the data
        try:
            data = views_helper.get_omsi_rawdata_numpy(request=request,
                                                       filename=filename,
                                                       expIndex=expIndex,
                                                       dataIndex=dataIndex,
                                                       anaIndex=anaIndex,
                                                       anaIdentifier=anaIdentifier,
                                                       anaDataName=anaDataName,
                                                       z=z,
                                                       operations=transformations)
        except ValueError:
            data = HttpResponseNotFound("omsi_access.view.get_data_slice(..) catch error in data retrieval")
    if isinstance(data, HttpResponse):
        # Return the error message
        return data

    if len(data.shape) > 2:
        if data.shape[2] <= 1:
            # Change the shape of the data array to get a 2D array
            data.shape = (data.shape[0], data.shape[1])

    #Set the precision of the data if requested
    if precision >= 0:
        data = np.around(data.astype('float'), precision)

    returnFilename = None
    if respFormat == views_definitions.available_formats['HDF5']:
        returnFilename = views_helper.generate_hdf5_filename(request=request,
                                                             basefile=filename,
                                                             parameters={"z": z},
                                                             comment=None)
    return views_helper.numpy_data_to_httpresponse(request=request,
                                                   data=data,
                                                   respFormat=respFormat,
                                                   returnFilename=returnFilename)


#//////////////////////////////////////////////////////////////////
#///             Django Data Cube Views                         ///
#//////////////////////////////////////////////////////////////////
def get_cube(request):
    """DJANOG view for requesting a JSON object of a general 3D subset of the raw MSI data
       or derived analysis data  based on the URL query-string.

       :param request: HttpRequest object. This object needs to specify in the request.GET query
                       dictionary the following query parameters:

       **Required query arguments:**

       * filename : The filename/path of the OpenMSI HDF5 datafile to be used
       * expIndex : The index of the experiment stored in the file

       **Required if original MSI data is requested:**

       * dataIndex : The index of the MSI dataset to be used (Required only if raw MSI data is requested)

       **Required if analysis data is requested:**

       * anaIndex : The index of the analysis dataset to be used (default None).
                   Either andIndex or anaIdentifier must be provided.
       * anaIdentifier : Identifier string of the analysis dataset (default None).
                   Either andIndex or anaIdentifier must be provided.
       * anaDataName : Name of the analysis dataset that should be retrieved.

       **Required if download of full HDF5 file is requested:**

       * format : The format must be set to format=HDF5 in order to enable a full file download

       **Optional query arguments:**

       * row : Selection string for the row in the image. [row,:,:] in array notation. Default value is':'
       * col : Selection string for the column in the image. [:,col,:] in array notation. Default value is':'
       * mz : Selection string for the data axis dimensions of the image. [:,:,mz] in array notation. \
              Default value is':'
       * format : The format of the requested return object. This is one of either: \
                  JSON, PNG, or HDF5 as defined in views_definitions.available_formats. \
                  Note, support for PNG is limited for qcube. (Default: 'JSON')
       * operations:  JSON string with list of dictionaries or a python \
                           list of dictionaries. Each dict specifies a single data \
                           transformation or data reduction that are applied in order. \
                           See omsi.shared.omsi_data_selection.transform_and_reduce_data(...) \
                           for details.

       :returns: django.http.HttpResponse with:

            * JSON object of the selected data (3D array)
            * Error message (e.g., HttpResponseNotFound etc. )

       **Uses:**

        This function uses other functions to retrieve and return the
        requested data:

        * get_data_cube(...)
        * get_analysis_data(...)

        See the documentation of those function for further details.

    """
    logger.debug("Entering view")

    # Get mandatory input parameters
    try:
        filename = request.GET[views_definitions.query_parameters['file']]
        try:
            expIndex = int(
                request.GET[views_definitions.query_parameters['expIndex']])
        except:
            expIndex = None
        try:
            dataIndex = int(
                request.GET[views_definitions.query_parameters['dataIndex']])
        except:
            dataIndex = None
    except:
        if settings.DEBUG:
            raise
        else:
            return HttpResponseNotFound("A required query parameter could not be read.")

    filename, filemodel, filetype = omsi_file_authorization.authorize_fileaccess(
        request=request, infilename=filename)
    if isinstance(filename, HttpResponse):  # Check if an error occured
        return filename

    # Get optional input parameters
    try:
        x = request.GET.get(views_definitions.query_parameters['row'], ":")
        y = request.GET.get(views_definitions.query_parameters['col'], ":")
        z = request.GET.get(views_definitions.query_parameters['mz'], ":")
        operations = request.GET.get(
            views_definitions.query_parameters['operations'], None)
        anaIndex = request.GET.get(
            views_definitions.query_parameters['anaIndex'], None)
        anaIdentifier = request.GET.get(
            views_definitions.query_parameters['anaIdentifier'], None)
        anaDataName = request.GET.get(
            views_definitions.query_parameters['anaDataName'], None)
        respFormat = request.GET.get(
            views_definitions.query_parameters['format'], views_definitions.available_formats['JSON'])
        if respFormat not in views_definitions.available_formats.values():
            return HttpResponseNotFound("Invalid response format requested. " + str(respFormat) +
                                        " Valid formats are: " + views_definitions.available_formats.values())
    except:
        if settings.DEBUG:
            raise
        else:
            return HttpResponseNotFound("An optional query parameter could not be read.")

    if respFormat == views_definitions.available_formats['HDF5']:
        if expIndex is None:
            return views_helper.generate_hdf5_httpresponse(request,
                                                           data=filename,
                                                           returnFilename=os.path.basename(filename))

    if expIndex is None:
        return HttpResponseNotFound("Missing parameter: expIndex not specified in the query." +
                                    "If you wished to download the full file then specify format=HDF5 " +
                                    "in the request as well as the default format is JSON.")

    # Retrieve raw MSI data
    if (anaIndex is None) and (anaIdentifier is None):
        if anaDataName is not None:
            return HttpResponseNotFound("Inconsitent query. anaDataName was specified in the query" +
                                        "but neither anaIndex not anaIdentifier were given")
        if dataIndex is None:
            return HttpResponseNotFound("Missing parameter: dataIndex not specified in the query")
        return get_data_cube(request=request,
                             filename=filename,
                             expIndex=expIndex,
                             dataIndex=dataIndex,
                             x=x,
                             y=y,
                             z=z,
                             operations=operations,
                             respFormat=respFormat)
    # Retrieve derived analysis data
    else:
        return get_analysis_data(request=request,
                                 filename=filename,
                                 expIndex=expIndex,
                                 anaIndex=anaIndex,
                                 anaIdentifier=anaIdentifier,
                                 anaDataName=anaDataName,
                                 x=x,
                                 y=y,
                                 z=z,
                                 operations=operations,
                                 respFormat=respFormat)


def get_data_cube(request,
                  filename,
                  expIndex,
                  dataIndex,
                  x=":",
                  y=":",
                  z=":",
                  operations=None,
                  respFormat=views_definitions.available_formats['JSON']):
    """DJANOG view for requesting a JSON object of a general 3D subset of the data\n

        **Required Keyword Arguments:**

        :param request: The http request object
        :param filename: The filename/path of the OpenMSI HDF5 datafile to be used
        :param expIndex: The index of the experiment stored in the file
        :param dataIndex: The index of the MSI dataset to be used

        **Optional Keyword Arguments:**

        :param x : Selection string for x. Default value is ":", i.e, all values.
        :param y : Selection string for y. Default value is ":", i.e, all values.
        :param z : Selection string for z. Default value is ":", i.e, all values.
        :param operations:  JSON string with list of dictionaries or a python
                           list of dictionaries. Each dict specifies a single data
                           transformation or data reduction that are applied in order.
                           See omsi.shared.omsi_data_selection.transform_and_reduce_data(...)
                           for details.
        :param respFormat: The respFormat of the requested return object. This is one of either: JSON, PNG,
                       or HDF5 as defined in views_definitions.available_formats. Note, support for
                        PNG is limited for qcube. (Default: 'JSON')

        :returns: django.http.HttpResponse with:

            * JSON object of the selected data (3D array)
            * Error message (e.g., HttpResponseNotFound etc. )

    """
    logger.debug("Entering view")

    if operations is None:
        transformations = []
    else:
        transformations = operations

    data = views_helper.get_omsi_rawdata_numpy(request=request,
                                               filename=filename,
                                               expIndex=expIndex,
                                               dataIndex=dataIndex,
                                               x=x,
                                               y=y,
                                               z=z,
                                               operations=transformations)
    if isinstance(data, HttpResponse):
        # Return the error message
        return data
    # Convert the numpy data to a response
    returnFilename = views_helper.generate_hdf5_filename(request=request,
                                                         basefile=filename,
                                                         parameters={'x': x, 'y': y, 'z': z},
                                                         comment='_subcube') # This is only needed if respFormat is HDF5
    return views_helper.numpy_data_to_httpresponse(request=request,
                                                   data=data,
                                                   respFormat=respFormat,
                                                   returnFilename=returnFilename)


#//////////////////////////////////////////////////////////////////
#///             Django Analyssis Data Cube Views               ///
#//////////////////////////////////////////////////////////////////
def get_analysis_data(request,
                      filename,
                      expIndex,
                      anaIndex=None,
                      anaIdentifier=None,
                      anaDataName=None,
                      x=":",
                      y=":",
                      z=":",
                      operations=None,
                      respFormat=views_definitions.available_formats['JSON']):
    """DJANOG view for requesting a JSON object of a general 3D subset of an analysis dataset.

        **Required Keyword Arguments**

        :param request: The http request object
        :param filename: The filename/path of the OpenMSI HDF5 datafile to be used
        :param expIndex: The index of the experiment stored in the file
        :param anaIndex: The index of the analysis dataset to be used (default None).
                         Either andIndex or anaIdentifier must be provided.
        :param anaIdentifier: Identifier string of the analysis dataset (default None).
                         Either andIndex or anaIdentifier must be provided.
        :param anaDataName: Name of the analysis dataset that should be retrieved.

        **Optional Keyword arguments:**

        :param x: x selection string
        :param y: y selection string
        :param z: z selection string
        :param operations:  JSON string with list of dictionaries or a python
                           list of dictionaries. Each dict specifies a single data
                           transformation or data reduction that are applied in order.
                           See omsi.shared.omsi_data_selection.transform_and_reduce_data(...)
                           for details.
        :param respFormat: The respFormat of the requested return object. This is one of either:
                       JSON, PNG, or HDF5 as defined in views_definitions.available_formats.
                       Note, support for PNG is limited for qcube. (Default: 'JSON')

        :returns: django.http.HttpResponse with:

            * JSON object of the selected data (3D array)
            * Error message (e.g., HttpResponseNotFound etc. )

    """
    logger.debug("Entering view")

    if anaDataName is None:
        # Return the data retrieved
        return HttpResponseNotFound("Missing parameter: anaDataName not specified in the query")

    if operations is None:
        transformations = []
    else:
        transformations = operations

    data = views_helper.get_omsi_rawdata_numpy(request=request,
                                               filename=filename,
                                               expIndex=expIndex,
                                               anaIndex=anaIndex,
                                               anaIdentifier=anaIdentifier,
                                               anaDataName=anaDataName,
                                               x=x,
                                               y=y,
                                               z=z,
                                               operations=transformations)
    if isinstance(data, HttpResponse):
        # Return the error message
        return data
    # Convert the numpy data to a response
    # This is only needed if the respFormat is HDF5
    returnFilename = views_helper.generate_hdf5_filename(
        basefile=filename, parameters={'x': x, 'y': y, 'z': z}, comment='_subcube')
    return views_helper.numpy_data_to_httpresponse(request=request,
                                                   data=data,
                                                   respFormat=respFormat,
                                                   returnFilename=returnFilename)


#//////////////////////////////////////////////////////////////////
#///             Django Metadata functions                      ///
#//////////////////////////////////////////////////////////////////
def get_metadata(request):
    """DJANOG view implementing the qmetadata URL pattern used to to request metadata
       information from various different objects (files, experiments, analysis etc.)
       based on the URL query-string\n

       :param request: HttpRequest object. This object needs to specify in the request.GET query
                       dictionary the following query parameters:

       **Required query arguments:**

       * mtype : Type of metadata requested, one of: 'filelistView':'filelistView' , \
                 'filelistEdit':'filelistEdit', 'filelistManage':'filelistManage', \
                 'file':'file' , 'provenance':'provenance', 'filelistRawData': 'filelistRawData'. \
                 See omsi_access.views_definitions.available_mtypes for details.

       **Required query parameters for mtype==file**

       * file : The filename/path of the OpenMSI HDF5 datafile to be used

       **To request metadata about a specific experiment specify:**

       * expIndex : The index of the experiment stored in the file

       **To request metadata about a specific analysis specify:**

       * expIndex : The index of the experiment stored in the file
       * anaIndex : The index of the analysis dataset to be used (default None).
                    Either andIndex or anaIdentifier must be provided.
       * anaIdentifier : Identifier string of the analysis dataset (default None).
                    Either andIndex or anaIdentifier must be provided.

       **To request metadata about a specific dataset specify:**

       * expIndex : The index of the experiment stored in the file
       * MSI data indicator:

            * dataIndex : Index of the MSI dataset (only when requesting information for a raw MSI dataset).

       * Analysis data indicators:

            * anaIndex : The index of the analysis dataset to be used (default None). \
                         Either andIndex or anaIdentifier must be provided.
            * anaIdentifier : Identifier string of the analysis dataset (default None). \
                         Either andIndex or anaIdentifier must be provided.
            * anaDataName : Name of the analysis dataset for which metadata information is requested

        **Optional querystring parameters**

        * format : The format of the requested return object. This is one of either:  \
                   JSON or HDF5 as defined in views_definitions.available_formats. Note, \
                   PNG is currently not supported by get_metadata. (Default: 'JSON')
        * `nameKey` : Used to indicate which key name should be used to store object names. (Default: 'name')
        * `childKey` : Used to indcate which key name should be used to store lists of children. (Default: '_children')
        * `depth` : Used by qmetadata mtype==file to indicate until which path depth the \
                    childKey should be used. For path deeper than depth an '_' is prepanded to childKey. \
                    This is used to indcate for D3 which children should be displayed and which one should \
                    be expanded by default.

    """
    logger.debug("Entering view")

    ##############################################
    # 1. Get inputs                              #
    ##############################################
    # 1.1 Get mandatory input parameters
    try:
        # Get and validate the mtype
        # one of file, experiment, analysis, method, instrument
        mtype = request.GET[views_definitions.query_parameters['mtype']]
        if mtype not in views_definitions.available_mtypes.values():
            return HttpResponseBadRequest("The given mtype parameter is invalid. Valid values are: " +
                                          str(views_definitions.available_mtypes.values()))
        # Determine whether the user requests a list of files. The filelist
        # mtype does not require, e.g., a filename to be provided, which all
        # other mtypes need.
        isFilelistRequest = (mtype == views_definitions.available_mtypes['filelistView']) or \
                            (mtype == views_definitions.available_mtypes['filelistEdit']) or \
                            (mtype == views_definitions.available_mtypes['filelistManage']) or \
                            (mtype == views_definitions.available_mtypes['filelistRawData'])
        # Get the name of the file if needed
        if not isFilelistRequest:
            urlfilename = str(
                request.GET[views_definitions.query_parameters['file']])
            filename, filemodel, filetype = omsi_file_authorization.authorize_fileaccess(
                request=request,
                infilename=urlfilename,
                accesstype=omsi_file_authorization.g_access_types['view'],
                check_omsi_files=True,
                check_raw_files=True)
            # Check if an error occurred
            if isinstance(filename, HttpResponse):
                return filename

    except:
        if settings.DEBUG:
            raise
        else:
            return HttpResponseNotFound("A required query parameter could not be read.")

    # 1.2 Get optional input parameters
    try:
        respFormat = request.GET.get(
            views_definitions.query_parameters['format'], views_definitions.available_formats['JSON'])
        if respFormat not in views_definitions.available_formats.values():
            return HttpResponseNotFound("Invalid response format requested. " +
                                        str(respFormat) + "Valid formats are: " +
                                        views_definitions.available_formats.values())
        expIndex = request.GET.get(views_definitions.query_parameters['expIndex'], None)
        dataIndex = request.GET.get(views_definitions.query_parameters['dataIndex'], None)
        anaIndex = request.GET.get(views_definitions.query_parameters['anaIndex'], None)
        anaIdentifier = request.GET.get(views_definitions.query_parameters['anaIdentifier'], None)
        anaDataName = request.GET.get(views_definitions.query_parameters['anaDataName'], None)
        if (anaIdentifier is not None) and (anaIndex is None):
            anaIndex = anaIdentifier
        nameKey = request.GET.get(views_definitions.query_parameters['nameKey'], "name")
        childKey = request.GET.get(views_definitions.query_parameters['childKey'], "children")
        depthKey = request.GET.get(views_definitions.query_parameters['depth'], None)
        if depthKey:
            try:
                depthKey = int(depthKey)
            except:
                return HttpResponseNotFound("Invalid depth key given. Depth must be an unsigned integer" +
                                            " value or -1 if depth should be set to infinite.")
    except:
        if settings.DEBUG:
            raise
        else:
            return HttpResponseNotFound("An optional query parameter could not be read.")

    #############################################################################
    # 2. Retrieve the required metadata                                         #
    #    - Note, views_helper.get_metadata may use data from the django cache   #
    #    - Note, views_helper.get_provenance may use data from the django cache #
    #############################################################################
    metadata = {}
    filenameParam = {}
    filenameComment = mtype
    hdf_outbasefilename = ""

    #3.1 Filelist request
    if isFilelistRequest:
        accesstype = omsi_file_authorization.g_access_types['view']
        if mtype == views_definitions.available_mtypes['filelistView']:
            accesstype = omsi_file_authorization.g_access_types['view']
        elif mtype == views_definitions.available_mtypes['filelistEdit']:
            accesstype = omsi_file_authorization.g_access_types['edit']
        elif mtype == views_definitions.available_mtypes['filelistManage']:
            accesstype = omsi_file_authorization.g_access_types['manage']
        elif mtype == views_definitions.available_mtypes['filelistRawData']:
            accesstype = omsi_file_authorization.g_access_types['manage']

        if mtype == views_definitions.available_mtypes['filelistRawData']:
            metadata = omsi_file_authorization.get_filedict_rawfile(
                request=request, accesstype=accesstype)
        else:
            metadata = omsi_file_authorization.get_filedict_omsi(
                request=request, accesstype=accesstype)

    # 3.2 HDF5 file object metadata
    elif mtype == views_definitions.available_mtypes['file']:
        # 3.2.1) Retrieve metadata for omsi data files
        if filetype == omsi_file_authorization.g_file_types['omsi']:
            omsiObj = views_helper.get_omsi_fileobject(request=request,
                                                       filename=filename,
                                                       expIndex=expIndex,
                                                       dataIndex=dataIndex,
                                                       anaIndex=anaIndex,
                                                       anaIdentifier=anaIdentifier,
                                                       anaDataName=anaDataName,
                                                       instrumentInfo=False,
                                                       methodsInfo=False,
                                                       mode='r')
            metadata = views_helper.get_metadata(omsiObj,
                                                 filename=filename,
                                                 request=request,
                                                 name_key=nameKey,
                                                 child_key=childKey,
                                                 depth=depthKey)
        # 3.2.2) Retrieve metadata for raw data files
        elif filetype == omsi_file_authorization.g_file_types['raw']:
            metadata = views_helper.get_metadata_rawfile(input_object=filemodel,
                                                         filename=filename,
                                                         request=request,
                                                         name_key=nameKey,
                                                         child_key=childKey,
                                                         depth=depthKey)
        # 3.2.3) This should not happen unless we added a g_file_type that we forgot to cover
        else:
            return HttpResponseNotFound("Unknown filetype found")

    # 3.3 Compute provenance information for an object
    elif mtype == views_definitions.available_mtypes['provenance']:
        omsiObj = views_helper.get_omsi_fileobject(request=request,
                                                   filename=filename,
                                                   expIndex=expIndex,
                                                   dataIndex=dataIndex,
                                                   anaIndex=anaIndex,
                                                   anaIdentifier=anaIdentifier,
                                                   anaDataName=anaDataName,
                                                   instrumentInfo=False,
                                                   methodsInfo=False,
                                                   mode='r')
        metadata = views_helper.get_provenance(omsiObj,
                                               filename=filename,
                                               request=request,
                                               name_key=nameKey)
    # 3.4 Unrecocnized mtype
    else:
        return HttpResponseNotFound("Invalid mtype paramter. Valid values are:" +
                                    " file, experiment, analysis, method, or instrument.")

    if isinstance(metadata, HttpResponse):  # Check if an error occurred
        return metadata

    ##############################################
    # 2. Generate and return metadata response   #
    ##############################################
    #Generate the approbriate response from the metadata
    if respFormat == views_definitions.available_formats['JSON']:
        return HttpResponse(content=json.dumps(metadata), content_type='application/json')
    elif respFormat == views_definitions.available_formats['HDF5']:
        # This is only needed if the format is HDF5
        returnFilename = views_helper.generate_hdf5_filename(
            request=request,
            basefile=hdf_outbasefilename,
            parameters=filenameParam,
            comment=filenameComment)
        return views_helper.generate_hdf5_httpresponse(request=request, data=metadata, returnFilename=returnFilename)
    elif respFormat == views_definitions.available_formats['PNG']:
        return HttpResponseNotFound("PNG format not supported by qmetadata")
    else:
        return HttpResponseNotFound("Invalid response format requested. " +
                                    str(respFormat) + "Valid formats are: " +
                                    views_definitions.available_formats.values())

