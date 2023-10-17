"""
Views related the management of OpenMSI resources (in particular file management.
"""
# TODO Should we remove the addfile view as this is handled by the processing.update view

# Create your views here.
from django.shortcuts import render_to_response, redirect
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseNotFound, HttpResponseRedirect, HttpResponseForbidden
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from django.template import RequestContext
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
import os
import sys
try:
    from omsi_server.omsi_resources.models import *  
except:
    from omsi_resources.models import *

try:
    from omsi_server.omsi_access import views_helper
except:
    from omsi_access import views_helper
from omsi.dataformat.omsi_file.main_file import omsi_file

import logging
logger = logging.getLogger(__name__)

import omsi_file_authorization
import json

from django.forms import ModelForm

"""Dictionary defining the names of all available query parameters for the omsi_resources app. Available parameters are:

   * `file` : Path to the file that should be imported

"""
query_paramters = {'file': 'file', 'owner': 'owner'}


def hierarchicalFilemanager(request, id=None, template_name='hierarchicalFileManager.html'):
    my_data_dict = {'api_root': settings.API_ROOT}
    return render_to_response(template_name, my_data_dict, context_instance=RequestContext(request))

@login_required
def fileProcessor(request, id=None, template_name='fileProcessor.html'):
    my_data_dict = {'api_root': settings.API_ROOT}
    return render_to_response(template_name, my_data_dict, context_instance=RequestContext(request))

@login_required
def jobManager(request, id=None, template_name='jobManager.html'):
    my_data_dict = {'api_root': settings.API_ROOT,
                    'is_superuser': request.user.is_superuser,
                    'username': request.user.username}
    return render_to_response(template_name, my_data_dict, context_instance=RequestContext(request))

def filemanager(request, template_name='filemanager.html'):
    logger.debug("Entering view")
    #Get the input parameters from the query string
    try:
        filename = request.GET[query_paramters['file']]
    except:
        if settings.DEBUG:
            raise 
        else:
            return HttpResponseNotFound("A required query parameter could not be read.")

    #Get full path to the file
    realFilename, myfile, filetype = omsi_file_authorization.authorize_fileaccess(
        request=request,
        infilename=filename,
        accesstype=omsi_file_authorization.g_access_types["manage"])
    if isinstance(realFilename, HttpResponse):  # Check if an error occured
        return realFilename
    # print Group.objects.all().values()
    # print dir(myfile)
    #Get the model
    if (realFilename is not None) and (myfile is None):
        #The file is not in the database but authorize_fileaccess returned a path.
        #This means the file exists but has not been added to the database yet.
        #Redirect the user to the view to add the file to the database
        redirect_url = reverse(addfile)
        redirect_url = redirect_url + "?"+query_paramters['file']+"="+realFilename
        return HttpResponseRedirect(redirect_url)

    userInfo = {'users': {}, 'permissions': {}}
    if myfile is not None:  # If the file was found and we are allowed to manage the file
        #This gets us a list of user and group models by their different permissions.
        userInfo['permissions']['viewUsers'] = [u['username'] for u in myfile.view_users.values()]
        userInfo['permissions']['editUsers'] = [u['username'] for u in myfile.edit_users.values()]
        userInfo['permissions']['ownerUsers'] = [u['username'] for u in myfile.owner_users.values()]
        userInfo['permissions']['viewGroups'] = [u['username'] for u in myfile.view_groups.values()]
        userInfo['permissions']['editGroups'] = [u['username'] for u in myfile.edit_groups.values()]
        userInfo['permissions']['ownerGroups'] = [u['username'] for u in myfile.owner_groups.values()]
        userInfo['is_public'] = myfile.is_public
        userInfo['users']['username'] = [u['username'] for u in User.objects.all().values()]
        userInfo['users']['first_name'] = [u['first_name'] for u in User.objects.all().values()]
        userInfo['users']['last_name'] = [u['last_name'] for u in User.objects.all().values()]
        dict((k, v) for k, v in userInfo['permissions'].iteritems() if v)
        # userInfo['permissions'] = {i:j for i,j in userInfo['permissions'].items() if j != []}
    print request.build_absolute_uri()
    # print userInfo
    if request.POST:
        form = FileFormOmsi(request.POST, instance=myfile)
        if form.is_valid():
            form.save()
            # messages.add_message(request, messages.SUCCESS, _('omsi_file entry correctly saved.'))
            # If the save was successful, redirect to another page
            # redirect_url = reverse(request)
            return HttpResponseRedirect(request.build_absolute_uri())
    else:
        form = FileFormOmsi(instance=myfile)
        # tempFilename, tempMyFile =  omsi_file_authorization.get_filelist_all( request=request, accesstype=omsi_file_authorization.g_access_types["manage"]  )

    return render_to_response(template_name, {
        'form': form,
        'file': realFilename,
        'api_root': settings.API_ROOT,
        'userInfo': json.dumps(userInfo),
    }, context_instance=RequestContext(request))
        
    # if request.method == 'POST':
    #       form = FileFormOmsi(request.POST)
    #       if form.is_valid():
    #           picked = form.cleaned_data.get('picked')
    #           # do something with your results
    # else:
    #       form = FileFormOmsi()
            
    # form = FileFormOmsi(instance=myfile)
    # formset = FileFormOmsi(request.POST)

    # omsi_files = FileModelOmsi.objects.all()
    # return render_to_response(template_name,  
                             # {'files': omsi_files,
                             # 'formset': form},
                              # context_instance=RequestContext(request))


