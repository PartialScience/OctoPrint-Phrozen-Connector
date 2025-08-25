# SMB Storage Setup

This plugin can mount your Phrozen printer's SMB share directly into OctoPrint's file manager as a "Phrozen SMB" folder.

## Prerequisites

1. **Install cifs-utils** (already done if you followed the main setup):
   ```bash
   sudo apt update && sudo apt install -y cifs-utils
   ```

2. **SMB Share Access**: Your Phrozen printer must have SMB sharing enabled and you need valid credentials.

## How It Works

When you enable SMB storage in the plugin settings:
1. The plugin creates a "Phrozen SMB" folder in your uploads directory
2. It mounts your printer's SMB share to this folder
3. Files appear directly in OctoPrint's Files tab under "Phrozen SMB"
4. You can upload files directly to your printer or download files from it

## Security Notes

- The plugin first tries to mount without sudo privileges (user mount)
- If that fails, it falls back to using sudo
- For security, consider setting up sudoers rules for the OctoPrint user:

```bash
# Add this to /etc/sudoers (use visudo):
octoprint ALL=(ALL) NOPASSWD: /bin/mount, /bin/umount
```

## Configuration

In the plugin settings:
1. Check "Enable SMB Storage"
2. Enter your printer's IP address
3. Provide SMB username and password
4. Set the share name (usually "share" for Phrozen printers)
5. Save settings and restart OctoPrint

## Troubleshooting

- Check OctoPrint logs for mounting errors
- Ensure the printer's SMB share is accessible from your network
- Verify credentials are correct
- Make sure cifs-utils is installed
- For permission issues, check the sudoers configuration above

## Manual Testing

You can test the SMB connection using the "Test SMB Connection" button in the settings, or manually:

```bash
# Create a test mount point
mkdir /tmp/test_smb

# Test mount
sudo mount -t cifs //PRINTER_IP/share /tmp/test_smb -o username=USERNAME,password=PASSWORD

# Check files
ls /tmp/test_smb

# Unmount
sudo umount /tmp/test_smb
rmdir /tmp/test_smb
```
