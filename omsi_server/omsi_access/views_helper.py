"""Collection of helper functions for omsi_access.views"""
# Get the DJANGO settings, e.g., to get the default file path
import logging

from django.conf import settings
from django.http import HttpResponse, HttpResponseNotFound
from django.core.urlresolvers import reverse
from django.http import QueryDict
from django.core.cache import cache

logger = logging.getLogger(__name__)
# Usually we should have the json module in python but in case we don't
# use simplejson as fallback solution
try:
    import json
except ImportError:
    from django.utils import simplejson as json
import os

import numpy as np
import h5py
from omsi.dataformat.omsi_file.main_file import omsi_file
from omsi.dataformat.omsi_file.analysis import omsi_file_analysis
from omsi.dataformat.omsi_file.msidata import omsi_file_msidata
from omsi.dataformat.omsi_file.common import omsi_file_common
from omsi.dataformat.omsi_file.experiment import omsi_file_experiment
from omsi.dataformat.omsi_file.dependencies import omsi_file_dependencydata
from omsi.dataformat.omsi_file.dependencies import omsi_dependencies_manager
from omsi.dataformat.omsi_file.methods import omsi_file_methods
from omsi.dataformat.omsi_file.instrument import omsi_file_instrument
from omsi.dataformat.omsi_file.format import \
    omsi_format_data , omsi_format_experiment, omsi_format_analysis
from omsi.analysis.analysis_views import analysis_views
from omsi.shared.data_selection import *
try:
    from omsi_server.omsi_resources import omsi_file_authorization
except ImportError:
    from omsi_resources import omsi_file_authorization

import views_definitions


##################################################################
#   Helper function for data retrieval                           #
##################################################################
def get_omsi_fileobject(request,
                        filename,
                        expIndex=None,
                        dataIndex=None,
                        anaIndex=None,
                        anaIdentifier=None,
                        anaDataName=None,
                        instrumentInfo=False,
                        methodsInfo=False,
                        mode='r'):
    """Helper function used to retrieve the h5py object associated with different parts of an OpenMSI HDF5 data file.

        :param request: The http request object
        :param filename: The filename/path of the OpenMSI HDF5 datafile to be used
        :param expIndex: The index of the experiment stored in the file (default None)
        :param dataIndex: The index of the MSI dataset to be used (default None)
        :param anaIndex: The index of the analysis dataset to be used (default None).
                          Note, anaIndex or anaIdentifier are redundant and only one should be specified.
        :param anaIdentifier: Identifier string of the analysis dataset (default None). Note, andIndex
                         or anaIdentifier are redundant and only one should be specified.
        :param anaDataName: Name of the analysis dataset that should be retrieved. (default None)
        :param instrumentInfo: Boolean indicating whether the instrument information object should
                         be retrieved (default False). The filename and expIndex  must be set as well.
        :param methodsInfo: Boolean indicating whether the method information object should be retrieved
                         (default False). The filename and expIndex must be set as well.
        :param mode: Mode in which the HDF5 file should be opened (default 'r' = read only).

        :returns:

            * Returns the corrsponding omsi_file object (e.g., omsi_file_msidata, omsi_file_analysis , \
              omsi_file_methods, omsi_file_instrument) for the requested objets :

                * omsi_file : if only filename is set
                * omsi_file_experiment : if filename and expIndex are set (and everything else  left at default values)
                * omsi_file_msidata : if only filename, expIndex, and dataIndex are set
                * omsi_file_analysis  : if filename, expIndex, anaIndex/anaIdentifier (and dataIndex==None)
                * h5py dataset for an analysis: if filename, expIndex, anaIndex/anaIdentifier, and anaDataName \
                  (and dataIndex==None)
                * omsi_file_instrument: : if filename, expIndex, and instrumentInfo are set (and dataIndex, \
                  anaIndex etc. are left at default).
                * omsi_file_methods : if filename expIndex, and methodsInfo are set (and dataIndex, anaIndex etc. \
                  are left at default).

         *  HttpResponse error message : in case of error

    """
    # 1) Open the input HDF5 file
    try:
        # Open file in read only mode
        omsiFile = omsi_file(str(filename), mode)
    except:
        if settings.DEBUG:
            raise
        else:
            return HttpResponseNotFound("File not found:" + str(filename) + " " + str(sys.exc_info()))

    # 2)   Get the requested omsi object from the file
    # 2.1) Return the omsi_file object itself
    if expIndex is None:
        return omsiFile

    # 2.2) Get the experiment
    exp = omsiFile.get_experiment(int(expIndex))
    if exp is None:
        return HttpResponseNotFound("Experiment not found " + str(expIndex) + " " + str(sys.exc_info()))

    # 2.3) Return the instrument information
    if instrumentInfo:
        inst = exp.get_instrument_info()
        if inst is None:
            return HttpResponseNotFound("Instrument information for experiment not found " +
                                        str(expIndex) + " " + str(sys.exc_info()))
        else:
            return inst

    # 2.4) Return the method information
    if methodsInfo:
        methodsinfo = exp.get_method_info()
        if methodsinfo is None:
            return HttpResponseNotFound("Sample information for experiment not found " +
                                        str(expIndex) + " " + str(sys.exc_info()))
        else:
            return methodsinfo

    # 2.5) Return the omsi_experiment object
    if (dataIndex is None) and (anaIndex is None) and (anaIdentifier is None):
        return exp

    # 2.6) Return an original MSI data
    if dataIndex is not None:

        data = exp.get_msidata(int(dataIndex))
        if data is not None:
            return data
        else:
            return HttpResponseNotFound("Dataset not found " + str(dataIndex) + " " + str(sys.exc_info()))

    # 2.7) Get the analysis object
    ana = None
    if (anaIndex is not None) and (anaIndex >= 0):
        ana = exp.get_analysis(int(anaIndex))
    elif anaIdentifier is not None:
        ana = exp.get_analysis_by_identifier(anaIdentifier)

    if ana is None:
        return HttpResponseNotFound("Analysis not found " + str(anaIndex) + " " + str(sys.exc_info()))

    # 2.8) Return the analysis object
    if anaDataName is None:
        return ana
    # 2.9) Return data from the analysis object
    else:
        data = ana[anaDataName]
        if data is None:
            return HttpResponseNotFound("Analysis dataset " + str(anaDataName) +
                                        "  not found" + " " + str(sys.exc_info()))

    return data


