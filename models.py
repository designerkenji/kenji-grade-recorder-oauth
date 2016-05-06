from google.appengine.ext import ndb

class Student(ndb.Model):
    """ Student. """
    first_name = ndb.StringProperty()
    last_name = ndb.StringProperty()
    rose_username = ndb.StringProperty()
    team = ndb.StringProperty()


class Assignment(ndb.Model):
    """ Assignment. """
    name = ndb.StringProperty()

class GradeEntry(ndb.Model):
    """ Score for a student on an assignment. """
    score = ndb.IntegerProperty()
    student_key = ndb.KeyProperty(kind=Student)
    assignment_key = ndb.KeyProperty(kind=Assignment)
