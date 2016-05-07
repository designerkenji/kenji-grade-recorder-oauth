'''
Created on May 6, 2016

@author: DesignerKenji
'''
import endpoints
import protorpc

import main
from models import Student, Assignment, GradeEntry


WEB_CLIENT_ID="59444852514-aj0l07tn4arg7c8a2q75up3np75mg5a3.apps.googleusercontent.com"
ANDROID_CLIENT_ID=""
IOS_CLIENT_ID=""

@endpoints.api(name="graderecorder", 
               version="v1", 
               description="Grade Recorder API", 
               audiences=[WEB_CLIENT_ID],
               allowed_client_ids=[endpoints.API_EXPLORER_CLIENT_ID, WEB_CLIENT_ID,ANDROID_CLIENT_ID,IOS_CLIENT_ID])
class GradeRecorderApi(protorpc.remote.Service):
    pass

    @Student.query_method(user_required="True", query_fields=("limit","order","pageToken"),
                             name="student.list", path="student/list", http_method="GET")
    def student_list(self, query):
        """ list all the students for a given user """
        user = endpoints.get_current_user()
        students = Student.query(ancestor=main.get_parent_key(user)).order(Student.rose_username)
        return students

    @Assignment.query_method(user_required="True", query_fields=("limit","pageToken"),
                             name="assignment.list", path="assignment/list", http_method="GET")
    def assignment_list(self, query):
        """ list all the assignments owned by a given user """
        user = endpoints.get_current_user()
        assignments = Assignment.query(ancestor=main.get_parent_key(user)).order(Assignment.name)
        return assignments

    @GradeEntry.query_method(user_required="True", query_fields=("limit","order","pageToken","assignment_key"),
                             name="gradeentry.list", path="gradeentry/list/{assignment_key}", http_method="GET")
    def gradeentry_list(self, query):
        """ list all the grade entries for a given assignment """
        return query
    
    @Assignment.method(user_required="True", 
                             name="assignment.insert", path="assignment/insert", http_method="POST")
    def assignment_insert(self, assignment):
        """ add or update an assignment owned by the given user """
        if assignment.form_datastore:
            assignment_with_parent = assignment
        else:
            user = endpoints.get_current_user()
            assignment_with_parent = Assignment(parent=main.get_parent_key(user), name=assignment.name)
        assignment_with_parent.put()
        return assignment_with_parent

    @GradeEntry.method(user_required="True", 
                             name="gradeentry.insert", path="gradeentry/insert", http_method="POST")
    def gradeentry_insert(self, grade_entry):
        """ add or update an grade entry for an assignment """
        if grade_entry.form_datastore:
            grade_entry_with_parent = grade_entry
        else:
            student = grade_entry.student_key.get()
            grade_entry_with_parent = GradeEntry(parent=grade_entry.assignment_key,
                                                 id=student.rose_username,
                                                 score=grade_entry.score,
                                                 student_key=grade_entry.student_key,
                                                 assignment_key=grade_entry.assignment_key)
        grade_entry_with_parent.put()
        return grade_entry_with_parent

app = endpoints.api_server(GradeRecorderApi, restricted=False)