def get_omsi_rawdata_numpy(request,
                           filename,
                           expIndex,
                           dataIndex=None,
                           anaIndex=None,
                           anaIdentifier=None,
                           anaDataName=None,
                           x=":",
                           y=":",
                           z=":",
                           operations=None):
    """ Helper function used to retrieve numpy data associated with different parts of an OpenMSI HDF5 data file.

        Uses get_omsi_fileobject(...) to retieve the h5py data handle. See the get_omsi_fileobject documentation
        for additional details.

        :param request: The http request object
        :param filename: The filename/path of the OpenMSI HDF5 datafile to be used
        :param expIndex: The index of the experiment stored in the file (default None)
        :param dataIndex: The index of the MSI dataset to be used (default None)
        :param anaIndex: The index of the analysis dataset to be used (default None).
                   Note, andIndex or anaIdentifier are redundant and only one should be sepcified.
        :param anaIdentifier: Identifier string of the analysis dataset (default None).
                   Note, andIndex or anaIdentifier are redundant and only one should be sepcified.
        :param anaDataName: Name of the analysis dataset that should be retrieved. (default None)

        Optional keyword arguments:

        :param x: x selection string. Default=':'
        :param y: y selection string. Default=':'
        :param z: z selection string. Default=':'
        :param operations: JSON string with list of dictionaries or a python
                           list of dictionaries. Each dict specifies a single data
                           transformation or data reduction that are applied in order.
                           See omsi.shared.omsi_data_selection.transform_and_reduce_data(...)
                           for details.


        :returns:

            * numpy data for (normalized/reduced) subset of:

                * experiment       : if filename and expIndex are set  (and everything else is left at default values).
                * msi dataset      :  if only filename, expIndex, and dataIndex are set
                * analysis dataset : if filename, expIndex, anaIndex/anaIdentifier (and dataIndex==None)

            * HttpResponse error message : in case of error
    """

    # Remove the "" characters from the filename string and other checks
    realFilename, filemodel, filetype = omsi_file_authorization.authorize_fileaccess(
        request=request, infilename=filename)
    if isinstance(realFilename, HttpResponse):  # Check if an error occured
        return realFilename

    # Get the h5py pointer to the dataset
    dataSet = get_omsi_fileobject(request=request,
                                  filename=realFilename,
                                  expIndex=expIndex,
                                  dataIndex=dataIndex,
                                  anaIndex=anaIndex,
                                  anaIdentifier=anaIdentifier,
                                  anaDataName=anaDataName)
    # Check if an error occured that needs to be reported to the client
    if isinstance(dataSet, HttpResponse):
        return dataSet

    xSelType = check_selection_string(x)
    ySelType = check_selection_string(y)
    zSelType = check_selection_string(z)
    if xSelType == selection_type['invalid']:
        return HttpResponseNotFound("Invalid selection specified for x: " + str(x))
    if ySelType == selection_type['invalid']:
        return HttpResponseNotFound("Invalid selection specified for y: " + str(y))
    if zSelType == selection_type['invalid']:
        return HttpResponseNotFound("Invalid selection specified for z: " + str(z))

    if len(dataSet.shape) == 3:
        numIndexSelection = int(xSelType == selection_type['indexlist']) + \
            int(ySelType == selection_type['indexlist']) + \
            int(zSelType == selection_type[
                'indexlist'])
    elif len(dataSet.shape) == 2:
        numIndexSelection = int(
            xSelType == selection_type['indexlist']) + int(ySelType == selection_type['indexlist'])
    else:
        numIndexSelection = int(xSelType == selection_type['indexlist'])

    # Load the data for a regular user selection
    if numIndexSelection <= 1:

        try:
            if len(dataSet.shape) == 1:
                data = eval("dataSet[%s]" % (x,))
            elif len(dataSet.shape) == 2:
                data = eval("dataSet[%s, %s]" % (x, y))
            elif len(dataSet.shape) == 3:
                data = eval("dataSet[%s, %s, %s]" % (x, y, z))
        except:
            if settings.DEBUG:
                raise
            else:
                return HttpResponseNotFound("access to the data failed " + str(sys.exc_info()))

    # Load the data for a selection with multiple lists specified in the
    # selection
    else:

        # The case (dataSet.shape) == 1) is actually not needed. It is evaluated
        # above as numIndexSelection<=1 in all cases. Just in case later code
        # changes should make this necessary so that we do not forget to cover
        # it.
        if len(dataSet.shape) == 1:
            data = eval("dataSet[%s]" % (x,))

        elif len(dataSet.shape) == 2:
            # We know that we must have two list selections specified
            xPointList = selection_to_indexlist(x)
            yPointList = selection_to_indexlist(y)
            if xPointList is not None and yPointList is not None:
                if len(xPointList) == len(yPointList):
                    pointList = [(x, y) for x in xPointList for y in yPointList]
                    data = dataSet[pointList]
                else:
                    return HttpResponseNotFound("Invalid selection. The index lists provided" +
                                                " for x and y do not have equal length")
            else:
                return HttpResponseNotFound("Parsing of the index lists for the point selection failed. " +
                                            "Check that the list is valid.")

        elif len(dataSet.shape) == 3:

            numIndexSelection = int(xSelType == selection_type['indexlist']) + \
                int(ySelType == selection_type['indexlist']) + \
                int(zSelType == selection_type['indexlist'])

            # Point-based selection:  [ (x1,y1,z1), ... , (xn,yn,zn) ]
            # If all selections are index lists then we need to convert the
            # lists to a list of individual data points, [ (x1,y1,z1), ... ,
            # (xn,yn,zn) ]
            if numIndexSelection == 3:
                xPointList = selection_to_indexlist(x)
                yPointList = selection_to_indexlist(y)
                zPointList = selection_to_indexlist(z)
                if len(xPointList) == len(yPointList) and len(xPointList) == len(zPointList):
                    #pointList = [ (xPointList[i], yPointList[i], zPointList[i]) for i in range(0,len(xPointList)) ]
                    data = np.zeros(len(xPointList), dtype=dataSet.dtype)
                    for i in xrange(0, len(xPointList)):
                        data[i] = dataSet[xPointList[i],
                                          yPointList[i],
                                          zPointList[i]]
                else:
                    return HttpResponseNotFound("Invalid selection. The index lists provided for x,y, and z " +
                                                "do not have equal length")

            # 2D Region of interest selections.
            # If two of the lists are index lists, then we need to take care of a
            # couple of cases, as we need to convert two of the lists to points and
            # leave the other dimension in tact
            elif numIndexSelection == 2:
                if (xSelType == selection_type['indexlist']) and (ySelType == selection_type['indexlist']):

                    xPointList = selection_to_indexlist(x)
                    yPointList = selection_to_indexlist(y)
                    # Determine the size of the required data array
                    xSize = len(xPointList)
                    ySize = len(yPointList)
                    if xSize != ySize:
                        return HttpResponseNotFound("Invalid selection. The index lists provided for x and y " +
                                                    "do not have equal length")
                    zSize = dataSet.shape[2]
                    if zSelType == selection_type['index']:
                        zSize = 1
                    elif zSelType == selection_type['range']:
                        ind = [int(i) for i in z.split(":")]
                        zSize = ind[1] - ind[0]
                    # Allocate the required memory
                    data = np.zeros((xSize, zSize), dtype=dataSet.dtype)
                    for i in xrange(0, xSize):
                        data[i, :] = eval("dataSet[%s,%s,%s]" %
                                          (str(xPointList[i]), str(yPointList[i]), z))

                if (xSelType == selection_type['indexlist']) and (zSelType == selection_type['indexlist']):

                    xPointList = selection_to_indexlist(x)
                    zPointList = selection_to_indexlist(z)
                    # Determine the size of the required data array
                    xSize = len(xPointList)
                    zSize = len(zPointList)
                    if xSize != zSize:
                        return HttpResponseNotFound("Invalid selection. The index lists provided for x and z " +
                                                    "do not have equal length")
                    ySize = dataSet.shape[2]
                    if ySelType == selection_type['index']:
                        ySize = 1
                    elif ySelType == selection_type['range']:
                        ind = [int(i) for i in y.split(":")]
                        ySize = ind[1] - ind[0]
                    # Allocate the required memory
                    data = np.zeros((xSize, ySize), dtype=dataSet.dtype)
                    for i in xrange(0, xSize):
                        data[i, :] = eval("dataSet[%s,%s,%s]" %
                                          (str(xPointList[i]), y, str(zPointList[i])))

                if (ySelType == selection_type['indexlist']) and (zSelType == selection_type['indexlist']):

                    yPointList = selection_to_indexlist(y)
                    zPointList = selection_to_indexlist(z)
                    # Determine the size of the required data array
                    ySize = len(yPointList)
                    zSize = len(zPointList)
                    if ySize != zSize:
                        return HttpResponseNotFound("Invalid selection. The index lists provided for y and z " +
                                                    "do not have equal length")
                    xSize = dataSet.shape[2]
                    if xSelType == selection_type['index']:
                        xSize = 1
                    elif xSelType == selection_type['range']:
                        ind = [int(i) for i in x.split(":")]
                        xSize = ind[1] - ind[0]
                    # Allocate the required memory
                    data = np.zeros((ySize, xSize), dtype=dataSet.dtype)
                    for i in xrange(0, ySize):
                        data[i, :] = eval("dataSet[%s,%s,%s]" %
                                          (x, str(yPointList[i]), str(zPointList[i])))

            # This case is already covered above as numIndexSelection<=1.
            # We do it here as well to ensure that all possible combinations are taken into account
            # just in case later code changes should make this necessary so
            # that we do not forget to cover it.
            elif numIndexSelection == 1:

                data = eval("dataSet[%s, %s, %s]" % (x, y, z))

            else:  # i.e., numIndexSelection == 0:
                return HttpResponseNotFound("No index list selections found for pointlist type selection")

    try:
        # Perform the requested reduction operation
        if operations:
            data = transform_and_reduce_data(data=data,
                                             operations=operations,
                                             http_error=True)
    except:
        if settings.DEBUG:
            raise
        else:
            return HttpResponseNotFound("Data operations failed: " + str(operations) + str(sys.exc_info()))

    if isinstance(data, HttpResponse):
        return data

    return data


