#
# Shared type definitions
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2006 The Trustees of Princeton University
#
# $Id: Parameter.py,v 1.2 2006/09/08 19:45:04 mlhuang Exp $
#

class Parameter:
    """
    Typed value wrapper. Use in accepts and returns to document method
    parameters. Set the optional and default attributes for
    sub-parameters (i.e., dict fields).
    """

    def __init__(self, type, doc = "",
                 min = None, max = None,
                 optional = True, default = None,
                 ro = False):
        # Basic type of the parameter. May be a builtin type or Mixed.
        self.type = type

        # Documentation string for the parameter
        self.doc = doc

        # Basic value checking. For numeric types, the minimum and
        # maximum possible values, inclusive. For string types, the
        # minimum and maximum possible UTF-8 encoded byte lengths.
        self.min = min
        self.max = max

        # Whether the sub-parameter is optional or not. If optional,
        # the default for the sub-parameter if not specified.
        self.optional = optional
        self.default = default

        # Whether the DB field is read-only.
        self.ro = ro

    def __repr__(self):
        return repr(self.type)

class Mixed(tuple):
    """
    A list (technically, a tuple) of types. Use in accepts and returns
    to document method parameters that may return mixed types.
    """

    def __new__(cls, *types):
        return tuple.__new__(cls, types)
