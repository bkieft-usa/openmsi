"""

"""
# DONE: Implemented jobs function
# DONE: Added support to resubmit a job using the update function
# DONE: Added functionality to delete a job, including the delete from the job queue


# TODO: Allow a fast check_job_status that uses only the status files but does not use NEWT to update job status. This would allow a fast job update.
# TODO: From the PBS output files parse out the memory usage, timings, and other job info to be stored in the database
# TODO: Check if file with the same name already exists before submitting the job and set the omsi update field instead of the omsi create field
# TODO: Allow users to define the output filename when submitting jobs
# TODO: Define module loads for the different machines at NERSC (different version of h5py etc.)
# TODO: Allow the use of edison and hopper serial queues
# TODO: Why does from omsi_resources.models import * work but not import FileModelRaw?
# TODO: When a job finishes we need to use the opportunity to schedule jobs for the user in the PBS script since we may not have a NEWT token on our end anymore
# TODO: When a user logs in we should check in the background if there are jobs that we need to submit for them

from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.http import HttpResponse, \
                        HttpResponseBadRequest, \
                        HttpResponseNotFound, \
                        HttpResponseRedirect, \
                        HttpResponseForbidden
from omsi.dataformat.omsi_file.main_file import omsi_file
try:
    from omsi_server.omsi_processing.models import *
    from omsi_server.omsi_resources import omsi_file_authorization
    from omsi_server.omsi_resources.models import *
    from omsi_server.omsi_access import views_helper
    from omsi_server.omsi_server.newt_auth_backend import NEWT
    from omsi_server.omsi_processing.machine_backend import BACKENDS as MACHINE_BACKENDS
    from omsi_server.omsi_processing.machine_backend import DEFAULT_BACKEND_KEY as DEFAULT_MACHINE_BACKEND_KEY
except ImportError:
    from omsi_processing.models import *
    from omsi_resources import omsi_file_authorization
    from omsi_resources.models import *
    # from omsi_resources.models import FileModelRaw
    from omsi_access import views_helper
    from omsi_server.newt_auth_backend import NEWT
    from omsi_processing.machine_backend import BACKENDS as MACHINE_BACKENDS
    from omsi_processing.machine_backend import DEFAULT_BACKEND_KEY as DEFAULT_MACHINE_BACKEND_KEY
try:
    import json
except ImportError:
    from django.utils import simplejson as json
import sys
import os
from django.contrib.auth.models import User
from django.conf import settings
import math
import ast

import warnings
import logging
logger = logging.getLogger(__name__)


