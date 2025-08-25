$(function() {
    function PhrozenConnectorViewModel(parameters) {
        var self = this;

        // Set up dependencies 
        self.settingsViewModel = parameters[0];
        self.apiConnector = new PhrozenApiConnector();

        // Observables
        self.devices = ko.observableArray([]);
        self.currentDeviceIndex = ko.observable(0);
        self.isLoading = ko.observable(false);
        self.errorMessage = ko.observable("");

        // Computed observables
        self.currentDevice = ko.computed(function() {
            if (self.devices().length > 0 && self.currentDeviceIndex() < self.devices().length) {
                return self.devices()[self.currentDeviceIndex()];
            }
            return null;
        });

        self.deviceNavigation = ko.computed(function() {
            if (self.devices().length === 0) return "";
            return `Device ${self.currentDeviceIndex() + 1} of ${self.devices().length}`;
        });

        self.stateClass = ko.computed(function() {
            if (!self.currentDevice()) return "";
            switch(self.currentDevice().state) {
                case 'print': return 'label-success';
                case 'idle': return 'label-info';
                case 'error': return 'label-important';
                default: return 'label-warning';
            }
        });

        self.layerProgress = ko.computed(function() {
            if (!self.currentDevice() || self.currentDevice().state !== 'print') return "";
            var current = self.currentDevice().currentLayer;
            var total = self.currentDevice().totalLayer;
            var percentage = Math.round((current / total) * 100);
            return `${current} / ${total} = ${percentage}%`;
        });

        self.layerPercentage = ko.computed(function() {
            if (!self.currentDevice() || self.currentDevice().state !== 'print') return 0;
            return Math.round((self.currentDevice().currentLayer / self.currentDevice().totalLayer) * 100);
        });

        self.timeProgress = ko.computed(function() {
            if (!self.currentDevice() || self.currentDevice().state !== 'print') return "";
            var current = self.currentDevice().currentTime;
            var total = self.currentDevice().totalTime;
            var percentage = Math.round((current / total) * 100);
            return `${self.formatDuration(current)} / ${self.formatDuration(total)} = ${percentage}%`;
        });

        self.timePercentage = ko.computed(function() {
            if (!self.currentDevice() || self.currentDevice().state !== 'print') return 0;
            return Math.round((self.currentDevice().currentTime / self.currentDevice().totalTime) * 100);
        });

        self.formattedStartTime = ko.computed(function() {
            if (!self.currentDevice() || self.currentDevice().state !== 'print') return "";
            // Convert Unix timestamp to local time
            var startTime = new Date(parseInt(self.currentDevice().startTime) * 1000);
            return startTime.toLocaleString();
        });

        self.timeRemaining = ko.computed(function() {
            if (!self.currentDevice() || self.currentDevice().state !== 'print') return "";
            var remaining = self.currentDevice().totalTime - self.currentDevice().currentTime;
            return self.formatDuration(remaining);
        });

        self.expectedEndTime = ko.computed(function() {
            if (!self.currentDevice() || self.currentDevice().state !== 'print') return "";
            var remaining = self.currentDevice().totalTime - self.currentDevice().currentTime;
            var endTime = new Date(Date.now() + (remaining * 1000));
            return endTime.toLocaleString();
        });

        // Set up ViewModel methods
        self.getPhrozenAuthToken = () => {
            try {
                token = self.settingsViewModel.settings.plugins.phrozen_connector.phrozen_auth_token();
            } catch(e) {
                token = "";
            }
            return token;
        }

        self.formatDuration = function(seconds) {
            var hours = Math.floor(seconds / 3600);
            var minutes = Math.floor((seconds % 3600) / 60);
            var secs = seconds % 60;
            return `${hours}h ${minutes}m ${secs}s`;
        };

        self.loadDevices = async function() {
            self.isLoading(true);
            self.errorMessage("");
            
            try {
                var response = await self.apiConnector.getDevices();
                if (response.status === 0) {
                    self.devices(response.devices || []);
                    self.currentDeviceIndex(0);
                } else {
                    self.errorMessage("Failed to load devices from API");
                }
            } catch (error) {
                console.error("Error loading devices:", error);
                self.errorMessage("Error loading devices: " + error.message);
            } finally {
                self.isLoading(false);
            }
        };

        self.previousDevice = function() {
            if (self.currentDeviceIndex() > 0) {
                self.currentDeviceIndex(self.currentDeviceIndex() - 1);
            }
        };

        self.nextDevice = function() {
            if (self.currentDeviceIndex() < self.devices().length - 1) {
                self.currentDeviceIndex(self.currentDeviceIndex() + 1);
            }
        };

        self.useToken = async function() {
            await self.loadDevices();
        };

        // This will get called before the PhrozenConnectorViewModel gets bound to the DOM, but after its
        // dependencies have already been initialized. It is especially guaranteed that this method
        // gets called _after_ the settings have been retrieved from the OctoPrint backend and thus
        // the SettingsViewModel been properly populated.
        self.onBeforeBinding = function() {
            // Auto-load devices if token is available
            if (self.getPhrozenAuthToken()) {
                self.loadDevices();
            }
        }
    }

    // This is how our plugin registers itself with the application, by adding some configuration
    // information to the global variable OCTOPRINT_VIEWMODELS
    OCTOPRINT_VIEWMODELS.push([
        // This is the constructor to call for instantiating the plugin
        PhrozenConnectorViewModel,

        // This is a list of dependencies to inject into the plugin, the order which you request
        // here is the order in which the dependencies will be injected into your view model upon
        // instantiation via the parameters argument
        ["settingsViewModel"],

        // Finally, this is the list of selectors for all elements we want this view model to be bound to.
        ["#tab_plugin_phrozen_connector"]
    ]);
});
