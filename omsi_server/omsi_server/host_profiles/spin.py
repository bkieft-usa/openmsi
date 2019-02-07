"""Custom host profile for openmsi.nersc.gov specifying custom DJANGO settings.
   NOTE:
   * openmsi uses a database cache. Call "python manage.py createcachetable" when
     deploying this site.
"""
import sys
import os

sys.path.append("/BASTet")
#sys.path.append("/data/openmsi/omsi_sources")

"""Specify a list of datapaths that a client is allowed to request data from.
   This is used, e.g., in omsi_access.views.get_real_filename
   to check whether the requested file is in fact located at one of the
   specified allowed locations. If the list is empty then all folders are
   assumed to be allowed for data access."""
ALLOWED_DATAPATHS = ['/data/openmsi/omsi_data']

"""Specify whether only those folders listed in ALLOWED_DATAPATHS are allowed to be accessed (True) or also any subfolders thereof (False)."""
ALLOWED_DATAPATHS_EXACT = True

"""Unmanaged folder with private data locations. These should be different from and not be subfolders of ALLOWED_DATAPTHS as the ALLOWED_DATAPATHS_EXACT if set to FALSE would provide access to the data right now."""
#PRIVATE_DATAPATHS = ['/project/projectdirs/openmsi/omsi_data_private']
PRIVATE_DATAPATHS = []

"""Managed data folder where new HDF5 files should be placed for users."""
""" Mounted from /project/projectdirs/openmsi/omsi_data_private' """
SYSTEM_USER_PRIVATEDATAPATHS = ['/data/openmsi/omsi_data_private']

"""Managed data folder with managed user data files in original (unconverted) file format"""
SYSTEM_USER_RAWDATAPATHS = ['/data/openmsi/original_data']

"""Specify which domain the OpenMSI viewer should use to request data from."""
API_ROOT = os.environ.get("API_ROOT", "https://openmsi.nersc.gov/openmsi/")

"""Disable debug mode for openmsi to ensure hackers only get normal error messages instead of detailed debug information"""
DEBUG = True

"""Restrict the domains that are allowed to access the site. This is also needed when DEBUG is False"""
ALLOWED_HOSTS = [".openmsi.nersc.gov", ".openmsi-dev.nersc.gov"]

"""Folder for storing temporary data files. Set this variable to ensure all temporary data is generated at the given location. This is useful to ensure that all temporary data can be easily cleaned up. The server implementation tries to clean up files as much as possible but, e.g., in case of crashes etc. that may not always be possible. If set to None then temporary files will be created using Pythons default behavior"""
TEMPORARY_DATAPATH = "/data/openmsi/omsi_temp"

"""
Location of the installation of BASTet (ie., the OpenMSI toolkit) that should be used for file conversion.
and processing. NOTE: This may not be the same installation of BASTet as used with the webserver.
"""
BASTET_PROCESSING_PATH = "/project/projectdirs/openmsi/omsi_processing_status/bastet"


"""
Folder where status files from processing jobs should be placed.
"""
PROCESSING_STATUS_FOLDER = "/project/projectdirs/openmsi/omsi_processing_status"


#CACHES = {
#    'default': {
#        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
#        'LOCATION': '/data/openmsi/omsi_cache',
#    }
#}

LOGIN_URL = "/openmsi/client/login"

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'openmsi_cache_table',
         #'TIMEOUT': 2592100,
        'TIMEOUT': None,
        'OPTIONS': {
            'MAX_ENTRIES': 50000
        }
    }
}


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',  # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': '/data/db/openmsi.sqlite',  # Or path to database file if using sqlite3.
        'USER': '',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    },
}