def convert(request):
    """
    View for creating processing tasks to convert raw data files and
    import them into the database. NOTE: The output name of the data file
    and its location are automatically determined by the system based on
    the name of the input filename/folder and the user that submitted the job.

    :param request: The django request object

    **Required query arguments:**

          * `file#` : The full path to the file to be converted. If only a single file is given, then
                      the key `file` without an index may also be used. Otherwise an index must be
                      assigned to each file that should be converted and stored in the same file.
                      Note, indices must be consecutive starting with 0. This important as in the case
                      that file0 and file4 appear in the query-string but not file2 and file3, then only
                      file0 would be identified and converted.
    **Optional query arguments
          * `outfile` : Name of the output HDF5 file. Set automatically based on the input filename(s) if missing.
          * `methods`: JSON dictionary with the description of the experiment methods
          * `instrument`: JSON dictionary with the description of the instrument and data instrument settings etc.
          * `notes`: JSON dictionary with additional user notes about the data
          * `nmf` : Boolean or integer indicating whether NMF should be run
          * `fpg` : Boolean or integer indicating whether global peak finding should be performed
          * `fpl` : Boolean or integer indicating whether local peak finding should be performed
          * `ticnorm` : Boolean or integer indicating whether tic normalization should be performed
          * `email` : Boolean or integer indicating whether the user should receive email upon success or failure via
          * `methods` :  JSON describing the methods for the experiment as a while (across all files listed)
          * `methods#` : JSON describing the methods for the dataset in file with index #. (entry_#/data_#/methods)
          * `instrument` : JSON describing the instrument for the experiment as a whole (across all files listed)
          * `instrument#` : JSON describing the instrument for the file with index # (entry_x/data_#/instrument)
          * `notes` : JSON with notes for the experiment as a while (across all files listed)
          * `notes#` : JSON with notes for the file with index #.

    """
    if (NEWT.get_session_id(request) is None) or (not request.user.is_authenticated()):
        return HttpResponseRedirect(settings.LOGIN_URL+"?next="+request.get_full_path())

    logger.debug('Entering convert view')
    # 1) Parse the query-string parameters
    # 1.1) Get required query string parameters
    try:
        fileindex = 0
        raw_files = []
        while True:
            currfile = request.GET.get('file'+str(fileindex), None)
            if currfile is not None:
                raw_files.append(currfile)
                fileindex += 1
            else:
                break
        if len(raw_files) == 0:
            raw_files.append(request.GET['file'])
    except KeyError:
        if settings.DEBUG:
            raise
        else:
            return HttpResponseBadRequest("A required query parameter could not be read. "+str(sys.exc_info()))

    # 1.2) Get additional query-string parameters
    # 1.2.1) Analysis parameters
    execute_nmf = value_to_bool(request.GET.get('nmf', False))
    execute_fpg = value_to_bool(request.GET.get('fpg', False))
    execute_fpl = value_to_bool(request.GET.get('fpl', False))
    execute_ticnorm = value_to_bool(request.GET.get('ticnorm', False))
    send_user_email = value_to_bool(request.GET.get('email', True))
    # 1.2.2) Metadata parameters
    methods_metadata = {}
    instrument_metadata = {}
    notes_metadata = {}
    if request.GET.get('methods', None) is not None:
        methods_metadata['methods'] = request.GET['methods']
    if request.GET.get('instrument', None) is not None:
        instrument_metadata['instrument'] = request.GET['instrument']
    if request.GET.get('notes', None) is not None:
        notes_metadata['notes'] = request.GET['notes']
    for mindex in range(len(raw_files)):
        mkey = 'methods'+str(mindex)
        ikey = 'instrument'+str(mindex)
        nkey = 'notes'+str(mindex)
        if request.GET.get(mkey, None) is not None:
            methods_metadata[mkey] = request.GET[mkey]
        if request.GET.get(ikey, None) is not None:
            instrument_metadata[ikey] = request.GET[ikey]
        if request.GET.get(nkey, None) is not None:
            notes_metadata[nkey] = request.GET[nkey]
    # 1.2.3 Optional output filename
    outfilename = request.GET.get('outfile', None)

    # 2) Authorize the operation for all raw files listed and create database models for the raw files as needed
    raw_filename_list = []
    raw_filemodel_list = []
    for rf in raw_files:
        # 2.1) Authorize the access to the file
        raw_filename, raw_filemodel, raw_filetype = omsi_file_authorization.authorize_fileaccess(
            request=request,
            infilename=rf,
            accesstype=omsi_file_authorization.g_access_types['view'],
            check_omsi_files=False,
            check_raw_files=True)
        # 2.2)  Return in case the file does not exist or the user does not have permissions
        if isinstance(raw_filename, HttpResponse):
            return raw_filename
        # 2.3) Make sure that acl permissions are set properly
        newt_session_id = NEWT.get_session_id(request)
        if newt_session_id:
            # Try multiple machines to execute the command in case
            acl_command = "setfacl -R -m u:48:rwx " + '"' + raw_filename + '"'
            machine_list = MACHINE_BACKENDS.keys()   #  ['carver', 'edison', 'hopper', 'cori']
            for machine_name in machine_list:
                acl_response = NEWT.run_command(session_id=newt_session_id,
                                                machine_name=machine_name,
                                                command=acl_command)
                try:
                    acl_success = (acl_response.json()['status'] == 'OK')
                except:
                    acl_success = False
                if acl_success:
                    break

        # 2.3) Create a new database model for the raw data file in the database
        if raw_filemodel is None:
            raw_filemodel = FileModelRaw(path=raw_filename)
            raw_filemodel.save()
            raw_filemodel.owner_users.add(request.user)
            FileModelRaw.status = FileModelRaw.CONVERSION_IN_PROGRESS
            raw_filemodel.save()
        raw_filename_list.append(raw_filename)
        raw_filemodel_list.append(raw_filemodel)

        # 2.4) Try to update the file reader for the model if necessary
        if not raw_filemodel.format_reader:
            try:
                raw_filemodel.__update_file_format__()
            except:
                pass

    # Define the machine and backend we need to use
    machine = DEFAULT_MACHINE_BACKEND_KEY  # 'cori'  # 'edison'
    backend_class = MACHINE_BACKENDS[machine]

    # 4) Create the description of the file conversion task
    task_description = ProcessingTaskDescription()
    task_description['job_runner'] = 'python'
    task_description['main_name'] = os.path.join(settings.BASTET_PROCESSING_PATH, 'omsi/tools/convertToOMSI.py')
    task_description['param_assign'] = ' '
    # 4.2 Set the script parameters
    task_description['params'] = [{'--error-handling': 'terminate-and-cleanup',     # clean up in case of error
                                   '--email': 'oruebel@lbl.gov bpbowen@lbl.gov',   # notify the openmsi team
                                   '--regions': 'merge',
                                   '--auto-chunking': '',
                                   '--compression': '',
                                   '--add-to-db': '',
                                   '--db-server': settings.API_ROOT.lstrip('openmsi/'),
                                   '--user': request.user.username,
                                   '--jobid': backend_class.get_jobid_var(), # Set the job ID directly. Alternatively
                                                                      # we can set jobid to 'auto' to have the script
                                                                      # discover the value from the environment.
                                   '--thumbnail': '',
                                   '--no-xdmf': ''}]
    # 4.3  Notify the user
    if send_user_email:
        if request.user.email:
            if '--email' in task_description['params'][0]:
                task_description['params'][0]['--email'] += ' ' + request.user.email
            else:
                task_description['params'][0]['--email'] += request.user.email
        else:
            send_user_email = False
    # 4.2 Define the file reader to be used if known
    # if raw_filemodel.format_reader:
    #     task_description['params'][0]['--format'] = unicode(raw_filemodel.format_reader.format)

    # 4.4 Set the options for the various analyses
    if execute_fpg:
        task_description['params'][0]['--fpg'] = ''
    else:
        task_description['params'][0]['--no-fpg'] = ''
    if execute_nmf:
        task_description['params'][0]['--nmf'] = ''
    else:
        task_description['params'][0]['--no-nmf'] = ''
    if execute_fpl:
        task_description['params'][0]['--fpl'] = ''
    else:
        task_description['params'][0]['--no-fpl'] = ''
    if execute_ticnorm:
        task_description['params'][0]['--ticnorm'] = ''
    else:
        task_description['params'][0]['--no-ticnorm'] = ''
    for mkey, mval in methods_metadata.iteritems():
        task_description['params'][0]['--'+mkey] = "'" + mval + "'"
    for ikey, ival in instrument_metadata.iteritems():
        task_description['params'][0]['--'+ikey] = "'" + ival + "'"
    for nkey, nval in notes_metadata.iteritems():
        task_description['params'][0]['--'+nkey] = "'" + nval + "'"

    # 4.6 Add the file to be converted to the command line
    for raw_filename in raw_filename_list:
        tempkey = '"'+raw_filename+'"'  # make sure everything works in case the filename has spaces
        task_description['params'].append({tempkey: ''})

    # 4.7 Define the output HDF5 file
    outpath = ""
    if len(settings.SYSTEM_USER_PRIVATEDATAPATHS) > 0:
        outpath = settings.SYSTEM_USER_PRIVATEDATAPATHS[0]
        outpath = os.path.join(outpath, request.user.username)
    if outfilename is None:
        outfilename = os.path.splitext(os.path.basename(raw_filename_list[0]))[0]
        if len(raw_filename_list) > 1:
            outfilename += "_multifile_"+str(len(raw_filename_list))
    if not outfilename.endswith('.h5'):
        outfilename += '.h5'
    outpath = os.path.join(outpath, outfilename)
    task_outpath = '"' + outpath + '"'  # Add quotes to deal with spaces in the filename
    task_description['params'].append({task_outpath: ''})

    # 5) Define the execution settings for the file conversion. We use default settings right now.
    task_execution_settings = ProcessingTaskExecutionSettings(machine=machine)

    # 5.1.1) Check the memory requirement for the file convert
    file_memory_size = None
    try:
        for fm in raw_filemodel_list:
            if fm.format_reader:
                format_reader = fm.format_reader.get_format_reader()
                try:
                    format_size = format_reader.size(name=fm.path)
                except TypeError:  # TODO: The mzml reader fails at times. Ensure the convert gets scheduled even if size estimate fails
                    continue
                if file_memory_size is None or file_memory_size < format_size:
                    file_memory_size = format_size
    except:
        warnings.warn('Could not determine size of file for conversion' + str(sys.exc_info()))

    # 5) Define the queue, walltime, memory etc. settings for the given machine (hopper,cori,edison,carver)
    task_execution_settings = backend_class.set_queue_and_time(task_execution_settings=task_execution_settings,
                                                               memory_size=file_memory_size)

    # 6) Create the database model of the new processing task
    filetask = ProcessingTaskModel()
    filetask.task_description = task_description  # Note: The database model JSONField serializes the object to JSON
    filetask.execution_settings = task_execution_settings  # Note: JSONField serializes the object to JSON
    filetask.task_user = request.user
    filetask.task_type = ProcessingTaskModel.TASK_TYPE_CONVERT
    filetask.save()
    # Create link between the job to the raw files it is going to read
    for rawmodel in raw_filemodel_list:
        filetask.rawfile_read.add(rawmodel)
    # Create a link to the OpenMSI file that is either being generated or updated
    f = FileModelOmsi.objects.filter(path__endswith=outpath)
    if len(f) > 0:
        filetask.omsi_file_update.add(f[0])  # We have updated an existing file
    else:
        filetask. omsi_file_create = [outpath]  # We are creating a new file
    filetask.save()

    # 7) Initiate execution of the job
    taskrunner = ProcessingTaskRunner(task_model=filetask,
                                      newt_session_id=NEWT.get_session_id(request))
    jobstatus, jobscript = taskrunner.submit_job()
    if jobstatus is None:
        jobstatus = {'status': 'ERROR', 'error': 'NEWT did not return a response'}
    elif jobstatus['status'] != 'OK':
        # Try to use the regular instead of the realtime queue instead
        task_execution_settings = backend_class.set_queue_and_time(task_execution_settings=task_execution_settings,
                                                                   queue='regular',
                                                                   memory_size=file_memory_size)
        filetask.execution_settings = task_execution_settings
        filetask.save()
        # Try to resubmit the job
        taskrunner = ProcessingTaskRunner(task_model=filetask,
                                          newt_session_id=NEWT.get_session_id(request))
        jobstatus, jobscript = taskrunner.submit_job()
        if jobstatus is None:
            jobstatus = {'status': 'ERROR', 'error': 'NEWT did not return a response'}

    jobstatus['user_email'] = send_user_email

    # 8) Notify the user that the job has been submitted
    try:
        if send_user_email:
            from omsi.shared.omsi_web_helper import WebHelper
            if jobstatus['status'] == 'OK':
                email_subject = "Submitted job: " + str(jobstatus['jobid'])
                email_body = ''
                if settings.DEBUG:
                    email_body += jobscript
                email_type = 'success'
            else:
                email_subject = "Job submission failed"
                email_body = jobstatus['error'] + u'\n\n'
                if settings.DEBUG:
                    email_body += jobscript
                email_type = 'error'
            email_recipient = [request.user.email]
            with warnings.catch_warnings(record=True) as w:
                WebHelper.send_email(subject=email_subject,
                                     body=email_body,
                                     sender='convert@openmsi.nersc.gov',
                                     email_type=email_type,
                                     email_success_recipients=email_recipient,
                                     email_error_recipients=email_recipient)
                warning_str = ''
                for wm in w:
                    warning_str += unicode(wm) + u'   |   '
            logger.debug('Submit email sent:' + warning_str)
    except:
        logger.debug('Email not send due to error')

    # 9) Return the job status
    return HttpResponse(content=json.dumps(jobstatus),
                        content_type='application/json')


