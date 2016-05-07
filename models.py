from google.appengine.ext import ndb
from endpoints_proto_datastore.ndb.model import EndpointsModel

class Student(EndpointsModel):
    """ Student. """
    _message_fields_schema = ("entityKey", "first_name", "last_name", "rose_username", "team")
    first_name = ndb.StringProperty()
    last_name = ndb.StringProperty()
    rose_username = ndb.StringProperty()
    team = ndb.StringProperty()

class Assignment(EndpointsModel):
    """ Assignment. """
    _message_fields_schema = ("entityKey", "name")
    name = ndb.StringProperty()

class GradeEntry(EndpointsModel):
    """ Score for a student on an assignment. """
    _message_fields_schema = ("entityKey", "score", "student_key", "assignment_key")
    score = ndb.IntegerProperty()
    student_key = ndb.KeyProperty(kind=Student)
    assignment_key = ndb.KeyProperty(kind=Assignment)
