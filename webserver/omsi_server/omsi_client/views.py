# Create your views here.
from django.shortcuts import render_to_response, redirect
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseNotFound, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from django.template import RequestContext
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
import os, sys

try :
    from omsi_server.omsi_resources import  omsi_file_authorization
except :
    from omsi_resources import omsi_file_authorization

import logging
logger = logging.getLogger(__name__)

def index(request, template_name='index.html'):
    """Render the index.html page"""
    logger.debug("Entering view")
    return render_to_response(template_name,
                              context_instance=RequestContext(request))


def viewer(request, template_name='viewer.html'):
    """Render the viewer.html page. The page supports various query-string parameters to allow loading of a dataset on startup.

        **Color channel setting query-string parameters:**

        * channel1Value : Floating point number indicating the m/z value to be used for the red channel
        * channel2Value : Floating point number indicating the m/z value to be used for the green channel
        * channel2Value : Floating point number indicating the m/z value to be used for the blue channel
        * rangeValue : Floating point number indicating the m/z range for all color channels
        * channel1RangeValue: Floating point number indicating the m/z range for channel 1
        * channel2RangeValue: Floating point number indicating the m/z range for channel 2
        * channel3RangeValue: Floating point number indicating the m/z range for channel 3

        **Viewer cursor 1 settings query-string parameters:**

        * cursorCol1 : X position to be used for the first cursor. NOTE: Only used if cursorRow1 is given as well.
        * cursorRow1 : Y position to be used for the first cursor. NOTE: Only used if cursorCol1 is given as well.

        **Viewer cursor 2 settings query-string parameters:**

        * cursorCol2 : X position to be used for the second cursor. NOTE: Only used if cursorRow2 is given as well.
        * cursorRow2 : Y position to be used for the second cursor. NOTE: Only used if cursorCol2 is given as well.

        **Data settings query-string parameters:**

        * file : The file to be opened in the viewer (if the file is valid)
        * expIndex : Integer index of the experiment to be loaded. NOTE: Will be ignored in case that no or an invalid file is given.
        * dataIndex : Integer index of the dataset to be loaded. NOTE: Will be ignored in case that no or an invalid file is given.
        * anaIndex : Integer index of the analysis to be loaded. NOTE: Will be ignored in case that no or an invalid file is given as well as in case that a dataIndex has been provided.

        **Example**
        * http://127.0.0.1:8000/openmsi/client/viewer/?&file=/work/data/11042008_NIMS.h5&expIndex=0&dataIndex=0&channel1Value=200&channel2Value=300&channel3Value=400&rangeValue=0.5

    """
    logger.debug("Entering view")

    #Get variable parameters if available for the color channels
    try:
        channel1Value =  request.GET.get( 'channel1Value' , None )
    except :
        channel1Value = None
    try:
        channel2Value =  request.GET.get( 'channel2Value' , None )
    except :
        channel2Value = None
    try:
        channel3Value =  request.GET.get( 'channel3Value' , None )
    except:
        channel3Value = None
    try:
        rangeValue =  request.GET.get( 'rangeValue' , None )
    except :
        rangeValue = None
    try:
        channel1RangeValue  = request.GET.get( 'channel1RangeValue', rangeValue )
    except :
        channel1RangeValue = rangeValue
    try:
        channel2RangeValue  = request.GET.get( 'channel2RangeValue', rangeValue )
    except :
        channel2RangeValue = rangeValue
    try:
        channel3RangeValue  = request.GET.get( 'channel3RangeValue', rangeValue )
    except :
        channel3RangeValue = rangeValue

    #Get variable values for the file
    try :
        default_file = request.GET.get( 'file' , None )
    except :
        default_file = None
    #Ignore the expIndex, anaIndex and dataIndex if not file is given
    if default_file is not None :
        try:
            expIndex =  request.GET.get( 'expIndex' , 0 )
        except :
            expIndex = 0 #Set the experiment and data index to ensure the page loads even if no parameters are set in the URL
        try:
            dataIndex =  request.GET.get( 'dataIndex' , None )
        except :
            dataIndex = 0 #Set the experiment and data index to ensure the page loads even if no parameters are set in the URL
        if dataIndex is None :
            try:
                anaIndex =  request.GET.get( 'anaIndex' , None )
            except :
                anaIndex = None
        else :
            anaIndex = None
    else :
        expIndex = None
        dataIndex = None
        anaIndex = None
    #Get default values for the two cursors
    try :
        cursorCol1 = request.GET.get( 'cursorCol1' , None )
    except :
        cursorCol1 = None
    try :
        cursorCol2 = request.GET.get( 'cursorCol2' , None )
    except :
        cursorCol2 = None
    try :
        cursorRow1 = request.GET.get( 'cursorRow1' , None )
    except :
        cursorRow1 = None
    try :
        cursorRow2 = request.GET.get( 'cursorRow2' , None )
    except :
        cursorRow2 = None
    #Client cache settings
    clientCacheDefault = int((not channel1Value) and
                             (not channel2Value) and
                             (not channel3Value) and
                             (not rangeValue) and
                             (not channel1RangeValue) and
                             (not channel2RangeValue) and
                             (not channel3RangeValue))
    try:
        enableClientCache = request.GET.get( 'enableClientCache' , clientCacheDefault  )
    except :
        enableClientCache = clientCacheDefault


    #Check if the default file exists and if the user has permissions to view it
    if default_file :
        realFilename, myfile, filetype =  omsi_file_authorization.authorize_fileaccess( request=request, infilename=default_file ,accesstype=omsi_file_authorization.g_access_types["view"]  )
        #Check if an error (e.g., no permissions to view) or a redirect has occured
        if isinstance(realFilename, HttpResponse ) :
            return realFilename

    #Generate the data dictionary
    my_data_dict = {}
    my_data_dict['image_name'] = request.GET.get('image_name', None)
    if enableClientCache is not None :
        #Check if the user set client-cache via an integer value 0,1
        try :
            tempVal = int(enableClientCache)
            if tempVal>0 :
                my_data_dict['enableClientCache'] = 'true'
            else :
                my_data_dict['enableClientCache'] = 'false'
        except :
            pass
        #Check if the user set the client-cache via true/false literals
        if (enableClientCache=='true') or (enableClientCache=='True') :
            my_data_dict['enableClientCache'] = 'true'
        elif(enableClientCache=='false') or (enableClientCache=='False') :
            my_data_dict['enableClientCache'] = 'false'
    if channel1Value is not None :
        my_data_dict['channel1Value'] = str(float(channel1Value)) #Check whether this is a float and not some bogus code
    if channel2Value is not None :
        my_data_dict['channel2Value'] = str(float(channel2Value)) #Check whether this  is a float and not some bogus code
    if channel3Value is not None :
        my_data_dict['channel3Value'] = str(float(channel3Value)) #Check whether this is a float and not some bogus code
    if rangeValue is not None :
        my_data_dict['rangeValue'] = str(float(rangeValue)) #Check whether this is a float and not some bogus code
    if channel1RangeValue is not None :
        my_data_dict['channel1RangeValue'] = str(float(channel1RangeValue)) #Check whether this is a float
    if channel2RangeValue is not None :
        my_data_dict['channel2RangeValue'] = str(float(channel2RangeValue)) #Check whether this is a float
    if channel3RangeValue is not None :
        my_data_dict['channel3RangeValue'] = str(float(channel3RangeValue)) #Check whether this is a float
    if default_file is not None :
        my_data_dict['default_file'] = str(default_file)
    else :
        my_data_dict['default_file'] = ""
    if expIndex is not None :
        my_data_dict['default_expIndex'] = str(int(expIndex)) #Check whether this is an int and not some bogus code
    else :
        my_data_dict['default_expIndex'] = ""
    if dataIndex is not None :
        my_data_dict['default_dataIndex'] = str(int(dataIndex)) #Check whether this is an int and not some bogus code
    else :
        my_data_dict['default_dataIndex'] = ""
    if anaIndex is not None :
        my_data_dict['default_anaIndex'] = str(int(anaIndex)) #Check whether this is an int and not some bogus code
    else :
        my_data_dict['default_anaIndex'] = ""
    if (cursorCol1 is not None) and (cursorRow1 is not None) :
        my_data_dict['default_cursorCol1'] = str( int(cursorCol1) ) #Check whether this is an int and not some bogus code
        my_data_dict['default_cursorRow1'] = str( int(cursorRow1) ) #Check whether this is an int and not some bogus code
    else :
        my_data_dict['default_cursorCol1'] = ""
        my_data_dict['default_cursorRow1'] = ""
    if (cursorCol2 is not None) and (cursorRow2 is not None) :
        my_data_dict['default_cursorCol2'] = str( int(cursorCol2) ) #Check whether this is an int and not some bogus code
        my_data_dict['default_cursorRow2'] = str( int(cursorRow2) ) #Check whether this is an int and not some bogus code
    else :
        my_data_dict['default_cursorCol2'] = ""
        my_data_dict['default_cursorRow2'] = ""

    my_data_dict['api_root'] = settings.API_ROOT
    #Render the response page
    return render_to_response(template_name, my_data_dict, context_instance=RequestContext(request))


