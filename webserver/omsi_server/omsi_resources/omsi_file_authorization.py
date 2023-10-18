#TODO: Refactor the code here to be encapsulated by a OMSIFileAuthorization class
#TODO: Complete get_filedict_rawfile once the models for raw data files are completed

import logging
logger = logging.getLogger(__name__)
from django.conf import settings  # Get the DJANGO settings, e.g., to get the default file path
from django.http import HttpResponse, \
                        HttpResponseNotFound, \
                        HttpResponseForbidden, \
                        HttpResponseRedirect, \
                        HttpResponseBadRequest
from django.db.models import Q
from django.contrib.auth import authenticate, login
import sys
import os

try:
    from omsi_server.omsi_resources.models import FileModelOmsi, FileModelRaw
except ImportError:
    from omsi_resources.models import FileModelOmsi, FileModelRaw

g_request_types = {'public': 'public:',
                   'private': 'private:',
                   'unknown': -1}
"""
For unmanaged file accesses define the type of access to perform

    * `public` : Access publicly shared file
    * `private` : Access private user data file

"""

g_access_types = {'view': 'view',
                  'edit': 'edit',
                  'manage': 'manage'}
"""
Type of available data access types:

    * `view` : View file
    * `edit` : Edit the file
    * `manage` : Manage the file, e.g., change access permissions

"""

g_file_status = {'managed': 'managed',
                 'unmanaged': 'unmanaged'}
"""
System status of the file:

    * `managed` : The file is registered with the database
    * `unmanaged` : The file is visible on the filesystem but not registere with the database

"""

g_filedict_keys = {'permissions': 'permissions',
                   'status': 'status'}
"""
Define keys used in the dict of files

    * `permissions` : Define the access permissions for the file, see g_access_type
    * `status`: Status of the file in the system. See g_file_status.

"""

g_file_types = {'omsi': 'omsi',
                'raw': 'raw'}
"""
Define the basic type of file (raw or omsi file)

    * `omsi` : File in openmsi file format
    * `raw` : Raw data file in third party format

"""


#####################################################################
#     Get file listings                                             #
#####################################################################
def get_filedict_omsi(request,
                     accesstype=g_access_types['view']):
    """Get a list of all managed and unmanged files that the user has access to.
       If a file is managed and appears in an unmanaged location, then the corresponding
       managed file entry takes precedence over the unmanaged entry. This is consistent
       with the overall authorization scheme of the system.

       :returns: filedict : Dictionary of files with the following information for each file:

                * key : Path of the file
                * value : For each file a dictionary with the following structure

                    * permissions : One of view, edit, manage
                    * status : One of manage or unmanaged
    """
    #Get list of managed and unmanaged files
    unmanaged_files = get_filedict_omsi_unmanaged(request=request, accesstype=accesstype)
    managed_files = get_fileldict_omsi_managed(request=request, accesstype=accesstype)
    #Merge the list of managed and unmanged files. The update merges the two dicts and overwrites any
    #values from the unmanaged dict with corresponding values from the managed dict if there are dublicate entries.
    #Dublicated may occure if a file is stored in an umanaged location but is added to the database as well.
    filedict = {}
    filedict.update(unmanaged_files)
    filedict.update(managed_files)
    #filedict = unmanaged_files.update( managed_files )
    #Return the merged list of files
    return filedict


