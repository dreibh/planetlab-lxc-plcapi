# Marta Carbone - unipi
# $Id: $

from PLC.Nodes import Node
from PLC.Accessors.Factory import define_accessors, all_roles

import sys
current_module = sys.modules[__name__]

# XXX define possible subclasses
# define the dummynetbox SubClass strings
dbox_subclass = 'DummynetBox'

# define the type of a node as a dummynetbox
define_accessors(current_module, Node, 'Subclass', 'subclass', 'node/config',
		'type of node definition', get_roles=all_roles, set_roles='pi')

# define the dummynetbox connected to a node
define_accessors(current_module, Node, 'DummynetBox', 'dummynetbox_id', 'node/config',
		'dummynetbox connected to the node', get_roles=all_roles, set_roles='pi')

