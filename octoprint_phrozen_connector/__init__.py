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
import os
import tempfile
import shutil
import subprocess
from flask import jsonify, request

try:
    from smb.SMBConnection import SMBConnection
    SMB_AVAILABLE = True
except ImportError:
    SMB_AVAILABLE = False

class Phrozen_connectorPlugin(
    octoprint.plugin.SettingsPlugin,
    octoprint.plugin.AssetPlugin,
    octoprint.plugin.TemplatePlugin,
    octoprint.plugin.BlueprintPlugin,
    octoprint.plugin.StartupPlugin,
    octoprint.plugin.ShutdownPlugin
):

    ##~~ SettingsPlugin mixin

    def get_settings_defaults(self):
        return {
            "phrozen_auth_token": "",
            "smb_ip": "",
            "smb_username": "",
            "smb_password": "",
            "smb_share_name": "share",
            "smb_enabled": False
        }
    
    def on_settings_save(self, data):
        """Handle settings save and refresh SMB mount if needed"""
        old_smb_enabled = self._settings.get(["smb_enabled"])
        old_smb_config = {
            "ip": self._settings.get(["smb_ip"]),
            "username": self._settings.get(["smb_username"]),
            "password": self._settings.get(["smb_password"]),
            "share_name": self._settings.get(["smb_share_name"])
        }
        
        # Save the new settings
        octoprint.plugin.SettingsPlugin.on_settings_save(self, data)
        
        # Check if SMB settings changed
        new_smb_enabled = self._settings.get(["smb_enabled"])
        new_smb_config = {
            "ip": self._settings.get(["smb_ip"]),
            "username": self._settings.get(["smb_username"]),
            "password": self._settings.get(["smb_password"]),
            "share_name": self._settings.get(["smb_share_name"])
        }
        
        # Refresh SMB mount if settings changed
        if old_smb_enabled != new_smb_enabled or old_smb_config != new_smb_config:
            self._logger.info("SMB settings changed, refreshing mount...")
            self._setup_smb_storage()

    ##~~ StartupPlugin mixin

    def on_after_startup(self):
        """Initialize SMB storage after startup"""
        self._setup_smb_storage()
    
    ##~~ ShutdownPlugin mixin
    
    def on_shutdown(self):
        """Clean up SMB mount on shutdown"""
        self._unmount_smb_storage()

    def _setup_smb_storage(self):
        """Set up SMB storage by mounting to uploads folder"""
        if not self._settings.get(["smb_enabled"]):
            self._unmount_smb_storage()  # Unmount if disabled
            return
            
        ip = self._settings.get(["smb_ip"])
        username = self._settings.get(["smb_username"])
        password = self._settings.get(["smb_password"])
        share_name = self._settings.get(["smb_share_name"])
        
        if not all([ip, username, password, share_name]):
            self._logger.warning("SMB storage enabled but configuration incomplete")
            return
            
        try:
            # Get OctoPrint's uploads folder
            uploads_folder = self._file_manager.get_folder("uploads")
            smb_mount_point = os.path.join(uploads_folder, "Phrozen SMB")
            
            # Create mount point directory if it doesn't exist
            if not os.path.exists(smb_mount_point):
                os.makedirs(smb_mount_point)
                self._logger.info(f"Created SMB mount point: {smb_mount_point}")
            
            # Check if already mounted
            if self._is_smb_mounted(smb_mount_point):
                self._logger.info("SMB share already mounted")
                return
            
            # Mount the SMB share using cifs-utils
            # Try without sudo first, then with sudo if needed
            mount_command_nosudo = [
                "mount", "-t", "cifs",
                f"//{ip}/{share_name}",
                smb_mount_point,
                "-o", f"username={username},password={password},uid={os.getuid()},gid={os.getgid()},iocharset=utf8,user"
            ]
            
            mount_command_sudo = [
                "sudo", "mount", "-t", "cifs",
                f"//{ip}/{share_name}",
                smb_mount_point,
                "-o", f"username={username},password={password},uid={os.getuid()},gid={os.getgid()},iocharset=utf8"
            ]
            
            # Try user mount first
            result = subprocess.run(mount_command_nosudo, capture_output=True, text=True)
            
            if result.returncode != 0:
                # Fall back to sudo mount
                result = subprocess.run(mount_command_sudo, capture_output=True, text=True)
            
            if result.returncode == 0:
                self._logger.info(f"SMB share mounted successfully at {smb_mount_point}")
            else:
                self._logger.error(f"Failed to mount SMB share: {result.stderr}")
                self._logger.error("Note: SMB mounting may require sudo privileges. Consider adding OctoPrint user to sudoers for mount operations.")
                
        except Exception as e:
            self._logger.error(f"Failed to setup SMB storage: {e}")
    
    def _is_smb_mounted(self, mount_point):
        """Check if SMB share is already mounted"""
        try:
            result = subprocess.run(["mount"], capture_output=True, text=True)
            return mount_point in result.stdout
        except Exception:
            return False
    
    def _unmount_smb_storage(self):
        """Unmount SMB storage"""
        try:
            uploads_folder = self._file_manager.get_folder("uploads")
            smb_mount_point = os.path.join(uploads_folder, "Phrozen SMB")
            
            if self._is_smb_mounted(smb_mount_point):
                # Try user unmount first, then sudo
                result = subprocess.run(["umount", smb_mount_point], capture_output=True, text=True)
                if result.returncode != 0:
                    result = subprocess.run(["sudo", "umount", smb_mount_point], capture_output=True, text=True)
                    
                if result.returncode == 0:
                    self._logger.info("SMB share unmounted successfully")
                else:
                    self._logger.error(f"Failed to unmount SMB share: {result.stderr}")
        except Exception as e:
            self._logger.error(f"Failed to unmount SMB storage: {e}")

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

    @octoprint.plugin.BlueprintPlugin.route("/smb/test", methods=["POST"])
    def test_smb_connection(self):
        """Test SMB connection by attempting a temporary mount"""
        data = request.get_json()
        
        ip = data.get('ip')
        username = data.get('username') 
        password = data.get('password')
        share_name = data.get('share_name', 'share')
        
        if not all([ip, username, password]):
            return jsonify({"success": False, "error": "Missing required parameters"}), 400
            
        try:
            # Create a temporary mount point for testing
            temp_mount = tempfile.mkdtemp(prefix="phrozen_smb_test_")
            
            try:
                # Test mount command - try user mount first
                mount_command_nosudo = [
                    "mount", "-t", "cifs",
                    f"//{ip}/{share_name}",
                    temp_mount,
                    "-o", f"username={username},password={password},uid={os.getuid()},gid={os.getgid()},iocharset=utf8,user"
                ]
                
                mount_command_sudo = [
                    "sudo", "mount", "-t", "cifs",
                    f"//{ip}/{share_name}",
                    temp_mount,
                    "-o", f"username={username},password={password},uid={os.getuid()},gid={os.getgid()},iocharset=utf8"
                ]
                
                # Try user mount first
                result = subprocess.run(mount_command_nosudo, capture_output=True, text=True, timeout=10)
                
                if result.returncode != 0:
                    # Fall back to sudo mount
                    result = subprocess.run(mount_command_sudo, capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    # Mount successful, count files and unmount
                    try:
                        file_count = len(os.listdir(temp_mount))
                        # Try user unmount first, then sudo
                        umount_result = subprocess.run(["umount", temp_mount], capture_output=True)
                        if umount_result.returncode != 0:
                            subprocess.run(["sudo", "umount", temp_mount], capture_output=True)
                        
                        return jsonify({
                            "success": True, 
                            "message": "SMB connection successful",
                            "file_count": file_count
                        })
                    except Exception as e:
                        # Cleanup on error
                        subprocess.run(["umount", temp_mount], capture_output=True)
                        subprocess.run(["sudo", "umount", temp_mount], capture_output=True)
                        raise e
                else:
                    return jsonify({
                        "success": False, 
                        "error": f"Mount failed: {result.stderr}"
                    }), 400
                    
            finally:
                # Clean up temp directory
                try:
                    os.rmdir(temp_mount)
                except Exception:
                    pass
            
        except subprocess.TimeoutExpired:
            return jsonify({"success": False, "error": "Connection timeout"}), 400
        except Exception as e:
            self._logger.error(f"SMB connection test failed: {e}")
            return jsonify({"success": False, "error": str(e)}), 500

    @octoprint.plugin.BlueprintPlugin.route("/smb/refresh", methods=["POST"])
    def refresh_smb_storage(self):
        """Refresh SMB storage configuration"""
        try:
            self._setup_smb_storage()
            return jsonify({"success": True, "message": "SMB storage refreshed"})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

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
