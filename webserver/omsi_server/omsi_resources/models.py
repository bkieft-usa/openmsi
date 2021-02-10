"""ToDo

    * experiment_model.description currently not available in the HDF5 file model
    * analysis dependencies currently not yet reflected in the database model but should be
    * analysis parameters not yet reflected in the database model
    * The file authorization does not use the database yet

    Note:
    * The methods and instrument model both have a \
      models.ForeignKey('omsi_file_model', verbose_name='File', editable=False) \
      This implies that each method is associated with a particular file \
      (but possibly with multiple experiments and datasets withing the same file). \
      Sharing a method/instrument across files means that we have to copy the \
      method and instrument in the database and file (this means they are from \
      the point of copy no longer synchronized when making changes).


   ToDo

   * Implement basic HPSS and file-system storage backends
   * Implement functionality to move files between the two file systems
   * Implement checks to restore a file to its original location if it was backed up. We should have a single \
     function to implement a "get_path_for_fileread." The function would then restore a file if it no longer\
     exists before returning the paths.
   * We also need to handle the case when a user wants to change the db entry for a file but the file is \
     already moved to backup storage.

"""

from django.db import models
from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin
from django.core.exceptions import ValidationError
from custom_fields import CountryField
import custom_validators
import os
import copy
import datetime
from omsi.dataformat import *
from omsi.dataformat import file_reader_base
from omsi.dataformat.omsi_file.instrument import omsi_file_instrument
from omsi.dataformat.omsi_file.main_file import omsi_file
from omsi.dataformat.omsi_file.methods import omsi_file_methods
from django.forms import ModelForm
from django import forms
from django.forms.models import modelform_factory


# class omsi_resources_basemodel(models.Model):
#    class Meta:
#        app_label = 'OpenMSI Resources'
#        abstract = True


#######################################################
#      Extend the default user model in django        #
#######################################################
class SiteUser(models.Model):
    """Model used to extend the default user model with additional data fields"""
    user = models.OneToOneField(User)


class FileModelBase(models.Model):
    """
    Base model for managing files. This is used as common base model
    for all specialiced file models (e.g., for raw and omsi data file
    models.

    Model Attributes:
    ----------------
    :cvar path: Unique path were the raw data file is stored. Note, if the file has been
                moved to alternate storage, then the file may no longer exist as the path,
                however, it is still seen as the primary path were the file should be
                located when accessed.
    :cvar alternate_paths: Alternate storage locations for the file (e.g., backup storage on HPSS)
    :cvar system_message: Optional text field with additional information and system messages
                         (e.g, file status messages, error message, update messages etc.)
    :cvar created_date: Date at which the file was created
    :cvar last_update_date: Last time the file model has been modified (this may not be the same as
                        the modification of the file itself. E.g., the model may also change for
                        usages of the file that may not necessarily effect the file itself. The
                        last modified timestamp for a file may be obtained from the file system
                        itself.

    """
    path = models.CharField(max_length=4000,
                            unique=True)
    alternate_paths = models.ManyToManyField('AlternateLocationModel',
                                             related_name='%(app_label)s_%(class)s_isalternate',
                                             verbose_name='Alternate locations were the file is stored.',
                                             null=True,
                                             blank=True)
    system_messages = models.TextField(verbose_name="System messages about the file's status",
                                       editable=True,
                                       null=True,
                                       blank=True)
    created_date = models.DateTimeField(auto_now_add=True,
                                        editable=True)
    last_update_date = models.DateTimeField(auto_now=True,
                                            editable=True)

    def save(self, *args, **kwargs):
        """Overwrite the save method so that we can autocorrect entries and generate
           any related data models when we save the model"""
        self.path = self.path.rstrip(" ")  # Autocorrect the path name by removing trailing spaced
        super(FileModelBase, self).save(*args, **kwargs)  # Save the model so that we can reference it

    def __unicode__(self):
        """Define the display name for the model object"""
        name = os.path.basename(self.path)
        if len(name) > 0:
            basedir = os.path.basename(os.path.dirname(self.path))
            return unicode(os.path.join(basedir, name))
        else:
            return unicode(self.path)

    class Meta:
        """
        This is a base class only so make it abstract, i.e, this will not
        be instantiated as a separate model in the database but only
        the child models.
        """
        abstract = True


