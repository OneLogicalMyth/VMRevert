# VMRevert
A script I threw together to revert VMs to snapshot.

# pre-reqs
* You will need flask installed `pip install flask`.
* You will need the wsgi module installed `apt install libapache2-mod-wsgi`.

# Setup
* Copy the contents of the repositry to `/var/www/VMRevert/`.
* Move the file `VMRevert.conf` to `/etc/apache2/sites-available/` and enable the site.
* Fill in the `config.json` with the correct credentials and folders.
* Restart apache.