def get_fileldict_omsi_managed(request,
                          accesstype=g_access_types['view']):
    """Get a list of all managed files that the user has access to.

       :param request: The http request object used to determine the users name.
       :param accesstype: Define what type of operation the user needs to perform on the data.
                          See g_access_types.

       :returns: fileDict : Dictionary of files with the following information for each file:

                * key : Path of the file
                * value : For each file a dictionary with the following structure

                    * permissions : One of view, edit, manage
                    * status : One of manage or unmanaged

    """
    #NOTE the code below has the following logic:
    #   - We first generate the list of files a user can view
    #   - We then check whether the user can edit
    #   - We then check whether the user can manage
    # In each of the step the values for different keys in the dictionaty may be overwritten.
    # In this way we get a list of unique files (no file appears twice) and we have the
    # highest permission the user has listed in the dictionary.
    global g_filedict_keys
    global g_file_status
    global g_access_types
    global g_request_types

    #Get the name, authentification status, and list of groups of the user
    username = request.user.username
    authenticated = request.user.is_authenticated()
    try:
        usergroups = request.user.groups.values_list('name', flat=True)
    except:
        usergroups = []

    #Get the list of public files
    f = FileModelOmsi.objects.filter(is_public__exact=True)
    filedict = {}
    if accesstype == g_access_types['view']:
        filedict = {p.path:  # Key in the dictionary
                        {g_filedict_keys['permissions']: g_access_types['view'],
                         g_filedict_keys['status']: g_file_status['managed']}  # Values in dictionary
                    for p in f  # for all public files
                   }
    if authenticated:
        #Query the database to see which files the user is allowed to view, edit manage files
        f_user_view = FileModelOmsi.objects.filter(view_users__username__contains=username)
        f_user_edit = FileModelOmsi.objects.filter(edit_users__username__contains=username)
        f_user_manage = FileModelOmsi.objects.filter(owner_users__username__contains=username)
        #Query the database to see which groups the user belongs to are allowed to view, edit, or manage files
        #The lamda functions used below generate the following basic type of query:
        #Q(auth_groups__name__contains=usergroups[0]) |
        #Q(auth_groups__name__contains=usergroups[1]) | ... |
        #Q(auth_groups__name__contains=usergroups[-1])
        #which simply checks whether any of the groups of the user
        #defined in usergroups is part of the list of auth_groups
        #Groups that can view
        try:
            f_groups_view = FileModelOmsi.objects.filter(reduce(lambda x, y: x | y, [Q(view_groups__name__contains=groupname) for groupname in usergroups]))
        except:
            f_groups_view = []
            print "omsi_file_authorization.get_fileldict_omsi_managed: "+str(sys.exc_info())
        #User groups that can edit
        try:
            f_groups_edit = FileModelOmsi.objects.filter(reduce(lambda x, y: x | y, [Q(edit_groups__name__contains=groupname) for groupname in usergroups]))
        except:
            f_groups_edit = []
            print "omsi_file_authorization.get_fileldict_omsi_managed: "+str(sys.exc_info())
        #User groups that own
        try:
            f_groups_manage = FileModelOmsi.objects.filter(reduce(lambda x, y: x | y, [Q(owner_groups__name__contains=groupname) for groupname in usergroups]))
        except:
            f_groups_manage = []
            print "omsi_file_authorization.get_fileldict_omsi_managed: "+str(sys.exc_info())

        #Check all files the user is allowed to view
        if accesstype == g_access_types['view']:
            for cf in f_groups_view:
                filedict[cf.path] = {g_filedict_keys['permissions']: g_access_types['view'], g_filedict_keys['status']: g_file_status['managed']}
            for cf in f_user_view:
                filedict[cf.path] = {g_filedict_keys['permissions']: g_access_types['view'], g_filedict_keys['status']: g_file_status['managed']}

        #Check all files that a user can edit. Files that can be edited by a user can also automatically be viewed by that user
        if (accesstype == g_access_types['view']) or (accesstype == g_access_types['edit']):
            for cf in f_groups_edit:
                filedict[cf.path] = {g_filedict_keys['permissions']: g_access_types['edit'], g_filedict_keys['status']: g_file_status['managed']}
            for cf in f_user_edit:
                filedict[cf.path] = {g_filedict_keys['permissions']: g_access_types['edit'], g_filedict_keys['status']: g_file_status['managed']}

        # Check all files that the user can manage. Files that the user can manage
        # can also automatically be viewed and edited by that user.
        if (accesstype == g_access_types['view']) or (accesstype == g_access_types['edit']) or (accesstype == g_access_types['manage']):
            for cf in f_groups_manage:
                filedict[cf.path] = {g_filedict_keys['permissions']: g_access_types['manage'], g_filedict_keys['status']: g_file_status['managed']}
            for cf in f_user_manage:
                filedict[cf.path] = {g_filedict_keys['permissions']: g_access_types['manage'], g_filedict_keys['status']:  g_file_status['managed']}

    return filedict