#######################################################
#      Models for storing original data file          #
#######################################################
class FileModelRaw(FileModelBase):
    """
    Model for storing raw user data related metadata

    Inherited Model Attributes:
    ---------------------------

    :cvar path: Unique path were the raw data file is stored. Note, if the file has been
                moved to alternate storage, then the file may no longer exist as the path,
                however, it is still seen as the primary path were the file should be
                located when accessed.
    :cvar alternate_paths: Alternate storage locations for the file (e.g., backup storage on HPSS)
    :cvar system_message: Optional text field with additional information and system messages
                         (e.g, file status messages, error message, update messages etc.)
    :cvar created_date: Date at which the file was created
    :cvar last_update_date: Last time the file model has been modified (this may not be the same as
                        the modification of the file itself. E.g., the model may also change for
                        usages of the file that may not necessarily effect the file itself. The
                        last modified timestamp for a file may be obtained from the file system
                        itself.

    Model Attributes:
    -----------------

    :cvar related_omsi_files: omsi_files that have been created from this raw data file (possibly many)
    :cvar owner_users: User who are allowed to manage this raw data file.
    :cvar status: The status of the file
    :cvar format_reader: Optional ForeignKey to the file format reader used to open the file.

    Other Attributes that do not map to a database column:
    ------------------------------------------------------

    :cvar STATUS_CHOICES: List of possible values for the status of the file
    :cvar ERROR:  Error status value 'er'
    :cvar UPLOAD_IN_PROGRESS: Upload in progress status value 'up'
    :cvar UPLOAD_COMPLETE: Upload complete status value 'uc'
    :cvar CONVERSION_IN_PROGRESS: Conversion in progress status value 'cp'
    :cvar CONVERSION_COMPLETE: Conversion complete status value 'cc

    """
    # path = models.CharField(max_length=4000,
    #                        validators=[custom_validators.validate_dirpath],
    #                        unique=True)
    # alternate_paths = models.ManyToManyField('AlternateLocationModel',
    #                                         related_name='alternate_rawpaths',
    #                                         verbose_name='Alternate locations were the file is stored.',
    #                                         null=True,
    #                                         blank=True)
    related_omsi_files = models.ManyToManyField('FileModelOmsi',
                                                related_name='related_omsi_files',
                                                verbose_name='OMSI files related to this raw file',
                                                null=True,
                                                blank=True)
    owner_users = models.ManyToManyField(User,
                                         blank=False,
                                         related_name="owner_users_rawfile",
                                         verbose_name="Users that can manage")
    ERROR = 'er'
    UPLOAD_IN_PROGRESS = 'up'
    UPLOAD_COMPLETE = 'uc'
    CONVERSION_IN_PROGRESS = 'cp'
    CONVERSION_COMPLETE = 'cc'
    STATUS_CHOICES = (
        (ERROR, 'Error'),
        (UPLOAD_IN_PROGRESS, 'Upload in progress'),
        (UPLOAD_COMPLETE, 'Upload complete'),
        (CONVERSION_IN_PROGRESS, 'Conversion in progress'),
        (CONVERSION_COMPLETE, 'Conversion complete')
    )
    status = models.CharField(max_length=40,
                              choices=STATUS_CHOICES,
                              default=UPLOAD_COMPLETE)
    format_reader = models.ForeignKey('FormatReaderModel',
                                      verbose_name='File format reader',
                                      editable=True,
                                      null=True,
                                      blank=True)

    class Meta:
        """Define custom display metadata fro the admin page"""
        verbose_name = "Raw Data File"
        verbose_name_plural = "Raw Data Files"

    def clean(self):
        """When we save the model we need to be sure that we actually have a valid
           model. In this case, upon creation we need to check whether the directory
           actually exists."""
        # 1) Check that the directory path exists when we first create the model
        if not self.pk:  # Check whether the object is being saved for the first time
            # 1) Check that we have a valid directory path. Correct for added spaces as they
            #    will be removed automatically upon save
            custom_validators.validate_dirpath(self.path.rstrip(" "))
            # 2) Determine the file format if not set
            # if not self.format_reader:
            #     availableformats = file_reader_base.file_reader_base.available_formats()
            #     print availableformats
            #     for formatname, formatclass in availableformats.items():
            #         print formatname
            #         if formatclass.is_valid_dataset(self.path):
            #             # Find the database model for the format
            #             formatmodel = FormatReaderModel.objects.filter(format__exact=formatname)
            #             # Create a database model for the reader if it does not exists
            #             if len(formatmodel) == 0:
            #                 formatmodel = FormatReaderModel(format=formatname)
            #                 formatmodel.save()
            #             # Extract the file reader model if found
            #             else:
            #                 formatmodel = formatmodel[0]
            #             # Assign the format model
            #             self.format_reader = formatmodel
            #             break
            # if not self.format_reader:
            #     raise ValidationError("File format unknown for: "+self.path)

    def save(self, *args, **kwargs):
        """Overwrite the save method so that we can autocorrect entries and generate
           any related data models when we save the model"""
        update_format = not self.pk  # Check whether the object is being saved for the first time
        super(FileModelRaw, self).save(*args, **kwargs)  # Save the model so that we can reference it
        # This is the first time the object is being saved. Create all related data models.
        # if update_format:
        if not self.format_reader:
            try:
                self.__update_file_format__()
            except:
                pass

    def __update_file_format__(self):
        # 2) Determine the file format if not set
        availableformats = file_reader_base.file_reader_base.available_formats()
        for formatname, formatclass in availableformats.items():
            # print (formatname, formatclass.is_valid_dataset(self.path), self.path)
            if formatclass.is_valid_dataset(self.path):
                # Find the database model for the format
                formatmodel = FormatReaderModel.objects.filter(format__exact=formatname)
                # Create a database model for the reader if it does not exists
                if len(formatmodel) == 0:
                    formatmodel = FormatReaderModel(format=formatname)
                    formatmodel.save()
                # Extract the file reader model if found
                else:
                    formatmodel = formatmodel[0]
                # Assign the format model
                self.format_reader = formatmodel
                self.save()
                break


