"""
Module used to define machine backends used to execute data processing jobs.
"""

from django.conf import settings


##############################################################
#  Base class for defining different machine backends        #
##############################################################
class machine_backend(object):
    """
    Interface class defining how a machine backend is defined.

    Every machine can have their own options to define scripts. To change settings we should hence
    use common functions, e.g, set_queue_and_time, to define specific settings. Every specific backend
    implements these kind of functions. Currently the set of functions available to change settings
    is limited but should be expanded in the future to allow for more general tasks. The basic functions
    available are e.g.:

    **Get Functions**

        * `get_machine_name` : Get the name of machine/profile
        * `get_cores_per_node` : Get the number of cores per node
        * `get_default_environment` : Retrieve s list of strings defining the default environment variables, e.g,. \
          library paths, installation directories etc.
        * `get_default_machine_parameters` : Get the dict with the default machine job execution settings, e.g.,
            queue, number of cores etc.
        * `get_jobid_var` : Get the variable used to define the job id in a job script
        * 'get_default_error_out` : Get the name of default error output file
        * `get_error_filename_parameter_name` : Get the name of the parameter that stores the error filename
        * `get_output_filename_parameter_name` : Get the name of the parameter that stores the output filename

    **Set Function**

        These are functions that are used to set specific parameters in the machine paramemter dictionary, e.g,
        generated by get_default_machine_parameters.

        * `set_queue_and_time` : Define the queue and walltime to be used

    **Create Functions**

        Based on the information about the machine create job scripts, start commands etc., so that we can
        compile a job script for submission to the machine.

        * `create_job_script_environment` : Create a string with the basic job script setting all job parameters
        * `create_launch_command` : Create a string with the command for actually launching the given compute command.

        The combination of these create functions allows us to create job scripts for different machines and
        schedulers without having to manually change scripts and variables.

    """
    def __init__(self):
        """
        Default constructor
        """
        pass

    @classmethod
    def set_queue_and_time(cls, task_execution_settings,  memory_size=None, queue=None, walltime=None):
        """
        Define the queue and walltime setting to be used for the machine

        :param task_execution_settings: Dictionary with all execution settings. This is the dict retrieved, e.g,
            via get_default_machine_paramters. The dict is updated according the user defined settings.
        :param memory_size: The expected size in byte of the full task in memory. May be None.
            If given then we try to determine the approbriate queue based on it.
        :param queue: String indicating the queue to be used
        :param walltime: String with with amount of time to be allocated in hh:mm:ss format

        **Side effects** task_execution_settings are modified in place

        :returns: the modified task_execution_settings given. NOTE: The settings are modified in place.
        """
        pass
        """
        if queue is not None:
            task_execution_settings['-q'] = queue
        if walltime is not None:
            task_execution_settings['walltime'] = walltime
        return task_execution_settings
        """

    @classmethod
    def get_machine_name(cls):
        """
        Get the name of the machine
        :return: Get basename of the machine, e.g., edison, cori, carver
        """
        raise NotImplementedError

    @classmethod
    def get_cores_per_node(cls):
        """
        Define the number of cores per node

        :return: Integer value with the number of cores per node
        """
        return 1

    @classmethod
    def get_default_environment(cls):
        """
        Get a list of strings with the default environment settings for OpenMSI on that machine.

        :return List of strings with commands defining the default environment. E.g, module load, export of paths etc.
        """
        return []

    @classmethod
    def get_default_machine_parameters(cls):
        """
        Get a dict with default machine parameters

        :return: Dict describing the default machine parameters where the keys are PBS/SLURM parameter names and the
            values are the corresponding settings.
        """
        raise NotImplementedError()

    @classmethod
    def get_default_error_out(cls, user_home="$HOME", script_header=False):
        """
        Get the name of the default file where standard error is written to

        :param user_home: Location of the users home directory. Default is $HOME.
        :param script_header: Is this the variable used in the script header (True) (e.g., as part of #SLURM) or the
                              main body of the script (False). Default value is False. This is needed as some
                              schedulers use different conventions for environment variables and header definitions.

        :return: Path to the default standard error file.
        """
        raise NotImplementedError()

    @classmethod
    def get_default_standard_out(cls, user_home="$HOME", script_header=False):
        """
        Get the name of the default file where standard out is written to

        :param user_home: Location of the users home directory. Default is $HOME.
        :param script_header: Is this the variable used in the script header (True) (e.g., as part of #SLURM) or the
                              main body of the script (False). Default value is False. This is needed as some
                              schedulers use different conventions for environment variables and header definitions.

        :return: Path to the default standard error file.
        """
        raise NotImplementedError()

    @classmethod
    def get_jobid_var(cls, script_header=False):
        """
        Get the name of the scheduler environment variable with the job id

        :param script_header: Is this the variable used in the script header (True) (e.g., as part of #SLURM) or the
                              main body of the script (False). Default value is False. This is needed as some
                              schedulers use different conventions for environment variables and header definitions.
        :return: String with the environment ID variable
        """
        raise NotImplementedError()

    @classmethod
    def get_error_filename_parameter_name(cls):
        """
        Get the name of the paramter that stores the name of the error file in the parameter dict

        :return: String with the error file parameter
        """
        raise NotImplementedError

    @classmethod
    def get_output_filename_parameter_name(cls):
        """
        Get the name of the paramter that stores the name of the standard out file in the parameter dict

        :return: String with the error file parameter
        """
        raise NotImplementedError

    @classmethod
    def create_job_script_environment(cls, execution_settings):
        """
        Based on the given settings dictionary create the string for a shell script
        that sets up the environment for the scheduling of a job

        :param execution_settings: dictionary with the specidicaiton of the execution environment
        :return: String with the environment for the job
        """
        raise NotImplementedError()

    @classmethod
    def create_launch_command(cls, job_command, machine_parameters):
        """
        Create the string with the launch command for the given application job command

        :param job_command: The application command to be executed, e.g., python convert.py ....
        :param machine_parameters: Dictionary with the machine parameters

        :return: String with the approbriate job command, e.g, aprun -n 24 -N 24 job_command ...
        """
        raise NotImplementedError()


