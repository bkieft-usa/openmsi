Tabel of Contents:
------------------
- Installation
- Required libraries
- Running the DJANGO omsi_server
- How are URL's contructed
- Example URL's for requesting different types of data
    -- Specifying function parameters in the query string
    -- Specifying function parameters in the URL
- Data Security
- ToDo


Installation:
-------------
- The server is written purly in python

Required libraries:
-------------------
- DJANGO: see https://www.djangoproject.com/download/
- OMSI: 
    -- svn checkout --username name https://codeforge.lbl.gov/svn/openmsi
    -- The required OMSI libraries are located at openmsi/trunk/omsi
    -- OMSI requires h5py 2.x: http://alfven.org/wp/hdf5-for-python/
       and the HDF5 >1.8x: http://www.hdfgroup.org/HDF5/release/obtain5.html

Running the DJANGO omsi_server:
------------------------------
Using the simple DJANGO webserver the omsi_server can be run locally simply
using the following command:

    python manage.py runserver

This starts DJANGO webserver on port 8000. To use a different port simply 
include it as input parameter, e.g. : 

    python manage.py runserver 8100


Data Security:
--------------
- Authorization for files that are in the database is handled via the
  omsi_resources app.
- In order to ensure that not just anyone can directly access data at any path
  I have added a fieled ALLOWED_DATA_PATHS to the omsi_server/settings.py 
  DJANOG settings file. Upon request the omsi_access.views.get_real_filename 
  function checks whether the requested file is in fact located at one of the
  specified locations. The parameter ALLOWED_DATAPATHS_EXACT then specifies
  whether only those folders listed are allowed to be accessed or also any
  direct subfolders (without ../) are allowed to be accessed. Note if
  ALLOWED_DATA_PATHS is empty, then any folder is allowed to be accessed.

