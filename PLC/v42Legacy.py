# $Id$
# $URL$

# apply rename on list (columns) or dict (filter) args
def patch (arg,rename):
    if isinstance(arg,list):
        for i in range(0,len(arg)):
            arg[i] = patch(arg[i],rename)
        return arg
    if isinstance(arg,dict):
        return dict ( [ (rename(k),v) for (k,v) in arg.iteritems() ] )
    return rename(arg)