def addfile(request):
    """View to add a new file to the system.
    
       **Required query arguments:**

          * file : The full path to the file to be added. This may \
            be an existing OpenMSI HDF5 file or a vendor file that needs to be converted.

    """
    # 1. Determine the file to be added
    try:
        filename = os.path.abspath(request.GET[query_paramters['file']])
    except:
        if settings.DEBUG:
            raise 
        else:
            return HttpResponseNotFound("A required query parameter could not be read.")

    # 2. Check if the file is valid
    if not os.path.isfile(filename):
        return HttpResponseNotFound("Invalid file path given\n%s"%filename)
    else:
        try:
            f = omsi_file(filename, 'r')
        except:
            return HttpResponseNotFound("File not a valid OMSI file"+str(sys.exc_info()))

    # 3. Check if the given file is already in the database
    f = FileModelOmsi.objects.filter(path__endswith=filename)
    if len(f) > 0:
        return HttpResponseNotFound("The given file is already in the database")

    ##### COMMENTED 20231017 DUE TO NEWT BEING DOWN #####
    # # 4. Determine who should be added as owner of the file
    # try:
    #     owner = request.GET[query_paramters['owner']]
    # except:
    #     #Check if we have a username
    #     username = request.user.username
    #     authenticated = request.user.is_authenticated()
    #     if not authenticated:
    #         return HttpResponseRedirect(settings.LOGIN_URL+"?next="+request.get_full_path())
    #     else:
    #         owner = username 
    # # 5. Check if the given owner is allowed to access the file
    # authorized = omsi_file_authorization.__authorize_fileaccess_nonregistered_file__(
    #     request=request,
    #     infilename=filename,
    #     accesstype=omsi_file_authorization.g_access_types["manage"],
    #     alternate_username=owner)
    # if request.user.is_superuser and request.user.is_authenticated():
    #     authorized = True 
    # if not authorized:
    #     HttpResponseForbidden("Operation not permitted")        
    # 6. Check if the user is in the database
    owner = 'bpb'
    try:
        user = User.objects.get(username=owner)
    except:
        try:
            if request.user.is_authenticated():
                user = request.user
            else:
                return HttpResponseForbidden("User not registered in the database")
        except:
            return HttpResponseForbidden("User not registered in the database")
        return HttpResponseForbidden("User not registered in the database")
    authorized=True


    # 7. Add the file to the database
    newModel = FileModelOmsi(path=filename)
    newModel.save()
    #Associate the owner with the file
    newModel.owner_users.add(user)

    newModel.is_public = True
    newModel.save()

    # 8. Update the metadata cache for the file
    try:
        inputFile = omsi_file(filename, mode='r')
        # 8.1 Compute the file metadata
        metadata = views_helper.get_metadata(inputFile,
                                             filename=filename,
                                             request=request)
        # 8.2 Compute the provenance graph for all analyses
        for expIndex in range(inputFile.get_num_experiments()):
            currExp = inputFile.get_experiment(expIndex)
            for anaIndex in range(currExp.get_num_analysis()):
                currAna = currExp.get_analysis(anaIndex)
                metadata = views_helper.get_provenance(currAna,
                                                       filename=filename,
                                                       request=request)
    except:
        logger.log("ERROR: Update of the metadata cache failed"+str(sys.exc_info()))
    return HttpResponse("Added file to database")