##################################################################
#   Helper functions for temporary data                          #
##################################################################
def generate_hdf5_filename(request=None,
                           basefile=None,
                           parameters=None,
                           comment=None):
    """Helper function used to generate an HDF5 filename. This function is usually used
       to generate names for HDF5 files to be returned as downloads

        :param request: The HTTP request object.
        :param basefile: The name of the originating HDF5 file or None.
        :param parameters: A dictionary of parameters to be encoded in the filename.
                           E.g., selections applied to the data.
        :param comment: Additional text to be included in the filename or None.

        :returns: A string of the new name. A random name is generated if no information is
                  provided via the input parameters.

    """
    respName = ""
    # start with the base filename
    if basefile is not None:
        respName = os.path.basename(basefile).rstrip(".hdf5").rstrip(".h5")
    # describe all selection applied
    if parameters is not None:
        respName += "_"
        for k, v in parameters.items():
            respName = respName + str(k) + str(v) + "_"
    # inclide additional test
    if comment is not None:
        if not respName.endswith("_"):
            respName += "_"
        respName = respName + comment
    # Generate a random name if the current name is of 0 length
    if len(respName) == 0:
        respName = generate_random_string(5)
    # Add the file extension
    respName += '.h5'
    return respName


def generate_random_string(length, characters=None):
    """Helper function used to generate random strings of a given length

       :param length: the length of the requested random string.
       :param characters: A string of all charaters to select from. If set to None,
                          then the function will use all uppercase letters and numbers.
    """
    import random
    chars = characters
    if chars is None:
        # This is equivilant to "string.ascii_uppercase + string.digits" but
        # avoids the import of string
        chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    return ''.join(random.choice(chars) for _ in range(length))


##################################################################
#   Helper functions for generating http responses for data      #
##################################################################
def numpy_data_to_httpresponse(request, data, respFormat, returnFilename=None):
    """Helper function used to turn a numpy data array into a httpresponse in the desired respFormat

        :param request: The http request object. May be set to None.
        :param data: The numpy data array
        :param respFormat: The respFormat of the requested return object. This is one of
                       either: JSON, PNG, or HDF5 as defined in views_definitions.available_formats.
                       Note, support for PNG is limited for qcube. (Default: 'JSON')
        :param returnFilename: The name of the output file in case that a file download
                       is requested. May be set to None.

        :returns: HttpReponse object with the data or an error message in case the conversion failed.
    """
    # Return the data retrieved in the requested respFormat
    if respFormat == views_definitions.available_formats['JSON']:
        # Convert the data into a JSON response
        return HttpResponse(content=json.dumps(data.tolist()), content_type='application/json')
    elif respFormat == views_definitions.available_formats['HDF5']:
        # Convert the data into an HDF5 download
        return generate_hdf5_httpresponse(request=request, data=data, returnFilename=returnFilename)
    elif respFormat == views_definitions.available_formats['PNG']:
        # Try to import required libraries
        try:
            from PIL import Image
        except:
            try:
                import Image
            except:
                if settings.DEBUG:
                    raise
                else:
                    return HttpResponseNotFound("PIL library not available on server")
        # Remove dimensions of size 1
        data = np.squeeze(data)
        # If we have a 1D dataset then make it 2D if possible
        if len(data.shape) == 1:
            data = data.reshape((data.shape[0], 1))
        elif len(data.shape) > 2:
            # Enforce fortan order in the reshape so that we get a picture of
            # 'image1 image2 image3 ...' when we have a 3D cube
            data = data.reshape(
                (data.shape[0], np.prod(data.shape[1:len(data.shape)])), order='F')
        # Now we should have a 2D array that we can turn into an image
        # Normalize the data in order to convert it to an image and multiply by
        # 255 to get gray-scale values
        data = data / float(np.max(data)) * 255.
        try:
            # TODO : This part may be inefficient with the various conversions
            # between int and float
            response = HttpResponse(content_type='image/png')
            # reshape the data to a 2D array and convert to float
            a = Image.fromarray(data)
            a.convert('L').save(response, 'PNG')
            return response
        except:
            if settings.DEBUG:
                raise
            else:
                return HttpResponseNotFound("Generation of image from the data failed " + str(sys.exc_info()))
    else:
        # Usually there are several checks for this problem before we reach
        # this place but just in case.
        return HttpResponseNotFound("Cannot convert data to response. Unknown respFormat requested.")


def generate_hdf5_httpresponse(request,
                               data,
                               returnFilename=None):
    """Return an HDF5 download for the given numpy object
       :param data: This may be one of the following :
                  * A dictionary defining the data to be stored. The dictonary may contain numpy datasets, \
                    strings, dictionaries or any format than can be converted to numpy via np.asarray(...) \
                    as values to be stored. Using dictionaries as values results in the generation of a \
                    file hierarchy, with each dictionary being represented by a group in HDF5. All \
                    dictionaries may only contain strings as keys.
                  * h5py.File object with the file that should be made available for download
                  * omsi_file object for the file that should be made available for download
       :param returnFilename: What should be the name of the file for download.
    """
    # Import h5py and FileWrapper
    try:
        import h5py
    except:
        if settings.DEBUG:
            raise
        else:
            return HttpResponseNotFound("The server experienced an error. Could not import h5py. " +
                                        "Please contact the system administrator.")
    try:
        from django.core.servers.basehttp import FileWrapper
    except:
        if settings.DEBUG:
            raise
        else:
            return HttpResponseNotFound("The server experienced an error. FileWrapper could not be imported. " +
                                        "Please contact the system administrator.")

    # Case1: Check if we are given an HDF5 file. Then we can download the
    # whole file directly
    if isinstance(data, h5py.File) or isinstance(data, omsi_file) or isinstance(data, str) or isinstance(data, unicode):
        filename = None
        if isinstance(data, h5py.File):
            filename = data.filename
        elif isinstance(data, omsi_file):
            filename = data.get_h5py_file().filename
        else:
            filename = data
        try:
            wrapper = FileWrapper(open(filename, 'r'))
        except:
            if settings.DEBUG:
                raise
            else:
                return HttpResponseNotFound('Could not open the requested file')
        try:
            response = HttpResponse(wrapper, content_type='application/hdf5')
            response[
                'Content-Disposition'] = 'attachment; filename=%s' % os.path.basename(filename)
            response['Content-Length'] = os.path.getsize(filename)
            return response
        except:
            if settings.DEBUG:
                raise
            else:
                return HttpResponseNotFound('Error while generating the HDF5 download')

    # Case2: Otherwise we need to contruct
    try:
        from tempfile import NamedTemporaryFile
    except:
        try:
            from django.core.files.temp import NamedTemporaryFile
        except:
            if settings.DEBUG:
                raise
            else:
                return HttpResponseNotFound("The server experienced an error. Could not generate temprorary file. " +
                                            "NamedTemporaryFile module could not be imported. Please contact the " +
                                            "system administrator.")

    # Create a named temporary file that will be automatically deleted by
    # Python
    tempfile = NamedTemporaryFile(dir=settings.TEMPORARY_DATAPATH)
    print tempfile.name
    tempfile.seek(0)
    #h5ret = omsi_file( h5py.File ( tempfile.name, driver='core', backing_store=False ) )
    # Wrap the temporay file into an HDF5 file
    # we can also warp this directly into an OpenMSI file via omsi_file(
    # h5py.File(tempfile.name) )
    h5ret = h5py.File(tempfile.name)
    add_data_to_hdf5(hdf5Group=h5ret['/'], data=data)
    h5ret.flush()
    # Wrap the hdf5 file into a file stream for download
    wrapper = FileWrapper(tempfile)
    response = HttpResponse(wrapper, content_type='application/hdf5')
    outFilename = returnFilename
    if outFilename is None:
        outFilename = tempfile.name
    response['Content-Disposition'] = 'attachment; filename=%s' % os.path.basename(outFilename)
    response['Content-Length'] = os.path.getsize(tempfile.name)
    return response