##############################################################
#  Base class for machines with a PBS scheduler              #
##############################################################
class pbs_scheduler_machine(machine_backend):
    """
    Base class for machines with a PBS scheduler.
    """
    def __init__(self):
        """
        Default constructor
        """
        super(pbs_scheduler_machine, self).__init__()

    @classmethod
    def set_queue_and_time(cls, task_execution_settings,  memory_size=None, queue=None, walltime=None):
        """
        Define the queue and walltime setting to be used for the machine

        :param task_execution_settings: Dictionary with all execution settings. This is the dict retrieved, e.g,
            via get_default_machine_paramters. The dict is updated according the user defined settings.
        :param memory_size: The expected size in byte of the full task in memory. May be None.
            If given then we try to determine the approbriate queue based on it.
        :param queue: String indicating the queue to be used
        :param walltime: String with with amount of time to be allocated in hh:mm:ss format

        **Side effects** task_execution_settings are modified in place

        :returns: the modified task_execution_settings given. NOTE: The settings are modified in place.
        """
        if queue is not None:
            task_execution_settings['-q'] = queue
        if walltime is not None:
            task_execution_settings['walltime'] = walltime
        return task_execution_settings

    @classmethod
    def get_jobid_var(cls, script_header=False):
        """
        Get the name of the scheduler environment variable with the job id

        :param script_header: Is this the variable used in the script header (True) (e.g., as part of #SLURM) or the
                              main body of the script (False). Default value is False. This is needed as some
                              schedulers use different conventions for environment variables and header definitions.
        :return: String with the environment ID variable
        """
        # We can here savely ignore the script_header variable since the PBS scripts the return value for
        # the header and body of the script are the same.
        return '$PBS_JOBID'

    @classmethod
    def create_job_script_environment(cls, execution_settings):
        """
        Based on the given settings dictionary create the string for a shell script
        that sets up the environment for the scheduling of a job

        :param execution_settings: dictionary with the specidicaiton of the execution environment. This is PBS so here
            a list of typical parameters used here.

            * `walltime` : #PBS -l walltime= ... : The maximum walltime requested HH:MM:SS
            * `-q` : queue_name : Name of the submit queue
            * `-N` : job_name	Name of job script	Name of job; up to 15 printable, non-whitespace characters
            * `nodes: Number of nodes assigned ot the the job (-l nodes=num_nodes:ppn=tasks_per_node)
            * `-A`: Charge job to repo
            * `-e` : filename <job_name>.e<job_id> Write stderr to filename
            * `-o` :filename <job_name>.o<job_id> Write stdout to filename
            * -j [oe | eo]	Do not merge Merge (join) stdout and stderr.  If oe, merge as output file; ie eo, \
                   merge as error file
            * -m [m | b | e | n] Email notification options. Options a, b, e may be combined

                * a=send mail if job aborted by system
                * b=send mail when job begins
                * e=send mail when job ends
                * n=never send email

            * `-S` : shell Login shell Specify shell to interpret batch script
            * `-V` : Do not export. Export current environment variables into the batch job environment

        :return: String with the environment for the job
        """
        job_script = ""
        if '-S' in execution_settings.keys():
            if execution_settings['-S'] == '/bin/bash':
                job_script += "#!/bin/bash -l \n"
            else:
                job_script += "#!" + execution_settings['-S']
        special_keys = ['ppn',
                        'mppnppn',
                        'mppwidth',
                        'machine',
                        'environment',
                        'walltime',
                        'nodes',
                        'pvmem',
                        'num_tasks']  # List of keys treated separately
        for key, value in execution_settings.iteritems():
            if value is not None:
                keyval = key
                if key in ['walltime', 'pvmem', 'mppnppn', 'mppwidth']:
                    job_script += "#PBS -l " + key + "=" + unicode(value)+"\n"
                elif key == 'nodes':
                    job_script += "#PBS -l " + key + "=" + unicode(value)
                    if 'ppn' in execution_settings.keys():
                        job_script += ":ppn" + execution_settings['ppn']
                    job_script += "\n"
                if key not in special_keys:
                    job_script += "#PBS " + keyval + " " + unicode(value)+"\n"
        # Set the PBS working directory
        job_script += "\n"
        job_script += "cd $PBS_O_WORKDIR \n"
        return job_script

    @classmethod
    def get_error_filename_parameter_name(cls):
        """
        Get the name of the paramter that stores the name of the error file in the parameter dict

        :return: String with the error file parameter
        """
        return '-e'

    @classmethod
    def get_output_filename_parameter_name(cls):
        """
        Get the name of the paramter that stores the name of the standard out file in the parameter dict

        :return: String with the error file parameter
        """
        return '-o'

    @classmethod
    def get_default_error_out(cls, user_home="$HOME", script_header=False):
        """
        Get the name of the default file where standard error is written to

        :param user_home: Location of the users home directory. Default is $HOME.
        :param script_header: Is this the variable used in the script header (True) (e.g., as part of #SLURM) or the
                              main body of the script (False). Default value is False. This is needed as some
                              schedulers use different conventions for environment variables and header definitions.

        :return: Path to the default standard error file.
        """
        return user_home + "/" + cls.get_jobid_var() + ".ER"

    @classmethod
    def get_default_standard_out(cls, user_home="$HOME", script_header=False):
        """
        Get the name of the default file where standard out is written to

        :param user_home: Location of the users home directory. Default is $HOME.
        :param script_header: Is this the variable used in the script header (True) (e.g., as part of #SLURM) or the
                              main body of the script (False). Default value is False. This is needed as some
                              schedulers use different conventions for environment variables and header definitions.

        :return: Path to the default standard error file.
        """
        return user_home + "/" + cls.get_jobid_var() + ".OU"


