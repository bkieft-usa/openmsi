from django.db import models

from fields import JSONField
from django.contrib.auth.models import User
from django.conf import settings
import os
try:
    import json
except ImportError:
    from django.utils import simplejson as json
try:
    from omsi_server.omsi_resources.models import *
    # from omsi_server.omsi_resources.models import FileModelOmsi
    # from omsi_server.omsi_resources.models import FileModelRaw
    from omsi_server.omsi_server.newt_auth_backend import NEWT
    from omsi_server.omsi_processing.machine_backend import BACKENDS as MACHINE_BACKENDS
    from omsi_server.omsi_processing.machine_backend import slurm_scheduler_machine
    from omsi_server.omsi_processing.machine_backend import DEFAULT_BACKEND_KEY as DEFAULT_MACHINE_BACKEND_KEY
except ImportError:
    from omsi_resources.models import *
    # from omsi_resources.models import FileModelOmsi
    # from omsi_resources.models import FileModelRaw
    from omsi_server.newt_auth_backend import NEWT
    from omsi_processing.machine_backend import BACKENDS as MACHINE_BACKENDS
    from omsi_processing.machine_backend import slurm_scheduler_machine
    from omsi_processing.machine_backend import DEFAULT_BACKEND_KEY as DEFAULT_MACHINE_BACKEND_KEY

import time
import datetime

# TODO: Update the api documentation (add missing modules etc.)
# TODO Update the check_status function to utilize the new job status files


#######################################################
#      Helper classes for dealing with the            #
#      specification and execution of job tasks       #
#######################################################
class ProcessingTaskRunner(object):
    """
    Class for running a single processing task.

    :ivar task_model: The ProcessingTaskModel to be run
    :type task_model: ProcessingTaskModel
    :ivar newt_session_id: The newt session id

    """

    def __init__(self, task_model, newt_session_id):
        """
        Create a runner to execute the processing task with the given
        parameters and description.

        :param task_model: The ProcessingTaskModel to be run
        :type task_model: ProcessingTaskModel
        :param newt_session_id: The newt session id

        """
        self.task_model = task_model
        self.newt_session_id = newt_session_id

    def submit_job(self):
        """
        Submit a job to the queue
        """
        # Validate that we can submit the job
        if self.newt_session_id is None:
            raise ValueError("Invalid newt_sessionid")

        # Error if the job is already finished, running, or currently in the queue
        curr_status = self.task_model.check_status()
        if curr_status == self.task_model.STATUS_COMPLETE or \
                curr_status == self.task_model.STATUS_RUNNING or \
                curr_status == self.task_model.STATUS_QUEUED:
            raise RuntimeError('The task is either already complete, running, or queued')
        # Error if the task is waiting for other tasks
        if curr_status == self.task_model.STATUS_WAIT_FOR_OTHERS:
            raise RuntimeError('Task cannot be executed. Waiting for other tasks to complete.')
        # If the job is ready or we encountered and error in a previous execution, then try to run.
        if curr_status == self.task_model.STATUS_READY or \
                curr_status == self.task_model.STATUS_ERROR:
            pass

        # Create the job textual description of the job to be submitted
        job_description = ProcessingTaskDescription.from_dict(self.task_model.task_description)
        job_command = job_description.get_command()
        task_params = ProcessingTaskExecutionSettings.from_dict(self.task_model.execution_settings)
        error_param = task_params.backend.get_error_filename_parameter_name()
        output_param = task_params.backend.get_output_filename_parameter_name()
        task_params[error_param] = ProcessingTaskExecutionSettings.\
            create_error_filename(username=self.task_model.task_user.username,
                                  machine=task_params.get_machine())
        task_params[output_param] = ProcessingTaskExecutionSettings.\
            create_out_filename(username=self.task_model.task_user.username,
                                machine=task_params.get_machine())
        job_script = task_params.to_job_script(job_command=job_command,
                                               username=self.task_model.task_user.username)

        # Change status to "in_queue"
        self.task_model.execution_settings = task_params
        self.task_model.status = self.task_model.STATUS_QUEUED
        self.task_model.start_time = None
        self.task_model.save()

        # Submit the job via NEWT
        r = NEWT.submit_job(session_id=self.newt_session_id,
                            job_script=job_script,
                            machine_name=task_params.get_machine())

        try:
            json_response = r.json()
        except ValueError:  # NEWT may not always return a json that can be decoded
            json_response = None
        if r.status_code != 200:
            self.task_model.status = self.task_model.STATUS_ERROR
            self.task_model.save()
            # raise ValueError("Error submitting job. " + unicode(json_response) + " " + unicode(r.status_code))

        # Update the job status and return the json response
        if json_response:
            if json_response['status'] == 'ERROR':
                self.task_model.status = self.task_model.STATUS_ERROR
                self.task_model.status_message = json_response['error']
                self.task_model.save()
                # raise ValueError("Error scheduling the job " + json_response['error'] + " " + unicode(r.status_code))
            elif json_response['status'] == 'FORBIDDEN':
                self.task_model.status = self.task_model.STATUS_ERROR
                self.task_model.status_message = json_response['error']
                self.task_model.save()
                # TODO forward to login page if forbidden
            else:
                # Save and extract the job id. NOTE: When submitting jobs to Cori we see that the
                # returned job id has the prefix ''Submitted batch job ' rather than just the job id
                # as returned for other systems (edison, hopper etc.). We remove this unwanted
                # prefix here to ensure that the process and database updates work correctly
                self.task_model.job_id = json_response['jobid'].lstrip('Submitted batch job ')
                self.task_model.number_of_tries += 1
                self.task_model.save()

        print ""
        print job_script
        print ""
        print json_response
        print ""

        return json_response, job_script


