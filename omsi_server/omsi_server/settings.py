import os
try:
    import Image
except ImportError:
    from PIL import Image
import sys
# Django settings for omsi_server project.

"""
Specify a list of unmanaged datapaths that a client is allowed to request data from.
This is used, e.g., in omsi_access.views.get_real_filename
to check whether the requested file is in fact located at one of the
specified allowed locations. If the list is empty then all folders are
assumed to be allowed for data access.
"""
ALLOWED_DATAPATHS = []

"""
Specify whether only those unmanaged folders listed in ALLOWED_DATAPATHS are allowed to be accessed (True)
or also any subfolders thereof (False).
"""
ALLOWED_DATAPATHS_EXACT = True

"""
Unmanaged folder with private data locations. These should be different from and not be subfolders of ALLOWED_DATAPTHS
as the ALLOWED_DATAPATHS_EXACT if set to FALSE would provide access to the data right now.
"""
PRIVATE_DATAPATHS = []

"""Managed data folder with managed user data files converted to a system-compliant file format"""
#SYSTEM_USER_DATAPATHS = []

"""Managed data folder with managed user data files in original (unconverted) file format"""
SYSTEM_USER_RAWDATAPATHS = []

"""
Managed data folder where new HDF5 files should be placed for users.
The default value is set for openmsi.nersc.gov.
"""
SYSTEM_USER_PRIVATEDATAPATHS = ['/project/projectdirs/openmsi/omsi_data_private']

"""
Folder for storing temporary data files. Set this variable to ensure all temporary data is generated at the
given location. This is useful to ensure that all temporary data can be easily cleaned up. The server implementation
tries to clean up files as much as possible but, e.g., in case of crashes etc. that may not always be possible.
If set to None then temporary files will be created using Pythons default behavior
"""
TEMPORARY_DATAPATH = None

"""
Folder where status files from processing jobs should be placed. The default parameter is set for openmsi.nersc.gov.
"""
PROCESSING_STATUS_FOLDER = "/project/projectdirs/openmsi/omsi_processing_status"

"""
Location of the installation of BASTet (ie., the OpenMSI toolkit) that should be used for file conversion.
and processing. NOTE: This may not be the same installation of BASTet as used with the webserver.
"""
BASTET_PROCESSING_PATH = "/project/projectdirs/openmsi/omsi_processing_status/bastet"

"""Specify which domain the OpenMSI viewer should use to request data from."""
API_ROOT = ""

"""Specify the location of the project"""
PROJECT_DIR = os.path.dirname(__file__)
sys.path.append(os.path.abspath(os.path.join('../../', PROJECT_DIR)))


DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('oruebel', 'oruebel@lbl.gov'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',  # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': PROJECT_DIR + '/openmsi.sqlite',  # Or path to database file if using sqlite3.
        'USER': '',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    },
}

LOGIN_URL = "/client/login"

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/Los_Angeles'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = ''

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/site_media/openmsi/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = '/var/www/html' + STATIC_URL

# Additional locations of static files
STATICFILES_DIRS = (
    os.path.join(PROJECT_DIR, "static"),
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    #    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'by^!i3o4$#g6in8v9%m!(jmo=0zl!m1_d#ljq0-qmvv-c*3a-c'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
    #     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    #'django.contrib.auth.middleware.RemoteUserMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

AUTHENTICATION_BACKENDS = (
    #'django.contrib.auth.backends.ModelBackend',
    #'django.contrib.auth.backends.RemoteUserBackend',
    'omsi_server.newt_auth_backend.NEWT',
)

# Expire session cookies in 12 hours to match the expiration time of NEWT login
SESSION_COOKIE_AGE = 43200

ROOT_URLCONF = 'omsi_server.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'omsi_server.wsgi.application'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(PROJECT_DIR, "templates/"),
    # os.path.join( PROJECT_DIR , "../omsi_client/templates/"),
    # os.path.join( PROJECT_DIR , "../omsi_resources/templates/")
    os.path.join(PROJECT_DIR, "../"),
)

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    "django.core.context_processors.tz",
    "django.contrib.messages.context_processors.messages",
    'django.core.context_processors.request'
)

INSTALLED_APPS = (
    'django.contrib.admindocs',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Uncomment the next line to enable the admin:
    'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    'django.contrib.admindocs',
    'omsi_access',
    'omsi_client',
    'omsi_resources',
    'omsi_processing'
)

# A method logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'django.utils.log.NullHandler',
        },
        'console': {
            'level': 'ERROR',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',  # set the logging class to log to a file
            'formatter': 'verbose',          # define the formatter to associate
            'filename': os.path.join(PROJECT_DIR, 'django.log')  # log file
        },
    },
    'loggers': {
        'django': {
            'handlers': ['null'],
            'propagate': True,
            'level': 'INFO',
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': True,
        },
        'omsi_client': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'omsi_access': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'omsi_processing': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
    'formatters': {
        'verbose': {
            'format': '[%(levelname)s] %(asctime)s %(name)s:%(funcName)s:%(lineno)d %(message)s'
        },
        'simple': {
            'format': '[%(levelname)s] %(message)s'
        },
    },

}

try:
    from local_settings import *
except ImportError:
    pass

