#!/usr/bin/python -tt

import os
all = [i[:-3] for i in os.listdir(os.path.dirname(__file__)) if i.endswith(".py") and not i.startswith(".")]