def add_data_to_hdf5(hdf5Group, data):
    """Function used by generate_hdf5_httpresponse to recursively add data from a dictionary to a file.
       NOTE: It is recommended to call flush() on the HDF5 file at the end as the function does not
             ensure that the data has been flushed to disk.

       :param hdf5Group: The HDF5 group to which the given data should be added.
       :param data:

       :raises: This function may raise a ValueError in case that a nonstring key or an unsupported
                data value for write is given.
    """
    try:
        import h5py
    except:
        if settings.DEBUG:
            raise
        else:
            return HttpResponseNotFound("The server experienced an error. Could not import h5py. " +
                                        "Please contact the system administrator.")
    # The standard case is that we are getting a dictionary that defines the names data.keys() and the data
    # to be stored data.values.
    if isinstance(data, dict):
        for k in data.keys():
            if not isinstance(k, str) and not isinstance(k, unicode):
                raise ValueError(
                    "Cannot write data to HDF5. Invalide name key given")
            v = data[k]
            if 'numpy' in str(type(v)):
                d = hdf5Group.require_dataset(name=unicode(k),
                                              shape=v.shape,
                                              dtype=v.dtype,
                                              chunks=True,
                                              compression='gzip',
                                              compression_opts=4)
                d[:] = v
            elif isinstance(v, dict):
                add_data_to_hdf5(
                    hdf5Group=hdf5Group.require_group(unicode(k)), data=v)
            elif isinstance(v, str) or isinstance(v, unicode):
                stringType = h5py.special_dtype(vlen=str)
                d = hdf5Group.require_dataset(name=unicode(k),
                                              shape=(1,),
                                              dtype=stringType)
                d[0] = v
            else:
                # Try to convert the object to numpy and save it
                try:
                    vt = np.array(v)
                    # Deal with the special case when we are given a single
                    # bool,int etc. as a data value
                    if len(vt.shape) == 0:
                        vt = vt.reshape((1,))
                    dtype = vt.dtype
                    # Deal with the case when we are given a list of strings
                    # that are converted to unicode numpy array
                    if str(dtype).startswith('<U'):
                        stringType = h5py.special_dtype(vlen=str)
                        dtype = stringType
                    d = hdf5Group.require_dataset(
                        name=unicode(k), shape=vt.shape, dtype=dtype)
                    # Avoid error due to trying to write data to empty
                    # datasets, e.g., when the peak finding did not result in
                    # any peaks.
                    if vt.size > 0:
                        d[:] = vt[:]
                except:
                    raise
                    # raise ValueError(
                    #    "Cannot write dataset to HDF5. Unsupported data format." + str(type(v)) + str(v))
    # We also allow numpy object to be provided directly which we then simply
    # store under a default name
    elif 'numpy' in str(type(data)):
        d = hdf5Group.require_dataset(
            name='data', shape=data.shape, dtype=data.dtype, chunks=True, compression='gzip', compression_opts=4)
        d[:] = data
    else:
        raise ValueError(
            "Cannot write dataset to HDF5. Invalid data definition given.")


##################################################################
#   Data provenance metadata function                            #
##################################################################
def get_provenance(input_object,
                   filename,
                   request=None,
                   name_key='name',
                   nodes_key='nodes',
                   links_key='links',
                   force_update=False):
    """Compute for a given h5py.Dataset of h5py.Group the corresponding dictionary metadata hierarchy.

       :param input_object: The h5py.File, h5py.Group, h5py.Dataset object for which the metadata should be computed
       :param filename: The full path (ie.,primary key of the file) the input
       :param request: Input http request. May be set to None, in which case URL's will
                       be determined based on the settings.API_ROOT setting instead.
       :param name_key: key value to be used to identify object names
       :param nodes_key: key to be used for storing the list of nodes of the graph
       :param links_key: key to be used for storing the list of links of the graph
       :param force_update: Force compute of the metadata from file and subsequent update
                     of the metadata cache. Default is False.
       :type force_update: Boolean.

       :returns: Dictionary with the full metadata hiearchy for the given object

       :raises ValueError: If h5pyInputObject is of an unsupported type. Currently only h5py.Dataset,
               h5py.Group, h5py.File or omis_file API objects are supported.
    """
    # 1) Compute the cache key and define basic settings
    ckey = __generate_cache_key__(data_type='provenance',
                                  primary_key=filename+input_object.name)
    default_namekey = "name"

    # 2) Compute the full provenance metadata
    # 2.1) Retrieve the metadata from cache
    try:
        if not force_update:
            cacheddata = cache.get(ckey)
        else:
            cacheddata = None
    except:
        if settings.DEBUG:
                raise
        cacheddata = None
        logger.log("Error accessing the cache.")

    # 2.2) Check if the cached data is up-to-data
    provenancedict = None
    if cacheddata:
        filetime = os.path.getmtime(filename)
        if filetime == cacheddata['filetime']:
            provenancedict = cacheddata['metadata']

    # 2.3) If the metadata was not cached or the cached data was out of date,
    #      then compute the full file metadata and update the cache
    if not provenancedict:
        # 2.3.1) Compute the metadata from file
        provenancedict = compute_provenance(input_object=input_object,
                                            request=request,
                                            name_key=default_namekey,
                                            nodes_key=nodes_key,
                                            links_key=links_key)
        # 2.3.2) Place the computed metadata into the cache
        cdata = {'filetime': os.path.getmtime(filename), 'metadata': provenancedict}
        try:
            #Define the timeout. For DJANGO version 1.6+ we can specify that the
            #cache entry should not expire. For earlier versions this was not possible.
            from django import VERSION as djangoversion
            if djangoversion[0] >= 1 and djangoversion[1] >= 6:
                timeout = None
            else:
                timeout = 2592100
            cache.set(key=ckey, value=cdata, timeout=timeout)
        except:
            if settings.DEBUG:
                raise
            logger.log("Error writing to the cache.")

    # 3) Update the name keys if needed
    if name_key != default_namekey:
        for node in provenancedict[nodes_key]:
            node[name_key] = node.pop(default_namekey)

    # 4) Return the final provenance dict
    return provenancedict