class FormatReaderModel(models.Model):
    """
    Model used to specify file formats.

    :cvar format: Name of the format. This corresponds to the name as specified in
                  omsi.dataformat.file_reader_base.available_formats().keys()
    """
    format = models.CharField(max_length=4000,
                              validators=[custom_validators.validate_file_reader_name],
                              unique=True)

    def get_format_reader(self):
        """
        Get the file format reader class associated with this format.

        :returns: File format reader class (which inherits from omsi.dataformat.file_reader_base)
                  that can be used to read the give format.
        """
        return file_reader_base.file_reader_base.available_formats()[self.format]

    class Meta:
        """Define custom display metadata fro the admin page"""
        verbose_name = "File Reader"
        verbose_name_plural = "File Readers"

    def __unicode__(self):
        """Define the display name for the model object"""
        return unicode(self.format)


class AlternateLocationModel(models.Model):
    """
    Model used to specify a complete file path, including the data storage system used.

    :cvar path: Path to the file on the storage system
    :cvar data_store: Data storage system used
    """
    path = models.CharField(max_length=4000,
                            unique=True)
    STORE_HPSS = 'hpss'
    STORE_LOCAL = 'local'
    STORE_CHOICES = (
        (STORE_HPSS, 'hpss'),
        (STORE_LOCAL, 'local')
    )
    data_store = models.CharField(max_length=40,
                                  choices=STORE_CHOICES,
                                  default=STORE_LOCAL)

    class Meta:
        """Define custom display metadata fro the admin page"""
        verbose_name = "Alienate Data Location"
        verbose_name_plural = "Alternate Data Locations"

    def __unicode__(self):
        """Define the display name for the model object"""
        return unicode(self.data_store+":"+self.path)