class ProcessingTaskExecutionSettings(dict):
    """
    Describe the PBS job parameters and other execution options.

    Supported Keys:

    * `walltime` : #PBS -l walltime= ... : The maximum walltime requested HH:MM:SS
    * `-q` : queue_name : Name of the submit queue
    * `-N` : job_name	Name of job script	Name of job; up to 15 printable, non-whitespace characters
    * `nodes: Number of nodes assigned ot the the job (-l nodes=num_nodes:ppn=tasks_per_node)
    * `-A`: Charge job to repo
    * `-e` : filename <job_name>.e<job_id> Write stderr to filename
    * `-o` :filename <job_name>.o<job_id> Write stdout to filename
    * -j [oe | eo]	Do not merge Merge (join) stdout and stderr.  If oe, merge as output file; ie eo, merge as error file
    * -m [m | b | e | n] Email notification options. Options a, b, e may be combined

        * a=send mail if job aborted by system
        * b=send mail when job begins
        * e=send mail when job ends
        * n=never send email

    * `shell` : shell Login shell Specify shell to interpret batch script
    * `-V` : Do not export. Export current environment variables into the batch job environment
    * 'num_tasks' : The number of parallel tasks to be performed

    Supported Additional Parameter Keys:

    * 'environment` : List of strings to be added to the PBS launch script to setup the environment, e.g., module laod.

    """
    def __init__(self, machine=None):
        """
        Create a ProcessingTaskParameter description using default settings. The
        default settings are defined for carver.

        :param machine: The machine to be used. This is used to define the default settings for the environment.
            If None (default) then machine_backend.DEFAULT_BACKEND_KEY will be used
        """
        super(ProcessingTaskExecutionSettings, self).__init__()
        if machine is None:
            machine = DEFAULT_MACHINE_BACKEND_KEY
        self.backend = MACHINE_BACKENDS[machine]()
        parameters = self.backend.get_default_machine_parameters()
        self.update(parameters)

    def get_error_filename(self, jobid=None):
        """
        Get the name of the error file currently set.

        :param jobid: Replace the symbolic $PBS_JOBID jobid with the given real id. This parameter is optional.
                      Default value is None, in which case the value of the '-e' option is returned unchanged.

        :returns: String of the filename or None.
        """
        if jobid is None:
            return self[self.backend.get_error_filename_parameter_name()]
        else:
            return self[self.backend.get_error_filename_parameter_name()].replace(self.backend.get_jobid_var(), jobid)

    def get_out_filename(self,  jobid=None):
        """
        Get the name of standard out filename currently set.

        :param jobid: Replace the symbolic $PBS_JOBID jobid with the given real id. This parameter is optional.
                      Default value is None, in which case the value of the '-o' option is returned unchanged.

        :returns: String of the filename or None.
        """
        if jobid is None:
            return self[self.backend.get_output_filename_parameter_name()]
        else:
            return self[self.backend.get_output_filename_parameter_name()].replace(self.backend.get_jobid_var(), jobid)

    @classmethod
    def create_error_filename(cls, username, jobid=None, machine=None):
        """
        String indicating the where the error output file is stored.

        :param username: The name of the user running the job
        :type username: str or unicode
        :param jobid: Either the integer of the job id or the string for
                      how the job scheduler variable for getting the id. If
                      None (default), then machine will be used to determine the
                      job id variable.
        :param machine: name of the machine (default=None). Used if jobid is set to None to
                        determine the name the environmnet variable with the job id.

        :return: The name of the file where standard error output should be stored.
        """
        if jobid is None:
            if machine is not None:
                jobid = MACHINE_BACKENDS[machine].get_jobid_var(script_header=True)
            else:
                jobid = ''
        e_fname = username + '_' + unicode(jobid) + '.err'
        return os.path.join(settings.PROCESSING_STATUS_FOLDER, e_fname)

    @classmethod
    def create_out_filename(cls, username, jobid=None, machine=None):
        """
        String indicating where the standard output file is stored.

        :param username: The name of the user running the job
        :type username: str or unicode
        :param jobid: Either the integer of the job id or the string for
                      how the job scheduler variable for getting the id. If
                      None (default), then machine will be used to determine the
                      job id variable.
        :param machine: name of the machine (default=None). Used if jobid is set to None to
                        determine the name the environmnet variable with the job id.

        :return: The name of the file where standard out should be stored.
        """
        if jobid is None:
            if machine is not None:
                jobid = MACHINE_BACKENDS[machine].get_jobid_var(script_header=True)
            else:
                jobid = ''
        o_fname = username + '_' + unicode(jobid) + '.out'
        return os.path.join(settings.PROCESSING_STATUS_FOLDER, o_fname)

    @classmethod
    def create_job_status_filename(cls, username, status, jobid=None, machine=None):
        """
        String indicating the name for job status files.

        :param username: The name of the user running the job
        :type username: str or unicode
        :param status: One of ProcessingTaskModel status values
        :param jobid: Either the integer of the job id or the string for
                      how the job scheduler variable for getting the id
        :param jobid: Either the integer of the job id or the string for
                      how the job scheduler variable for getting the id. If
                      None (default), then machine will be used to determine the
                      job id variable.
        :param machine: name of the machine (default=None). Used if jobid is set to None to
                        determine the name the environmnet variable with the job id.

        :return: The name of the status file
        """
        if jobid is None:
            if machine is not None:
                jobid = MACHINE_BACKENDS[machine].get_jobid_var()
            else:
                jobid = ''
        s_fname = username + '_' + unicode(jobid) + '.status.' + status
        return os.path.join(settings.PROCESSING_STATUS_FOLDER, s_fname)

    @classmethod
    def from_json(cls, json_obj):
        """
        Create a processing task parameter descriptions
        from a JSON dictionary.

        :param json_obj: The json object with the PBS parameters.
        """
        json_dict = json.loads(json_obj)
        return cls.from_dict(dict_obj=json_dict)

    @classmethod
    def from_dict(cls, dict_obj):
        """
        Create a processing task parameter desription object
        from a given dict.

        :param dict_obj: The python dict object
        """
        try:
            machine = dict_obj['machine']
        except KeyError:
            machine = DEFAULT_MACHINE_BACKEND_KEY
        task_param = ProcessingTaskExecutionSettings(machine=machine)
        task_param.update(dict_obj)
        return task_param

    def to_json(self):
        """
        Convert the dict to json.
        """
        return json.dumps(self)

    def to_job_script(self, job_command, username):
        """
        Convert the dict to a PBS or SLURM job parameter script.

        :param job_command: The actual command to be run
        :type job_command: str or unicode
        :param username: The name of the user running the job
        :type username: str or unicode

        :return: String with the PBS or SLURM job script, depending on the machine
        """
        # Convert the base parameters (e.g., shell, PBS settings etc. to a base script with shell script)
        job_script = self.backend.create_job_script_environment(execution_settings=self)
        # NOTE: If we need to put something in the script-header than the default name for the output files
        #       may be different than what is stored in the following two variables.
        default_standard_out_file = self.backend.get_default_standard_out(script_header=False)
        default_error_out_file = self.backend.get_default_error_out(script_header=False)

        def permission_string(filenname):
            """
            Internal helper function to create the command to update the permissions for
            a given file so that the OpenMSI can read the file and so that APACHE can
            read the file.

            :param filenname: The name of the file (i.e, full path)
            :type filenname: str or unicode
            """
            status_string = "chgrp m1541 " + filenname + "\n"
            status_string += "chmod 770 " + filenname + "\n"
            status_string += "setfacl -R -m u:48:rwx " + filenname + "\n"
            return status_string

        # Create file indicating the job has started
        job_script += "\n"
        job_script += "# Create job status file indicating that the job is running and set permissions for the file \n"
        job_status_file_running = self.create_job_status_filename(username=username,
                                                                  status=ProcessingTaskModel.STATUS_RUNNING,
                                                                  machine=self.get_machine())
        job_script += 'echo running > ' + job_status_file_running + "\n"
        job_script += permission_string(filenname=job_status_file_running)

        # Set the file permissions for the error and out files to make sure we can read them
        job_script += "\n"
        job_script += "# Set permissions for the system out and error files  \n"
        job_script += permission_string(filenname=default_error_out_file)
        job_script += permission_string(filenname=default_standard_out_file)

        # Create a link to the job error and out files where we expect them to be
        if not isinstance(self.backend, slurm_scheduler_machine):
            if self.get_error_filename() is not None or self.get_out_filename() is not None:
                job_script += "\n"
                job_script += "# Add links to custom error/out file target locations if applicable. \n"
                job_script += "# This is needed to allow read of the files before the job-script is completed. \n"
                if self.get_error_filename() is not None:
                    job_script += "ln -s %s %s\n" % (default_error_out_file, self.get_error_filename())
                if self.get_out_filename() is not None:
                    job_script += "ln -s %s %s\n" % (default_standard_out_file, self.get_out_filename())

        # Setup the environment for the script
        job_script += "\n"
        job_script += "# Setup the compute environment \n"
        for env in self['environment']:
            job_script += env + "\n"

        # Set the job launch parameters
        job_script += "\n"
        job_script += "# Execute the job \n"
        job_script += self.backend.create_launch_command(job_command=job_command,
                                                         machine_parameters=self)
        job_script += "\n"

        # Update the job status file, i.e., create a new file to indicate the job is complete and delete the running
        job_script += "\n"
        job_script += "# Update the job status file from running to complete " + \
                      "(create new file, set permissions and remove old file).\n"
        job_status_file_complete = self.create_job_status_filename(username=username,
                                                                   status=ProcessingTaskModel.STATUS_COMPLETE,
                                                                   machine=self.get_machine())

        job_script += 'echo complete > ' + job_status_file_complete + "\n"
        job_script += permission_string(filenname=job_status_file_complete)
        job_script += 'rm ' + job_status_file_running + "\n"

        # Delete the symlinks we created for the job error and out files to ensure the files are copied correctly
        # Create a link to the job error and out files where we expect them to be
        if not isinstance(self.backend, slurm_scheduler_machine):
            if self.get_error_filename() is not None or self.get_out_filename() is not None:
                job_script += "\n"
                job_script += "# Remove links to custom error/out file target locations if applicable. \n"
                if self.get_error_filename() is not None:
                    job_script += "rm " + self.get_error_filename() + "\n"
                if self.get_out_filename() is not None:
                    job_script += "rm " + self.get_out_filename() + "\n"

        # Return the completed job script
        return job_script

    def get_machine(self):
        """
        Get the name of the machine backend
        :return: String with the machine backend name
        """
        return self.backend.get_machine_name()

    def add_environment_option(self, option):
        """
        Add a new parameter to the environment.

        :param option: String to be included with the PBS job launch script to setup the environment.
        :type option: str

        """
        if 'environment' not in self.keys():
            self['environment'] = []
        self['environment'].append(option)

    def set_environment(self, environment):
        """
        Define the setup of the execution environment.

        :param environment: List of strings, each of which is a command to be executed to setup the
                            environment, e.g., module load commands, setting of paths etc.

        """
        self['environment'] = environment