def get_filedict_omsi_unmanaged(request,
                                accesstype=g_access_types['view']):
    """Get a list of all unmanaged files that the user has access to.

       :param request: The http request object used to determine the users name.
       :param accesstype: Define what type of operation the user needs to perform on the data.
                          See g_access_types.

       :returns: fileDict : Dictionary of files with the following information for each file:

                * key : Path of the file
                * value : For each file a dictionary with the following structure

                    * permissions : One of view, edit, manage
                    * status : One of manage or unmanaged

    """
    global g_file_status
    global g_access_types
    global g_filedict_keys

    #Get the name of the user
    username = request.user.username
    authenticated = request.user.is_authenticated()
    filedict = {}

    #Check if we know any possible data paths
    if len(settings.ALLOWED_DATAPATHS) == 0 and len(settings.PRIVATE_DATAPATHS) == 0:
        #return HttpResponseNotFound("No folders with allowed files specified. Contact your system admin to define the ALLOWED_DATAPATHS")
        return filedict

    if accesstype == g_access_types['view']:
        #Generate the list of public data files
        for p in settings.ALLOWED_DATAPATHS:
            #Check if the data path exists, else ignore it
            if os.path.exists(p):
                currentlist = []
                if settings.ALLOWED_DATAPATHS_EXACT:  # Look only at the current directory
                    currentlist = [os.path.join(p, fn) for fn in os.listdir(p)]
                else:   # Look also at all subdirectories
                    for (path, dirs, files) in os.walk(p):
                        currentlist = currentlist + [os.path.join(path, fn) for fn in files]

                #Check which of the entries in the list are hdf5 files
                for name in currentlist:
                    if name.endswith(".h5"):
                        filedict[name] = {g_filedict_keys['permissions']: g_access_types['view'], g_filedict_keys['status']: g_file_status['unmanaged']}

    #Generate list of private unmanged data files
    if authenticated:
        currentlist = []
        #Iteate through all private data locations for the user
        for p in settings.PRIVATE_DATAPATHS:
            currentpath = os.path.join(p, username)
            if os.path.exists(currentpath):
                for (path, dirs, files) in os.walk(currentpath):
                    currentlist = currentlist + [os.path.join(path, fn) for fn in files]
        #Check which of the entries in the list are hdf5 files
        for name in currentlist:
            if name.endswith(".h5"):
                filedict[name] = {g_filedict_keys['permissions']: g_access_types['manage'],
                                  g_filedict_keys['status']: g_file_status['unmanaged']}

    return filedict


def get_filedict_rawfile(request,
                         accesstype=g_access_types['manage']):
    """Get a list of all raw data files that the user has access to.

       :param request: The http request object used to determine the users name.
       :param accesstype: Define what type of operation the user needs to perform on the data.
                          See g_access_types. Default is g_access_types['manage']. Currently
                          not used, but included in preparation for future support of
                          auth on raw data files.

       :returns: fileDict : Dictionary of files with the following information for each file:

                * key : Path of the file
                * value : For each file a dictionary with the following structure

                    * permissions : One of view, edit, manage
                    * status : One of manage or unmanaged

    """
    global g_file_status
    global g_access_types
    global g_filedict_keys

    # 1) Get the name of the user
    username = request.user.username
    authenticated = request.user.is_authenticated()

    # 2) Check if we know any allowed data paths
    if len(settings.SYSTEM_USER_RAWDATAPATHS) == 0:
        return HttpResponseNotFound("No folders for raw data storage specified. " +
                                    "Contact your system admin to define the ALLOWED_DATAPATHS")
    # 3) Compute the dictionary of raw files the user is allowed to access
    filedict = {}
    if authenticated:
        # 3.1) Run a query to find all raw files the user owns
        rawfiles_user_owns = FileModelRaw.objects.filter(owner_users__username__contains=username)

        # 3.1) Look at all raw data files in the system raw data path ot the user
        #      used by the user to upload their raw data to the system. Add all
        #      folders to the filedict
        for basefolder in settings.SYSTEM_USER_RAWDATAPATHS:
            userfolder = os.path.join(basefolder, username)
            if os.path.exists(userfolder):
                for rawdir in os.listdir(userfolder):
                    rawdirpath = os.path.abspath(os.path.join(userfolder, rawdir))
                    if os.path.isdir(rawdirpath):
                        filedict[rawdirpath] = {g_filedict_keys['permissions']: g_access_types['manage'],
                                                g_filedict_keys['status']: g_file_status['unmanaged']}
        # 3.2) Find all raw data files that are in the system and update the filedict accordingly
        for cf in rawfiles_user_owns:
            # Note, this will intentionally overwrite previously added entries
            # to update their status from managed to unmanaged
            filedict[os.path.abspath(cf.path)] = {g_filedict_keys['permissions']: g_access_types['manage'],
                                                  g_filedict_keys['status']: g_file_status['managed']}
    return filedict


