import requests
from django.contrib.auth.models import User
import string
import random


class NEWT(object):

    def __init__(self):
        self.auth_newt_groups = [u'm1541']
        self.newt_base_url = "https://newt.nersc.gov/newt"
        self.newt_auth_url = self.newt_base_url+"/auth"
        self.newt_account_url = self.newt_base_url+"/account/iris"
        self.newt_logout_url = self.newt_base_url+"/logout"
        self.newt_queue_url = self.newt_base_url+"/queue"

    def logout(self, request=None):
        """Logout a user from NEWT.

           :param request: The DJANGO request object.

           :returns: JSON object with the logout status.
        """
        s = requests.Session()
        r = s.get(self.newt_logout_url)
        return r.json()

    def authenticate(self, username=None, password=None, request=None):
        """ Authenticate user using NERSC's NEWT framework.

            :param username: The name of the user
            :param password: The user's password
            :param request: The DHANGO request object

        """
        #import pdb; pdb.set_trace()
        s = requests.Session()
        r = s.post(self.newt_auth_url, {"username": username, "password": password})
        try:
 	    r.raise_for_status()
        except HTTPError:
            return None
        result = r.json()
        if not result['auth']:
            return None
        newt_sessionid = result['newt_sessionid']

        #NEWT session id for the user. We can use this to run at NERSC as the user.
        if request:
            request.session['newt_sessionid'] = newt_sessionid

        #If user is authenticated via NEWT, check if the user exists
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            #If the user does not exists check whether they are in the required repos
            #Check if the user in a auth group
            in_auth_group = False
            for i in self.get_groups(newt_sessionid, username):
                if i in self.auth_newt_groups:
                    in_auth_group = True
                    break
            #Add the user to the DJANGO user database if it is part of an authorized group at NERSC
            if in_auth_group:
                # Create a new user
                # TODO: Finish user creation
                user = User(username=username, password=self.__create_random_string__())
                user.is_active = True
                user.is_staff = False
                user.is_superuser = False
                user_attributes = self.get_user_attributes(newt_sessionid, username)
                try:
                    user.email = user_attributes['email']
                    user.first_name = user_attributes['firstname']
                    user.last_name = user_attributes['lastname']
                except KeyError:
                    pass
                user.save()
            else:
                return None
        return user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

    def get_groups(self, session_id, user_id):
        """
	Get all unix group names for the user_id

        :param session_d: NEWT session id
        :param user_id: unix username to query
        :returns: list of unix group names or empty list if query fails
        """
        s = requests.Session()
        query_function = 'groups(username: \\"'+user_id+'\\") {name}'
        cookies = {"newt_sessionid": session_id}
        r = s.post(self.newt_account_url, {'query':  query_function}, cookies=cookies)
        try:
 	    r.raise_for_status()
        except HTTPError:
 	    return []
        return [x['name'] for x in r.json()['data']['newt']['groups']]

    def get_user_attributes(self, session_id, user_id):
        """
	Get email address, first name and last name for the user_id

        :param session_d: NEWT session id
        :param user_id: unix username to query
        :returns: dict with keys email, lastname, firstname or empty dict if query fails
        """
        s = requests.Session()
        query_function = 'user(username: \\"'+user_id+'\\") {email, lastname, firstname}'
        cookies = {"newt_sessionid": session_id}
        r = s.post(self.newt_account_url, {'query':  query_function}, cookies=cookies)
        try:
 	    r.raise_for_status()
        except:
 	    return {}
        return(r.json()['data']['newt']['user'])

    @staticmethod
    def run_command(session_id, machine_name, command):
        """
        Run the given command

        :param session_id: The NEWT session id
        :param machine_name: The name of the machine where the job should be executed
        :param command: String with the command to be executed

        """
        newt_url = "https://newt.nersc.gov/newt/command/" + machine_name
        cookies = {"newt_sessionid": session_id}
        payload = {"executable": command, "loginenv": "true"}
        return requests.post(newt_url, data=payload, cookies=cookies)

    @staticmethod
    def job_showstart(session_id, job_id, machine_name):
        """
        Get estimated start time for the job using the showstart command.

        :param session_id: The NEWT session id
        :param job_id: The NERSC job id to be deleted
        :param machine_name: The name of the machine where the job should be executed
        """
        newt_url = "https://newt.nersc.gov/newt/command/" + machine_name
        cookies = {"newt_sessionid": session_id}
        command = "/usr/syscom/opt/moab/7.2.7-e7c070d1-b4/bin/showstart " + job_id
        payload = {"executable": command, "loginenv": "true"}
        return requests.post(newt_url, data=payload, cookies=cookies)

    @staticmethod
    def submit_job(session_id, job_script, machine_name):
        """
        Submit a job to the queue

        :param session_id: The NEWT session id
        :param job_script: The job script to be executed
        :param machine_name: The name of the machine where the job should be executed

        :returns: requests.Response object with the response. To get the json response
                  from newt use the .json() method of the Response object. The NEWT
                  JSON string will be of the form:
                  JSON String: { "status": ["OK" | "ERROR"], "error": string, "jobid" : string }

        """
        cookies = {"newt_sessionid": session_id}
        payload = {"jobscript": job_script}
        newt_url = "https://newt.nersc.gov/newt/queue/%(machine_name)s/" % \
                   {"machine_name": machine_name}
        return requests.post(newt_url, data=payload, cookies=cookies)

    @staticmethod
    def delete_job(session_id, job_id, machine_name):
        """
        Delete a job from the queue

        :param session_id: The NEWT session id
        :param job_id: The NERSC job id to be deleted
        :param machine_name: The name of the machine where the job should be executed

        :returns: requests.Response object with the response. To get the json response
                  from newt use the .json() method of the Response object. The NEWT
                  JSON string will be of the form:
                  JSON String: {"status": ["OK | ERROR"], "output": string, "error": string}

        """
        newt_url = "https://newt.nersc.gov/newt/queue/%(machine_name)s/%(job_id)s" % \
                   {"machine_name": machine_name, "job_id": job_id}
        cookies = {"newt_sessionid": session_id}
        return requests.delete(newt_url, cookies=cookies)

    @staticmethod
    def job_status(session_id, job_id, machine_name):
        """
        Get the status of the job

        Example outputs:

        * `{"status": "ERROR", "output": "", "error": "'qstat did not return output'"}` \
           This occurs, e.g., when the job is not found
        *  {"status": "Q", "repo": "m1541", "name": "omsi_user_", "timeuse": "-", \
            "hostname": "carver", "rank": "105", "jobid": "9936469.cvrsvc09-ib", \
            "queue": "serial", "submittime": "Aug 21 11:45:49", "state": "Idle", \
            "user": "oruebel", "nodes": "1", "timereq": "48:00:00", "procs": "1"}

        :param session_id: The NEWT session id
        :param job_id: The NERSC job id to be deleted
        :param machine_name: The name of the machine where the job should be executed

        :returns: requests.Response object with the response. To get the json response
                  from newt use the .json() method of the Response object. The NEWT
                  JSON string will be of the form:
                  JSON String: {"jobid": string, "name": string, "user": string,
                              "timeuse": string, "status": string, "queue": string}
        """
        newt_url = "https://newt.nersc.gov/newt/queue/%(machine_name)s/%(job_id)s" % \
                   {"machine_name": machine_name, "job_id": job_id}
        cookies = {"newt_sessionid": session_id}
        return requests.get(newt_url, cookies=cookies)

    @staticmethod
    def completed_job_info(session_id, username,  limit=2147483647):
        """
        Get information about completed jobs.

        Example output:

        [
            {
                "hostname": "Carver",
                "jobid": "10346079",
                "jobid_long": "10346079.cvrsvc09-ib",
                "jobname": "omsi_user_job",
                "owner": "...",
                "status": "0",
                "account": "m1541",
                "queue": "regular",
                "nodes": "1",
                "procs": "1",
                "completiontime": "10/10/14 17:04",
                "completionunix": 1412985858,
                "starttime": "10/10/14 17:04",
                "queuedtime": "10/10/14 16:45",
                "wallclock": "0.003",
                "wallclock_requested": "10.000",
                "rawhours": "0.00"
            },
            {
                "hostname": "Carver",
                "jobid": "10275335",
                "jobid_long": "10275335.cvrsvc09-ib",
                "jobname": "omsi_user_job",
                "owner": "...",
                "status": "0",
                "account": "m1541",
                "queue": "regular",
                "nodes": "1",
                "procs": "1",
                "completiontime": "10/03/14 15:48",
                "completionunix": 1412376512,
                "starttime": "10/03/14 15:44",
                "queuedtime": "10/03/14 15:41",
                "wallclock": "0.074",
                "wallclock_requested": "10.000",
                "rawhours": "0.07"
            }]

        :param session_id: The NEWT seesion id
        :param username: NERSC username
        :param limit: The maximum number of jobs to be retrieved. The default is the max of int32 to retrieve all.

        """
        newt_url = "https://newt.nersc.gov/newt/queue/completedjobs?username=%(username)s&limit=%(limit)s" % \
                   {"username": username, "limit": str(limit)}
        cookies =  {"newt_sessionid": session_id}
        return requests.get(newt_url, cookies=cookies)

    @staticmethod
    def completed_info_for_job(session_id, username, jobid):
        """
        Get the information about a specific completed job.

        :param session_id: The NEWT seesion id
        :param username: NERSC username
        :param job_id: The NERSC job id of the job of interest

        :returns: Python dict with the job info or None.
        """
        response = NEWT.completed_job_info(session_id=session_id,
                                           username=username)
        try:
            job_status = response.json()
        except ValueError:  # NEWT may not always return a json that can be decoded
            job_status = None
        re_status = None
        if job_status:
            for job in job_status:
                try:
                    if job['jobid'] == jobid or job['jobid_long'] == jobid:
                        re_status = job
                        break
                except KeyError:
                    pass
        return re_status


    @staticmethod
    def get_session_id(request):
        """
        Get the NEWT session id from the request object

        :param request: The DJANGO request object.

        :returns: The newt session ID or NONE if no session id exists or if the requests object was None.
        """
        if request is not None:
            return request.session.get("newt_sessionid", None)
        else:
            return None

    @staticmethod
    def __create_random_string__(size=10, chars=string.ascii_uppercase + string.digits + string.ascii_lowercase):
        return ''.join(random.choice(chars) for x in range(size))
