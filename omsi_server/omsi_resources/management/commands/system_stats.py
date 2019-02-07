from django.core.management.base import BaseCommand
from optparse import make_option
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Q
import time
import os
import pickle
import numpy as np
try:
    import matplotlib.pyplot as plt
except ImportError:
    Command.plot_supported = False

try:
    from omsi_server.omsi_access.views_helper import get_metadata, get_provenance
    from omsi_server.omsi_access.views_definitions import available_mtypes, query_parameters
    from omsi_server.omsi_resources.models import FileModelOmsi
except ImportError:
    from omsi_access.views_helper import get_metadata, get_provenance
    from omsi_resources.models import FileModelOmsi
    from omsi_access.views_definitions import available_mtypes, query_parameters


class Command(BaseCommand):
    """DJANGO admin command to compute various statistics"""
    help = 'Compute system statistics'
    """Django help for manage.py"""

    #Add compute userstats only options
    option_list = BaseCommand.option_list
    #Add save to file option
    option_list += (make_option('--save',
                                action='store_true',
                                dest='save',
                                default=False,
                                help='Save the results (including plots) to the new folder system_stat_TIME'),)
    option_list += (make_option('--managed-only',
                                action='store_true',
                                dest='managed-only',
                                default=False,
                                help='Compute statistics only for managed files'),)

    plot_supported = True

    def __init__(self):
        """Setup basic data structures to capture system stat results"""
        super(Command, self).__init__()
        self.result = {'errors': [],
                       'warnings': [],
                       'messages': [],
                       'filestats': {},
                       'userstats': {}}

    def handle(self, *args, **options):
        """Handle called by manage.py to compute the actual system_stat command.

           Errors reported include:

             * ALLOWED_DATAPATHS settings invalid (see get_all_files)
             * PRIVATE_DATAPATHS settings invalid (see get_all_files)
             * Illegal files in PRIVATE_DATAPATH (see get_all_files)
             * Managed files that do not exists (i.e., the file is listed in the database but does not exist)

           File statistics reported on a per class basis \
           (managed vs. unmanaged, public vs. private include:

             * Number of files per category
             * Total file size per category
             * Average file size per category

        """

        checkusers = True
        checkfiles = True
        saveresult = options['save']
        managedonly = options['managed-only']
        if (not checkusers) and (not checkfiles):
            checkusers = True
            checkfiles = True

        if checkusers or checkfiles:
            self.print_message(message="STATUS: Compiling list of files",
                               message_type='message',
                               print_to_console=True,
                               record_message=False)
            m_public, m_private, um_public, um_private = self.get_all_files(managed_only=managedonly)

        if checkusers:
            self.print_message(message="STATUS: Compiling user statistics",
                               message_type='message',
                               print_to_console=True,
                               record_message=False)
            self.record_userstats(m_public=m_public,
                                  m_private=m_private,
                                  um_public=um_public,
                                  um_private=um_private)
            self.print_message(message=self.userstats_to_rst(),
                               message_type='message',
                               print_to_console=False)

        if checkfiles:
            self.print_message(message="STATUS: Compiling file statistics",
                               message_type='message',
                               print_to_console=True,
                               record_message=False)
            self.record_filestats(m_public=m_public,
                                  m_private=m_private,
                                  um_public=um_public,
                                  um_private=um_private)
            self.print_message(message=self.filestats_to_rst(),
                               message_type='message',
                               print_to_console=False)

        self.print_message(message=None,
                           message_type='warning',
                           print_to_console=True)
        self.print_message(message=None,
                           message_type='error',
                           print_to_console=True)
        self.print_message(message=None,
                           message_type='message',
                           print_to_console=True)

        if saveresult:
            outdir = 'system_stat_'+time.strftime("%d_%m_%Y")
            if os.path.exists(outdir):
                outdir += "_Time_"+time.strftime("%H_%M_%S")
            plotdir = outdir+"/plots"
            os.mkdir(outdir)
            os.mkdir(plotdir)
            messagefile = open(outdir+"/system_stat.rst", 'w')
            messagefile.write(self.print_message(
                message=None,
                message_type='warning',
                print_to_console=False,
                record_message=False))
            messagefile.write(self.print_message(
                message=None,
                message_type='error',
                print_to_console=False,
                record_message=False))
            messagefile.write(self.print_message(
                message=None,
                message_type='message',
                print_to_console=False,
                record_message=False))
            messagefile.close()

            picklefile = open(outdir+'/system_stat.pkl', 'wb')
            pickle.dump(self.result, picklefile)
            picklefile.close()

            if self.plot_supported:
                self.plot_result(plotdir=plotdir)


    def record_userstats(self, m_public, m_private, um_public, um_private):
        """Compute userstats and store the results in the self.results dict.

           :param m_public: QueryDict of managed public omsi_file_models
           :param m_private: QueryDict of managed private omsi_file_models
           :param um_public: List of paths of unmanaged public files
           :param um_private: List of paths of unmanaged private files

           Errors reported include:

           * Users without email, name etc.

           Aggregate user statistics reported include:

           * Total number of users
           * Total number of groups

           Group-level user statistics reported include:

           * Number of users per group
           * Number of files per group

           Per user stats include:

           * username
           * first name
           * last name
           * email
           * is_staff
           * is_active
           * is_superuser
           * last_joined
           * data_joined
           * owns_managed: Number of files owned by user or user's group
           * primary_owns_managed: Number of files directly owned by the user
           * owns_unmanaged: Private files not managed by the database
           * owns_public: User or user-group owned files made public
           * primary_owns_public: User owned files made public
           * view_managed : Total number of managed files a user can see (i.e., has view, edit, or owner permissions)
           * edit_managed : Total number of managed files a user can edit (i.e. hase edit or owner permissions)
           * view_total: Total number of managed and unmanaged files a user can view (including public files)
        """

        # * Number of files shared with user
        # * Total number of files per user
        # * Number of groups per user
        users = []
        for user in User.objects.all():
            #Record user information
            username = user.username
            userdict = {'username': username,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'email': user.email,
                        'is_staff': user.is_staff,
                        'is_active': user.is_active,
                        'is_superuser': user.is_superuser,
                        'date_joined': user.date_joined,
                        'last_login': user.last_login}
            #ownsmanaged = FileModelOmsi.objects.filter(owner_users__id__exact=user.id)
            usergroups = user.groups.values_list('name', flat=True)
            canviewmanaged = FileModelOmsi.objects.filter(
                #Owns
                reduce(lambda x, y: x | y,
                [Q(owner_groups__name__contains=groupname) for groupname in usergroups],
                Q(owner_users__id__exact=user.id)) |
                #Can edit
                reduce(lambda x, y: x | y,
                [Q(edit_groups__name__contains=groupname) for groupname in usergroups],
                Q(edit_users__id__exact=user.id)) |
                #Can view
                reduce(lambda x, y: x | y,
                [Q(view_groups__name__contains=groupname) for groupname in usergroups],
                Q(view_users__id__exact=user.id)) |
                #Public files
                Q(is_public__exact=True)
            )
            ownsmanaged = canviewmanaged.filter(
                reduce(lambda x, y: x | y,
                       [Q(owner_groups__name__contains=groupname) for groupname in usergroups],
                       Q(owner_users__id__exact=user.id)))
            editmanaged = canviewmanaged.filter(
                reduce(lambda x, y: x | y,
                       [Q(edit_groups__name__contains=groupname) for groupname in usergroups],
                       Q(edit_users__id__exact=user.id)))

            ownsunmanaged = [fn for fn in um_private if username in fn]
            ownspublic = ownsmanaged.filter(is_public__exact=True)
            primaryownsmanaged = FileModelOmsi.objects.filter(owner_users__id__exact=user.id)
            primaryownspublic = primaryownsmanaged.filter(is_public__exact=True)

            userdict['owns_managed'] = len(ownsmanaged)
            userdict['primary_owns_managed'] = len(primaryownsmanaged)
            userdict['owns_unmanaged'] = len(ownsunmanaged)
            userdict['owns_public'] = len(ownspublic)
            userdict['primary_owns_public'] = len(primaryownspublic)
            userdict['view_managed'] = len(canviewmanaged)
            userdict['edit_managed'] = len(editmanaged) + len(ownsmanaged)
            userdict['view_total'] = len(canviewmanaged) + userdict['owns_unmanaged'] + len(um_public)

            users.append(userdict)

            #Check if there are problems with the user record
            recordwarningmsg = ''
            if user.first_name == '':
                recordwarningmsg += 'Missing first_name | '
            if user.last_name == '':
                recordwarningmsg += 'Missing last name | '
            if user.email == '':
                recordwarningmsg += 'Missing email | '
            if len(recordwarningmsg) > 0:
                recordwarningmsg = 'User record incomplete: ' + user.username + " : " + recordwarningmsg
                self.print_message(message=recordwarningmsg,
                                   message_type='warning',
                                   print_to_console=False)

        self.result['userstats']['users'] = users


    def record_filestats(self,  m_public, m_private, um_public, um_private):
        """Compute filestats and store the results in the self.results dict.

           :param m_public: QueryDict of managed public omsi_file_models
           :param m_private: QueryDict of managed private omsi_file_models
           :param um_public: List of paths of unmanaged public files
           :param um_private: List of paths of unmanaged private files

           Errors reported include:

           * Managed files that do not exists (i.e., the file is listed in the database but does not exist

          File statistics reported on a per class basis \
           (managed vs. unmanaged, public vs. private include:

             * Number of files per category
             * Total file size per category
             * Average file size per category

        """
        filestats = self.result['filestats']

        # 1) Number of files per category
        filestats['num_files'] = {
            'm_public': len(m_public),
            'm_private': len(m_private),
            'um_public': len(um_public),
            'um_private': len(um_private),
            'total': (len(m_public)+len(m_private)+len(um_public)+len(um_private))}

        # 2) Filesize stats
        totalsize = 0
        m_publicsize = 0
        m_privatesize = 0
        um_publicsize = 0
        um_privatesize = 0
        for fm in m_public:
            if os.path.exists(fm.path):
                m_publicsize += os.stat(fm.path).st_size
            else:
                self.print_message(message="Managed file does not exist: "+fm.path,
                                   message_type='error',
                                   print_to_console=True)
        for fm in m_private:
            if os.path.exists(fm.path):
                m_privatesize += os.stat(fm.path).st_size
            else:
                self.print_message(message="Managed file does not exist: "+fm.path,
                                   message_type='error',
                                   print_to_console=True)
        for fp in um_public:
            um_publicsize += os.stat(fp).st_size
        for fp in um_private:
            um_privatesize += os.stat(fp).st_size

        m_publicsize = round(m_publicsize / (1024.*1024.), 2)
        m_privatesize = round(m_privatesize / (1024.*1024.), 2)
        um_publicsize = round(um_publicsize / (1024.*1024.), 2)
        um_privatesize = round(um_privatesize / (1024.*1024.), 2)
        totalsize = m_publicsize + m_privatesize + um_publicsize + um_privatesize
        filestats['sum(size) MB'] = {
            'm_public': m_publicsize,
            'm_private': m_privatesize,
            'um_public': um_publicsize,
            'um_private': um_privatesize,
            'total': (len(m_public)+len(m_private)+len(um_public)+len(um_private))}
        numfiles = filestats['num_files']
        filestats['avg(size) MB'] = {
            'm_public': 0 if numfiles['m_public'] == 0 else round(m_publicsize/numfiles['m_public'], 2),
            'm_private': 0 if numfiles['m_private'] == 0 else round(m_privatesize/numfiles['m_private'], 2),
            'um_public': 0 if numfiles['um_public'] == 0 else round(um_publicsize/numfiles['um_public'], 2),
            'um_private': 0 if numfiles['um_private'] == 0 else round(um_privatesize/numfiles['um_private'], 2),
            'total': 0 if numfiles['total'] == 0 else round(totalsize/numfiles['total'], 2)}


    def userstats_to_rst(self):
        """Create restructured text message from the user statistics"""

        # 1)Create table of per user statistics
        ustats = self.result['userstats']['users']
        ustatstable = [
            ['username',
             'first_name',
             'last_name',
             'email',
             'is_staff',
             'is_active',
             'is_superuser',
             'date_joined',
             'last_login',
             'owns_managed_files',
             'owns_unmanaged_files',
             'owns_public_files']
        ]
        ufilesstatstable = [
            ['username',
             'owns_managed',
             'primary_owns_managed',
             'owns_unmanaged',
             'owns_public',
             'primary_owns_public',
             'view_managed',
             'edit_managed',
             'view_total']
        ]
        for value in ustats:
            ulist = ['']*9
            ulist[0] = unicode(value['username'])
            ulist[1] = unicode(value['first_name'])
            ulist[2] = unicode(value['last_name'])
            ulist[3] = unicode(value['email'])
            ulist[4] = unicode(value['is_staff'])
            ulist[5] = unicode(value['is_active'])
            ulist[6] = unicode(value['is_superuser'])
            ulist[7] = unicode(value['date_joined'])
            ulist[8] = unicode(value['last_login'])

            uflist = ['']*9
            uflist[0] = unicode(value['username'])
            uflist[1] = unicode(value['owns_managed'])
            uflist[2] = unicode(value['primary_owns_managed'])
            uflist[3] = unicode(value['owns_unmanaged'])
            uflist[4] = unicode(value['owns_public'])
            uflist[5] = unicode(value['primary_owns_public'])
            uflist[6] = unicode(value['view_managed'])
            uflist[7] = unicode(value['edit_managed'])
            uflist[8] = unicode(value['view_total'])

            ustatstable.append(ulist)
            ufilesstatstable.append(uflist)

        # 2) Compile the output message
        message = "USER STATISTICS \n"
        message += "--------------- \n"
        message += "\n"
        message += "User Information \n"
        message += "^^^^^^^^^^^^^^^^ \n"
        message += self.create_rst_table(tabledata=ustatstable, has_header=True)
        message += "\n"
        message += "User-files Information \n"
        message += "^^^^^^^^^^^^^^^^^^^^^^ \n"
        message += "owns_managed_files: Files owned by the user or groups of the user \n"
        message += "primary_owns_managed: Files directly owned by the user (not including files owned via groups) \n"
        message += "owns_unmanaged_files: Files owned by the user that are not in the database \n"
        message += "owns_public_files: Publicly shared files owned by the user or groups of the user  \n"
        message += "primary_owns_public: Publicly shared files directly owned by the user (without groups) \n"
        message += "view_managed : Total number of managed files a user can see \n " + \
                   "               (i.e., has view, edit, or owner permissions) \n"
        message += "edit_managed : Total number of managed files a user can edit \n" + \
                   "               (i.e. hase edit or owner permissions) \n"
        message += "view_total: Total number of managed and unmanaged files a user can view (including public files) \n"
        message += "\n"
        message += self.create_rst_table(tabledata=ufilesstatstable, has_header=True)

        # 3) Return the message
        return message


    def filestats_to_rst(self):
        """Create restructured text message from the file statistics"""

        # 1)Create table of file statistics
        stats = self.result['filestats']
        statstable = [
            [""],
            ["Managed Public"],
            ["Managed Private"],
            ["Unmanaged Public"],
            ["Unmanaged Private"],
            ["Total"]
        ]
        for key, value in stats.items():
            statstable[0].append(unicode(key))
            statstable[1].append(unicode(value['m_public']))
            statstable[2].append(unicode(value['m_private']))
            statstable[3].append(unicode(value['um_public']))
            statstable[4].append(unicode(value['um_private']))
            statstable[5].append(unicode(value['total']))

        # 2) Compile the output message
        message = "FILE STATISTICS \n"
        message += "--------------- \n"
        message += "\n"
        message += self.create_rst_table(tabledata=statstable, has_header=True)

        # 3) Return the message
        return message

    def plot_result(self, plotdir):

        filestats = self.result['filestats']
        #Plot number of files per category
        keys = filestats['num_files'].keys()[0:-1]
        values = filestats['num_files'].values()[0:-1]
        numfiles = np.asarray(values).reshape((1, len(values)))
        self.barchart(bar_vals=numfiles,
                      bar_ticks=tuple(keys),
                      val_ticks=('Number of files',),
                      bar_label='File type',
                      val_label='Number of files',
                      plot_title='Number of files per type',
                      bar_width=0.35,
                      stacked=False,
                      filepath=os.path.join(plotdir, 'filestats_numfiles'))
        #Plot file size per category
        keys = filestats['sum(size) MB'].keys()[0:-1]
        values = filestats['sum(size) MB'].values()[0:-1]
        sumfiles = np.asarray(values).reshape((1, len(values)))
        self.barchart(bar_vals=sumfiles,
                      bar_ticks=tuple(keys),
                      val_ticks=('Total file size in MB',),
                      bar_label='File type',
                      val_label='Size in MB',
                      plot_title='Total size of files per type in MB',
                      bar_width=0.35,
                      stacked=False,
                      filepath=os.path.join(plotdir, 'filestats_sumsize'))
         #Plot average size per category
        keys = filestats['avg(size) MB'].keys()[0:-1]
        values = filestats['avg(size) MB'].values()[0:-1]
        avgfiles = np.asarray(values).reshape((1, len(values)))
        self.barchart(bar_vals=avgfiles,
                      bar_ticks=tuple(keys),
                      val_ticks=('Average file size in MB',),
                      bar_label='File type',
                      val_label='Size in MB',
                      plot_title='Average size of files per type in MB',
                      bar_width=0.35,
                      stacked=False,
                      filepath=os.path.join(plotdir, 'filestats_avgsize'))
        #Plot number of files per user results
        ustats = self.result['userstats']['users']
        bar_ticks = []
        val_ticks = ('unmanaged: public',
                     'unmanaged: owns',
                     'managed: max_permission(manage)',
                     'managed: max_permission(edit)',
                     'managed: max_permission(view)')
        #userdict['view_total'] = len(canviewmanaged) + userdict['owns_unmanaged'] + len(um_public)
        num_user_files = np.zeros(shape=(5, len(ustats)))
        num_unmanaged_public = self.result['filestats']['num_files']['um_public']
        for index, value in enumerate(ustats):
            bar_ticks.append(unicode(value['username']))
            num_user_files[0, index] = num_unmanaged_public
            num_user_files[1, index] = value['owns_unmanaged']
            num_user_files[2, index] = value['owns_managed']
            num_user_files[3, index] = value['edit_managed'] - value['owns_managed']
            num_user_files[4, index] = value['view_managed'] - value['edit_managed']

            #if value['view_total'] != np.sum(num_user_files[:, index]):
            #    print  (value['view_total'], np.sum(num_user_files[:, index]))
            #    print "Error in logic for computing number of viewable files."

        self.barchart(bar_vals=num_user_files,
                      bar_ticks=tuple(bar_ticks),
                      val_ticks=val_ticks,
                      bar_label='Username',
                      val_label='Number of files',
                      plot_title='Total number of files a user can view',
                      bar_width=0.35,
                      stacked=True,
                      filepath=os.path.join(plotdir, 'userstats_viewable_files_by_maximum_permission_level'))


    def get_all_files(self, managed_only):
        """Generate list of all files accessible via the system system,
           i.e., registered and unregistered files.

           :param managed_only: Compile only list of managed files and return empty lists for
                                the unmanaged files.

           Potential errors checked by this function are:

             * ALLOWED_DATAPATHS settings valid
             * PRIVATE_DATAPATHS settings valid
             * Illegal files in PRIVATE_DATAPATH

           :returns:

              * managedfiles_public : QueryDict of all omsi_file_models that are public
              * managedfiles_private : QueryDict of all omsi_file models that are private
              * unmanagedfiles_public : List of strings of all paths of unmanaged public files
              * unmanagedfiles_private: List of strings of all paths of unmanaged private files

        """

        #1) compute the list of all managed files
        managedfiles_public = FileModelOmsi.objects.filter(is_public__exact=True)
        managedfiles_private = FileModelOmsi.objects.filter(is_public__exact=False)

        if managed_only:
            return managedfiles_public, managedfiles_private, [], []

        #2) compute the list of all unmanaged public files
        unmanagedfiles_public = []
        #Generate the list of unmanaged  public data files
        for p in settings.ALLOWED_DATAPATHS:
            #Check if the data path exists, else ignore it
            if os.path.exists(p):
                currentlist = []
                if settings.ALLOWED_DATAPATHS_EXACT:  # Look only at the current directory
                    currentlist = [os.path.join(p, fn) for fn in os.listdir(p)]
                else:   # Look also at all subdirectories
                    for (path, dirs, files) in os.walk(p):
                        currentlist = currentlist + [os.path.join(path, fn) for fn in files]

                #Check which of the entries in the list are hdf5 files
                for name in currentlist:
                    if name.endswith(".h5"):
                        if len(FileModelOmsi.objects.filter(path__endswith=name)) == 0:
                            unmanagedfiles_public.append(name)
            else:
                self.print_message(message='ALLOWED_DATAPATHS: ' + p + 'does not exist',
                                   message_type='error',
                                   print_to_console=True)
        #3) Generate list of private unmanaged data files
        unmanagedfiles_private = []
        #Iteate through all private data locations for the user
        for privatepath in settings.PRIVATE_DATAPATHS:
            privatefolders = [os.path.join(privatepath, fn) for fn in os.listdir(privatepath)]
            for currentpath in privatefolders:
                currentlist = []
                if os.path.exists(currentpath):
                    if os.path.isdir(currentpath):
                        for (path, dirs, files) in os.walk(currentpath):
                            currentlist = currentlist + [os.path.join(path, fn) for fn in files]
                    else:
                        self.print_message(message='File found in PRIVATE_DATAPATH, please move:' + currentpath,
                                           message_type='warning',
                                           print_to_console=True)
                else:
                    self.print_message(message='PRIVATE_DATAPATHS: ' + currentpath + 'does not exist',
                                       message_type='error',
                                       print_to_console=True)
                #Check which of the entries in the list are hdf5 files
                for name in currentlist:
                    if name.endswith(".h5"):
                        if len(FileModelOmsi.objects.filter(path__endswith=name)) == 0:
                            unmanagedfiles_private.append(name)

        return managedfiles_public, managedfiles_private, unmanagedfiles_public, unmanagedfiles_private


    def print_message(self,
                      message=None,
                      message_type='message',
                      print_to_console=True,
                      record_message=True):
        """Print the message to stdout and save the message in the internal message board.

           :param message: String with the message to be saved. Set to None if the recorded
                           message of the given type should be printed.
           :param message_type: One of 'message', 'error', 'warning'
           :param print_to_console: Set to false if the message should only be recorded.
           :param record_message: Set to false if the message should not be recorded but only printed.

        """

        # 1) Record the message and determine which message should be printed to the console
        pmessage = message

        if message is not None and record_message:
            if message_type == 'message':
                self.result['messages'].append(message)
            elif message_type == 'error':
                self.result['errors'].append(message)
            elif message_type == 'warning':
                self.result['warnings'].append(message)

        if message is None:
            if message_type == 'message':
                if len(self.result['messages']) > 0:
                    pmessage  = "Summary Statistics:\n"
                    pmessage += "===================\n"
                    for m in self.result['messages']:
                        pmessage += m + "\n"
                    pmessage += "\n"
                    pmessage += "Number of warnings: " + str(len(self.result['warnings'])) + "\n"
                    pmessage += "Number of errors: " + str(len(self.result['errors'])) + "\n"
                else:
                    pmessage = None
            elif message_type == 'error':
                if len(self.result['errors']) > 0:
                    pmessage  = "Summary of errors:\n"
                    pmessage += "==================\n"
                    for m in self.result['errors']:
                        pmessage += m + "\n"
                    pmessage += "\n"
                else:
                    pmessage = None
            elif message_type == 'warning':
                if len(self.result['warnings']) > 0:
                    pmessage  = "Summary of warnings:\n"
                    pmessage += "====================\n"
                    for m in self.result['warnings']:
                        pmessage += m + "\n"
                    pmessage += "\n"
                else:
                    pmessage = None

        # 2) Print the message to the console
        if print_to_console and (pmessage is not None):
            try:
                self.stdout.write(pmessage, ending=' \n')
            except TypeError:
                #Older versions of django do not support the 'ending' keyword parameter
                #and do not automatically append the endline
                self.stdout.write(pmessage + '\n')

        if pmessage is None:
            pmessage = ''
        return pmessage

    @staticmethod
    def create_rst_table(tabledata, has_header=True):
        """Convert a 2D list of rows to a restructured text table.

           :param tabledata: Grid of table data
           :type tabledata: List of list. The rows must be of equal length.
           :param has_header: Should the first row be seen as a header.
           :type has_header: Boolean

        """
        ###
        def table_divider(header_flag=False):
            """Internal helper function used to add row dividers to the table"""
            rowdivider = ""
            if header_flag:
                style = "="
            else:
                style = "-"

            for cw in col_widths:
                rowdivider += cw * style + " "

            rowdivider += "\n"
            return rowdivider

        ###
        def add_row_entry(rowdata):
            """Internal helper function used to add row data to the table"""
            rowtext = ""
            for i, cw in enumerate(col_widths):
                rowtext += rowdata[i] + (cw - len(rowdata[i]) + 1) * " "

            return rowtext + "\n"
        ###

        col_widths = [max(out) for out in map(list, zip(*[[len(item) for item in row] for row in tabledata]))]
        if has_header:
            rst = table_divider(header_flag=True)
            rst += add_row_entry(rowdata=tabledata[0])
            rst += table_divider(header_flag=True)
        else:
            rst = table_divider(header_flag=False)

        for rowindex in range(int(has_header), len(tabledata)):
            rst += add_row_entry(rowdata=tabledata[rowindex])
            rst += table_divider(header_flag=False)
        return rst

    @staticmethod
    def barchart(bar_vals,
                 bar_ticks,
                 val_ticks,
                 bar_label,
                 val_label,
                 plot_title,
                 bar_width=0.35,
                 stacked=True,
                 filepath=None):
        """Create a stacked barchart from 2D array

           :param bar_vals: Values of the bars stored as a 2D numpy array. The first dimensions
                           are the y values to be stacked  and the second dimension are the bars
                           (i.e., the [:,i] is the dataseries with index i)
           :param bar_ticks: Tuple of lables for each bar shown on the x-axis of the plot
           :param bar_width: Single float value or array indicting the width of each bar
           :param val_ticks: Tuple of labels for the stacked values shown in the legend.
           :param bar_lable: Global lable for the bars shown on the x axis
           :param val_label: Global label for the values shown on the y axis
           :param plot_title: Title of the plot
           :param bar_width: Width of each bar
           :param stacked: Stacked or regular barchart
           :param filepath: Save plot to file. If set to None, then the plot will be shown on screen.
        """
        # 1) Close any previous plot
        plt.close()
        # 2) Determine the number of data series and the values per series
        vals_per_series = bar_vals.shape[1]
        num_series = bar_vals.shape[0]
        # 3) Define the basic x locations for the bars and compute the shifts needed for stacking the bars
        ind = np.arange(vals_per_series)    # the x locations for the groups
        bottom = np.cumsum(bar_vals, axis=0)
        bottom = np.vstack((np.zeros(vals_per_series), bottom))
        # 4) Generate a list of colors for the different data series
        colormap = plt.cm.gist_ncar
        colors = [colormap(i) for i in np.linspace(0, 0.9, num_series)]
        #4) Plot all bars
        barlist = []
        for i in range(num_series):
            if stacked:
                barlist.append(plt.bar(ind, bar_vals[i, :], bottom=bottom[i, :], width=bar_width, color=colors[i])[0])
            else:
                barlist.append(plt.bar(ind+(i*bar_width), bar_vals[i, :], width=bar_width, color=colors[i])[0])
        # 5) Define the plot annotations
        # 5.1) Define the axis labels
        plt.ylabel(val_label)
        plt.xlabel(bar_label)
        # 5.2) Define the plot title
        plt.title(plot_title)
        # 5.3) Define the x tick marks with the names of the bars
        if stacked:
            plt.xticks(ind+bar_width/2., bar_ticks)
        else:
            plt.xticks(ind+(bar_width*num_series)/2., bar_ticks)
        # 5.4) Define the legend with the names of the data series
        plt.legend(tuple(barlist), val_ticks)
        # 6) Save the plot to file or display the plot

        if filepath is not None:
            basefilepath = filepath.rstrip('.png').rstrip('.pdf')
            plt.savefig(basefilepath+'.png', format='PNG')
            plt.savefig(basefilepath+'.pdf', format='PDF')
        else:
            plt.show()
