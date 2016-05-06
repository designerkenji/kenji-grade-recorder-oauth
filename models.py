from endpoints_proto_datastore.ndb.model import EndpointsModel
from google.appengine.ext import ndb

class Student(EndpointsModel):
    """ Student. """
    _message_fields_schema = ("entityKey","first_name","last_name","rose_username","team")
    first_name = ndb.StringProperty()
    last_name = ndb.StringProperty()
    rose_username = ndb.StringProperty()
    team = ndb.StringProperty()


class Assignment(ndb.Model):
    """ Assignment. """
    _message_fields_schema = ("entityKey","name")
    name = ndb.StringProperty()

class GradeEntry(ndb.Model):
    """ Score for a student on an assignment. """
    _message_fields_schema = ("entityKey","score","student_key","assignment_key")
    score = ndb.IntegerProperty()
    student_key = ndb.KeyProperty(kind=Student)
    assignment_key = ndb.KeyProperty(kind=Assignment)
