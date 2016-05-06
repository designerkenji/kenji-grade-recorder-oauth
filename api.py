'''
Created on May 6, 2016

@author: DesignerKenji
'''
import endpoints
import protorpc

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

app = endpoints.api_server(GradeRecorderApi, restricted=False)