#######################################################
#      Models for storing file related metadata       #
#######################################################
class FileModelOmsi(FileModelBase):
    """
    Model for storing openmsi file related metadata

     Inherited Model Attributes:
    ---------------------------

    :cvar path: Unique path were the raw data file is stored. Note, if the file has been
                moved to alternate storage, then the file may no longer exist as the path,
                however, it is still seen as the primary path were the file should be
                located when accessed.
    :cvar alternate_paths: Alternate storage locations for the file (e.g., backup storage on HPSS)
    :cvar system_message: Optional text field with additional information and system messages
                         (e.g, file status messages, error message, update messages etc.)
    :cvar created_date: Date at which the file was created
    :cvar last_update_date: Last time the file model has been modified (this may not be the same as
                        the modification of the file itself. E.g., the model may also change for
                        usages of the file that may not necessarily effect the file itself. The
                        last modified timestamp for a file may be obtained from the file system
                        itself. For FileModelOmsi this timestamp is updated also if directly
                        related models, e.g., MsiDatasetModel, AnalysisModel, MethodsModel etc.,
                        which describe changes that effect the file itself as well.

    Model Attributes:
    -----------------

    :cvar is_public: Boolean key indicating whether the file is shared with the public
    :cvar view_users: List of users that are explicitly allowed to view the file
    :cvar view_groups: List of groups that are explicitly allowed to view the file
    :cvar edit_users: List of users that are explicitly allowed to view and edit the file
    :cvar edit_groups: List of groups that are explicitly allowed to view and edit the file
    :cvar owner_users: List of users that are explicitly allowed to view, edit and perform
                       owner-specific tasks to the file (e.g., change permissions)
    :cvar owner_groups: List of groups that are explicitly allowed to view, edit and
                        perform owner-specific tasks to the file (e.g., change permissions)

    """
    # path = models.CharField(max_length=4000,
    #                        validators=[custom_validators.valdidate_omsifile],
    #                        unique=True)
    # alternate_paths = models.ManyToManyField('AlternateLocationModel',
    #                                         related_name='alternate_omsipaths',
    #                                         verbose_name='Alternate locations were the file is stored.',
    #                                         null=True,
    #                                         blank=True)
    is_public = models.BooleanField(default=False,
                                    verbose_name="Make file public")
    view_users = models.ManyToManyField(User,
                                        blank=True,
                                        related_name="view_users",
                                        verbose_name="User that can view")
    view_groups = models.ManyToManyField(Group,
                                         blank=True,
                                         related_name="view_groups",
                                         verbose_name="Groups that can view")
    edit_users = models.ManyToManyField(User,
                                        blank=True,
                                        related_name="edit_users",
                                        verbose_name="User that can edit")
    edit_groups = models.ManyToManyField(Group,
                                         blank=True,
                                         related_name="edit_groups",
                                         verbose_name="Groups that can edit")
    owner_users = models.ManyToManyField(User,
                                         blank=True,
                                         related_name="owner_users",
                                         verbose_name="Users that can manage")
    owner_groups = models.ManyToManyField(Group,
                                          blank=True,
                                          related_name="owner_groups",
                                          verbose_name="Groups that can manage")

    class Meta:
        """Define custom display metadata for the admin page"""
        verbose_name = "OpenMSI Data File"
        verbose_name_plural = "OpenMSI Data Files"
        permissions = (
            ("view_file", "Can view the file"),
            ("update_metadata", "Can update file"),
        )

    def clean(self):
        """When we save the model we need to be sure that we actually have a valid
           model. In this case, upon creation we need to check whether we actually
           have a valid omsi_file associated with the model."""
        # 1) Check that the directory path exists when we first create the model
        if not self.pk:  # Check whether the object is being saved for the first time
            # Check that we have a valid omsi file. Correct for added spaces as they
            # will be removed automatically upon save
            custom_validators.valdidate_omsifile(self.path.rstrip(" "))

    def save(self, *args, **kwargs):
        """Overwrite the save method so that we can autocorrect entries and generate
           any related data models when we save the model"""
        # custom_validators.valdidate_omsifile(self.path)  # Check if the file is valid
        create_submodels = not self.pk  # Check whether the object is being saved for the first time
        super(FileModelOmsi, self).save(*args, **kwargs)  # Save the model so that we can reference it
        # This is the first time the object is being saved. Create all related data models.
        if create_submodels:
            self.__create_related_models_from_file__()

    def __create_related_models_from_file__(self):
        """Helper function used to initalize models related to a file upon first
           creation of the database entry for the file"""

        # Open the file
        f = omsi_file(self.path, 'r')
        # Create the experiments for the file
        for ei in range(0, f.get_num_experiments()):
            # Get the experiment from file
            e = f.get_experiment(ei)

            # Create the method model
            if e.has_method_info():
                methodsinfo = e.get_method_info()
                if methodsinfo.has_method_name():
                    exp_methods = MethodsModel(name=methodsinfo.get_method_name()[0],
                                               file_store=self)
                else:
                    exp_methods = MethodsModel(name='undefined',
                                               file_store=self)
                exp_methods.save()
            else:
                exp_methods = None
            # Create the instrument model
            if e.has_instrument_info():
                instrument = e.get_instrument_info()
                if instrument.has_instrument_name():
                    exp_instrument = InstrumentModel(name=instrument.get_instrument_name()[0],
                                                     file_store=self)
                else:
                    exp_instrument = InstrumentModel(name='undefined',
                                                     file_store=self)
                exp_instrument.save()
            else:
                exp_instrument = None
            # Create the experiment object
            exp = ExperimentModel(experiment_identifier=e.get_experiment_identifier()[0],
                                  experiment_index=ei,
                                  description=" ",
                                  file_store=self,
                                  methods=exp_methods,
                                  instrument=exp_instrument)
            exp.save()

            # Create the msi datasets available for the experiment
            for di in range(0, e.get_num_msidata()):
                # Get the msi dataset from file withou loading the actual dataset and create the corresponding db model
                d = e.get_msidata(di, preload_mz=False, preload_xy_index=False)
                # Create the method model if needed
                dat_methods = copy.deepcopy(exp_methods)
                if d.has_method_info():
                    dmethod_info = d.get_method_info()
                    if dmethod_info.has_method_name():
                        dat_methods = MethodsModel(name=dmethod_info.get_method_name()[0],
                                                   file_store=self)
                    else:
                        dat_methods = MethodsModel(name='undefined',
                                                   file_store=self)
                    dat_methods.save()
                # Create the instrument model if needed
                dat_instrument = copy.deepcopy(exp_instrument)
                if d.has_instrument_info():
                    dinstrument_info = d.get_instrument_info()
                    if dinstrument_info.has_instrument_name():
                        dat_instrument = InstrumentModel(name=dinstrument_info.get_instrument_name()[0],
                                                         file_store=self)
                    else:
                        dat_instrument = InstrumentModel(name='undefined',
                                                         file_store=self)
                    dat_instrument.save()
                datname = unicode(self)+"/"+unicode(exp)+"/"+str(di)
                dataset = MsiDatasetModel(name=datname,
                                          data_index=di,
                                          x_size=d.shape[0],
                                          y_size=d.shape[1],
                                          mz_size=d.shape[2],
                                          methods=dat_methods,
                                          instrument=dat_instrument,
                                          experiment=exp,
                                          file_store=self)
                dataset.save()

            # Create the analysis models for the experiment
            for ai in range(0, e.get_num_analysis()):
                # Get the analysis data object from file without loading any data
                a = e.get_analysis(ai)
                a_type = a.get_analysis_type()[0]
                a_identifier = a.get_analysis_identifier()[0]
                analysis = AnalysisModel(analysis_type=a_type,
                                         analysis_identifier=a_identifier,
                                         analysis_index=ai,
                                         experiment=exp,
                                         file_store=self)
                analysis.save()


