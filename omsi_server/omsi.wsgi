import os
import site
import sys

rootpath=os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
omsipath=rootpath+"/omsi_server"

# This will make Django run in a virtual env
# Remember original sys.path.
prev_sys_path = list(sys.path) 

# Add each new site-packages directory.
if sys.version_info >= (2, 6) and sys.version_info < (2, 7) and os.path.exists('/project/projectdirs/openmsi/omsi_django/lib/python2.6/site-packages/'):
    site.addsitedir('/project/projectdirs/openmsi/omsi_django/lib/python2.6/site-packages/')

# Reorder sys.path so new directories at the front.
new_sys_path = [] 
for item in list(sys.path): 
    if item not in prev_sys_path: 
        new_sys_path.append(item) 
        sys.path.remove(item) 
sys.path[:0] = new_sys_path



for i in [rootpath, omsipath]:
    sys.path.append(i)

print os.environ 


# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "omsi_server.settings")
os.environ['DJANGO_SETTINGS_MODULE'] = "omsi_server.settings"

# This application object is used by any WSGI server configured to use this
# file. This includes Django's development server, if the WSGI_APPLICATION
# setting points here.
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

