#
# PLCAPI XML-RPC faults
#
# Aaron Klingaman <alk@absarokasoft.com>
# Mark Huang <mlhuang@cs.princeton.edu>
#
# Copyright (C) 2004-2006 The Trustees of Princeton University
# $Id: Faults.py,v 1.1 2006/09/06 15:36:06 mlhuang Exp $
#

import xmlrpclib

class PLCFault(xmlrpclib.Fault):
    def __init__(self, faultCode, faultString, extra = None):
        if extra:
            faultString += ": " + extra
        xmlrpclib.Fault.__init__(self, faultCode, faultString)

class PLCInvalidAPIMethod(PLCFault):
    def __init__(self, method, role = None, extra = None):
        faultString = "Invalid method " + method
        if role:
            faultString += " for role " + role
        PLCFault.__init__(self, 100, faultString, extra)

class PLCInvalidArgumentCount(PLCFault):
    def __init__(self, got, min, max = min, extra = None):
        if min != max:
            expected = "%d-%d" % (min, max)
        else:
            expected = "%d" % min
        faultString = "Expected %s arguments, got %d" % \
                      (expected, got)
        PLCFault.__init__(self, 101, faultString, extra)

class PLCInvalidArgument(PLCFault):
    def __init__(self, extra = None, name = None):
        if name is not None:
            faultString = "Invalid %s value" % name
        else:
            faultString = "Invalid argument"
        PLCFault.__init__(self, 102, faultString, extra)

class PLCAuthenticationFailure(PLCFault):
    def __init__(self, extra = None):
        faultString = "Failed to authenticate call"
        PLCFault.__init__(self, 103, faultString, extra)

class PLCLocalObjectRequired(PLCFault):
    def __init__(self,method_name="anonymous",obj_name="anonymous",
		 peer_id=None,extra=None):
	faultString = "Method: <%s> - Object <%s> must be local"%(method_name,obj_name)
	if peer_id is not None:
	    faultString += " (authoritative plc has peer_id %d)"%peer_id
        PLCFault.__init__(self, 104, faultString, extra)

class PLCDBError(PLCFault):
    def __init__(self, extra = None):
        faultString = "Database error"
        PLCFault.__init__(self, 106, faultString, extra)

class PLCPermissionDenied(PLCFault):
    def __init__(self, extra = None):
        faultString = "Permission denied"
        PLCFault.__init__(self, 108, faultString, extra)

class PLCNotImplemented(PLCFault):
    def __init__(self, extra = None):
        faultString = "Not fully implemented"
        PLCFault.__init__(self, 109, faultString, extra)

class PLCAPIError(PLCFault):
    def __init__(self, extra = None):
        faultString = "Internal API error"
        PLCFault.__init__(self, 111, faultString, extra)

####################
# shorthands to check various types of objects for localness (are we authoritative)
def PLCCheckLocalNode (node,method_name):
    if node['peer_id'] is not None:
	raise PLCLocalObjectRequired(method_name,node['hostname'],node['peer_id'])

def PLCCheckLocalPerson (person,method_name):
    if person['peer_id'] is not None:
	raise PLCLocalObjectRequired(method_name,person['email'],person['peer_id'])

def PLCCheckLocalSite (site,method_name):
    if site['peer_id'] is not None:
	raise PLCLocalObjectRequired(method_name,site['name'],site['peer_id'])

def PLCCheckLocalSlice (slice,method_name):
    if slice['peer_id'] is not None:
	raise PLCLocalObjectRequired(method_name,slice['name'],slice['peer_id'])

def PLCCheckLocalKey (key,method_name):
    if key['peer_id'] is not None:
	raise PLCLocalObjectRequired(method_name,key['key_id'],key['peer_id'])

def PLCCheckLocalSliceAttributeType (sliceAttributeType,method_name):
    if sliceAttributeType['peer_id'] is not None:
	raise PLCLocalObjectRequired(method_name,sliceAttributeType['name'],sliceAttributeType['peer_id'])

def PLCCheckLocalSliceAttribute (sliceAttribute,method_name):
    if sliceAttribute['peer_id'] is not None:
	raise PLCLocalObjectRequired(method_name,sliceAttribute['name'],sliceAttribute['peer_id'])