class ExperimentModel(models.Model):
    """
    Model for storing experiment related metadata

    :cvar experiment_identifier: String with the experiment identifier define by the user
    :cvar file_store: Foreign key to the file where the experiment is stored
    :cvar experiment_index: Index of the experiment in the file
    :cvar description: Textual description of the experiment
    :cvar method: Foreign key to the method associated with the experiment
    :cvar instrument: Foreign key to the instrument associated with the experiment
    :cvar __original_experiment_identifier: Private variable used to avoid database lookups

    """
    experiment_identifier = models.CharField(max_length=3000,
                                             verbose_name='Experiment Identifier',
                                             editable=True)
    file_store = models.ForeignKey('FileModelOmsi',
                                   verbose_name='File',
                                   editable=False)
    experiment_index = models.IntegerField(verbose_name='Experiment_Index',
                                           editable=False)
    description = models.TextField(verbose_name="Description",
                                   editable=True)
    methods = models.ForeignKey('MethodsModel',
                                verbose_name='Methods',
                                editable=False,
                                blank=True,
                                null=True)
    instrument = models.ForeignKey('InstrumentModel',
                                   verbose_name='Instrument',
                                   editable=False,
                                   blank=True,
                                   null=True)
    __original_experiment_identifier = None

    def __init__(self, *args, **kwargs):
        """Overwrite the init to keep track fo values for validation"""
        super(ExperimentModel, self).__init__(*args, **kwargs)
        self.__original_experiment_identifier = self.experiment_identifier

    class Meta:
        """Define custom display metadata fro the admin page"""
        verbose_name = "Experiment"
        verbose_name_plural = "Experiments"

    def __unicode__(self):
        """Define the display name for the model object"""
        return unicode(self.experiment_identifier)

    def clean(self):
        """When we save the model we need to be sure that we can write any potentially changes back to the file"""

        # Check if the experiment_identifier has changed and needs to be written back to the file
        if self.__original_experiment_identifier != self.experiment_identifier:
            # Try to open the HDF5 file
            custom_validators.validate_omsifile_writeable(self.file_store.path)

    def save(self, *args, **kwargs):
        """Overwrite the save method so that we can update the file"""
        if self.__original_experiment_identifier != self.experiment_identifier:
            f = omsi_file(self.file_store.path, 'a')
            e = f.get_experiment(self.experiment_index)
            e.get_experiment_identifier()[0] = str(self.experiment_identifier)
            f.close_file()
        super(ExperimentModel, self).save(*args, **kwargs)  # Save the model so that we can reference it
        self.file_store.last_update_date = datetime.datetime.now()
        self.file_store.save()