def update(request):
    """
    Submit a job-update.

    :param request: The django request object

    Required query-string arguments:

    * `jobid` : The job identifier string


    Optional query-string arguments:

    * `status` : One of `running` (`r`), `error` (`e`), `complete` (`c`) . If missing then the system will try \
               to update the status in terms of `ready`, `running`, `queued`
    * `showstart` : Boolean indicating whether we should also check for when the job is going to start. \
               This is only relevant if the job is waiting in the queue. Default value is False.
    * `submit` : Boolean indicating whether the job should be submitted. If set to true the job will be submitted if
                 and only if it is either: i) ready but has not been queued yet or ii) has finished with an error.
    * `delete` : Boolean indicating whether the job should be deleted. This is only possible if the job is in the \
                 queue or waiting. We currently do not allow running jobs to be canceled, as this may result in \
                 unintended behavior, e.g., corrupt HDF5 files, that will require complex cleanup. NOTE: The `delete` \
                 option may not be combined with either the `status`, `submit`, or `showstart` option.

    """
    # 1) Retrieve the input parameters
    # 1.1) Get the required querystring parameters
    try:
        jobid = request.GET['jobid']
    except KeyError:
        if settings.DEBUG:
            raise
        else:
            return HttpResponseBadRequest("A required query parameter could not be read. "+str(sys.exc_info()))

    # 1.2) Get optional query string parameters status
    status = request.GET.get('status', None)
    showstart = value_to_bool(request.GET.get('showstart', False))
    submit_if_ready = value_to_bool(request.GET.get('submit', False))
    delete_if_possible = value_to_bool(request.GET.get('delete', False))
    redict = {'jobid': jobid}
    # 1.2.1) Check if any input option collides with the delete option.
    if delete_if_possible and (submit_if_ready or showstart or (status is not None)):
        return HttpResponseBadRequest("A query-parameter is colliding with the delete=true option.")

    # 2) Get the task model object
    task_model = ProcessingTaskModel.objects.get(job_id=jobid)
    if not task_model:
        return HttpResponseNotFound('No job found for jobid '+jobid)

    # 3) Update the status of the job if the request did not indicate one
    precomplete_statuses = [ProcessingTaskModel.STATUS_RUNNING,
                            ProcessingTaskModel.STATUS_QUEUED,
                            ProcessingTaskModel.STATUS_READY,
                            ProcessingTaskModel.STATUS_ERROR]
    if status is None:
        pass
    elif status in ['r', 'running'] and task_model.status in precomplete_statuses:
        task_model.status = ProcessingTaskModel.STATUS_RUNNING
        task_model.save()
    elif status in ['e', 'error'] and task_model.status in precomplete_statuses:
        task_model.status = ProcessingTaskModel.STATUS_ERROR
        task_model.save()
    elif status in ['c', 'complete'] and task_model.status in precomplete_statuses:
        task_model.status = ProcessingTaskModel.STATUS_COMPLETE
        task_model.save()
    elif status in ['r', 'running', 'e', 'error', 'c', 'complete']:
        logger.debug('Status not updated. Current status %s. New status %s' % (task_model.status, status))
    else:
        return HttpResponseBadRequest("Invalid value given for 'status' parameter.")
    # logger.debug("Current task status: " + str(task_model.status))
    task_status, task_newt_status = task_model.check_status(request=request,
                                                            showstart=showstart)
    # logger.debug("New task status " + str(task_status))
    redict['status'] = task_status

    # 3.1 Delete the job if requested/possible
    if delete_if_possible:
        if task_status in [ProcessingTaskModel.STATUS_QUEUED,
                           ProcessingTaskModel.STATUS_READY,
                           ProcessingTaskModel.STATUS_WAIT_FOR_OTHERS]:
            try:
                delete_status = task_model.delete_from_queue(newt_session_id=NEWT.get_session_id(request))
                redict['status'] = delete_status['status']
                redict['message'] = ''
            except ValueError:
                redict['status'] = 'ERROR'
                redict['message'] = unicode(sys.exc_info())
            if redict['status'] == 'OK':
                task_model.delete()
            # Return the result of out delete attemt
            return HttpResponse(content=json.dumps(redict),
                                content_type='application/json')
        else:
            return HttpResponse(content=json.dumps({'status': 'ERROR',
                                                    'output': '',
                                                    'error': 'Cannot delete job due to job status'}))

    # 3.2. Submit the job to the queue if possible
    if task_status in [ProcessingTaskModel.STATUS_READY, ProcessingTaskModel.STATUS_ERROR] and submit_if_ready:
        # 3.2) Forward the user to the login page if they try to submit a job but are not logged in
        if not request.user.is_authenticated():
            return HttpResponseRedirect(settings.LOGIN_URL+"?next="+request.get_full_path())
        # 3.3) Submit the job
        taskrunner = ProcessingTaskRunner(task_model=task_model,
                                          newt_session_id=NEWT.get_session_id(request))
        jobstatus, jobscript = taskrunner.submit_job()
        # 3.4) Update the job status
        task_status, task_newt_status = task_model.check_status(request=request,
                                                                showstart=showstart)

    # 4) Read the status files for the job, save the status message, and delete the status files
    if task_status in [ProcessingTaskModel.STATUS_COMPLETE, ProcessingTaskModel.STATUS_ERROR]:
        redict['message'] = task_model.get_status_message()
    elif task_status in [ProcessingTaskModel.STATUS_RUNNING, ProcessingTaskModel.STATUS_QUEUED]:
        # Check the job status using NEWT
        redict['message'] = task_newt_status
    else:
        redict['message'] = None

    # 5 Create the new openmsi file models in the database if needed
    redict['file_add_success'] = []
    redict['file_add_error'] = []
    # logger.debug('Create filelist ' + str(task_model.omsi_file_create))
    if task_status == ProcessingTaskModel.STATUS_COMPLETE:
        create_filelist = task_model.omsi_file_create
        username = task_model.task_user.username  # request.user.username
        for omsi_new_file in create_filelist:
            try:
                add_omsi_file(request=request,
                              filepath=omsi_new_file,
                              username=username)
                redict['file_add_success'].append(omsi_new_file)
            except ValueError as e:
                redict['file_add_error'].append({'filename:': omsi_new_file, 'error': e.message})

        # 6) TODO Update the models of the OMSI files that are being updated by the task

        # 7 Update the status of raw data files if needed
        if task_model.task_type == ProcessingTaskModel.TASK_TYPE_CONVERT:
            for rawfile in task_model.rawfile_read.all():
                rawfile.status = FileModelRaw.CONVERSION_COMPLETE
                rawfile.save()

    # 8 For all openmsi files modified by the task update the metadata cache
    for updatefile in task_model.omsi_file_update.all():
        update_metadata_cache(filepath=updatefile.path,
                              request=request)

    # 9) Return the job status
    if isinstance(redict, basestring):  # Bug fix to ensure we always return a JSON object not a JSON with a string
        try:
            redict = json.loads(redict)
        except:
            pass
    return HttpResponse(content=json.dumps(redict),
                        content_type='application/json')