#####################################################################
#         File authorization                                        #
#####################################################################
def authorize_fileaccess(request,
                         infilename,
                         accesstype=g_access_types['view'],
                         check_omsi_files=True,
                         check_raw_files=False):
    """The function computes the real file name and checks whether the user is authorized to access
       the given file.

       :param request: The http request object used to determine the users name.
       :param infilename: Filename as given by DJANGO based on provided URL.
       :param accesstype: Define what type of operation the user needs to perform on the data. See g_access_types.
       :param check_omsi_files: Authorize access to omsi files.
       :type check_omsi_files: bool
       :param check_raw_files: Authorize access to raw data files.
       :type check_raw_files: bool

       :returns: The function returns the following two items:
                * The functions returns a string indicating the full name of the file.
                  If the file does not exists or the user is not allowed to access the
                  file then an appropriate HttpResponse is returned.
                * The function returns the corresponding FileModelOmsi if it exists and \
                  None if the file does not exist in the database.
                * filetype string indicating whether the file is an openmis file or a \
                  raw data file.

       :raises: ValueError is raised in case that both check_omsi_files and check_raw_files is
                set to False.


       Authorization Diagram for Omsi Files::

             +----------------------+     +---------------------------------------------------------+
             |authorize_file_access |     | authorize_file_access_registered_file                   |
             |----------------------|     |---------------------------------------------------------|
             |  - http request      |     | - If a matching file is in the database                 |
             |  - file name         |     |   --> NO : Return None :                                |
             |  - access type       |     |            Use authorize_file_access_nonregistered_file |
             |  - (view,edit,manage)|     |   --> Yes                                               |
             |                      |     |         --> If the user wants to view the file          |
             +----------+-----------+     |             (access_type==view) AND the file is_public  |
                        |                 |           --> YES Return the file path                  |
                        |                 |           --> NO:                                       |
             +--------------------+       |             1)--> Check if the user is part of the list |
             |If file is managed  | Yes   |                   of view_users, edit_users, owner_users|
             |in the database     +-------|                   -- if view access and user can view,  |
             +--------------------+       |                      edit,or own--> return the file path|
                        |                 |                   -- if edit access and user can edit or|
                        |                 |                      own --> return the file path       |
                        |                 |                   -- if manage access and user can own  |
                        |                 |                      --> return the file path           |
                        |                 |             2) --> Same as 1) but for view_groups,      |
                        |                 |                    edit_groups and owner_groups for the |
                        |                 |                    file that the user can be part of    |
                        |                 |             3) If 1), 2) do not return a file path then |
                        |                 |                    deny access                          |
                        |                 +---------------------------------------------------------+
                        |
                        |                 +---------------------------------------------------------+
                        |                 | authorize_file_access_nonregistered_file                |
                        |       No        |---------------------------------------------------------|
                        +---------------->| - Determine whether a public or private file is accessed|
                                          |   -- If file path starts with public: --> Public access |
                                          |      --> YES : Public access                            |
                                          |      --> No:                                            |
                                          |          -- If file path start with private:            |
                                          |             --> YES: Private access                     |
                                          |             --> No:                                     |
                                          |                 -- If an absolute path is given and the |
                                          |                    path is a private data location      |
                                          |                    --> YES: Private access              |
                                          |                    --> No:                              |
                                          |                        If user is authenticated and the |
                                          |                        path starts with username :      |
                                          |                        -->Yes: Private access           |
                                          |                        -->No: Public access             |
                                          | - If we can resolve the path given by the user to an    |
                                          |   existing path                                         |
                                          |   --> YES                                               |
                                          |       -- If __authorize_directory_access__ allows access|
                                          |          --> YES: Return the full path                  |
                                          |          --> NO:  Access denied                         |
                                          |   --> NO                                                |
                                          |       -- If Public access requested                     |
                                          |          YES:                                           |
                                          |          --> Search all ALLOWED_DATAPATHS to find a     |
                                          |              matching file for which                    |
                                          |              __authorize_directory_access allows access |
                                          |       -- If Private access requested                    |
                                          |          --> Search all PRIVATE_DATAPATHS to find a     |
                                          |              matching file  for which                   |
                                          |              __authorize_directory_access allows access |
                                          | - If none of the above has worked, indicate that the    |
                                          |   requested file  was not found in an allowed location  |
                                          +---------------------+-----------------------------------+
                            Uses                                |
                      +-----------------------------------------+
                      |
                      |                   +---------------------------------------------------------+
                      |                   | authorize_directory_access                              |
                      |                   |---------------------------------------------------------|
                      |                   | - If private access requested (request_type==private)   |
                      |                   |   --> YES : The access_type is irrelevant since a user  |
                      |                   |             owns its private files and hence can        |
                      |                   |             view,edit and manage                        |
                      |                   |       -- if user is authenticated                       |
                      |                   |          YES: --> Reroute to login page                 |
                      |                   |       -- if user is authenticated                       |
                      |                   |          NO: Return false (access denied)               |
                      |                   |          YES:                                           |
                      |                   |            -- Check whether the file is in any of the   |
                      |                   |               user's private data locations             |
                      |                   |               YES: --> Return file path                 |
                      |                   |   --> NO :                                              |
                      +-------------------+       - If public access (request_type==public)         |
                                          |         -->YES:                                         |
                                          |            - If access_type is view (we can only view   |
                                          |              public files but an system admin is needed |
                                          |              to change a public file that is not managed|
                                          |              by the database. This is to avoid anybody  |
                                          |              changing any file.)                        |
                                          |              --> NO : Return false (access denied)      |
                                          |              --> YES:                                   |
                                          |                  -- Check whether the file is in an     |
                                          |                     ALLOWED_DATAPATHS                   |
                                          |                     YES: return true (access granted)   |
                                          |                     NO:                                 |
                                          |                     - If ALLOWED_DATAPATHS_EXACT==False |
                                          |                       YES: Check whether the file is in |
                                          |                            a subdir of ALLOWED_DATAPATHS|
                                          |                            YES: Return true             |
                                          |                                 (access granted)        |
                                          | - Return false (access denied, none of the above methods|
                                          |                 have granted access to the requested    |
                                          |                 directory                               |
                                          +---------------------------------------------------------+

    """
    global g_access_types
    global g_file_types

    try:
         #Remove the "" characters from the filename string if necessary
        realfilename = str(infilename).rstrip("'").rstrip('"').lstrip("'").lstrip('""')
    except:
        return HttpResponseNotFound("Invalid filename. "), None, g_file_types['omsi']

    # 1) Authorize access to openmsi files
    if check_omsi_files:
        # 1.1) Check if the file is registered in the database and authorize access
        response, model = __authorize_fileaccess_registered_file__(request, realfilename, accesstype)
        if response is not None:
            return response, model, g_file_types['omsi']
        # 1.2 If the file is not registered in the database authorize access for non-registered files
        else:
            response = __authorize_fileaccess_nonregistered_file__(request, realfilename, accesstype)
            # If the file was not found and we are asked to check raw files, then
            # go on and check raw files, otherwise return the response.
            if not (isinstance(response, HttpResponseNotFound) and check_raw_files):
                return response, None, g_file_types['omsi']

    # 2) Authorize access for raw data files
    if check_raw_files:
        # 2.1) Original files are always in manage only mode
        accesstype = g_access_types['manage']
        # 2.2) Authorize the file access
        response, model = __authorize_fileaccess_rawfile__(request, realfilename, accesstype)
        return response, model, g_file_types['raw']

    # 3) Usage error.
    # 3.1) The user somehow specified to check neither omsi nor raw files.
    if not check_raw_files and not check_omsi_files:
        raise ValueError('Invalid use of authorize_file access. At least one of ' +
                         'check_raw_files and check_omsi_files must be set to True')
    # 3.2) Some other strange error. This case should be impossible to reach.
    else:
        return HttpResponseBadRequest("File authorization request invalid."), None, g_file_types['omsi']