class MsiDatasetModel(models.Model):
    """
    Model for storing msi dataset related metadata

    :cvar name: String with the name of the dataset
    :cvar data_index: Integer index of the dataset
    :cvar x_size: Number of pixels in x (i.e., first array dimension)
    :cvar y_size: Number of pixles in y (i.e., second array dimension)
    :cvar mz_size: Number of bins in the m/z axis
    :cvar method: Foreign key to the method associated with the dataset
    :cvar instrument: Foreign key to instrument associated with the dataset
    :cvar experiment: Foreign key to experiment associated with the dataset
    :cvar file_store: Foreing key to the file associated with the dataset

    """
    name = models.CharField(max_length=1000,
                            editable=True,
                            verbose_name="Dataset Name")
    data_index = models.IntegerField(verbose_name='Dataset Index',
                                     editable=False)
    x_size = models.IntegerField(verbose_name='Image Size X',
                                 editable=False)
    y_size = models.IntegerField(verbose_name='Image Size Y',
                                 editable=False)
    mz_size = models.IntegerField(verbose_name='Image Size M/Z',
                                  editable=False)
    methods = models.ForeignKey('MethodsModel',
                                verbose_name='Sample',
                                editable=False,
                                blank=True,
                                null=True)
    instrument = models.ForeignKey('InstrumentModel',
                                   verbose_name='Instrument',
                                   editable=False,
                                   blank=True,
                                   null=True)
    experiment = models.ForeignKey('ExperimentModel',
                                   verbose_name='Experiment',
                                   editable=False)
    file_store = models.ForeignKey('FileModelOmsi',
                                   verbose_name='File',
                                   editable=False)

    class Meta:
        """Define custom display metadata fro the admin page"""
        verbose_name = "MSI Dataset"
        verbose_name_plural = "MSI Datasets"

    def __unicode__(self):
        """Define the display name for the model object"""
        return unicode(self.name)

    def save(self, *args, **kwargs):
        super(MsiDatasetModel, self).save(*args, **kwargs)  # Save the model so that we can reference it
        self.file_store.last_update_date = datetime.datetime.now()
        self.file_store.save()