def jobs(request):
    """
    Get job information.

    :param request: The django request object

    **Optional query arguments:**

        * `status` : Retrieve all jobs with the given status. Multiple `status` key/value pairs may \
                     be provided in the query-string to retrieve the status for multiple status types \
                     in a single call. Default behavior is to check for all jobs a user has.
                     Available status types are:

            ** `g`, `go`, `ready` : Jobs that are ready to run but have not been scheduled yet
            ** `w`, `wait`, `waiting` : Jobs that are waiting on other jobs
            ** `q` , `queue`, `queued` : Jobs that are waiting in the queue
            ** `r` , `run`, `running` : Jobs that are currently running
            ** `e` , `error` : Jobs that failed due to some error
            ** `c`, `complete` : Jobs that are complete
        * `jobid` : The job identifier string (Optional)
        * `username`: The name of the user for which we request information (Optional). Default value is \
                      the name of the requesting user.
        * status_message: Boolean indicating whether the status message should be included in the request

    """
    # Confirm that the user is authenticated
    if not request.user.is_authenticated():
        return HttpResponseRedirect(settings.LOGIN_URL+"?next="+request.get_full_path())
    username = request.GET.get('username', None)
    jobid = request.GET.get('jobid', None)
    user_given = username is not None
    if not user_given:
        username = request.user.username
    if username != request.user.username:
        if not request.user.is_superuser:
            return HttpResponseForbidden('Only superusers may request information about other users.')

    # Define the list of all possible status types
    status_types = {ProcessingTaskModel.STATUS_READY: [ProcessingTaskModel.STATUS_READY,
                                                       'go',
                                                       'ready'],
                    ProcessingTaskModel.STATUS_WAIT_FOR_OTHERS: [ProcessingTaskModel.STATUS_WAIT_FOR_OTHERS,
                                                                 'wait',
                                                                 'waiting'],
                    ProcessingTaskModel.STATUS_QUEUED: [ProcessingTaskModel.STATUS_QUEUED,
                                                        'queue',
                                                        'queued'],
                    ProcessingTaskModel.STATUS_RUNNING: [ProcessingTaskModel.STATUS_RUNNING,
                                                         'run',
                                                         'running'],
                    ProcessingTaskModel.STATUS_ERROR: [ProcessingTaskModel.STATUS_ERROR,
                                                       'error'],
                    ProcessingTaskModel.STATUS_COMPLETE: [ProcessingTaskModel.STATUS_COMPLETE,
                                                          'complete']}

    # Get all jobs that are relevant to the request
    status_request = request.GET.getlist(key='status',
                                         default=status_types.keys())  # Get list of status types requested
    if request.user.is_superuser and not user_given:
        user_tasks = ProcessingTaskModel.objects.all()  # If we have a superuser allow them to manage all tasks
    else:
        user_tasks = ProcessingTaskModel.objects.filter(task_user__username=username)  # get list of all user's tasks
    if jobid is not None:
        user_tasks = user_tasks.filter(job_id=jobid)
    read_status_message = value_to_bool(request.GET.get('status_message', False))
    selected_tasks = ProcessingTaskModel.objects.none()     # Create an empty list of selected tasks
    # Find all tasks with the given set of status types
    for status in status_request:
        if status in status_types[ProcessingTaskModel.STATUS_READY]:
            selected_tasks = selected_tasks | user_tasks.filter(status=ProcessingTaskModel.STATUS_READY)
        elif status in status_types[ProcessingTaskModel.STATUS_WAIT_FOR_OTHERS]:
            selected_tasks = selected_tasks | user_tasks.filter(status=ProcessingTaskModel.STATUS_WAIT_FOR_OTHERS)
        elif status in status_types[ProcessingTaskModel.STATUS_QUEUED]:
            selected_tasks = selected_tasks | user_tasks.filter(status=ProcessingTaskModel.STATUS_QUEUED)
        elif status in status_types[ProcessingTaskModel.STATUS_RUNNING]:
            selected_tasks = selected_tasks | user_tasks.filter(status=ProcessingTaskModel.STATUS_RUNNING)
        elif status in status_types[ProcessingTaskModel.STATUS_ERROR]:
            selected_tasks = selected_tasks | user_tasks.filter(status=ProcessingTaskModel.STATUS_ERROR)
        elif status in status_types[ProcessingTaskModel.STATUS_COMPLETE]:
            selected_tasks = selected_tasks | user_tasks.filter(status=ProcessingTaskModel.STATUS_COMPLETE)

    # From the list of tasks we have found. Create a response dictionary with the required information
    result_dict = {}
    for task in selected_tasks:
        if task.status == ProcessingTaskModel.STATUS_COMPLETE and not task.start_time:
            pass

        result_dict[task.job_id] = {'job_id': task.job_id,
                                    'task_description': task.task_description,
                                    'execution_settings': task.execution_settings,
                                    'task_type': task.task_type,
                                    'status': task.status,
                                    'status_message': "" if not read_status_message else task.get_status_message(),
                                    'number_of_tries': task.number_of_tries,
                                    'omsi_file_create': task.omsi_file_create,
                                    'omsi_file_update': [f.path for f in task.omsi_file_update.all()],
                                    'omsi_file_read': [f.path for f in task.omsi_file_read.all()],
                                    'rawfile_update': [f.path for f in task.rawfile_update.all()],
                                    'rawfile_read': [f.path for f in task.rawfile_read.all()],
                                    'task_user': task.task_user.username,
                                    'created_time': unicode(task.created_date),
                                    'last_update': unicode(task.last_update_date),
                                    'wall_time_used': task.wall_time_used,
                                    'start_time': task.start_time}
        # Try to safely convert the status message to a python object if possible. This has the
        # advantage that the returned message is well-formated if possible and not just a long python string.
        try:
            result_dict[task.job_id]['status_message'] = ast.literal_eval(result_dict[task.job_id]['status_message'])
        except:
            pass

    # Return the response
    return HttpResponse(content=json.dumps(result_dict),
                        content_type='application/json')