def login_page(request, template_name='login.html') :
    """Render the login page"""
    logger.debug("Entering view")

    state = ""
    username = ""
    password = ""
    next = ""
    defaultNext = reverse(index)  #this redirects to the index page by default if no next is given but we should set a more appropriate default for this in the settings

    #The user is asked to provide their username and password
    if request.GET:
        state = "Log in required ..."
        #next = request.GET.get( 'next' , defaultNext )
        next = request.META['QUERY_STRING'].lstrip('next=') #ToDo: We here get the querystring directly to ensure that we pick up the full querystring of the redirect


    #The user sends us there username and password
    if request.POST:
        #Get the username and password that the user has sent us
        username = request.POST['username']
        password = request.POST['password']

        #Authenticate the user using DJANGO
        user = authenticate(username=username, password=password, request=request)
        #print request.session['newt_sessionid']
        #We need to have the option here to authenticate agains NERST instead here

        #If the user has been logged in succesfully
        if user is not None:
            #If the user is active in the system
            if user.is_active:
                #Login the user so that they stay logged in
                login(request, user)
                state = "You're successfully logged in!"
                if next == "":
                    return HttpResponseRedirect( defaultNext )
                else:
                    return HttpResponseRedirect(next)
            else:
                state = "Your account is inactive, please contact the OpenMSI admin."
        else:
            state = "Your username and/or password were incorrect."

    my_data_dict = {}
    my_data_dict['state']=state
    my_data_dict['username']=username
    my_data_dict['next']=next

    return render_to_response(template_name, my_data_dict, context_instance=RequestContext(request))