def compute_provenance(input_object, request=None, name_key="name", nodes_key='nodes', links_key='links'):
    """Use get_provenance(...) if possible. This function is used to compute the metadata from
       a file object directly, whereas, get_provenance(..) allows the use of cached data.
       Compute for a given h5py.Dataset of h5py.Group the corresponding dictionary metadata hierarchy.

       :param input_object: The h5py.File, h5py.Group, h5py.Dataset object for which the metadata should be computed
       :param request: Input http request. May be set to None, in which case no URL's
                       will be specified as part of the metadata.
       :param name_key: key value to be used to identify object names
       :param nodes_key: key to be used for storing the list of nodes of the graph
       :param links_key: key to be used for storing the list of links of the graph

       :returns: Dictionary with the full metadata hiearchy for the given object

       :raises ValueError: If h5pyInputObject is of an unsupported type. Currently only h5py.Dataset,
               h5py.Group, h5py.File or omis_file API objects are supported.
    """
    # Retrieve the corresponding h5py object for the given input
    f = omsi_file_common.get_omsi_object(input_object, resolve_dependencies=True)
    metadata_dict = {nodes_key: [], links_key: []}

    # Generate the provenance of a single object that manages dependencies
    if isinstance(f, omsi_dependencies_manager):
        depObj = f.dependencies
        if depObj:
            # Compute the nodes and links
            startlevel = 0
            metadata_generator = add_metadata
            # Additional arguments needed for add_metadata
            metadata_generator_kwargs = {'request': request}
            # Add all dependencies for depObj to the nodes and links.
            # NOTE: If depObj is not yet part of the graph, then this call will add
            #       depObj to the list of nodes as well
            metadata_dict[nodes_key], metadata_dict[links_key] = depObj.get_all_dependency_data_graph(
                include_omsi_dependency=False,
                include_omsi_file_dependencydata=False,
                recursive=True,
                level=startlevel,
                name_key=name_key,
                prev_nodes=metadata_dict[nodes_key],
                prev_links=metadata_dict[links_key],
                parent_index=None,
                metadata_generator=metadata_generator,
                metadata_generator_kwargs=metadata_generator_kwargs)
    # Generate the provenance of all objects in an experiment
    elif isinstance(f, omsi_file_experiment):

        # Iterate through all elements stored in the group
        for exp_element in f.managed_group.itervalues():
            # Map the object to the omsi API class
            exp_element_omsi = omsi_file_common.get_omsi_object(exp_element)
            # Check if the object can define dependencies
            if isinstance(exp_element_omsi, omsi_dependencies_manager):
                # Get all dependencies
                depObj = exp_element_omsi.dependencies
                # If there are any dependencies that can be processed
                if depObj:
                    startlevel = 1
                    metadata_generator = add_metadata
                    metadata_generator_kwargs = {'request': request}   # Additional arguments needed for add_metadata
                    # Expand the provenance graph to include the various data objects
                    metadata_dict[nodes_key], metadata_dict[links_key] = depObj.get_all_dependency_data_graph(
                        include_omsi_dependency=False,
                        include_omsi_file_dependencydata=False,
                        recursive=True,
                        level=startlevel,
                        name_key=name_key,
                        prev_nodes=metadata_dict[nodes_key],
                        prev_links=metadata_dict[links_key],
                        parent_index=None, # msidataNodes[i],
                        metadata_generator=metadata_generator,
                        metadata_generator_kwargs=metadata_generator_kwargs)

    elif isinstance(f, omsi_file):

        metadata_generator = add_metadata
        metadata_generator_kwargs = {'request': request}
        # Determine all objects that manage dependencies
        for file_element in f.managed_group.itervalues():
            file_element_omsi = omsi_file_common.get_omsi_object(file_element)
            if isinstance(file_element_omsi, omsi_dependencies_manager):
                if file_element_omsi.dependencies is not None:
                    startlevel = 0
                    print file_element_omsi.name
                    # Expand the provenance graph to include the various data objects
                    metadata_dict[nodes_key], metadata_dict[links_key] = \
                        file_element_omsi.get_all_dependency_data_graph(
                            include_omsi_dependency=False,
                            include_omsi_file_dependencydata=False,
                            recursive=True,
                            level=startlevel,
                            name_key=name_key,
                            prev_nodes=metadata_dict[nodes_key],
                            prev_links=metadata_dict[links_key],
                            parent_index=None, # msidataNodes[i],
                            metadata_generator=metadata_generator,
                            metadata_generator_kwargs=metadata_generator_kwargs)
            if isinstance(file_element_omsi, omsi_file_experiment):
                for exp_element in file_element_omsi.managed_group.itervalues():
                    exp_element_omsi = omsi_file_common.get_omsi_object(exp_element)
                    if isinstance(exp_element_omsi, omsi_dependencies_manager):
                        print exp_element_omsi.name
                        if exp_element_omsi.dependencies is not None:
                            startlevel = 1
                            # Expand the provenance graph to include the various data objects
                            metadata_dict[nodes_key], metadata_dict[links_key] = \
                                exp_element_omsi.get_all_dependency_data_graph(
                                    include_omsi_dependency=False,
                                    include_omsi_file_dependencydata=False,
                                    recursive=True,
                                    level=startlevel,
                                    name_key=name_key,
                                    prev_nodes=metadata_dict[nodes_key],
                                    prev_links=metadata_dict[links_key],
                                    parent_index=None, # msidataNodes[i],
                                    metadata_generator=metadata_generator,
                                    metadata_generator_kwargs=metadata_generator_kwargs)


        # for i in range(f.get_num_experiments()):
        #
        #     curr_exp_meta = compute_provenance(f.get_experiment(i), request=request, name_key=name_key)
        #     # Update the indices of the links
        #     numNodes = len(metadata_dict[nodes_key])
        #     for li in curr_exp_meta[links_key]:
        #         li['source'] += numNodes
        #         li['target'] += numNodes
        #     # Merge the results with the current list
        #     metadata_dict[nodes_key] = metadata_dict[nodes_key] + curr_exp_meta[nodes_key]
        #     metadata_dict[links_key] = metadata_dict[links_key] + curr_exp_meta[links_key]

    return metadata_dict


##################################################################
#   Raw File metadata function                                   #
##################################################################
def get_metadata_rawfile(input_object,
                         filename,
                         request,
                         name_key="name",
                         child_key="children",
                         depth=2,
                         force_update=False):
    """Get the metadata for a given raw data file.

       Note, the signature of the function is designed ot be consistent with the get_metadata
       function and to allow future extension of the implementation. The current implementation
       may not honor all input parameters (request, child_key, depth, and force_update) are
       currently unused because:

            * no url requests are supported by rawfiles (request not needed),
            * the metadata hierarchy does not include file details (child_key and depth not needed)
            * the metadata is constructed from the database directly and is not cached (force_update not needed)

       :param input_object: The FileModelRaw database model describing the raw data file.
                         May be set to None, in which case the function assumes that the
                         file is not registered/managed by the system.
       :param filename: The full path (ie.,primary key of the file) the input
       :param request: Input http request. May be set to None, in which case URL's will
                       be determined based on the settings.API_ROOT setting instead.
       :param name_key: key value to be used to identify object names
       :type name_key: String
       :param child_key: key value to be used to identify child objects
       :type child_key: String
       :param depth: until which path length should the child_key be used as provided. For
                     deeper path an '_' is prepended to the child_key. Set to None or -1
                     to essentially set to depth as infinity.
       :type depth: int
       :param force_update: Force compute of the metadata from file and subsequent update
                     of the metadata cache. Default is False.
       :type force_update: Boolean.

       :returns: Dictionary with the full metadata hierarchy for the given object

       :raises ValueError: If h5pyInputObject is of an unsupported type. Currently only h5py.Dataset,
               h5py.Group, h5py.File or omis_file API objects are supported.

    """
    # Define the web API functions supported by the format
    metadata = {'do_qmz': False,
                'do_qspectrum': False,
                'do_qcube': False,
                'do_qslice': False,
                'do_qmetadata': True,
                'filesize': None}
    # metadata['manageURL'] : Online permission management for raw data files not yet implemented
    # metadata['downURL'] : Download of raw files currently not supported
    # Define name, path and reader type
    if not input_object:
        metadata[name_key] = filename
        metadata['path'] = filename
        metadata['class'] = None
        metadata['managed'] = False
        metadata['converted'] = False
        metadata['related_files'] = []
    else:
        metadata[name_key] = input_object.path
        metadata['path'] = input_object.path
        if input_object.format_reader is not None:
            metadata['class'] = input_object.format_reader.format
        else:
            metadata['class'] = None
        metadata['managed'] = True
        metadata['converted'] = len(input_object.related_omsi_files.all()) > 0
        relatedfiles = [m.path for m in input_object.related_omsi_files.all()]
        metadata['related_files'] = relatedfiles
    return metadata