class ProcessingTaskDescription(dict):
    """
    Describe the actual task.

    Supported Keys:

    * `job_runner` : E.g. `python` to run a python script, `./` to run an executable etc.
    * `main_name` : Name and path to the script to be executed
    * `params` : List of dicts with the parameters to be given to the script.
                 Each dict may contain multiple key:value pairs which can
                 appear in arbitrary order on the command line.
    * `param_assign` : Assignment operator to be used on the command line.
                 Default value is ' '

    """

    def __init__(self):
        super(ProcessingTaskDescription, self).__init__()
        self['params'] = []
        self['main_name'] = None
        self['job_runner'] = 'python'
        self['param_assign'] = ' '

    def to_json(self):
        """
        Convert the dict to json.
        """
        return json.dumps(self)

    @classmethod
    def from_json(cls, json_obj):
        """
        Create a processing task description
        from a JSON dictionary.

        :param json_obj: The json object with the job description.
        """
        json_dict = json.loads(json_obj)
        task_description = ProcessingTaskDescription()
        task_description.update(json_dict)
        return task_description

    @classmethod
    def from_dict(cls, dict_obj):
        """
        Create a processing task description object
        from a given dict.

        :param dict_obj: The python dict object
        """
        task_description = ProcessingTaskDescription()
        task_description.update(dict_obj)
        return task_description

    def get_command(self):
        """
        Generate the basic command to be run to execute the given task.
        I.e., the basic command and input parameters.
        """
        # Add the job runner
        cmd = ""
        if self['job_runner'] is not None:
            cmd += self['job_runner'] + " "
        # Add the main name
        if self['main_name'] is not None:
            cmd += self['main_name']
        # Add all parameters
        sep = unicode(self['param_assign'])
        for params in self['params']:
            for parma_key, param_value in params.iteritems():
                cmd += " "+unicode(parma_key)
                if len(param_value) > 0:
                    cmd += sep + unicode(param_value)
        # Return the completed command
        return cmd