#######################################################
#  Internal helper functions                          #
#######################################################
def add_omsi_file(request, filepath, username):
    """
    Add a new OpenMSI file to the database

    :param request: The DJANGO request object
    :param filepath : The full path to the file
    :param username: The name of the user to which the file should be assigned to

    :raises: ValueError in case that: i) an invalid file is given, ii) username is invalid

    """
    logger.debug("Adding omsi file="+filepath + " user=" + username)
    # 1. Check if the file is valid
    if not os.path.isfile(filepath):
        raise ValueError("Invalid file path given: "+unicode(filepath))
    else:
        try:
            input_file = omsi_file(filepath, 'r')
        except:
            logger.debug("File is not a valid OMSI file"+str(sys.exc_info()))
            raise ValueError("File is not a valid OMSI file"+str(sys.exc_info()))

    # 3. Check if the given file is already in the database
    f = FileModelOmsi.objects.filter(path__endswith=filepath)
    if len(f) > 0:
        logger.debug("File already in the database: "+filepath)

    # 6. Check if the user is in the database
    try:
        user = User.objects.get(username=username)
    except:
        logger.debug("User not registered in the database")
        raise ValueError("User not registered in the database. "+username)

    # 7. Add the file to the database
    if len(f) == 0:
        new_model = FileModelOmsi(path=filepath)
        new_model.save()
        # Associate the owner with the file
        new_model.owner_users.add(user)
        new_model.save()
        logger.debug("Added file to database. file=" + filepath + " user=" + username)

    # 8. Update the metadata cache for the file
    update_metadata_cache(filepath=filepath,
                          request=request,
                          input_file=input_file,
                          force_update=True)

    # 9. Notify the user if necessary
    try:
        if len(f) == 0:
            from omsi.shared.omsi_web_helper import WebHelper
            email_subject = "Added file to DB: " + str(filepath)
            email_body = ''
            email_type = 'success'
            email_recipient = [user.email, "oruebel@lbl.gov", "bpbowen@lbl.gov"]
            with warnings.catch_warnings(record=True) as w:
                WebHelper.send_email(subject=email_subject,
                                     body=email_body,
                                     sender='dbmanager@openmsi.nersc.gov',
                                     email_type=email_type,
                                     email_success_recipients=email_recipient,
                                     email_error_recipients=email_recipient)
                warning_str = ''
                for wm in w:
                    warning_str += unicode(wm) + u'   |   '
            logger.debug('Add to DB email sent:' + warning_str)
    except:
        logger.debug('Add to DB email not send due to error. ' + str(sys.exc_info()))

    # try:
    #     from omsi.shared.omsi_web_helper import WebHelper
    #     email_subject = str(task_status) + " : Updated job status : " + str(task_model.job_id)
    #     email_body = redict['message'] if redict['message'] is not None else ''
    #     email_type = 'success'
    #     email_recipient = [task_model.task_user.email, 'oruebel@lbl.gov']
    #     with warnings.catch_warnings(record=True) as w:
    #         WebHelper.send_email(subject=email_subject,
    #                              body=email_body,
    #                              sender='processmanager@openmsi.nersc.gov',
    #                              email_type=email_type,
    #                              email_success_recipients=email_recipient,
    #                              email_error_recipients=email_recipient)
    #         warning_str = ''
    #         for wm in w:
    #             warning_str += unicode(wm) + u'   |   '
    #     logger.debug('Update email sent:' + warning_str)
    # except:
    #     logger.debug('Update email not send due to error:' + unicode(sys.exc_info()))


