from django.core.management.base import BaseCommand
from optparse import make_option
from django.core.cache import cache
from omsi.dataformat.omsi_file.main_file import omsi_file

try:
    from omsi_server.omsi_access.views_helper import get_metadata, get_provenance
    from omsi_server.omsi_access.views_definitions import available_mtypes, query_parameters
    from omsi_server.omsi_resources.models import FileModelOmsi
except ImportError:
    from omsi_access.views_helper import get_metadata, get_provenance
    from omsi_resources.models import FileModelOmsi
    from omsi_access.views_definitions import available_mtypes, query_parameters


class Command(BaseCommand):
    help = 'Clear and repopulate the metadata cache table'

    option_list = BaseCommand.option_list + (
        make_option('--update-only',
                    action='store_true',
                    dest='update-only',
                    default=False,
                    help='Update out-of-date only without clearing the cache'),)
    option_list += (make_option('--clear-only',
                                action='store_true',
                                dest='clear-only',
                                default=False,
                                help='Clear the metadata cache and exit'),)

    def handle(self, *args, **options):

        clearall = not options['update-only']
        clearonly = options['clear-only']
        # 1) Clear the cache if requested
        if clearall or clearonly:
            try:
                self.stdout.write('Clearing cache', ending=' \n')
            except TypeError:
                #Older versions of django do not support the 'ending' keyword parameter
                #and do not automatically append the endline
                self.stdout.write('Clearing cache \n')
            cache.clear()
        # 1.1) Terminate if we should only clear the cache
        if clearonly:
            return

        # 2) Update the cache
        # 2.1) Iterate over all file models in the database
        for i in FileModelOmsi.objects.all():
            currpath = i.path
            try:
                self.stdout.write(currpath, ending=' \n')
            except TypeError:
                #Older versions of django do not support the 'ending' keyword parameter
                #and do not automatically append the endline
                self.stdout.write(currpath+" \n")

            # 2.3) Open the file
            try:
                currfile = omsi_file(filename=currpath, mode='r')
            except IOError:
                self.stderr.write("ERROR: The file could not be read: " + currpath + "\n")
                continue

            # 2.4) Construct and cache the metadata
            tempdata = get_metadata(input_object=currfile,
                                    filename=currpath,
                                    request=None,
                                    force_update=clearall)

            # 2.5) Construct and cache the dependency graphs for all analysis objects
            # 2.5.1) Iterate over all experiments
            for expindex in range(currfile.get_num_experiments()):
                currexp = currfile.get_experiment(expindex)
                # 2.5.2) Iterate over all analyses
                for anaindex in range(currexp.get_num_analysis()):
                    # 2.5.2.2) Get the analysis omsi object
                    currana = currexp.get_analysis(anaindex)
                    # 2.5.2.3) Get the metadata to populate/update the cache
                    tempdata = get_provenance(input_object=currana,
                                              filename=currpath,
                                              request=None,
                                              force_update=clearall)

            # 2.6) Close and delete the file
            currfile.close_file()
            del currfile


        #from django.core.urlresolvers import reverse
        #from django.conf import settings
        #from django.core.handlers.wsgi import WSGIRequest
        #from django.http import QueryDict
        #from django.http import HttpRequest

        # 2.2) Construct a http request for the current file. This is needed
        #      to construct the URL's of the file metadata
        # qd = QueryDict('')
        # tempqd = qd.copy()
        # tempqd.update({query_parameters['file']: currpath,
        #                query_parameters['mtype']: available_mtypes['file']})
        # httphost = str(settings.API_ROOT).lstrip('http://').lstrip('https://').lstrip('www.').rstrip('/')
        # environ = {
        #     'PATH_INFO': reverse('omsi_access.qmetadata'),
        #     'REMOTE_ADDR': str(settings.API_ROOT),
        #     'QUERY_STRING': tempqd.urlencode(),
        #     'REQUEST_METHOD': str('GET'),
        #     'SCRIPT_NAME': str(''),
        #     'SERVER_NAME': str(settings.API_ROOT),
        #     'HTTP_HOST': httphost,
        #     'SERVER_PORT': str('80'),
        #     'SERVER_PROTOCOL': str('HTTP/1.1'),
        #     'wsgi.version': (1, 0),
        #     'wsgi.url_scheme': str('http'),
        #     'wsgi.input': '',
        #     'wsgi.errors': None,
        #     'wsgi.multiprocess': True,
        #     'wsgi.multithread': False,
        #     'wsgi.run_once': False,
        # }
        # metadatarequest = WSGIRequest(environ)

        # 2.5.2.1) Construct HttpRequest used for the provenance function
        # tempqd.update({query_parameters['file']: currpath,
        #                query_parameters['expIndex']: str(expindex),
        #                query_parameters['anaIndex']: str(anaindex),
        #                query_parameters['mtype']: available_mtypes['provenance']})
        # environ['QUERY_STRING'] = tempqd.urlencode()
        # metadatarequest = WSGIRequest(environ)