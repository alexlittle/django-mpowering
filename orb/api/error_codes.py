
from django.utils.translation import ugettext as _


HTML_OK = 200
HTML_CREATED = 201
HTML_NO_CONTENT = 204
HTML_UNAUTHORIZED = 401 
HTML_TOO_MANY_REQUESTS = 429 
HTML_BADREQUEST = 400
HTML_METHOD_NOT_ALLOWED = 405
HTML_SERVERERROR = 500

ERROR_CODE_RESOURCE_EXISTS = 2000
ERROR_CODE_RESOURCE_DOES_NOT_EXIST = 3000
ERROR_CODE_RESOURCE_NO_TITLE = 4000
ERROR_CODE_RESOURCE_NO_DESCRIPTION = 4001
ERROR_CODE_RESOURCETAG_NO_RESOURCE = 4100
ERROR_CODE_RESOURCETAG_NO_TAG = 4101
ERROR_CODE_RESOURCETAG_EXISTS = 4110

ERROR_CODE_SEARCH_NO_QUERY = 6000

ERROR_CODE_TAG_EXISTS = 5000
ERROR_CODE_TAG_EMPTY = 5001
ERROR_CODE_TAG_DOES_NOT_EXIST = 5010

ERROR_CODES = {
               ERROR_CODE_RESOURCE_EXISTS : _(u"You have already uploaded a resource with this title"),
               ERROR_CODE_RESOURCE_DOES_NOT_EXIST : _(u"Resource not found"),
               ERROR_CODE_RESOURCE_NO_TITLE : _(u"No title provided"),
               ERROR_CODE_RESOURCE_NO_DESCRIPTION : _(u"No description provided"),
               ERROR_CODE_TAG_EXISTS : _(u'This tag already exists'),
               ERROR_CODE_TAG_EMPTY : _(u'Cannot add empty tag'),
               ERROR_CODE_SEARCH_NO_QUERY : _(u'Please supply a string to search for'),
               ERROR_CODE_RESOURCETAG_NO_RESOURCE : _(u'No resource specfified'),
               ERROR_CODE_RESOURCETAG_NO_TAG : _(u'No tag specfified'),
               ERROR_CODE_TAG_DOES_NOT_EXIST: _(u'Tag not found'),
               ERROR_CODE_RESOURCETAG_EXISTS: _(u'Resource already tagged with this tag'),
               }