def update_metadata_cache(filepath, request, input_file=None, force_update=False):
    """
    Update the metadata cache for the given file.

    :param filepath: String with the path to the file for which the metadata caech should be updated
    :param request: The django request object
    :param input_file: Optional input_file if its already open, otherwise filepath will be opened here.
    :param force_update: Boolean indicating whether we should force the update of the cache even if it should
        not be necessary.
    """
    logger.debug("Updating metadata cache for: "+filepath)
    try:
        if input_file is None:
            input_file = omsi_file(filepath, mode='r')
        # 1 Compute the file metadata
        metadata = views_helper.get_metadata(input_file,
                                             filename=filepath,
                                             request=request,
                                             force_update=force_update)
        # 2 Compute the provenance graph for all analyses
        for expIndex in range(input_file.get_num_experiments()):
            current_exp = input_file.get_experiment(expIndex)
            for anaIndex in range(current_exp.get_num_analysis()):
                current_ana = current_exp.get_analysis(anaIndex)
                metadata = views_helper.get_provenance(current_ana,
                                                       filename=filepath,
                                                       request=request,
                                                       force_update=force_update)
    except:
        logger.debug("ERROR: Update of the metadata cache failed"+str(sys.exc_info()))


def value_to_bool(value):
        """
        Internal helper function to convert a query-string parameter to boolean

        :param value: The value to be converted to a bool
        :type value: basestring, int, ool
        """
        if isinstance(value, str) or isinstance(value, unicode):
            if value.isdigit():
                return bool(int(value))
            elif value in ('True', 'true', 'TRUE', 'yes', 'Yes', 'y', 'on', 'ON', 'On'):
                return True
            else:
                return False
        elif isinstance(value, int):
            return bool(value)
        elif isinstance(value, bool):
            return value
        else:
            return False
