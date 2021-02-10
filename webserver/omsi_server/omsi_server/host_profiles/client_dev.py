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
API_ROOT = "https://openmsi.nersc.gov/openmsi/"
