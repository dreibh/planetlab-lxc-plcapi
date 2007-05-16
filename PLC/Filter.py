from types import StringTypes
try:
    set
except NameError:
    from sets import Set
    set = Set

import time

from PLC.Faults import *
from PLC.Parameter import Parameter, Mixed, python_type

class Filter(Parameter, dict):
    """
    A type of parameter that represents a filter on one or more
    columns of a database table.

    field should be a dictionary of field names and types, e.g.

    {'node_id': Parameter(int, "Node identifier"),
     'hostname': Parameter(int, "Fully qualified hostname", max = 255),
     ...}

    Only filters on non-sequence type fields are supported.

    filter should be a dictionary of field names and values
    representing an intersection (if join_with is AND) or union (if
    join_with is OR) filter. If a value is a sequence type, then it
    should represent a list of possible values for that field.

    Special forms:
    * a field starting with the ~ character means negation.
    example :  { '~peer_id' : None }
    * a field starting with < [  ] or > means lower than or greater than
      < > uses strict comparison
      [ ] is for using <= or >= instead
    example :  { '>time' : 1178531418 }
    example :  { ']event_id' : 2305 }
    * a field starting with [ or ] means older than or more recent than
      the associated value should be a given unix timestamp
    * a (string) value containing either a * or a % character is
      treated as a (sql) pattern; * are replaced with % that is the
      SQL wildcard character.
    example :  { 'hostname' : '*.jp' } 
    """

    def __init__(self, fields = {}, filter = {}, doc = "Attribute filter"):
        # Store the filter in our dict instance
        dict.__init__(self, filter)

        # Declare ourselves as a type of parameter that can take
        # either a value or a list of values for each of the specified
        # fields.
        self.fields = {}

        for field, expected in fields.iteritems():
            # Cannot filter on sequences
            if python_type(expected) in (list, tuple, set):
                continue
            
            # Accept either a value or a list of values of the specified type
            self.fields[field] = Mixed(expected, [expected])

        # Null filter means no filter
        Parameter.__init__(self, self.fields, doc = doc, nullok = True)

    # this code is not used anymore
    # at some point the select in the DB for event objects was done on
    # the events table directly, that is stored as a timestamp, thus comparisons
    # needed to be done based on SQL timestamps as well
    def unix2timestamp (self,unix):
	s = time.gmtime(unix)
	return "TIMESTAMP'%04d-%02d-%02d %02d:%02d:%02d'" % (s.tm_year,s.tm_mon,s.tm_mday,
							     s.tm_hour,s.tm_min,s.tm_sec)

    def sql(self, api, join_with = "AND"):
        """
        Returns a SQL conditional that represents this filter.
        """

        # So that we always return something
        if join_with == "AND":
            conditionals = ["True"]
        elif join_with == "OR":
            conditionals = ["False"]
        else:
            assert join_with in ("AND", "OR")

        for field, value in self.iteritems():
	    # handle negation, numeric comparisons
	    # simple, 1-depth only mechanism

	    modifiers={'~' : False, 
		       '<' : False, '>' : False,
		       '[' : False, ']' : False,
		       }

	    for char in modifiers.keys():
		if field[0] == char:
		    modifiers[char]=True;
		    field = field[1:]
		    break

            if field not in self.fields:
#		print 'current fields',self.fields
                raise PLCInvalidArgument, "Invalid filter field '%s'" % field

            if isinstance(value, (list, tuple, set)):
                # Turn empty list into (NULL) instead of invalid ()
                if not value:
                    value = [None]

                operator = "IN"
                value = map(str, map(api.db.quote, value))
                value = "(%s)" % ", ".join(value)
            else:
                if value is None:
                    operator = "IS"
                    value = "NULL"
                elif isinstance(value, StringTypes) and \
                     (value.find("*") > -1 or value.find("%") > -1):
		    operator = "LIKE"
                    value = str(api.db.quote(value.replace("*", "%")))
		else:
                    operator = "="
		    if modifiers['<']:
			operator='<'
		    if modifiers['>']:
			operator='>'
		    if modifiers['[']:
			operator='<='
		    if modifiers[']']:
			operator='>='
		    else:
			value = str(api.db.quote(value))

            clause = "%s %s %s" % (field, operator, value)

	    if modifiers['~']:
		clause = " ( NOT %s ) " % (clause)

            conditionals.append(clause)

#	print 'sql=',(" %s " % join_with).join(conditionals)
        return (" %s " % join_with).join(conditionals)
