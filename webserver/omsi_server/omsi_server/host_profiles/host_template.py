"""This template lists some of the more commen host-specifc parameters. One may
   change any of the paramters specified for the DJANGO server here. In order 
   to use a different host profile, simply generate a local_settings.py file
   that looks as follows:
   
   -----'local_settings.py'----------------------------------------------------
   | from host_profiles.<your-profile> import *                               |
   ----------------------------------------------------------------------------

   and place it in the same folder as the settings.py file. 
"""

"""Specify a list of datapaths that a client is allowed to request data from. 
   This is used, e.g., in omsi_access.views.get_real_filename 
   to check whether the requested file is in fact located at one of the
   specified allowed locations. If the list is empty then all folders are
   assumed to be allowed for data access."""
ALLOWED_DATAPATHS = []
"""Specify whether only those folders listed in ALLOWED_DATAPATHS are allowed to be accessed (True) or also any subfolders thereof (False)."""
ALLOWED_DATAPATHS_EXACT = True
"""Specify which domain the OpenMSI viewer should use to request data from."""
API_ROOT = ""
"""Folder with private data locations. These should be different from and not be subfolders of ALLOWED_DATAPTHS as the ALLOWED_DATAPATHS_EXACT if set to FALSE would provide access to the data right now."""
PRIVATE_DATAPATHS = []
"""Managed data folder with managed user data files in original (unconverted) file format"""
SYSTEM_USER_RAWDATAPATHS = []
"""Folder for storing temporary data files. Set this variable to ensure all temporary data is generated at the given location. This is useful to ensure that all temporary data can be easily cleaned up. The server implementation tries to clean up files as much as possible but, e.g., in case of crashes etc. that may not always be possible. If set to None then temporary files will be created using Pythons default behavior"""
TEMPORARY_DATAPATH = None
"""Managed data folder where new HDF5 files should be placed for users. The default value is set for openmsi.nersc.gov"""
SYSTEM_USER_PRIVATEDATAPATHS = ['/project/projectdirs/openmsi/omsi_data_private']
"""Folder where status files from processing jobs should be placed. The default parameter is set for openmsi.nersc.gov."""
PROCESSING_STATUS_FOLDER = "/project/projectdirs/openmsi/omsi_processing_status"
