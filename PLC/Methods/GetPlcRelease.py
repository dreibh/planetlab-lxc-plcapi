from PLC.Method import Method
from PLC.Auth import Auth
from PLC.Faults import *

import re

comment_regexp = '\A\s*#.|\A\s*\Z|\Axxxxx'

regexps = { 'build'   : '\A[bB]uild\s+(?P<key>[^:]+)\s*:\s*(?P<value>.*)\Z',
            'tags'    : '\A(?P<key>[^:]+)\s*:=\s*(?P<value>.*)\Z',
# spaces not part of key : ungreedy
            'rpms'    : '\A(?P<key>[^:]+?)\s*::\s*(?P<value>.*)\Z',
}

class GetPlcRelease(Method):
    """
    Returns various information about the current myplc installation.
    """

    roles = ['admin', 'pi', 'user', 'tech', 'node', 'anonymous']

    accepts = [
        Auth(),
        ]

    # for now only return /etc/myplc-release verbatim
    returns = { 'build' : 'information about the build',
                'tags' : 'describes the codebase location and tags used for building',
                'rpms' : 'details the rpm installed in the myplc chroot jail' }

    def call(self, auth):

        comment_matcher = re.compile(comment_regexp)

        matchers = {}
        result = {}
        for field in regexps.keys():
            matchers[field] = re.compile(regexps[field])
            result[field]={}

        try:
            release = open('/etc/myplc-release')
            for line in release.readlines():
                line=line.strip()
                if comment_matcher.match(line):
                    continue
                for field in regexps.keys():
                    m=matchers[field].match(line)
                    if m:
                        (key,value)=m.groups(['key','value'])
                        result[field][key]=value
                        break
                else:
                    if not result.has_key('unexpected'):
                        result['unexpected']=""
                    result['unexpected'] += (line+"\n")
        except:
            raise PLCNotImplemented, 'Cannot open /etc/myplc-release'
        return result
