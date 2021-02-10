
# Create your views here.
#Usually we should have the json module in python but in case we don't use simplejson as fallback solution
try:
    import json
except ImportError:
    from django.utils import simplejson as json

from django.http import HttpResponse, HttpResponseBadRequest
from django.contrib.auth.decorators import login_required
import os, sys

import logging
logger = logging.getLogger(__name__)

@login_required
def index(request):
    """Render a response. This can be an html page, json object etc."""
    logger.debug("Entering view")
    testResponse = {'ResponseHELLO': range(20)}
    content = json.dumps( testResponse )
    return HttpResponse(content=content, content_type='application/json')