##################################################################
#   Omsi File metadata function                                  #
##################################################################
def get_metadata(input_object,
                 filename,
                 request=None,
                 name_key="name",
                 child_key="children",
                 depth=2,
                 force_update=False):
    """Get the metadata for a given omsi_file API object h5py object, get the corresponding
       dictionary metadata hierarchy.

       :param input_object: The h5py.File, h5py.Group, h5py.Dataset object or omsi_file API
                       object for which the metadata should be computed
       :param filename: The full path (ie.,primary key of the file) the input
       :param request: Input http request. May be set to None, in which case URL's will
                       be determined based on the settings.API_ROOT setting instead.
       :param name_key: key value to be used to identify object names
       :type name_key: String
       :param child_key: key value to be used to identify child objects
       :type child_key: String
       :param depth: until which path length should the child_key be used as provided. For
                     deeper path an '_' is prepended to the child_key. Set to None or -1
                     to essentially set to depth as infinity.
       :type depth: int
       :param force_update: Force compute of the metadata from file and subsequent update
                     of the metadata cache. Default is False.
       :type force_update: Boolean.

       :returns: Dictionary with the full metadata hierarchy for the given object

       :raises ValueError: If h5pyInputObject is of an unsupported type. Currently only h5py.Dataset,
               h5py.Group, h5py.File or omis_file API objects are supported.

    """
    # 1) Compute the cache key and define basic settings
    ckey = __generate_cache_key__(data_type='file_metadata',
                                  primary_key=filename)
    default_childkey = "children"
    default_closechildkey = "_"+default_childkey
    default_namekey = "name"
    default_depth = None  # NOTE, this should always be None or -1, i.e., we cache the data with full depth
    close_child_key = "_" + child_key
    path_key = 'path'

    # 2) Compute the full file metadata
    # 2.1) Retrieve the metadata from cache
    try:
        if not force_update:
            cacheddata = cache.get(ckey)
        else:
            cacheddata = None
    except:
        if settings.DEBUG:
                raise
        cacheddata = None
        logger.log("Error accessing the cache.")

    # 2.2) Check if the cached data is up-to-data
    fullmetadata = None
    if cacheddata:
        filetime = os.path.getmtime(filename)
        if filetime == cacheddata['filetime']:
            fullmetadata = cacheddata['metadata']

    # 2.3) If the metadata was not cached or the cached data was out of date,
    #      then compute the full file metadata and update the cache
    if not fullmetadata:
        # 2.3.1) Compute the metadata from file
        fullmetadata = compute_metadata(input_object=input_object,
                                        request=request,
                                        name_key=default_namekey,
                                        child_key=default_childkey,
                                        depth=default_depth)
        # 2.3.2) Place the computed metadata into the cache
        cdata = {'filetime': os.path.getmtime(filename), 'metadata': fullmetadata}
        try:
            #Define the timeout. For DJANGO version 1.6+ we can specify that the
            #cache entry should not expire. For earlier versions this was not possible.
            from django import VERSION as djangoversion
            if djangoversion[0] >= 1 and djangoversion[1] >= 6:
                timeout = None
            else:
                timeout = 2592100
            cache.set(key=ckey, value=cdata, timeout=timeout)
        except:
            if settings.DEBUG:
                raise
            logger.log("Error writing to the cache.")

    # 3) Extract/adapt the appropriate metadata from the full cached metadata
    # 3.1) Remove the manageURL if the user does not have permissions to access the file
    # 3.1.1) Determine whether the user has manage rights
    manageaccess = False
    try:
        if request is not None:
            realFilename, filemodel, filetype = omsi_file_authorization.authorize_fileaccess(
                request=request,
                infilename=filename,
                accesstype=omsi_file_authorization.g_access_types['manage'])
            if not isinstance(realFilename, HttpResponse):  # Check if an error occured
                manageaccess = True
    except:
        pass

    if not manageaccess:
        try:
            fullmetadata.pop("manageURL")
        except KeyError:
            pass

    # 3.2) Find the metadata dictionary that belongs to the requested object
    objectmetadata = find_group_in_metadatadict(name=input_object.name,
                                                metadata_dict=fullmetadata,
                                                name_key=default_namekey,
                                                child_key=default_childkey,
                                                close_child_key=default_closechildkey)

    ## BEGIN Internal helper function to recursively change depth and name keys
    def update_keys(in_dict):
        """Recursively update name and child keys in the given metadata dictionary.

           NOTE: default_childkey, depth, defualt_namekey, are parameters that are
                 used from the closure in a read-only fashion.

           :param in_dict: The dictionary to be updated
        """
        #Update the name key as needed
        try:
            in_dict[name_key] = in_dict.pop(default_namekey)
        except KeyError:
            pass
        #Follow the trace to visit all children
        if default_childkey in in_dict:
            #Update the child key
            currdepth = len(in_dict[path_key].split('/'))
            children = in_dict.pop(default_childkey)
            if (depth == -1) or (depth is None) or (currdepth <= depth):
                in_dict[child_key] = children
            else:
                in_dict[close_child_key] = children
            #Change keys recursively
            for child in children:
                update_keys(child)
    ##END Internal helper function to recursively change child and name keys

    # 3.3) Determine whether any keys need to be updated
    update_required = (name_key != default_namekey)
    update_required |= (child_key != default_childkey)
    if depth is not None:
        update_required |= (depth > 0)
    # 3.4) Update name and child keys if necessary
    if update_required:
        update_keys(objectmetadata)

    # 4) Return the final metadata object
    return objectmetadata


def compute_metadata(input_object, request=None, name_key="name", child_key="children", depth=2):
    """Use get_metdata(...) if possible. This function is used to compute the metadata from
       a file object directly, whereas, get_metadata allows the use of cached data. If cached
       data is not available, then get_metadata will automatically fall back to this method.
       Compute for a given omsi_file API object or h5py h5py object, compute the corresponding
       dictionary metadata hierarchy.

       :param request: Input http request. May be set to None, in which case URL's will
                       be determined based on the settings.API_ROOT setting instead.
       :param input_object: The h5py.File, h5py.Group, h5py.Dataset object or omsi_file API
                       object for which the metadata should be computed
       :param name_key: key value to be used to identify object names
       :param child_key: key valye to be used to identify child objects
       :param depth: until which path lenght should the child_key be used as provided. For
                     deeper path an '_' is prepanded to the child_key. Set to None or -1
                     to essentially set to depth as infinity.

       :returns: Dictionary with the full metadata hiearchy for the given object

       :raises ValueError: If h5pyInputObject is of an unsupported type. Currently only h5py.Dataset,
               h5py.Group, h5py.File or omis_file API objects are supported.

    """
    # Setup basic context of the current closure
    f = input_object
    metadata_dict = {}  # dictionary used to record all metadata
    # previous parent dictionary. Used to speed-up search for parent dicts.
    # prevDict = metadata_dict
    # previous parent path. Used to speed-up the search for parent dicts.
    # prevName = ""
    closeChildKey = "_" + child_key

    # BEGIN addItems(...)
    # Function within the current closure used to added singel HDF5 objects to
    # the metadata_dict
    def addItems(name, obj):
        """Add the given object from the HDF5 file to the metadata_dict.

           :param name: Name (full path) of the object
           :param obj: The h5py object (h5py.Dataset or h5pyGroup) object ot be added to the metadata_dict.
        """
        a = int(20)
        parentName = os.path.dirname(name)
        childName = os.path.basename(name)
        # Find the parent group
        g = find_group_in_metadatadict(name=parentName,
                                       metadata_dict=metadata_dict,
                                       name_key=name_key,
                                       child_key=child_key,
                                       close_child_key=closeChildKey)
        # Add a list for childrent to the parent group if needed
        if (child_key not in g.keys()) and (closeChildKey not in g.keys()):
            currDepth = len(name.split('/'))
            if (depth == -1) or (depth is None) or (currDepth <= depth):
                g[child_key] = []
            else:
                g[closeChildKey] = []
        # Construct a dict to describe the current object
        nd = {}
        add_metadata(in_dict=nd, name=childName, obj=obj,
                    request=request, name_key=name_key)
        # if isinstance(obj, h5py.Group):
        #    # TODO: Closures are read only, ie, assignemnt to outer scope variable has no effect
        #    prevDict = nd
        #    # TODO: Closures are read only, ie, assignemnt to outer scope variable has no effect
        #    prevName = name

        # Added the dict for the object to the list of children objects
        try:
            g[child_key].append(nd)
        except:
            g[closeChildKey].append(nd)
    # END addItems(...)

    # Retrieve the corresponding h5py object for the given input
    f = omsi_file_common.get_h5py_object(input_object)

    # Visit all items of the inpute HDF5 file object to fill the metadata_dict
    # with data
    if isinstance(f, h5py.File):
        add_metadata(in_dict=metadata_dict, name=f.filename,
                    obj=f, request=request, name_key=name_key)
        # visititems is a function of h5py.Group used to recursively visit all
        # items in the group
        f['/'].visititems(addItems)
    elif isinstance(f, h5py.Group):
        add_metadata(in_dict=metadata_dict, name=f.name,
                    obj=f, request=request, name_key=name_key)
        # visititems is a function of h5py.Group used to recursively visit all
        # items in the group
        f.visititems(addItems)
    elif isinstance(f, h5py.Dataset):
        add_metadata(in_dict=metadata_dict, name=f.name,
                    obj=f, request=request, name_key=name_key)
    else:
        raise ValueError(
            "Unsupported input type. Input must be h5py.Group or h5py.Dataset")

    # print request.build_absolute_uri( reverse('omsi_client.viewer') )

    # Return the completed dict
    return metadata_dict


