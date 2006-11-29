from PLC.Faults import *
from PLC.Parameter import Parameter, Mixed, python_type

class Filter(Parameter, dict):
    """
    A type of parameter that represents a filter on one or more
    columns of a database table. fields should be a dictionary of
    field names and types, e.g.

    {'node_id': Parameter(int, "Node identifier"),
     'hostname': Parameter(int, "Fully qualified hostname", max = 255),
     ...}

    Only filters on non-sequence type fields are supported.

    filter should be a dictionary of field names and values
    representing an intersection (if join_with is AND) or union (if
    join_with is OR) filter. If a value is a sequence type, then it
    should represent a list of possible values for that field.
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
            # provide for negation with a field starting with ~
            negation=False
            if field[0]=='~':
                negation=True
                field=field[1:]

            if field not in self.fields:
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
                elif not isinstance(value, bool) \
		and (value.find("*") > -1 or value.find("%") > -1):
		    operator = "LIKE"
                    value = str(api.db.quote(value.replace("*", "%")))
		else:
                    operator = "="
                    value = str(api.db.quote(value))

            clause = "%s %s %s" % (field, operator, value)
            if negation:
                clause = " ( NOT %s ) "%clause
                
            conditionals.append(clause)

        return (" %s " % join_with).join(conditionals)
