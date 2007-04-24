from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Auth import Auth

class GetSlicesMD5(Method):
    """
    Returns the current md5 hash of slices.xml file
    (slices-0.5.xml.md5)
    """

    roles = ['admin', 'pi', 'user', 'tech', 'node']

    accepts = [
        Auth(),
        ]

    returns = Parameter(str, "MD5 hash of slices.xml")
    

    def call(self, auth):
	try:
	    file_path = '/var/www/html/xml/slices-0.5.xml.md5'
	    slices_md5 = file(file_path).readline().strip()
	    if slices_md5 <> "":		    
		return slices_md5
	    raise PLCInvalidArgument, "File is empty"
	except IOError:
	    raise PLCInvalidArgument, "No such file"
	