def is_file_registered(infilename):
    """Simple function used to check whether the given file is part of the
       file database.

       :param infilename: The full path or name of the file.

       :returns: Boolean indicting whether a matching file entry was found.
    """
    f = FileModelOmsi.objects.filter(path__endswith=infilename)
    return len(f) > 0


def __authorize_fileaccess_rawfile__(request,
                                     infilename,
                                     accesstype):
    """
    Authorize access to a raw data file. The file may be managed in the
    system or unmangaged. If the file is unmanaged None is returned for
    the filemodel.

    :param request: The http request object used to determine the users name.
    :param infilename: Filename as given by DJANGO based on provided URL.
    :param accesstype: Define what type of operation the user needs to perform on the data.
                       See g_access_types.

    :returns: The function returns two items:
           1) The path to the file identified as:

              * String with the path of the file
              * HttpResponseForbidden if access is not allowed.
              * HttpResponseRedirect if login is  needed.
              * HttpResonseNotFound if the file was not found.

           2) The corresponding FileModelRaw if it exists or None in case the file is not in the database \
              Note, file may exist and access is authorized (i.e., we return a filename) but no model is \
              available in the database
    """
    global g_request_types
    global g_access_types

    username = request.user.username
    authenticated = request.user.is_authenticated()

    # 1) Check if the user is authenticated
    # Currently we only have owner permissions so the user must always be
    # logged in to gain access to a raw data file
    # Redirect the user to login page
    if not authenticated:
        return redirect_to_login(request=request), None
    authenticated = request.user.is_authenticated()
    # If the user is still not authenticated then return an error
    if not authenticated:
        return HttpResponseNotFound("File access not permitted."), None

    # 2) Strip the filename of any possible access indicators
    realfilename = infilename.lstrip(g_request_types['private']).lstrip(g_request_types['public'])

    # 3) Check if the file is in the database
    f = FileModelRaw.objects.filter(path__endswith=realfilename)
    if len(f) > 0:
        # 3.1) Check if the user is allowed to access the file
        f = f.filter(owner_users__username__contains=username)
        # 3.1.1) The user is allowed to access the file
        if len(f) > 0:
            return f[0].path, f[0]
        # 3.1.2) The file is in the database but the user is not allowed to access the file
        else:
            return HttpResponseForbidden("Access to file denied."), None

    # 4) The file was not in the database, check whether it exists in one of
    #    the users raw data folders
    directorypath, filename = os.path.split(realfilename)
    for basefolder in settings.SYSTEM_USER_RAWDATAPATHS:
            userfolder = os.path.join(basefolder, username)
            if os.path.exists(userfolder):
                userfile = os.path.join(userfolder, filename)
                if os.path.exists(userfile):
                    return userfile, None

    # 5) The file is not in the database and was not found in a user's private data location
    return HttpResponseNotFound("Requested file not found."), None


