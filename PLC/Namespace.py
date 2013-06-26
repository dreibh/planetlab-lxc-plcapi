#
# Thierry, April 2013
# 
# This file here is the connection to the SFA code
# at some point in time we had duplicated this from sfa
# but of course both versions have entirely diverged since then
# in addition we really only need 2 hepler functions here, that allow to maintain 
# hrn for nodes and persons and that is all
#
# So in order to avoid such situations in the future, 
# we try to import and re-use the SFA code
# assumption being that if these hrn's are of importance then it makes sense to
# require people to have sfa-plc installed as well
# however we do not want this requirement to break myplc in case it is not fulfilled
# 

#################### try to import from sfa
try:
    from sfa.planetlab.plxrn import hostname_to_hrn
except:
    hostname_to_hrn=None

try:
    from sfa.planetlab.plxrn import email_to_hrn
except:
    email_to_hrn=None

#################### if not found, bring our own local version
import re
def escape(token): return re.sub(r'([^\\])\.', r'\1\.', token)

if hostname_to_hrn is None:
    def hostname_to_hrn (auth_hrn, login_base, hostname):
        return ".".join( [ auth_hrn, login_base, escape(hostname) ] )

if email_to_hrn is None:
    def email_to_hrn (auth_hrn, email):
        return '.'.join([auth_hrn,email.split('@')[0].replace(".", "_").replace("+", "_")])