##################################################################
#   Metadata helper function used for both file and provenance   #
#   metadata computations                                        #
##################################################################
def add_metadata(in_dict, name, obj, request, name_key="name"):
    """Add the metadata for the given input object to the given dictionary.

        :param in_dict: Dictionary to which the metadata for the input object should be added to.
        :param name: The name to be used for the input object.
        :param obj: The input object for which the metadata should be added to in_dict.
        :param name_key: key value to be used to identify object names
        :param request: The http request object. Used to compute URLs.

        :returns: This function does not have any return values but in_dict is modified directly.
    """
    # Get the omsi object
    omsiObj = omsi_file_common.get_omsi_object(obj)
    if omsiObj is None:
        omsiObj = obj

    # Add the name to the dict (this task needs to be done for any object)
    in_dict[name_key] = name
    in_dict['path'] = obj.name
    # General properties
    in_dict['do_qslice'] = False
    in_dict['do_qspectrum'] = False
    in_dict['do_qcube'] = False
    in_dict['do_qmz'] = False
    in_dict['do_qmetadata'] = True
    in_dict['class'] = str(omsiObj.__class__)
    # Check if we have a download URL
    downURL = get_download_URL(request, omsiObj)
    if downURL is not None:
        in_dict['downURL'] = downURL
    # Check if we have a viewer URL
    if isinstance(omsiObj, omsi_file_dependencydata):
        viewURL = get_viewer_URL(
            request, omsi_file_common.get_omsi_object(obj, resolve_dependencies=True))
    else:
        viewURL = get_viewer_URL(request, omsiObj)
    if viewURL is not None:
        in_dict['viewURL'] = viewURL
    # Check if we have a manager URL
    managerURL = get_manager_URL(request, omsiObj)
    if managerURL is not None:
        in_dict['manageURL'] = managerURL

    # Add file specific metadata
    if isinstance(omsiObj, omsi_file):
        in_dict['filesize'] = os.stat(
            omsiObj.get_h5py_file().filename).st_size
        in_dict['num_exp'] = omsiObj.get_num_experiments()
    # Add experiment specific metadata
    elif isinstance(omsiObj,  omsi_file_experiment):
        in_dict['num_msidata'] = omsiObj.get_num_msidata()
        in_dict['num_ana'] = omsiObj.get_num_analysis()
        in_dict['ana_identifiers'] = omsiObj.get_analysis_identifiers()
        in_dict['type'] = 'omsi_file_experiment'
        in_dict['timestamp'] = omsiObj.get_timestamp()
        in_dict['version'] = omsiObj.get_version()
    # Add method specific metadata
    elif isinstance(omsiObj, omsi_file_methods):
        in_dict['type'] = 'omsi_file'
        in_dict['timestamp'] = omsiObj.get_timestamp()
        in_dict['version'] = omsiObj.get_version()
    # Add instrument specific metadata
    elif isinstance(omsiObj, omsi_file_instrument):
        in_dict['timestamp'] = omsiObj.get_timestamp()
        in_dict['version'] = omsiObj.get_version()
    # Add analysis specific metadata
    elif isinstance(omsiObj, omsi_file_analysis):
        anaDataNames = omsiObj.get_analysis_data_names()
        in_dict['do_qslice'] = analysis_views.supports_slice(omsiObj)
        in_dict['do_qspectum'] = analysis_views.supports_spectra(omsiObj)
        in_dict['do_qmz '] = (in_dict['do_qslice'] or in_dict['do_qspectum'])
        in_dict['do_qcube'] = False
        in_dict['do_qmetadata'] = True
        in_dict['qslice_viewerOptions'] = analysis_views.get_qslice_viewer_options(omsiObj)
        in_dict['qspectrum_viewerOptions'] = analysis_views.get_qspectrum_viewer_options(omsiObj)
        in_dict['ana_data_names'] = anaDataNames
        in_dict['num_ana_data'] = len(anaDataNames)
        in_dict['timestamp'] = omsiObj.get_timestamp()
        in_dict['version'] = omsiObj.get_version()
    # Add dependency specific metadata
    elif isinstance(omsiObj, omsi_file_dependencydata):
        in_dict['timestamp'] = omsiObj.get_timestamp()
        in_dict['version'] = omsiObj.get_version()
    # Add raw msi data specific metadata
    elif isinstance(omsiObj, omsi_file_msidata):
        in_dict['do_qslice'] = True
        in_dict['do_qspectum'] = True
        in_dict['do_qmz'] = True
        in_dict['do_qcube'] = True
        in_dict['do_qmetadata'] = True
        in_dict['timestamp'] = omsiObj.get_timestamp()
        in_dict['version'] = omsiObj.get_version()
    # Add dataset specific metadata
    # This case occurs regularly as it covers h5py.Dataset objects which typically
    # don't have a corresponing omsi file API object
    elif isinstance(omsiObj, h5py.Dataset):
        in_dict['dtype'] = str(omsiObj.dtype)
        in_dict['shape'] = str(omsiObj.shape)
        # If the dataset identifies a single string object. Then load the data
        # and return it as part of the metadata
        # (omsiObj.dtype == omsi_format_common.str_type) and (omsiObj.shape == (1,)) :
        if omsiObj.shape == (1,):
            try:
                in_dict['value'] = unicode(omsiObj[0])
            except:
                pass
    # Add non omsi file specific metadata
    # This case may occur if an HDF5 file is given that is not an OMSI file
    #(unless the omsi_file API checks for format compliance this may not occur).
    elif isinstance(omsiObj, h5py.File):
        in_dict['filesize'] = os.stat(omsiObj.filename).st_size
    # This case may occure in case we have an unmanaged group that doesn not have
    # a corrsponsing omsi file API object
    elif isinstance(omsiObj, h5py.Group):
        pass
    # Unknown objects
    else:
        pass


def find_group_in_metadatadict(name, metadata_dict, name_key, child_key, close_child_key):
    """Find the dictionary in metadata_dict that belongs to the given file path.

       :param name: Path in the given hdf5 file.
       :param metadata_dict: File object metadata dictonary.
       :param name_key: The name key to be used
       :param child_key: The child key to be used.
       :param close_child_key: The key to be used for closed childs
              (i.e., children that should not be displayed).

    """
    l = name.split('/')
    # Check if the previously used dictionary is still valid
    #if prevName == name:
    #    return prevDict
    # Find the correct dictionary
    s = metadata_dict
    for i in l:
        if len(i) > 0:
            try:
                sc = s[child_key]
            except:
                sc = s[close_child_key]
            for c in sc:
                if c[name_key] == i:
                    s = c
                    break
    return s


def get_manager_URL(request, omsiObj):
    """ Get the manager URL for the given omsi file API object.

        :param request: HTTP request object used to determine the absolute URL. If set to
                        None, URL's will be determined based on the settings.API_ROOT instead.
        :param omsiObj: The omsi file API object for which a manager URL should be determined.

        :returns:

            * String with the manager URL
            * None in case no manager URL can be determined for the given object.
    """
    managerURL = None
    queryParams = {}
    if isinstance(omsiObj, omsi_file):
        if request:
            managerURL = request.build_absolute_uri(reverse('omsi_resources.filemanager'))
        else:
            managerURL = settings.API_ROOT.rstrip("/") + "/" + reverse('omsi_resources.filemanager').lstrip("/")
        queryParams['file'] = omsi_file_common.get_h5py_object(omsiObj).file.filename
    if managerURL is not None:
        a = QueryDict('')
        d = a.copy()
        # Make a mutable QueryDict by calling copy() and copy the
        # queryParameters into it by calling update()
        d.update(queryParams)
        # Add the querystring to our URL
        return managerURL + '?' + d.urlencode()
    else:
        return None


# Get download URL
def get_download_URL(request, omsiObj):
    """ Get the download URL for the given omsi file API object.

        :param request: HTTP request object used to determine the absolute URL. If set to
                        None, URL's will be determined based on the settings.API_ROOT instead.
        :param omsiObj: The omsi file API object for which a download URL should be determined.

        :returns:

            * String with the download URL
            * None in case no download URL can be determined for the given object.
    """
    if request:
        qcubeURL = request.build_absolute_uri(reverse('omsi_access.qcube'))
    else:
        qcubeURL = settings.API_ROOT.rstrip("/") + "/" + reverse('omsi_access.qcube').lstrip("/")
    queryParams = {}
    if isinstance(omsiObj, omsi_file):
        h5pyObj = omsi_file_common.get_h5py_object(omsiObj)
        queryParams[views_definitions.query_parameters['file']
                    ] = h5pyObj.file.filename
        queryParams[views_definitions.query_parameters['format']
                    ] = views_definitions.available_formats['HDF5']

    if queryParams:
        a = QueryDict('')
        d = a.copy()
        # Make a mutable QueryDict by calling copy() and copy the
        # queryParameters into it by calling update()
        d.update(queryParams)
        # Add the querystring to our URL
        return qcubeURL + '?' + d.urlencode()
    else:
        return None


