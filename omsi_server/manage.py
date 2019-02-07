# coding: utf-8
"""The ``manage`` module is automatically created by DJANGO in each project.
   The ``manage`` module is a thin wrapper around ``django-admin.py`` and takes
   care of two things for you before delegating to ``django-admin.py``:

    * It puts your project's package on sys.path.
    * It sets the ``DJANGO_SETTINGS_MODULE`` environment variable so that it points to the project’s settings.py file.

   See also the `django-admin <https://docs.djangoproject.com/en/dev/ref/django-admin/>`_ 
   documentation for further details.

"""


#!/usr/bin/env python
import os
import sys
try:
    import Image
except ImportError:
    from PIL import Image
if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "omsi_server.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
