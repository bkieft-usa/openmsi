#Add required python packages to the path
import sys
sys.path.append("/d/visguests/oruebel/devel/openmsi/openmsi-tk/trunk")
sys.path.append("/d/visguests/oruebel/devel/openmsi/openmsi/trunk")
"""Specify a list of datapaths that a client is allowed to request data from. 
This is used, e.g., in omsi_access.views.get_real_filename 
to check whether the requested file is in fact located at one of the
specified allowed locations. If the list is empty then all folders are
assumed to be allowed for data access."""
ALLOWED_DATAPATHS = ['/work2/bowen']
"""Specify whether only those folders listed in ALLOWED_DATAPATHS are allowed to be accessed (True) or also any subfolders thereof (False)."""
ALLOWED_DATAPATHS_EXACT = True
"""Specify which domain the OpenMSI viewer should use to request data from."""
API_ROOT = "http://127.0.0.1:8000/"
"""Folder with private data locations. These should be different from and not be subfolders of ALLOWED_DATAPTHS as the ALLOWED_DATAPATHS_EXACT if set to FALSE would provide access to the data right now."""
PRIVATE_DATAPATHS = []
