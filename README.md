# VMRevert
A script I threw together to revert VMs to snapshot.

# pre-reqs
* You will need flask installed `pip install flask`.
* You will need the [pyvmomi](https://github.com/vmware/pyvmomi) installed `pip install --upgrade pyvmomi`
* You will need the wsgi module installed `apt install libapache2-mod-wsgi`.

# Setup
* Copy the contents of the repositry to `/var/www/VMRevert/`.
* Move the file `VMRevert.conf` to `/etc/apache2/sites-available/` and enable the site.
* Fill in the `config.json` with the correct credentials and folders.
* Restart apache.

# Auto Power Off
If you use pfsense to VPN into a lab environment the power off script will parse the current OpenVPN status page for a client list and if no connections are present power off all VMs within the configured folders. I run this as a cron job every hour. Just snapshot the VMs in a powered on state.
