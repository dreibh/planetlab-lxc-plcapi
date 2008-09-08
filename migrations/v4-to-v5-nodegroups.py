#!/usr/bin/env python

import sys
import re

class Nodegroups:

    def __init__ (self,input,output=None):
        self.input=input
        self.output=output

    # strip off comments
    comment=re.compile("\s*#.*")
    id="[\w\.-]+|\'[^\']+\'"
    id3="\s*(?P<groupname>%s)\s+(?P<tagname>%s)\s+(?P<tagvalue>%s\s*)"%(id,id,id)
    line=re.compile(id3)

    def parse (self):
        if self.output:
            outfile = open(self.output,"w")
        else:
            outfile = sys.stdout
        lineno=0
        print >> outfile, """
CREATE TABLE mgn_site_nodegroup (groupname text, tagname text, tagvalue text);
"""
        for line in file(self.input).readlines():
            lineno += 1
            if Nodegroups.comment.match(line):
                continue
            match=Nodegroups.line.match(line)
            if not match:
                print "%s:%s:%d: syntax error %s"%(
                    sys.argv[0],self.input,lineno,line)
                sys.exit(1)
            def normalize (id):
                if id.find("'")==0:
                    return id
                return "'%s'"%id
            [groupname,tagname,tagvalue]=[normalize(x) for x in match.groups()]

            print >> outfile, \
"INSERT INTO mgn_site_nodegroup (groupname,tagname,tagvalue) VALUES (%s,%s,%s);"%\
(groupname,tagname,tagvalue)
        if outfile != sys.stdout:
            outfile.close()

if __name__ == '__main__':
    if len(sys.argv) not in [2,3]:
        print 'Usage:',sys.argv[0],'input [output]'
        sys.exit(1)
    input=sys.argv[1]
    try:
        output=sys.argv[2]
    except:
        output=None
    Nodegroups(input,output).parse()
