#
# Shared type definitions
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2006 The Trustees of Princeton University
#
# $Id: Parameter.py,v 1.1 2006/09/06 15:36:07 mlhuang Exp $
#

class Parameter:
    """
    Typed value wrapper. Use in accepts and returns to document method
    parameters. Set the optional and default attributes for
    sub-parameters (i.e., dict fields).
    """

    def __init__(self, type, doc = "", min = None, max = None, optional = True, default = None):
        (self.type, self.doc, self.min, self.max, self.optional, self.default) = \
                    (type, doc, min, max, optional, default)

    def __repr__(self):
        return repr(self.type)

class Mixed(tuple):
    """
    A list (technically, a tuple) of types. Use in accepts and returns
    to document method parameters that may return mixed types.
    """

    def __new__(cls, *types):
        return tuple.__new__(cls, types)
