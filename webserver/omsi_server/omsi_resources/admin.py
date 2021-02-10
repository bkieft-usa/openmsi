from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
try:
    from omsi_resources.models import SiteUser, \
                                      MsiDatasetModel, \
                                      ExperimentModel, \
                                      FileModelOmsi, \
                                      MethodsModel, \
                                      InstrumentModel, \
                                      FileModelRaw, \
                                      AlternateLocationModel, \
                                      FormatReaderModel
except ImportError:
    from omsi_server.omsi_resources.models import SiteUser, \
                                                  MsiDatasetModel, \
                                                  ExperimentModel, \
                                                  FileModelOmsi, \
                                                  MethodsModel, \
                                                  InstrumentModel, \
                                                  FileModelRaw, \
                                                  AlternateLocationModel, \
                                                  FormatReaderModel


#Register the msi datasets
#class experiment_inline(admin.StackedInline) :
    #model = MsiDatasetModel
    #can_delete = False

#class MsiDatasetModel(MsiDatasetModel) :
    #inlines = [experiment_inline, ]
class OmsiFileModelAdmin(admin.ModelAdmin):
    fieldsets = [(None, {'fields': ['path', ]}),
                 ('Permissions', {'fields': ['is_public',
                                             'view_users',
                                             'view_groups',
                                             'edit_users',
                                             'edit_groups',
                                             'owner_users',
                                             'owner_groups']})]
    date_hierarchy = 'created_date' 
    search_fields = ['created_date',
                     'path',
                     'view_users__last_name',
                     'view_groups__name',
                     'edit_users__last_name',
                     'edit_groups__name',
                     'owner_users__last_name',
                     'owner_groups__name',
                     'methods_model__name',
                     'instrument_model__name']
    
admin.site.register(FileModelOmsi, OmsiFileModelAdmin)
admin.site.register(ExperimentModel)
admin.site.register(MsiDatasetModel)
admin.site.register(MethodsModel)
admin.site.register(InstrumentModel)
admin.site.register(FileModelRaw)
admin.site.register(AlternateLocationModel)
admin.site.register(FormatReaderModel)
    

#Define inline admin descriptor for the SiteUser models
class SiteUserInline(admin.StackedInline):
    model = SiteUser
    can_delete = False


# Add the user to the django admin page 
class UserAdmin(UserAdmin):
    inlines = (SiteUserInline, )
 
# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
