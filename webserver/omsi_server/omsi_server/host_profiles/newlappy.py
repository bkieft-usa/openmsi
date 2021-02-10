"""This template lists some of the more commen host-specifc parameters. One may
   change any of the paramters specified for the DJANGO server here. In order
   to use a different host profile, simply generate a local_settings.py file
   that looks as follows:

   -----'local_settings.py'----------------------------------------------------
   | from host_profiles.<your-profile> import *                               |
   ----------------------------------------------------------------------------

   and place it in the same folder as the settings.py file.
"""
import sys
sys.path.append("/Users/oruebel/Devel/openmsi")
sys.path.append("/Users/oruebel/Devel/BASTet-git/bastet")

"""Specify a list of datapaths that a client is allowed to request data from.
   This is used, e.g., in omsi_access.views.get_real_filename
   to check whether the requested file is in fact located at one of the
   specified allowed locations. If the list is empty then all folders are
   assumed to be allowed for data access."""
ALLOWED_DATAPATHS = ['/Users/oruebel/Devel/openmsi-data/msidata']
"""Specify whether only those folders listed in ALLOWED_DATAPATHS are allowed to be accessed (True) or also any subfolders thereof (False)."""
ALLOWED_DATAPATHS_EXACT = True
"""Specify which domain the OpenMSI viewer should use to request data from."""
API_ROOT = "http://127.0.0.1:8000/"
"""Folder with private data locations. These should be different from and not be subfolders of ALLOWED_DATAPTHS as the ALLOWED_DATAPATHS_EXACT if set to FALSE would provide access to the data right now."""
PRIVATE_DATAPATHS = ['/Users/oruebel/Devel/openmsi-data/private_msidata']
"""Managed data folder with managed user data files in original (unconverted) file format"""
SYSTEM_USER_RAWDATAPATHS = ['/Users/oruebel/Devel/openmsi-data/rawdata']

TEMPORARY_DATAPATH = '/Users/oruebel/Devel/openmsi-data/temp_msidata'





CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': '/Users/oruebel/Devel/openmsi-data/cache',
    }
}