##############################################################
#  Base class for machines with a SLURM scheduler            #
##############################################################
class slurm_scheduler_machine(machine_backend):
    """
    Base class for machines with a SLURM scheduler.
    """
    def __init__(self):
        """
        Default constructor
        """
        super(slurm_scheduler_machine, self).__init__()


    @classmethod
    def set_queue_and_time(cls, task_execution_settings,  memory_size=None, queue=None, walltime=None):
        """
        Define the queue and walltime setting to be used for the machine

        :param task_execution_settings: Dictionary with all execution settings. This is the dict retrieved, e.g,
            via get_default_machine_paramters. The dict is updated according the user defined settings.
        :param memory_size: The expected size in byte of the full task in memory. May be None.
            If given then we try to determine the approbriate queue based on it.
        :param queue: String indicating the queue to be used
        :param walltime: String with with amount of time to be allocated in hh:mm:ss format

        **Side effects** task_execution_settings are modified in place

        :returns: the modified task_execution_settings given. NOTE: The settings are modified in place.
        """
        if queue is not None:
            task_execution_settings['--partition'] = queue
        if walltime is not None:
            task_execution_settings['--time'] = walltime
        return task_execution_settings

    @classmethod
    def get_jobid_var(cls, script_header=False):
        """
        Get the name of the scheduler environment variable with the job id

        :param script_header: Is this the variable used in the script header (True) (e.g., as part of #SLURM) or the
                              main body of the script (False). Default value is False. This is needed as some
                              schedulers use different conventions for environment variables and header definitions.
        :return: String with the environment ID variable
        """
        if script_header:
            # When specifying --output SLURM header variables we need to use %j instead of
            # the $SLURM_JOB_ID environment variable
            return '%j'
        else:
            return '$SLURM_JOB_ID'

    @classmethod
    def create_job_script_environment(cls, execution_settings):
        """
        Based on the given settings dictionary create the string for a shell script
        that sets up the environment for the scheduling of a job

        :param execution_settings: dictionary with the specidicaiton of the execution environment. This is PBS so here
            a list of typical parameters used here.

            * `walltime` : #PBS -l walltime= ... : The maximum walltime requested HH:MM:SS
            * `-q` : queue_name : Name of the submit queue
            * `-N` : job_name	Name of job script	Name of job; up to 15 printable, non-whitespace characters
            * `nodes: Number of nodes assigned ot the the job (-l nodes=num_nodes:ppn=tasks_per_node)
            * `-A`: Charge job to repo
            * `-e` : filename <job_name>.e<job_id> Write stderr to filename
            * `-o` :filename <job_name>.o<job_id> Write stdout to filename
            * -j [oe | eo]	Do not merge Merge (join) stdout and stderr.  If oe, merge as output file; ie eo, \
               merge as error file
            * -m [m | b | e | n] Email notification options. Options a, b, e may be combined

                * a=send mail if job aborted by system
                * b=send mail when job begins
                * e=send mail when job ends
                * n=never send email

            * `-S` : shell Login shell Specify shell to interpret batch script
            * `-V` : Do not export. Export current environment variables into the batch job environment

        :return: String with the environment for the job
        """
        job_script = ""
        if '-S' in execution_settings.keys():
            if execution_settings['-S'] == '/bin/bash':
                job_script += "#!/bin/bash -l \n"
            else:
                job_script += "#!" + execution_settings['-S']
        else:
            job_script += "#!/bin/bash -l \n"
        special_keys = ['environment',
                        'machine',
                        'num_tasks']  # List of keys treated separately
        for key, value in execution_settings.iteritems():
            if key not in special_keys:
                if value is not None:
                    assign_op = '=' if key.startswith('--') else ' '
                    job_script += '#SBATCH ' + key + assign_op + unicode(value) + '\n'

        # Set the working directory
        job_script += "\n"
        job_script += "cd $SLURM_SUBMIT_DIR \n"
        return job_script

    @classmethod
    def get_error_filename_parameter_name(cls):
        """
        Get the name of the paramter that stores the name of the error file in the parameter dict

        :return: String with the error file parameter
        """
        return '--error'

    @classmethod
    def get_output_filename_parameter_name(cls):
        """
        Get the name of the paramter that stores the name of the standard out file in the parameter dict

        :return: String with the error file parameter
        """
        return '--output'

    @classmethod
    def get_default_error_out(cls, user_home="$HOME", script_header=False):
        """
        Get the name of the default file where standard error is written to

        :param user_home: Location of the users home directory. Default is $HOME.
        :param script_header: Is this the variable used in the script header (True) (e.g., as part of #SLURM) or the
                              main body of the script (False). Default value is False. This is needed as some
                              schedulers use different conventions for environment variables and header definitions.

        :return: Path to the default standard error file.
        """
        return user_home + "/slurm-" + cls.get_jobid_var(script_header=script_header) + ".out"

    @classmethod
    def get_default_standard_out(cls, user_home="$HOME", script_header=False):
        """
        Get the name of the default file where standard out is written to

        :param user_home: Location of the users home directory. Default is $HOME.
        :param script_header: Is this the variable used in the script header (True) (e.g., as part of #SLURM) or the
                              main body of the script (False). Default value is False. This is needed as some
                              schedulers use different conventions for environment variables and header definitions.

        :return: Path to the default standard error file.
        """
        return user_home + "/slurm-" + cls.get_jobid_var(script_header=script_header) + ".out"


