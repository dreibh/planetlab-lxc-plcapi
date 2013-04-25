import sys
import pkg_resources
import traceback

from PLC.Debug import log

"""
from PLC.Plugins import PluginManager
pm = PluginManager(None, None)
pm.dump()
pm.notify("who", {"what": "this!"})
"""

class PluginManager:
    def __init__(self, api, auth):
        self.api = api
        self.auth = auth
        self.plugins = []

        for entrypoint in pkg_resources.iter_entry_points("plcapi.plugin","api_notify"):
            save = sys.path
            try:
                # pkg_resources looks for modules in sys.path. Make sure it can
                # find our plugins.
                sys.path.append("/usr/share/plc_api")

                try:
                    pluginclass = entrypoint.load()
                    plugin = pluginclass()
                    self.plugins.append(plugin)
                except Exception, exc:
                    print >>log, "WARNING: failed to load plugin %s" % str(entrypoint)
                    traceback.print_exc(5,log)
            finally:
                sys.path = save

    def notify(self, action, info={}):
        for plugin in self.plugins:
            try:
                plugin.notify(self.api, self.auth, action, info)
            except Exception, exc:
                print >>log, "WARNING: failed to run plugin during action %s" % str(action)
                traceback.print_exc(5,log)

    def dump(self):
        for plugin in self.plugins:
            print plugin.__class__.__name__

