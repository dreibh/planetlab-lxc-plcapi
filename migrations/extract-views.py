#!/usr/bin/env python

import sys
import re

class Schema:

    def __init__ (self,input,output=None):
        self.input=input
        self.output=output

    # left part is non-greedy
    comment=re.compile("(.*?)--.*")
    spaces=re.compile("^\s+(\S.*)")
    view=re.compile("(?i)\s*create\s+(or\s+replace)?\s+view.*")

    def parse (self):
        if self.output:
            outfile = open(self.output,"w")
        else:
            outfile = sys.stdout
        contents = file(self.input).read()
        parts=contents.split(";")
        for part in parts:
            # normalize: remove comments, linebreaks, trailing spaces..
            normalized=''
            lines=part.split('\n');
            out_lines=[]
            for line in lines:
                # remove comment
                match=Schema.comment.match(line)
                if match:
                    line=match.group(1)
                out_lines.append(line)
            # get them together
            out_line = " ".join(out_lines)
            # remove trailing spaces
            match=Schema.spaces.match(out_line)
            if match:
                out_line=match.group(1)
            match=Schema.view.match(out_line)
            if match:
                print >>outfile, out_line,';'
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
    Schema(input,output).parse()