##############################################################
# cori.nersc.gov                                             #
##############################################################
class cori_backend(slurm_scheduler_machine):
    """
    Backend specification for cori
    """
    def __init__(self):
        """
        Default constructor
        """
        super(cori_backend, self).__init__()

    @classmethod
    def set_queue_and_time(cls, task_execution_settings,  memory_size=None, queue=None, walltime=None):
        """
        Define the queue and walltime setting to be used for the machine

        :param task_execution_settings: Dictionary with all execution settings
        :param memory_size: The expected size in byte of the full task in memory. May be None.
            If given then we try to determine the approbriate queue based on it.
        :param queue: String indicating the queue to be used
        :param walltime: String with with amount of time to be allocated in hh:mm:ss format

        **Side effects** task_execution_settings are modified in place

        :returns: the modified task_execution_settings given. NOTE: The settings are modified in place.
        """
        import math
        _ = super(cori_backend, cls).set_queue_and_time(task_execution_settings,
                                                        memory_size=memory_size,
                                                        queue=queue,
                                                        walltime=walltime)
        task_execution_settings['--partition'] = 'realtime' if queue is None else queue # 'regular'
        if memory_size is None or math.ceil(memory_size / float(1000*1000*1000)) > 48:
            if walltime is None:
                task_execution_settings['--time'] = "12:00:00"
        else:
            if walltime is None:
                task_execution_settings['--time'] = "01:30:00"
        return task_execution_settings

    @classmethod
    def get_cores_per_node(cls):
        """
        Define the number of cores per node

        :return: Integer value with the number of cores per node
        """
        return 36

    @classmethod
    def get_machine_name(cls):
        """
        Get the name of the machine
        :return: Get basename of the machine, e.g., edison, cori, carver
        """
        return 'cori'

    @classmethod
    def get_default_environment(cls):
        """
        Get a list of strings with the default environment settings for OpenMSI on that machine.

        :return List of strings with commands defining the default environment. E.g, module load, export of paths etc.
        """
        return ['module load python',
                'module load h5py',
                'export PYTHONPATH=' + settings.BASTET_PROCESSING_PATH + ':$PYTHONPATH',
                'export PYTHONPATH=/project/projectdirs/openmsi/python_modules/edison/lib/python:$PYTHONPATH']

    @classmethod
    def get_default_machine_parameters(cls):
        """
        Get a dict with default machine parameters

        :return: Dict describing the default machine parameters where the keys are PBS/SLURM parameter names and the
            values are the corresponding settings.
        """
        return {'--partition': 'debug',
                '--job-name': 'omsi_user_job',
                '--time': "00:30:00",  # max is 48:00:00
                '--nodes': 1,
                '--ntasks-per-node': cls.get_cores_per_node(),    # By default use all cores on a node
                '--account': 'm1541',
                '--error': None,   # Set in ProcessingTaskRunner.submit_job()
                '--output': None,   # Set in ProcessingTaskRunner.submit_job()
                'num_tasks': 1,
                'environment': cls.get_default_environment(),
                'machine': cls.get_machine_name()
                }

    @classmethod
    def create_launch_command(cls, job_command, machine_parameters):
        """
        Create the string with the launch command for the given application job command

        :param job_command: The application command to be executed, e.g., python convert.py ....
        :param machine_parameters: Dictionary with the machine parameters

        :return: String with the approbriate job command, e.g, aprun -n 24 -N 24 job_command ...
        """
        launch_command = 'srun '

        # total number of tasks
        total_num_tasks = machine_parameters['num_tasks']
        if total_num_tasks is None:
            total_num_tasks = machine_parameters['--ntasks-per-node'] * machine_parameters['--nodes']
        launch_command += '-n ' + unicode(total_num_tasks) + " "

        # Number of nodes
        launch_command += '-N ' + unicode(machine_parameters['--nodes']) + " "
        # TODO set number of tasks per node

        # Add the job command
        launch_command += job_command

        # Return the result
        return launch_command


