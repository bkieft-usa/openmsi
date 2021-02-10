from django.contrib import admin

# Register your models here.
try:
    from omsi_processing.models import ProcessingTaskModel
except ImportError:
    from omsi_server.omsi_processing.models import ProcessingTaskModel

admin.site.register(ProcessingTaskModel)