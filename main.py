#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import webapp2
import jinja2
import os

from google.appengine.api import users
from google.appengine.ext import ndb

from models import Student, Assignment, GradeEntry
import logging

import cStringIO
import csv
import re

# Jinja environment instance necessary to use Jinja templates.
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)), autoescape=True)

class MainHandler(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if not user:
            self.redirect(users.create_login_url(self.request.uri))
            return
        assignments, assignments_map = get_assignments(user)
        students, students_map, teams = get_students(user)
        grade_entries = get_grade_entries(user, assignments_map, students_map)
        # Optional adding some meta data about the assignments for the badge icon.
        assignment_badge_data = {}
        for assignment in assignments:
            assignment_badge_data[assignment.key] = [0, 0]  # Count, Score Accumulator
        for grade_entry in grade_entries:
            assignment_badge_data[grade_entry.assignment_key][0] += 1
            assignment_badge_data[grade_entry.assignment_key][1] += grade_entry.score
        for assignment in assignments:
            metadata = assignment_badge_data[assignment.key]
            if metadata[0] > 0:
                metadata.append(metadata[1] / metadata[0])  # Average
            else:
                metadata.append("na")  # Average is NA
        template = jinja_env.get_template("templates/graderecorder.html")
        self.response.out.write(template.render({'assignments': assignments,
                                                 'active_assignemnt': self.request.get('active_assignemnt'),
                                                 'students': students,
                                                 'teams': teams,
                                                 'grade_entries': grade_entries,
                                                 'assignment_badge_data': assignment_badge_data,
                                                 'user_email': user.email(),
                                                 'logout_url': users.create_logout_url("/")}))

    def post(self):
        user = users.get_current_user()
        if not user:
            self.redirect(users.create_login_url(self.request.uri))
            return
        next_active_assignemnt = None
        if (self.request.get('type') == 'Student'):
            rose_username = self.request.get('rose_username')
            new_student = Student(parent=get_parent_key(user),
                                  id=rose_username,
                                  first_name=self.request.get('first_name'),
                                  last_name=self.request.get('last_name'),
                                  rose_username=rose_username,
                                  team=self.request.get('team'))
            new_student.put()
        elif (self.request.get('type') == 'Assignment'):
            active_assignment = Assignment(parent=get_parent_key(user),
                                           name=self.request.get('assignment_name'))
            if len(self.request.get('assignment_entity_key')) > 0:
                assignment_key = ndb.Key(urlsafe=self.request.get('assignment_entity_key'))
                if assignment_key:
                    assignment = assignment_key.get()
                    if assignment:
                        active_assignment = assignment
                        active_assignment.name = self.request.get('assignment_name')
            active_assignment.put()
            next_active_assignemnt = active_assignment.key.urlsafe()
        elif (self.request.get('type') == 'SingleGradeEntry'):
            assignment_key = ndb.Key(urlsafe=self.request.get('assignment_key'))
            student_key = ndb.Key(urlsafe=self.request.get('student_key'))
            student = student_key.get()
            score = int(self.request.get('score'))
            new_grade_entry = GradeEntry(parent=assignment_key,
                                         id=student.rose_username,
                                         assignment_key=assignment_key,
                                         student_key=student_key,
                                         score=score)
            new_grade_entry.put()
            next_active_assignemnt = assignment_key.urlsafe()
        elif (self.request.get('type') == 'TeamGradeEntry'):
            assignment_key = ndb.Key(urlsafe=self.request.get('assignment_key'))
            score = int(self.request.get('score'))
            team = self.request.get('team')
            student_query = Student.query(Student.team==team, ancestor=get_parent_key(user))
            for student in student_query:
                new_grade_entry = GradeEntry(parent=assignment_key,
                                             id=student.rose_username,
                                             assignment_key=assignment_key,
                                             student_key=student.key,
                                             score=score)
                new_grade_entry.put()
            next_active_assignemnt = assignment_key.urlsafe()
        if next_active_assignemnt:
          self.redirect("/?active_assignemnt=" + next_active_assignemnt)
        else:
          self.redirect("/")

def get_parent_key(user):
    return ndb.Key("Entity", user.email().lower())

def get_assignments(user):
    """ Gets all of the assignments for this user and makes a key map for them. """
    assignments = Assignment.query(ancestor=get_parent_key(user)).order(Assignment.name).fetch()
    assignments_map = {}
    for assignment in assignments:
        assignments_map[assignment.key] = assignment
    return assignments, assignments_map


def get_students(user):
    """ Gets all of the students for this user and makes a key map for them. """
    students = Student.query(ancestor=get_parent_key(user)).order(Student.rose_username).fetch()
    students_map = {}
    teams = []
    for student in students:
        students_map[student.key] = student
        if student.team not in teams:
          teams.append(student.team)
    return students, students_map, sorted(teams)


def get_grade_entries(user, assignments_map, students_map):
    """ Gets all of the grade entries for this user.
          Replaces the assignment_key and student_key with an assignment and student. """
    grade_entries = GradeEntry.query(ancestor=get_parent_key(user)).fetch()
    for grade_entry in grade_entries:
        grade_entry.assignment = assignments_map[grade_entry.assignment_key]
        grade_entry.student = students_map[grade_entry.student_key]
    return grade_entries


class BulkStudentImportAction(webapp2.RequestHandler):
    def post(self):
        user = users.get_current_user()
        if not user:
            self.redirect(users.create_login_url(self.request.uri))
            return
        if len(self.request.get("remove_all_students")) > 0:
          remove_all_students(user)
        imported_file = self.request.params["bulk-import-file"].value
        process_roster(imported_file, user)
        self.redirect(self.request.referer)

def process_roster(imported_file, user):
    try:
      csv_file = cStringIO.StringIO(imported_file)
      # Read the first kb to ensure the file is a valid CSV file.
      csv.Sniffer().sniff(csv_file.read(1024), ",")
      csv_file.seek(0)
      reader = csv.DictReader(csv_file, dialect="excel")
    except:
      raise Exception("Invalid CSV file")
    reader.fieldnames = [re.compile('[\W_]+', flags=re.UNICODE).sub('', field).lower()
                         for field in reader.fieldnames]
    for row in reader:
        rose_username = row.get("username", None)
        new_student = Student(parent=get_parent_key(user),
                              id=rose_username,
                              first_name=row.get("first", None),
                              last_name=row.get("last", None),
                              team=row.get("team", None),
                              rose_username=rose_username)
        new_student.put()

class DeleteStudentAction(webapp2.RequestHandler):
    def post(self):
        user = users.get_current_user()
        if not user:
            self.redirect(users.create_login_url(self.request.uri))
            return
        if self.request.get('student_to_delete_key') == "AllStudents":
          remove_all_students(user)
        else:
          student_key = ndb.Key(urlsafe=self.request.get('student_to_delete_key'))
          remove_all_grades_for_student(user, student_key)
          student_key.delete();
        self.redirect(self.request.referer)

def remove_all_students(user):
  """ Removes all grades and all students for a user. (use with caution) """
  all_grades = GradeEntry.query(ancestor=get_parent_key(user))
  for grade in all_grades:
    grade.key.delete()
  all_students = Student.query(ancestor=get_parent_key(user))
  for student in all_students:
    student.key.delete()

def remove_all_grades_for_student(user, student_key):
  """ Removes all grades for the given student. """
  grades_for_student = GradeEntry.query(GradeEntry.student_key==student_key, ancestor=get_parent_key(user))
  for grade in grades_for_student:
    grade.key.delete()

class DeleteAssignmentAction(webapp2.RequestHandler):
    def post(self):
        user = users.get_current_user()
        if not user:
            self.redirect(users.create_login_url(self.request.uri))
            return
        assignment_key = ndb.Key(urlsafe=self.request.get('assignment_to_delete_key'))
        remove_all_grades_for_assignment(user, assignment_key)
        assignment_key.delete();
        self.redirect("/")

def remove_all_grades_for_assignment(user, assignment_key):
  """ Removes all grades for the given student. """
  grades_for_assignment = GradeEntry.query(ancestor=assignment_key)
  for grade in grades_for_assignment:
    grade.key.delete()

class DeleteGradeEntryAction(webapp2.RequestHandler):
    def post(self):
        user = users.get_current_user()
        if not user:
            self.redirect(users.create_login_url(self.request.uri))
            return
        grade_entry_key = ndb.Key(urlsafe=self.request.get('grade_entry_to_delete_key'))
        grade = grade_entry_key.get()
        next_active_assignemnt = grade.assignment_key.urlsafe()
        grade_entry_key.delete();
        self.redirect("/?active_assignemnt=" + next_active_assignemnt)

class ExportCsvAction(webapp2.RequestHandler):
  def post(self):
    user = users.get_current_user()
    if not user:
        self.redirect(users.create_login_url(self.request.uri))
        return
    export_student_name = len(self.request.get("student_name")) > 0
    export_rose_username = len(self.request.get("rose_username")) > 0
    export_team = len(self.request.get("team")) > 0
    urlsafe_assignment_keys = self.request.get_all("assignment_keys[]")
    csv_data = get_csv_export_lists(user, export_student_name, export_rose_username,
                                    export_team, urlsafe_assignment_keys)
    self.response.headers['Content-Type'] = 'application/csv'
    writer = csv.writer(self.response.out)
    for csv_row in csv_data:
      writer.writerow(csv_row)

def get_csv_export_lists(user, export_student_name, export_rose_username,
                         export_team, urlsafe_assignment_keys):
  table_data = []
  student_row_index_map = {} # Map of student_key to row in the table_data
  assignment_col_index_map = {} # Map of assignment_key to column in the table_data
  header_row = []
  table_data.append(header_row)
  num_columns = 0

  # Student Header
  if export_student_name:
    header_row.append("First")
    header_row.append("Last")
    num_columns += 2
  if export_rose_username:
    header_row.append("Username")
    num_columns += 1
  if export_team:
    header_row.append("Team")
    num_columns += 1

  # Assignment Prep
  assignment_keys = []
  for urlsafe_assignment_key in urlsafe_assignment_keys:
    assignment_keys.append(ndb.Key(urlsafe=urlsafe_assignment_key))
  assignments = ndb.get_multi(assignment_keys)
  assignments.sort(key=lambda assignment: assignment.name)
  num_assignments_found = 0
  for assignment in assignments:
    if assignment:
      header_row.append(assignment.name)
      assignment_col_index_map[assignment.key] = num_columns
      num_columns += 1
      num_assignments_found += 1

  # Student Data + assignment placeholders
  num_rows = 1
  students = Student.query(ancestor=get_parent_key(user)).order(Student.rose_username)
  for student in students:
    current_row = []
    if export_student_name:
      current_row.append(student.first_name)
      current_row.append(student.last_name)
    if export_rose_username:
      current_row.append(student.rose_username)
    if export_team:
      current_row.append(student.team)
    for i in range(num_assignments_found):
      current_row.append("-")
    table_data.append(current_row)
    student_row_index_map[student.key] = num_rows
    num_rows += 1

  # Add the grades
  grade_query = GradeEntry.query(ancestor=get_parent_key(user))
  for grade in grade_query:
    if grade.student_key in student_row_index_map and grade.assignment_key in assignment_col_index_map:
      row = student_row_index_map[grade.student_key]
      col = assignment_col_index_map[grade.assignment_key]
      table_data[row][col] = grade.score

  # Removing rows with no grades (allows for data merging)
  for row_index in reversed(range(1, num_rows)):
    row = table_data[row_index]
    blank_grades = row.count("-")
    if blank_grades == num_assignments_found:
      table_data.remove(row)

  return table_data

app = webapp2.WSGIApplication([
    ("/", MainHandler),
    ("/bulk_student_import", BulkStudentImportAction),
    ("/delete_student", DeleteStudentAction),
    ("/delete_assignment", DeleteAssignmentAction),
    ("/delete_grade_entry", DeleteGradeEntryAction),
    ("/grade_recorder_grades.csv", ExportCsvAction)
], debug=True)