##############################################################
#  edison.nersc.gov                                          #
##############################################################
class edison_backend(cori_backend):
    """
    Backend specification for edison
    """

    def __init__(self):
        """
        Default constructor
        """
        super(edison_backend, self).__init__()

    @classmethod
    def get_machine_name(cls):
        """
        Get the name of the machine
        :return: Get basename of the machine, e.g., edison, cori, carver
        """
        return 'edison'

    @classmethod
    def set_queue_and_time(cls, task_execution_settings,  memory_size=None, queue=None, walltime=None):
        """
        Define the queue and walltime setting to be used for the machine

        :param task_execution_settings: Dictionary with all execution settings
        :param memory_size: The expected size in byte of the full task in memory. May be None.
            If given then we try to determine the approbriate queue based on it.
        :param queue: String indicating the queue to be used
        :param walltime: String with with amount of time to be allocated in hh:mm:ss format

        **Side effects** task_execution_settings are modified in place

        :returns: the modified task_execution_settings given. NOTE: The settings are modified in place.
        """
        import math
        _ = super(cori_backend, cls).set_queue_and_time(task_execution_settings,
                                                        memory_size=memory_size,
                                                        queue=queue,
                                                        walltime=walltime)
        task_execution_settings['--partition'] = 'realtime' if queue is None else queue # 'regular'
        if memory_size is None or math.ceil(memory_size / float(1000*1000*1000)) > 48:
            if walltime is None:
                task_execution_settings['--time'] = "12:00:00"
        else:
            if walltime is None:
                task_execution_settings['--time'] = "01:30:00"
        return task_execution_settings

    @classmethod
    def get_cores_per_node(cls):
        """
        Define the number of cores per node

        :return: Integer value with the number of cores per node
        """
        return 24


BACKENDS = {'edison': edison_backend,
            'cori': cori_backend}
"""
Dictionary with all registered machine backends
"""

DEFAULT_BACKEND_KEY = 'edison'
"""
Name of the default machine backend to be used
"""