class AnalysisModel(models.Model):
    """
    Model for storing analysis data related metadata

    :cvar analysis_type: String indicating the analysis type, i.e., the class used to generate the analysis
    :cvar analysis_identifier: User-defined identifier string of the analysis
    :cvar analysis_index: Index of the analysis in the HDF5 file
    :cvar experiment: Foreign key ot the experiment the analysis is associated with
    :cvar file_store: Foreign key to the file the analysis is associated with
    """

    analysis_type = models.CharField(max_length=1000,
                                     editable=False,
                                     verbose_name="Analysis Type")
    analysis_identifier = models.CharField(max_length=1000,
                                           editable=True,
                                           verbose_name="Analysis Identifier")
    analysis_index = models.IntegerField(verbose_name='Dataset Index',
                                         editable=False)
    experiment = models.ForeignKey('ExperimentModel',
                                   verbose_name='Experiment',
                                   editable=False)
    file_store = models.ForeignKey('FileModelOmsi',
                                   verbose_name='File',
                                   editable=False)

    __original_analysis_identifier = None  # Used to avoid database lookup

    def __init__(self, *args, **kwargs):
        """Overwrite the init to keep track fo values for validation"""
        super(AnalysisModel, self).__init__(*args, **kwargs)
        self.__original_analysis_identifier = self.analysis_identifier

    class Meta:
        """Define custom display metadata fro the admin page"""
        verbose_name = "Analysis"
        verbose_name_plural = "Analyses"

    def __unicode__(self):
        """Define the display name for the model object"""
        return unicode(self.analysis_identifier)

    def clean(self):
        """When we save the model we need to be sure that we can write any potentially changes back to the file"""

        # Check if the analysis_identifier has changed and needs to be written back to the file
        if self.__original_analysis_identifier != self.analysis_identifier:
            # Try to open the HDF5 file
            custom_validators.validate_omsifile_writeable(self.file_store.path)

    def save(self, *args, **kwargs):
        """Overwrite the save method so that we can update the file"""
        if self.__original_analysis_identifier != self.analysis_identifier and self.pk:
            f = omsi_file(self.file_store.path, 'a')
            e = f.get_experiment(self.experiment.experiment_index)
            a = e.get_analysis(self.analysis_index)
            a.get_analysis_identifier()[0] = str(self.analysis_identifier)
            f.close_file()

        super(AnalysisModel, self).save(*args, **kwargs)  # Save the model so that we can reference it
        self.file_store.last_update_date = datetime.datetime.now()
        self.file_store.save()


class MethodsModel(models.Model):
    """
    Model for storing method related metadata

    :cvar name: Name of the method
    :cvar file_store: Foreign key to the file the method is associated with
    :cvar __original_name: Internal variable used to avoid database lookups

    """

    name = models.CharField(max_length=1000)
    file_store = models.ForeignKey('FileModelOmsi',
                                   verbose_name='File',
                                   editable=False)

    __original_name = None

    def __init__(self, *args, **kwargs):
        """Overwrite the init to keep track fo values for validation"""
        super(MethodsModel, self).__init__(*args, **kwargs)
        self.__original_name = self.name

    class Meta:
        """Define custom display metadata fro the admin page"""
        verbose_name = "Method"
        verbose_name_plural = "Methods"

    def __unicode__(self):
        """Define the display name for the model object"""
        return unicode(self.name)

    def clean(self):
        """When we save the model we need to be sure that we can write any potentially changes back to the file"""

        # Check if the analysis_identifier has changed and needs to be written back to the file
        if self.__original_name != self.name:
            # Try to open the HDF5 file
            custom_validators.validate_omsifile_writeable(self.file_store.path)

    def save(self, *args, **kwargs):
        """Overwrite the save method so that we can update the file"""

        if (self.__original_name != self.name) and self.pk:
            f = omsi_file(self.file_store.path, 'a')
            # Get all experiments that point to self
            e = ExperimentModel.objects.select_related().filter(methods=self.id)
            # Get all datasets that point to self
            d = MsiDatasetModel.objects.select_related().filter(methods=self.id)
            methods_paths = []
            for ei in e:
                methods_paths.append(f.get_experiment(ei.experiment_index).get_method_info().get_managed_group().name)
            for di in d:
                methods_paths.append(f.get_experiment(di.experiment.experiment_index).get_msidata(di.data_index).get_method_info().get_managed_group().name)
            unique_samplepaths = set(methods_paths)
            # Update all possible copies of that method within the file
            for s in unique_samplepaths:
                s = omsi_file_methods(method_group=f[s])
                s.get_method_name()[0] = str(self.name)
            f.close_file()

        super(MethodsModel, self).save(*args, **kwargs)  # Save the model so that we can reference it
        self.file_store.last_update_date = datetime.datetime.now()
        self.file_store.save()


