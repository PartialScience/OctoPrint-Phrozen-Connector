/**
 * Phrozen API Connector Class
 */
class PhrozenApiConnector {
    
    constructor() {}
    
    /**
     * Get devices from Phrozen API via OctoPrint plugin endpoint
     * @param {number} offset - Starting offset for pagination (default: 0)
     * @param {number} count - Number of devices to retrieve (default: 10)
     * @returns {Promise} - Promise that resolves with devices data
     */
    async getDevices(offset = 0, count = 10) {
        const response = await fetch(`/plugin/phrozen_connector/devices?offset=${offset}&count=${count}`, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'X-Api-Key': UI_API_KEY
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    }

}
