from django.core.exceptions import ValidationError
from omsi.dataformat.omsi_file.main_file import omsi_file
import os


def validate_filepath(path):
    """
    Validate that the given path points to an existing file.
    """
    if not os.path.exists(path):
        raise ValidationError(u'Invalid path')
    if not os.path.isfile(path):
        raise ValidationError(u'The path does not specify a file')


def validate_dirpath(path):
    """
    Validate that the given path points ot an existing directory.
    """
    if not os.path.exists(path):
        raise ValidationError(u'Invalid path')
    if not os.path.isdir(path):
        raise ValidationError(u'The path does not specify a directory')


def validate_file_reader_name(name):
    """
    Validate the name of the file reader and create the according
    file format model if it does not exist.
    """
    # 1) Check whether the name is valid
    from omsi.dataformat.file_reader_base import file_reader_base
    from omsi_server.omsi_resources.models import FormatReaderModel
    if name not in file_reader_base.available_formats().keys():
        raise ValidationError(u'Unknown file reader class given')

    # 2) Create the file reader model if it is not in the database yet
    if FormatReaderModel.objects.filter(format__eq=name).count() == 0:
        newformat = FormatReaderModel(format=name)
        newformat.save()

def valdidate_omsifile(path):
    """
    Validate that the given file can be read using the OMSI file API.
    """
    filepath = path.rstrip(" ")
    validate_filepath(filepath)
    try:
        f = omsi_file(filename=filepath, mode='r')
        num_exp = f.get_num_experiments()
        f.close_file()
        del f
    except:
        raise ValidationError(u'File is not a valid OMSI data file')
    

def validate_omsifile_writeable(path):
    """
    Validate that the given file can be written to using the OMSI file API.
    """
    try:
        f = omsi_file(filename=path, mode='a')
        num_exp = f.get_num_experiments()
        f.close_file()
        del f
    except:
        raise ValidationError(u'File is not a writable OMSI file.')