#######################################################
#      Models for managing data processing jobs       #
#######################################################
class ProcessingTaskModel(models.Model):
    """
    Model for describing and monitoring a single data processing task.
    """
    # The user who created the task
    task_user = models.ForeignKey(User,
                                  null=False,
                                  blank=False,
                                  related_name="processing_task_user",
                                  verbose_name="User that initiated the processing task.")
    # Date when the task was created
    created_date = models.DateTimeField(auto_now_add=True,
                                        editable=True)
    # Date when the task was last updated
    last_update_date = models.DateTimeField(auto_now=True,
                                            editable=True)
    # JSON with the description of the actual task to be executed
    task_description = JSONField(verbose_name='JSON with the description of the actual task',
                                 validators=[JSONField.validate_json_serializable],
                                 null=False,
                                 blank=False,
                                 editable=True)
    # JSON with the description of the execution parameters
    execution_settings = JSONField(verbose_name='JSON dict with the execution parameters, e.g., PBS.',
                                   validators=[JSONField.validate_json_serializable],
                                   null=False,
                                   blank=False,
                                   editable=True,
                                   default=ProcessingTaskExecutionSettings().to_json())
    # Wall time used in seconds
    wall_time_used = models.IntegerField(null=True,
                                         blank=True,
                                         verbose_name="Wall time used in seconds",
                                         editable=True)
    # Start time
    start_time = models.TimeField(null=True,
                                  blank=True,
                                  verbose_name="Time when the job started",
                                  editable=True)

    # Completion time
    completion_time = models.TimeField(null=True,
                                       blank=True,
                                       verbose_name="Time when the job started",
                                       editable=True)

    # The type of job that is executed
    TASK_TYPE_CONVERT = 'c'
    TASK_TYPE_ANALYSIS = 'a'
    TASK_TYPE_CHOICES = (
        (TASK_TYPE_CONVERT, 'Convert a set of raw files to the OpenMSI file format.'),
        (TASK_TYPE_ANALYSIS, 'Generate a new analysis.')
    )
    task_type = models.CharField(max_length=40,
                                 choices=TASK_TYPE_CHOICES,
                                 default=TASK_TYPE_ANALYSIS,
                                 editable=True)

    # The job id as indicated by the job submission system
    job_id = models.CharField(verbose_name='The job id from the scheduler',
                              max_length=40,
                              default=None,
                              null=True,
                              editable=True,
                              blank=True,
                              unique=True)
    # The execution status of the job
    STATUS_READY = 'g'
    STATUS_WAIT_FOR_OTHERS = 'w'
    STATUS_QUEUED = 'q'
    STATUS_RUNNING = 'r'
    STATUS_ERROR = 'e'
    STATUS_COMPLETE = 'c'
    STATUS_CHOICES = (
        (STATUS_READY, 'ready to run'),
        (STATUS_WAIT_FOR_OTHERS, 'wait for previous jobs'),
        (STATUS_QUEUED, 'queued'),
        (STATUS_RUNNING, 'running'),
        (STATUS_ERROR, 'error'),
        (STATUS_COMPLETE, 'complete')
    )
    status = models.CharField(max_length=40,
                              choices=STATUS_CHOICES,
                              default=STATUS_READY,
                              editable=True)

    # How often did we try to execute this task
    number_of_tries = models.IntegerField(verbose_name='Number of attempts to complete the job',
                                          editable=True,
                                          default=0)
    # Are there other tasks that need to complete before this task can be run
    task_dependencies = models.ManyToManyField('ProcessingTaskModel',
                                               related_name='dependent_tasks',
                                               verbose_name='Tasks that need to complete before this task can run.',
                                               blank=True,
                                               editable=True)
    # Which OpenMSI files are created by this task
    omsi_file_create = JSONField(verbose_name='List of files created by the task.',
                                 validators=[JSONField.validate_json_serializable],
                                 null=True,
                                 blank=True,
                                 editable=True,
                                 default=None)
    # Which OpenMSI files are updated/modified by this task
    omsi_file_update = models.ManyToManyField('omsi_resources.FileModelOmsi',
                                              related_name='update_tasks',
                                              verbose_name='Omsi files modified by the task',
                                              blank=True,
                                              editable=True)
    # Which OpenMSI files are read by this task
    omsi_file_read = models.ManyToManyField('omsi_resources.FileModelOmsi',
                                            related_name='read_tasks',
                                            verbose_name='Omsi files used in read-mode by the task',
                                            blank=True,
                                            editable=True)
    # Which raw files are updated/edited by this task
    rawfile_update = models.ManyToManyField('omsi_resources.FileModelRaw',
                                            related_name='update_tasks',
                                            verbose_name='Raw files modified by the task',
                                            blank=True,
                                            editable=True)
    # Which raw files are read by this task
    rawfile_read = models.ManyToManyField('omsi_resources.FileModelRaw',
                                          related_name='read_tasks',
                                          verbose_name='Raw files used in read-mode by the task',
                                          blank=True,
                                          editable=True)

    class Meta:
        """Define custom display metadata fro the admin page"""
        verbose_name = "Processing Task"
        verbose_name_plural = "Processing Tasks"

    def check_status(self, request=None, showstart=False):
        """
        Use this function to check the status of the task. The function
        may update the self.status field in case the status has
        changed

        :param request: Optional DJANGO request object needed if the function
                        should also check the newt update status (e.g, if a
                        job is in the QUEUE)
        :param showstart: Boolean indicating whether we should also check for
                        the estimated time when the job is going to start if
                        the job is still in the queue. This may take additional time.
        :type showstart: bool

        """
        # 1) If we are waiting for other jobs, then check if they all completed
        #    and update the status accordingly
        newt_status = None
        newt_session_id = NEWT.get_session_id(request)
        if self.task_dependencies.count() > 0:
            if self.status == self.STATUS_WAIT_FOR_OTHERS:
                ready = True
                for deptask in self.task_dependencies.all():
                    dep_status, dep_newt_status = deptask.check_status()
                    ready &= (dep_status == self.STATUS_COMPLETE)
                if ready:
                    self.status = self.STATUS_READY
                    self.save()
        if self.status in [self.STATUS_QUEUED, self.STATUS_RUNNING]:
            task_params = ProcessingTaskExecutionSettings.from_dict(self.execution_settings)
            # Try to get a job update from NEWT using qstat
            if newt_session_id is not None:
                response = NEWT.job_status(session_id=newt_session_id,
                                           job_id=self.job_id,
                                           machine_name=task_params.get_machine())
                try:
                    job_status = response.json()
                except ValueError:  # NEWT may not always return a json that can be decoded
                    job_status = None
            else:
                job_status = None
            newt_status = job_status
            # Try to get a job update based on job files
            file_status = None
            status_file_running = ProcessingTaskExecutionSettings.\
                create_job_status_filename(username=self.task_user.username,
                                           jobid=self.job_id,
                                           status=self.STATUS_RUNNING,
                                           machine=task_params.get_machine())
            status_file_complete = ProcessingTaskExecutionSettings.\
                create_job_status_filename(username=self.task_user.username,
                                           jobid=self.job_id,
                                           status=self.STATUS_COMPLETE,
                                           machine=task_params.get_machine())
            status_file_error = ProcessingTaskExecutionSettings.\
                create_job_status_filename(username=self.task_user.username,
                                           jobid=self.job_id,
                                           status=self.STATUS_ERROR,
                                           machine=task_params.get_machine())
            if os.path.exists(status_file_running):
                file_status = self.STATUS_RUNNING
                # os.remove(status_file_running)  # Can't do this on read-only project file system
            if os.path.exists(status_file_complete):
                file_status = self.STATUS_COMPLETE
                # os.remove(status_file_complete)  # Can't do this on read-only project file system
            if os.path.exists(status_file_error):
                file_status = self.STATUS_ERROR

            # If we only have information from qstat, update the status
            if (job_status is not None) and (file_status is None):
                self.status_message = unicode(job_status)
                if job_status['status'] == 'Q':
                    self.status = self.STATUS_QUEUED
                elif job_status['status'] == 'C':
                    self.status = self.STATUS_COMPLETE
                elif job_status['status'] == 'R':
                    self.status = self.STATUS_RUNNING
                elif job_status['status'] == 'ERROR':
                    if self.status == self.STATUS_RUNNING and \
                            job_status['error'] == "'qstat did not return output'":
                        self.status = self.STATUS_ERROR
            # We only have information from the files
            elif (file_status is not None) and (job_status is None):
                self.status = file_status
            # We have information from both NEWT and the status files
            elif (file_status is not None) and (job_status is not None):
                self.status_message = unicode(job_status)
                if job_status['status'] == 'Q':
                    self.status = self.STATUS_QUEUED
                elif job_status['status'] == 'C' and file_status == self.STATUS_RUNNING:
                    self.status = self.STATUS_ERROR
                elif job_status['status'] == 'C' and file_status == self.STATUS_ERROR:
                    self.status = self.STATUS_ERROR
                elif job_status['status'] == 'C' and file_status == self.STATUS_COMPLETE:
                    self.status = self.STATUS_COMPLETE
                elif job_status['status'] == 'R':
                    self.status = self.STATUS_RUNNING
                elif job_status['status'] == 'ERROR':
                    self.status = file_status
            # Save the updated status
            self.save()

            # If the job is in the queue then try to determine the start time
            if self.status == self.STATUS_QUEUED and showstart:
                response = NEWT.job_showstart(session_id=newt_session_id,
                                              job_id=self.job_id,
                                              machine_name=task_params.get_machine())
                try:
                    job_start = response.json()
                except ValueError:  # NEWT may not always return a json that can be decoded
                    job_start = None
                if newt_status is None:
                    newt_status = job_start
                elif job_start is not None:
                    newt_status['showstart'] = job_start['output']

        # If the job is complete and we have not read the information from the NERSC job database
        if self.status == self.STATUS_COMPLETE and newt_session_id is not None:
            if not self.start_time:  # Try to read the status error file
                job_status = NEWT.completed_info_for_job(session_id=newt_session_id,
                                                         username=request.user.username,
                                                         jobid=self.job_id)

                if job_status:
                    print job_status
                    self.completion_time = datetime.datetime.fromtimestamp(int(job_status['completionunix'])).strftime('%a %b %d %H:%M:%S %Z %Y')
                    self.wall_time_used = job_status['wallclock']*60.*60.
                    self.start_time = time.strptime(job_status['starttime'].replace("/", " "), '%d %m %y %H:%M')
                    self.save()

        # 2) Return the current status
        return self.status, newt_status

    def get_status_message(self):
        """
        Read the error and out files generated by the job and update the model.
        """
        # 4.1 Compute the list of status files to be investigated
        task_exec_settings = ProcessingTaskExecutionSettings.from_dict(self.execution_settings)
        error_filename = task_exec_settings.get_error_filename(jobid=self.job_id)
        out_filename = task_exec_settings.get_out_filename(jobid=self.job_id)
        status_filelist = [error_filename, out_filename]
        # 4.2 Get the current status message
        status_text = ""

        # Read the error file
        file_size_limit = 10485760  # Size limit set to 10MB
        if error_filename not in status_text:
            if error_filename is not None and os.path.exists(error_filename):
                status_text += "------------------------------- \n"
                status_text += "File:" + unicode(error_filename) + " \n"
                status_text += "------------------------------- \n"
                curr_filesize = os.stat(error_filename).st_size
                if file_size_limit > curr_filesize > 0:
                    try:
                        error_file = open(error_filename)
                        status_text += error_file.read()
                        error_file.close()
                    except IOError:
                        status_text += "IOError while trying to read the error file."
                else:
                    status_text += "Error file > %i bytes." % curr_filesize

        if out_filename not in status_text:
            if out_filename is not None and os.path.exists(out_filename):
                status_text += "------------------------------- \n"
                status_text += "File:" + unicode(out_filename) + " \n"
                status_text += "------------------------------- \n"
                curr_filesize = os.stat(out_filename).st_size
                if file_size_limit > curr_filesize > 0:
                    try:
                        out_file = open(out_filename)
                        status_text += out_file.read()
                        out_file.close()
                    except IOError:
                        status_text += "IOError while trying to read the out file."
                else:
                    status_text += "Out file > %i bytes." % curr_filesize

        return status_text

    def __unicode__(self):
        """Define the display name for the model object"""
        name = unicode(self.task_user.username) + "__" + unicode(self.job_id)
        return name

    def delete_from_queue(self, newt_session_id):
        """
        Call this function whenever model instance is deleted. The function
        is used to delete associated jobs from the queue to ensure the jobs
        is not running after the model has been deleted.

        :param newt_session_id: The NEWT session id
        """
        cur_status, _ = self.check_status()
        if cur_status in [ProcessingTaskModel.STATUS_QUEUED, ProcessingTaskModel.STATUS_RUNNING]:
            if newt_session_id is not None:
                machine_name = ProcessingTaskExecutionSettings.from_dict(self.execution_settings).get_machine()
                response = NEWT.delete_job(session_id=newt_session_id,
                                           job_id=self.job_id,
                                           machine_name=machine_name)
                try:
                    job_status = response.json()
                except ValueError:  # NEWT may not always return a json that can be decoded
                    job_status = None
                # Raise error if the deletion of the job failed
                if job_status is None:
                    raise ValueError('Deletion of job from the queue failed.')
                elif job_status is not None and job_status['status'] == 'ERROR':
                    raise ValueError('Deletion of job from the queue failed. '+str(job_status))
                return job_status
            else:
                raise ValueError("NEWT Session id required to delete the task")
        else:
            return {'status': 'OK', 'output': '', 'error': ''}





    #def retry_after_error(self):
    #    """
    #    Try to run the job again after an error has occurred
    #    """
    #    if self.status == self.STATUS_ERROR:
    #        if not self.status_message:
    #            self.status_message = "-------------------Retry------------------\n"
    #        else:
    #            self.status_message += "\n-------------------Retry------------------\n"
    #        self.status = self.STATUS_WAIT_FOR_OTHERS  # Reschedule the job
    #        self.number_of_tries += 1  # Update the number of tries
    #        self.save()  # Save the model
    #        self.check_status()  # Update the status to ready if possible



