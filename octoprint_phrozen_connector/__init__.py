# coding=utf-8
from __future__ import absolute_import

### (Don't forget to remove me)
# This is a basic skeleton for your plugin's __init__.py. You probably want to adjust the class name of your plugin
# as well as the plugin mixins it's subclassing from. This is really just a basic skeleton to get you started,
# defining your plugin as a template plugin, settings and asset plugin. Feel free to add or remove mixins
# as necessary.
#
# Take a look at the documentation on what other plugin mixins are available.

import octoprint.plugin
import requests
from flask import jsonify, request

class Phrozen_connectorPlugin(
    octoprint.plugin.SettingsPlugin,
    octoprint.plugin.AssetPlugin,
    octoprint.plugin.TemplatePlugin,
    octoprint.plugin.BlueprintPlugin
):

    ##~~ SettingsPlugin mixin

    def get_settings_defaults(self):
        return {
            "phrozen_auth_token": ""
        }

    ##~~ TemplatePlugin mixin

    def get_template_configs(self):
        return [
            dict(type="settings", template="phrozen_connector_settings.jinja2", custom_bindings=False),
            dict(type="tab", template="phrozen_connector_tab.jinja2")
        ]

    ##~~ AssetPlugin mixin

    def get_assets(self):
        # Define your plugin's asset files to automatically include in the
        # core UI here.
        return {
            "css": ["css/phrozen_connector.css"],
            "js": [
                "js/view_models/phrozen_connector.js",
                "js/api_connectors/phrozen_api_connector.js"
            ]
        }

    ##~~ BlueprintPlugin mixin

    @octoprint.plugin.BlueprintPlugin.route("/devices", methods=["GET"])
    def get_devices(self):
        # Get auth token from settings
        auth_token = self._settings.get(["phrozen_auth_token"])
        if not auth_token:
            return jsonify({"error": "No auth token configured"}), 400

        # Get query parameters
        offset = request.args.get('offset', 0, type=int)
        count = request.args.get('count', 10, type=int)

        try:
            # Make request to Phrozen API
            url = f"https://device.phrozen3d.com/mobile/devices?offset={offset}&count={count}"
            headers = {
                'Accept': 'application/json, text/plain, */*',
                'Accept-Encoding': 'gzip',
                'User-Agent': 'okhttp/4.12.0',
                'authorization': f'Bearer {auth_token}'
            }
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            return jsonify(response.json())
            
        except requests.exceptions.RequestException as e:
            self._logger.error(f"Failed to fetch devices from Phrozen API: {e}")
            return jsonify({"error": str(e)}), 500

    ##~~ Softwareupdate hook

    def get_update_information(self):
        # Define the configuration for your plugin to use with the Software Update
        # Plugin here. See https://docs.octoprint.org/en/master/bundledplugins/softwareupdate.html
        # for details.
        return {
            "phrozen_connector": {
                "displayName": "Phrozen Connector Plugin",
                "displayVersion": self._plugin_version,

                # version check: github repository
                "type": "github_release",
                "user": "PartialScience",
                "repo": "OctoPrint-Phrozen-Connector",
                "current": self._plugin_version,

                # update method: pip
                "pip": "https://github.com/PartialScience/OctoPrint-Phrozen-Connector/archive/{target_version}.zip",
            }
        }


# If you want your plugin to be registered within OctoPrint under a different name than what you defined in setup.py
# ("OctoPrint-PluginSkeleton"), you may define that here. Same goes for the other metadata derived from setup.py that
# can be overwritten via __plugin_xyz__ control properties. See the documentation for that.
__plugin_name__ = "Phrozen Connector Plugin"


# Set the Python version your plugin is compatible with below. Recommended is Python 3 only for all new plugins.
# OctoPrint 1.4.0 - 1.7.x run under both Python 3 and the end-of-life Python 2.
# OctoPrint 1.8.0 onwards only supports Python 3.
__plugin_pythoncompat__ = ">=3,<4"  # Only Python 3

def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = Phrozen_connectorPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
    }