def __authorize_fileaccess_registered_file__(request,
                                             infilename,
                                             accesstype):
    """A registered file is a file that has been added to the SQL database and
       is fully managed by the system. This function implements the authorization
       for these files.

       :param request: The http request object used to determine the users name.
       :param infilename: Filename as given by DJANGO based on provided URL.
       :param accesstype: Define what type of operation the user needs to perform on the data.
                          See g_access_types.

       :returns: The function returns two items:
           1) The path to the file identified as:

              * None, in case that the file is not registered in the system.
              * String with the path of the file
              * HttpResponse with a redirect to login if needed or a response indicating that the access is forbidden.

           2) The corresponding FileModelOmsi if it exists or None in case the file is not in the database
    """

    global g_request_types
    global g_access_types

    username = request.user.username
    authenticated = request.user.is_authenticated()
    #Strip the filename of any possible access indicators
    realfilename = infilename.lstrip(g_request_types['private']).lstrip(g_request_types['public'])

    #Check if the file is in the database
    f = FileModelOmsi.objects.filter(path__endswith=realfilename)
    #If the file is not in the database return None to indicate that this is not a registered file
    if len(f) == 0:
        return None, None

    #Check whether there is a public version of the file for view access
    if accesstype == g_access_types['view']:
        f2 = f.filter(is_public__exact=True)
        if len(f2) > 0:  # A public copy of the file is available
            return f2[0].path, f2[0]

    #If the user explicitly specified that only a public data copy should be used then return None
    #since no public copy of the file was found
    #if infilename.startswith(g_request_types['public'])
    #    logger.warn("Public access to file not possible.")
    #    return HttpResponseForbidden("Public access to the file was not possible. You possibly indicated public: access when regular/private access rights are need. " )

    #Check if the user is an authorized user of the file
    #Query whether the user is allowed to view, edit or own the file
    f3_view = f.filter(view_users__username__contains=username)
    f3_edit = f.filter(edit_users__username__contains=username)
    f3_own = f.filter(owner_users__username__contains=username)
    if accesstype == g_access_types['view']:
        if len(f3_view) > 0:
            f3 = f3_view
        elif len(f3_edit) > 0:
            f3 = f3_edit
        else:
            f3 = f3_own
    elif accesstype == g_access_types['edit']:
        if len(f3_edit) > 0:
            f3 = f3_edit
        else:
            f3 = f3_own
    elif accesstype == g_access_types['manage']:
        f3 = f3_own
    else:
        #Unknown access type, therefore we are being most restrictive
        f3 = f3_own
    if len(f3) > 0:  # The user is exlicitly an authorized user of the file
        if authenticated:  # The user is logged in
            return f3[0].path, f3[0]
        else:  # require the user to log in
            return redirect_to_login(request=request), None

    #Check whether the user is part of an authorized group of the file
    #Get all groups the user is part of
    usergroups = request.user.groups.values_list('name', flat=True)
    #If the user is part of some groups, check whether the file is part of any of the
    #groups the user is part of
    if len(usergroups) > 0:
        #The lamda functions used below generate the following basic type of query:
        #Q(auth_groups__name__contains=usergroups[0]) |
        #Q(auth_groups__name__contains=usergroups[1]) | ... |
        #Q(auth_groups__name__contains=usergroups[-1])
        #which simply checks whether any of the groups of the user
        #defined in usergroups is part of the list of auth_groups
        try:
            f4_view = f.filter(reduce(lambda x, y: x | y, [Q(view_groups__name__contains=groupname) for groupname in usergroups]))
        except:
            f4_view = []
            print "omsi_file_authorization.__authorize_fileaccess_registered_file__: "+str(sys.exc_info())
        try:
            f4_edit = f.filter(reduce(lambda x, y: x | y, [Q(edit_groups__name__contains=groupname) for groupname in usergroups]))
        except:
            f4_edit = []
            print "omsi_file_authorization.__authorize_fileaccess_registered_file__: "+str(sys.exc_info())
        try:
            f4_own = f.filter(reduce(lambda x, y: x | y, [Q(owner_groups__name__contains=groupname) for groupname in usergroups]))
        except:
            f4_own = []
            print "omsi_file_authorization.__authorize_fileaccess_registered_file__: "+str(sys.exc_info())
        if accesstype == g_access_types['view']:
            if len(f4_view) > 0:
                f4 = f4_view
            elif len(f4_edit) > 0:
                f4 = f4_edit
            else:
                f4 = f4_own
        elif accesstype == g_access_types['edit']:
            if len(f4_edit) > 0:
                f4 = f4_edit
            else:
                f4 = f4_own
        elif accesstype == g_access_types['manage']:
            f4 = f4_own
        else:
            #Unknown access type, therefore we are being most restrictive
            f4 = f4_own
        #The user is part of at least one of the groups authorized to perform the requested access to the file
        if len(f4) > 0:
            if authenticated:  # The user is logged in
                return f4[0].path, f4[0]
            else:  # require the user to log in
                return redirect_to_login(request=request), None

    # At this point we know that the file is in the database and that
    # the user is not an authorized user nor is the user part of any
    # of the authorized groups
    logger.warn("Access to file denied.")
    return HttpResponseForbidden("Access to file denied."), None