def logout(request) :
    """Logout"""
    try:
        from omsi_server.omsi_server.newt_auth_backend import NEWT
    except ImportError:
        from omsi_server.newt_auth_backend import NEWT
    from django.contrib.auth import logout as django_logout
    try:
        import json
    except ImportError:
        from django.utils import simplejson as json
    #Logout from NEWT
    backend = NEWT()
    status = backend.logout(request)
    #Logout from DJANGO
    django_logout( request )
    #Render the logout status
    #print status
    #Foward the user to the index page
    next = reverse(index)
    return HttpResponseRedirect( next )
    #return HttpResponse(content=json.dumps(status), content_type='application/json')

def news(request, template_name='news.html'):
    """Render the contact.html page"""
    logger.debug("Entering view")
    return render_to_response(template_name, context_instance=RequestContext(request))

def omsiAccount(request, template_name='omsiAccount.html'):
    """Render the contact.html page"""
    logger.debug("Entering view")
    return render_to_response(template_name, context_instance=RequestContext(request))

def publications(request, template_name='publications.html'):
    """Render the contact.html page"""
    logger.debug("Entering view")
    return render_to_response(template_name, context_instance=RequestContext(request))

def bastet(request, template_name='bastet.html'):
    """Render the contact.html page"""
    logger.debug("Entering view")
    return render_to_response(template_name, context_instance=RequestContext(request))

def about(request, template_name='about.html'):
    """Render the about.html page"""
    logger.debug("Entering view")
    return render_to_response(template_name, context_instance=RequestContext(request))

def terms(request, template_name='terms.html'):
    """Render the terms.html page"""
    logger.debug("Entering view")
    return render_to_response(template_name, context_instance=RequestContext(request))

def uploadHelp(request, template_name='uploadHelp.html'):
    """Render the uploadHelp.html page"""
    logger.debug("Entering view")
    return render_to_response(template_name, context_instance=RequestContext(request))

def contact(request):
    """Render the contact.html page"""
    logger.debug("Entering view")
    return render_to_response('contact.html', context_instance=RequestContext(request))


def testpage(request, template_name='test_access.html') :
    """Render the test page"""
    logger.debug("Entering view")
    my_data_dict = {}
    my_data_dict['api_root'] = settings.API_ROOT
    return render_to_response(template_name, my_data_dict,  context_instance=RequestContext(request))

#def docs(request):
#    """Render the doc.html page"""
#    logger.debug("Entering view")
#    return render_to_response('docs.html', context_instance=RequestContext(request))

#def algorithms(request):
#    """Render the algorithms.html page"""
#    logger.debug("Entering view")
#    return render_to_response('algorithms.html', context_instance=RequestContext(request))

#def examples(request):
#    """Render the examples.html page"""
#    logger.debug("Entering view")
#    return render_to_response('examples.html', context_instance=RequestContext(request))

#def downloads(request):
#    """Render the downloads.html page"""
#    logger.debug("Entering view")
#    return render_to_response('downloads.html', context_instance=RequestContext(request))

#def benchmarks(request):
#    """Render the benchmarks.html page"""
#    logger.debug("Entering view")
#    return render_to_response('benchmarks.html', context_instance=RequestContext(request))

#def layeredCanvas(request):
#    """Render the layeredCanvas.html demo/test page"""
#    logger.debug("Entering view")
#    return render_to_response('layeredCanvas.html', context_instance=RequestContext(request))

#def kineticJSCanvas(request):
#    """Render the layeredCanvas.html demo/test page"""
#    logger.debug("Entering view")
#    return render_to_response('kineticJSCanvas.html', context_instance=RequestContext(request))

#@login_required
#def login_test(request) :
#    """Render the test page"""
#    logger.debug("Entering view")
#
#    my_data_dict = {}
#    my_data_dict['api_root'] = settings.API_ROOT
#    my_data_dict['username'] = request.user.username
#
#    return render_to_response('login-test.html', my_data_dict,  context_instance=RequestContext(request))