#class rawfile_processing_task_model(ProcessingTaskModel):
#    """
#    Task for processing of raw data files
#    """
#    uses_rawfiles = models.ManyToManyField

#!/bin/bash \n#PBS -A=m1541\n#PBS -N=omsi_user_job\n#PBS -S=/bin/bash\n#PBS -l walltime=02:00:00\n#PBS -e=/project/projectdirs/openmsi/omsi_processing_status/oruebel_$PBS_JOBID.err\n#PBS -o=/project/projectdirs/openmsi/omsi_processing_status/oruebel_$PBS_JOBID.out\n#PBS -q=serial\n\ncd $PBS_O_WORKDIR \nmodule load h5py\nmodule load python\nexport PYTHONPATH=/project/projectdirs/openmsi/devel/openmsi-tk:$PYTHONPATH\n\npython /project/projectdirs/openmsi/devel/openmsi-tk/omsi/tools/convertToOMSI.py --add-to-db --no-xdmf --fpl --fpg --regions merge --db-server http://127.0.0.1:8000/ --compression --thumbnail --email oruebel@lbl.gov bpbowen@lbl.gov --auto-chunking --nmf --error-handling terminate-and-cleanup --owner oruebel /Users/oruebel/Devel/openmsi-data/rawdata/oruebel/20120711_Brain /project/projectdirs/openmsi/omsi_data_private/oruebel/20120711_Brain.h5