class InstrumentModel(models.Model):
    """
    Model for storing instrument related metadata

    :cvar name: Name of the instrument
    :cvar file_store: Foreign key to the file the instrument is associated with
    :cvar __original_name: Internal variable used to avoid database lookups

    """
    name = models.CharField(max_length=1000)
    file_store = models.ForeignKey('FileModelOmsi',
                                   verbose_name='File',
                                   editable=False)

    __original_name = None  # Used to avoid database lookup

    def __init__(self, *args, **kwargs):
        """Overwrite the init to keep track fo values for validation"""
        super(InstrumentModel, self).__init__(*args, **kwargs)
        self.__original_name = self.name

    class Meta:
        """Define custom display metadata fro the admin page"""
        verbose_name = "Instrument"
        verbose_name_plural = "Instruments"

    def __unicode__(self):
        """Define the display name for the model object"""
        return unicode(self.name)

    def clean(self):
        """When we save the model we need to be sure that we can write any potentially changes back to the file"""

        # Check if the analysis_identifier has changed and needs to be written back to the file
        if self.__original_name != self.name:
            # Try to open the HDF5 file
            custom_validators.validate_omsifile_writeable(self.file_store.path)

    def save(self, *args, **kwargs):
        """Overwrite the save method so that we can update the file"""

        if self.__original_name != self.name and self.pk:
            f = omsi_file(self.file_store.path, 'a')
            # Get all experiments that point to self
            e = ExperimentModel.objects.select_related().filter(instrument=self.id)
            # Get all datasets that point to self
            d = MsiDatasetModel.objects.select_related().filter(instrument=self.id)
            instrument_paths = []
            for ei in e:
                instrument_paths.append(f.get_experiment(ei.experiment_index).get_instrument_info().get_managed_group().name)
            for di in d:
                instrument_paths.append(f.get_experiment(di.experiment.experiment_index).get_msidata(di.data_index).get_instrument_info().get_managed_group().name)
            unique_instrumentpaths = set(instrument_paths)
            # Update all possible copies of that instrument within the file
            for s in unique_instrumentpaths:
                s = omsi_file_instrument(instrument_group=f[s])
                s.get_instrument_name()[0] = str(self.name)
            f.close_file()

        super(InstrumentModel, self).save(*args, **kwargs)  # Save the model so that we can reference it
        self.file_store.last_update_date = datetime.datetime.now()
        self.file_store.save()

# FileFormOmsi = modelform_factory(queryset = FileModelOmsi.objects.all())
# path = models.CharField(max_length=4000 , validators=[custom_validators.valdidate_omsifile], unique=True)
# is_public = models.BooleanField(default=False , verbose_name="Make file public")
# auth_users = models.ManyToManyField(User, blank=True)
# auth_groups = models.ManyToManyField(Group, blank=True)
# created_date = models.DateTimeField(auto_now_add=True, editable=True)
# last_update_date = models.DateTimeField(auto_now=True, editable=True)
# class Meta:
#     model = Documents
#     fields = ('secretdocs', )
#     widgets = {
#         'secretdocs': Select(attrs={'class': 'select'}),
#     }


class FileFormOmsi(ModelForm):
    # name = forms.CharField(max_length=100)
    # path = forms.ModelMultipleChoiceField(queryset=FileModelOmsi.objects.all())
    # files = forms.ChoiceField(choices=[omsi_file.path for omsi_file in FileModelOmsi.objects.all()])

    class Meta:
        model = FileModelOmsi
        fields = ('view_users',
                  'view_groups',
                  'edit_users',
                  'edit_groups',
                  'owner_users',
                  'owner_groups')
