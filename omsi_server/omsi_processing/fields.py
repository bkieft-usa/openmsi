from django.db import models
from django.core.serializers.json import DjangoJSONEncoder
try:
    import json
except ImportError:
    from django.utils import simplejson as json
from django.core.exceptions import ValidationError


class JSONField(models.TextField):
    """
    JSONField is a just a TextField with the main difference that the
    test is automatically serialized to JSON and deserialized to python
    dict when reading the data.
    """
    __metaclass__ = models.SubfieldBase

    def to_python(self, value):
        """
        Convert JSON string to Python object once DJANGO has
        loaded it from the database.

        :param value: The JSON string loaded from the database

        :returns: The resulting Python object (usually a dict).

        """
        # 1) Check if we have an empty string
        if value == "":
            return None
        # 2) Convert the loaded string to python
        try:
            if isinstance(value, basestring):
                return json.loads(value)
        except ValueError:
            pass
        # 3) Return the converted value
        return value

    def get_db_prep_save(self, value, connection):
        """Convert python object to JSON"""
        # 1) Check if we have an empty string
        if value == "":
            return None
        # 2) Encode the python object in json
        if isinstance(value, dict) or isinstance(value, list):
            value = json.dumps(value, cls=DjangoJSONEncoder)
        # 3) Hand the converted object to the original implementation of get_db_prep_save
        return super(JSONField, self).get_db_prep_save(value, connection)

    @staticmethod
    def validate_json_serializable(pyobject):
        """
        Validate that the given python object can be serialized to JSON
        for storage in the database
        """
        try:
            json.dumps(pyobject)
        except:
            raise ValidationError(u'Object not JSON serializable')
