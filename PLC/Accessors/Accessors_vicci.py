# Accessors for Vicci, used to toggle between Vicci simplified UI and full planetlab UI

from PLC.Persons import Person

from PLC.Accessors.Factory import define_accessors, admin_roles, all_roles, tech_roles

import sys
current_module = sys.modules[__name__]

define_accessors(current_module, Person, "Advanced", "advanced",
                  "person/vicci", "advanced mode",
                  get_roles=all_roles, set_roles=all_roles, expose_in_api=True)