# Compute viewer URL for a given object
def get_viewer_URL(request, omsiObj):
    """ Get the viewer URL for the given omsi file API object.

        :param request: HTTP request object used to determine the absolute URL. If set to
                        None, URL's will be determined based on the settings.API_ROOT instead.
        :param omsiObj: The omsi file API object for which a viewer URL should be determined.

        :returns:

            * String with the viewer URL
            * None in case no viewer URL can be determined for the given object.
    """
    # Check whether the object supports the viewer
    supportsViewer = False
    if isinstance(omsiObj, omsi_file_msidata):
        supportsViewer = True
    if isinstance(omsiObj, omsi_file_analysis):
        supportsViewer = (analysis_views.get_qslice_viewer_options(omsiObj) and
                          analysis_views.get_qspectrum_viewer_options(omsiObj))
    if not supportsViewer:
        return None

    if request:
        viewerURL = request.build_absolute_uri(reverse('omsi_client.viewer'))
    else:
        viewerURL = settings.API_ROOT.rstrip("/") + "/" + reverse('omsi_client.viewer').lstrip("/")
    h5pyObj = omsi_file_common.get_h5py_object(omsiObj)
    path = h5pyObj.name
    sp = path.split("/")

    # Define the query parameter values
    filename = h5pyObj.file.filename
    expIndex = None
    dataIndex = None
    anaIndex = None
    channel1Value = None
    channel2Value = None
    channel3Value = None
    rangeValue = None
    cursorCol1 = 0
    cursorRow1 = 0
    cursorCol2 = 5
    cursorRow2 = 5
    image_name = os.path.basename(filename)
    expList = filter(lambda x: omsi_format_experiment.exp_groupname in x, sp)
    expIndex = expList[0].lstrip(omsi_format_experiment.exp_groupname)
    expIndex = int(expIndex, base=10)
    if isinstance(omsiObj, omsi_file_msidata):
        dataList = filter(lambda x: omsi_format_data.data_groupname in x, sp)
        if len(dataList) > 0:
            dataIndex = int(
                dataList[0].lstrip(omsi_format_data.data_groupname))
            rowSize, colSize, mzSize = omsiObj.shape
            mzaxis = omsiObj.mz[:]
            minmz = mzaxis.min()
            maxmz = mzaxis.max()
            stepmz = (maxmz - minmz) / 5.0
            cuttoff = 10000.0
            channel1Value = int(cuttoff * (minmz + stepmz)) / cuttoff
            channel2Value = int(cuttoff * (minmz + 2 * stepmz)) / cuttoff
            channel3Value = int(cuttoff * (minmz + 3 * stepmz)) / cuttoff
            # Range is set to 10 average-width m/z bins
            rangeValue = 10 * \
                ((omsiObj.mz[-1] - omsiObj.mz[0]) / float(omsiObj.mz.shape[0]))
            cursorCol1 = int(colSize / 3.0)
            cursorCol2 = int(2 * (colSize / 3.0))
            cursorRow1 = int(rowSize / 3.0)
            cursorRow2 = int(2 * (rowSize / 3.0))
        else:
            # ToDo Fix case when we have an omsi_file_msidata object but cannot
            # identify its index
            # We have an omsi_file_msidata object but we cannot identify its
            # index in the file
            return None
    elif isinstance(omsiObj, omsi_file_analysis):
        anaList = filter(
            lambda x: omsi_format_analysis.analysis_groupname in x, sp)
        anaIndex = int(
            anaList[0].lstrip(omsi_format_analysis.analysis_groupname))
        try:
            # , qslice_viewerOption=0, qspectrum_viewerOption=0 )
            valuesSpectra, labelSpectra, valuesSlice, labelSlice, valuesX, labelX, valuesY, labelY, valuesZ, labelZ = \
                analysis_views.get_axes(omsiObj)
            rangeValue = 0
            if not valuesSlice:
                valuesSlice = valuesSpectra
            mzSize = valuesSlice.shape[0]
            minmz = valuesSlice.min()
            maxmz = valuesSlice.max()
            stepmz = (maxmz - minmz) / 5.0
            cuttoff = 1.0
            channel1Value = int(cuttoff * (minmz + stepmz)) / cuttoff
            channel2Value = int(cuttoff * (minmz + 2 * stepmz)) / cuttoff
            channel3Value = int(cuttoff * (minmz + 3 * stepmz)) / cuttoff
        except:
            pass

    queryParams = {}
    if image_name is not None:
        queryParams['image_name'] = image_name
    queryParams['file'] = filename
    queryParams['expIndex'] = expIndex
    if dataIndex is not None:
        queryParams['dataIndex'] = dataIndex
    if anaIndex is not None:
        queryParams['anaIndex'] = anaIndex
    if channel1Value is not None:
        queryParams['channel1Value'] = channel1Value
    if channel2Value is not None:
        queryParams['channel2Value'] = channel2Value
    if channel3Value is not None:
        queryParams['channel3Value'] = channel3Value
    if rangeValue is not None:
        queryParams['rangeValue'] = rangeValue
    queryParams['cursorCol1'] = cursorCol1
    queryParams['cursorRow1'] = cursorRow1
    queryParams['cursorCol2'] = cursorCol2
    queryParams['cursorRow2'] = cursorRow2
    queryParams['enableClientCache'] = 'true'

    a = QueryDict('')
    d = a.copy()
    # Make a mutable QueryDict by calling copy() and copy the queryParameters
    # into it by calling update()
    d.update(queryParams)
    # Add the querystring to our URL
    viewerURL = viewerURL + '?' + d.urlencode()
    return viewerURL


def send_email(subject, recipients, body, sender='openmsi.automail@openmsi.nersc.gov'):
    """Send email notification to users.

       :param subject: Subject line of the email
       :param recipients: List of email recipients
       :param body: Body text of the email.
       :param sender: The originating email address

    """
    #Remove duplicates from the list of recipients
    recipients = list(set(recipients))
    #Check if we have any recipients
    if len(recipients) == 0:
        return

    from smtplib import SMTP
    from email.MIMEText import MIMEText
    from email.Header import Header
    from email.Utils import parseaddr, formataddr

    header_charset = 'ISO-8859-1'
    body_charset = 'US-ASCII'
    for bc in 'US-ASCII', 'ISO-8859-1', 'UTF-8':
        try:
            body_charset = bc
            body.encode(body_charset)
        except UnicodeError:
            pass
        else:
            break

    # Define the sender and recipients
    sender_name, sender_addr = parseaddr(sender)
    sender_name = str(Header(unicode(sender_name), header_charset))
    sender_addr = sender_addr.encode('ascii')

    tostr = ""
    for ri in range(len(recipients)):
        rec = recipients[ri]
        recname, recaddr = parseaddr(rec)
        recname = str(Header(unicode(recname), header_charset))
        recaddr = recaddr.encode('ascii')
        tostr += formataddr((recname, recaddr))
        if ri < (len(recipients)-1):
            tostr += ", "

    # Construct the message
    msg = MIMEText(body.encode(body_charset), 'plain', body_charset)
    msg['From'] = formataddr((sender_name, sender_addr))
    msg['To'] = tostr
    msg['Subject'] = Header(unicode(subject), header_charset)

    # Send the message using sendmail
    try:
        smtp = SMTP("localhost")
        smtp.sendmail(sender, recipients, msg.as_string())
        smtp.quit()
    except:
        warnings.warn('Email could not be sent' + str(sys.exc_info()))


def __generate_cache_key__(data_type, primary_key):
    """Helper function used to generate keys for the DJANGO cache based on the
       type of data requested and the primary key (usually the full name of the
       file as stored in the SQL database).

       :param data_type: String indicating the type of data requested, e.g,
                         metadata, provenance
       :type data_type: String
       :param primary_key: Primary key of the main object the cache entry is
                         associated with.
       :type primary_key: String

       :returns: String indicating the cache key to be used.
    """
    return unicode(data_type)+u':'+unicode(primary_key)


# def generate_cache_key(request, filename=None):
#     """Helper function used to generate keys for the DJANGO cache based on the request.
#
#        :param request: The DJANOG request for the view
#        :param filename: Full name of the file. This is used to ensure that if a user used
#                         relative paths in their request that ultimately all point to the
#                         same file, that we do not generate multiple cache entries for
#                         requests that actually generate the same data. This also means
#                         that the user will be able to benefit from the cache in more cases.
#
#        :returns: Unicode string to be used as cache key.
#     """
#     key = request.path
#     querydict = request.GET.copy()
#     if 'file' in querydict and filename:
#         querydict['file'] = filename
#     key += querydict.urlencode()
#     return key