def __authorize_fileaccess_nonregistered_file__(request,
                                                infilename,
                                                accesstype,
                                                alternate_username=None):
    """An unregistered file is a file that exists on the storage system but the file
        has not yet been added to the SQL database. This function implements the authorization
       for these files.

       :param request: The http request object used to determine the users name.
       :param infilename: Filename as given by DJANGO based on provided URL.
       :param accesstype: Define what type of operation the user needs to perform on the data.
                          See g_access_types.
       :param alternate_username: This parameter is used to check if a user different then the one \
                           specified in the request object is allowed to access the given file, \
                           assuming that user is logged in.

       :returns:

            * String with the path of the file
            * HttpResponseForbidden if access is not allowed.
            * HttpResponseRedirect if login is  needed.
            * HttpResonseNotFound if the file was not found.
    """

    global g_request_types
    global g_access_types

    request_type = g_request_types['unknown']
    username = request.user.username
    authenticated = request.user.is_authenticated()
    if alternate_username:
        username = alternate_username
        authenticated = True
    realfilename = infilename

    #Check if the file is indicated to be in a public data location
    #Check if we have a private data request
    if realfilename.startswith(g_request_types['private']):
        request_type = g_request_types['private']
        realfilename = realfilename.lstrip(g_request_types['private'])
    elif realfilename.startswith(g_request_types['public']):
        request_type = g_request_types['public']
        realfilename = realfilename.lstrip(g_request_types['public'])
    else:
        request_type = g_request_types['public']  # By default only look in public places
        # If a full path is given then try to determine whether we have private request instead
        if os.path.isabs(realfilename):
            for p in settings.PRIVATE_DATAPATHS:
                if realfilename.startswith(p):
                    request_type = g_request_types['private']
                    break
        elif authenticated and realfilename.startswith(username):
            request_type = g_request_types['private']
            realfilename = realfilename.lstrip(username).lstrip(":").lstrip("/")

    #Create a list of files to be checked. We convert all paths to abosulte paths to ensure that we don't
    #have any hackers trying to access other files by adding ../ in the path

    #Check whether the user has given us an absolute path that they are allowed to accessed
    fname = os.path.abspath(realfilename)
    if os.path.exists(fname):
        #Check whether the user is authorized to access the file
        directorypath, filename = os.path.split(fname)
        if __authorize_directory_access__(request, directorypath, request_type, accesstype):
            return fname
        else:
            logger.warn("Access to file not granted.")
            return HttpResponseForbidden("Access to file not granted.")

    #If we do not have an aboslute path given, then we need to check the different possible locations for the file
    if not os.path.isabs(realfilename):

        #Check all public locations if we have a public request
        if request_type == g_request_types['public']:  # Create list of public files
            for p in settings.ALLOWED_DATAPATHS:
                fname = os.path.abspath(os.path.join(p, realfilename))  # Construct the absolute file path
                if os.path.exists(fname):  # Retrun the public file path if it exists
                    # We call __authorize_directory_access__ as an extra precaution
                    # just in case the logic for authorizing public access changes in the future
                    directorypath, filename = os.path.split(fname)
                    if __authorize_directory_access__(request, directorypath, request_type, accesstype):
                        return fname
                    else:
                        logger.warn("Access to file not granted.")
                        return HttpResponseForbidden("Access to file not granted.")

        #If we have a private request and the user is not authenticated, then require the user to login
        if request_type == g_request_types['private']:
            #Redirect the user to login page
            if not request.user.is_authenticated():
                return redirect_to_login(request=request)
            #If the user is still not authenticated then return an error
            if not request.user.is_authenticated():
                return HttpResponseNotFound("File access not permitted.")

            # If we have a private data request and the user si authenticated,
            # then check all possible private file locations
            if request.user.is_authenticated():
                for p in settings.PRIVATE_DATAPATHS:
                    fname = os.path.abspath(os.path.join(os.path.join(p, username), realfilename))
                    if os.path.exists(fname):  # Retrun the file name if it exists at the private data location
                        # We call __authorize_directory_access__ as an extra precaution just in case
                        # the logic for private data accesses should change in the future
                        directorypath, filename = os.path.split(fname)
                        if __authorize_directory_access__(request, directorypath, request_type, accesstype):
                            return fname
                        else:
                            logger.warn("Access to file not granted.")
                            return HttpResponseForbidden("Access to file not granted.")

    # We did not find a matching file. Return error.
    logger.warn("Requested file not found.")
    return HttpResponseNotFound("Requested file not found.")


def __authorize_directory_access__(request,
                                   directory_path,
                                   request_type,
                                   accesstype):
    """Helper function for non-registered file access, ie., __authorize_fileaccess_nonregistered_file__,
       used to provide access to a particular directory path.

       :param request: The http request object used to determine the users name.
       :param directory_path: The directory that should be accessed.
       :param request_type: The type of request as specified by g_request_types
       :param accesstype: Define what type of operation the user needs to perform on the data.
                          See g_access_types.

    """
    global g_request_types
    global g_access_types

    username = request.user.username
    authenticated = request.user.is_authenticated()

    #Check whether we have a private access
    #In case of a private access we allow all accesses types to proceed
    if request_type == g_request_types['private']:
        #Require the user to log in
        if not authenticated:  # If we have a private request and the user is not authenticated
            return redirect_to_login(request=request)
        authenticated = request.user.is_authenticated()
        if authenticated:  # If the user is still not authenticated then return an error
            # Check whether the file is loated in one of the users private data locations
            for p in settings.PRIVATE_DATAPATHS:
                if directory_path.startswith(os.path.join(p, username)):
                    return True
        else:
            return False
    # In case of pulic access we only allow view access to avoid anyone from messing things up for others
    elif request_type == g_request_types['public']:
        # Check the access type
        if accesstype != g_access_types['view']:
            return False
        # Check if the file is located in one of the public locations
        if directory_path in settings.ALLOWED_DATAPATHS:
            return True
        # Check whether the file is in a subfolder of an allowed public location
        if not settings.ALLOWED_DATAPATHS_EXACT:
            for p in settings.ALLOWED_DATAPATHS:
                if directory_path.startswith(p):
                    return True

    return False


def redirect_to_login(request):
    """Simple helper function to create the redirect to the login page with forwarding
    to the currently requested URL.

       :param request: The current http request object.

       :returns: HttpResponseRedirect object with the redirect to the login page and the
                 next parameter set to the current full path.

    """
    return HttpResponseRedirect(settings.LOGIN_URL+"?next="+request.get_full_path())
