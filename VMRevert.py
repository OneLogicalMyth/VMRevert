from flask import Flask, render_template, redirect, url_for
from os.path import abspath, exists
from vmware import vmware
from tables import tables
import json, sys, urllib

# check if the config.json file is present
f_config = abspath("config.json")
if not exists(f_config):
    print "config.json not found"
    sys.exit()

# first load the configuration
with open(f_config, 'r') as json_data:
    config = json.load(json_data)

# place config into vars
VCENTER = config.get('vcenter', None)
USERNAME = config.get('username', None)
PASSWORD = config.get('password', None)
FOLDERS = config.get('folders', None)

# quit if nothing is set
if not VCENTER or not USERNAME or not PASSWORD or not FOLDERS:
    print "Configuration is missing in config.json"
    sys.exit()

app = Flask(__name__)


# template function
def index(status,alerttype):

    # connect to vmware
    obj_vmware = vmware()
    connection = obj_vmware.connect(VCENTER, USERNAME, PASSWORD)

    # build the tables
    tbl = tables()
    html_tables = ''
    for folder in FOLDERS:
        vms = obj_vmware.get_folder_vms(connection, folder["name"])
        html_tables += tbl.create_table(folder["name"], folder["title"], folder["revert_type"], vms)

    # create VPN user list
    list = tbl.create_vpnlist()

    # disconnect from vcenter
    obj_vmware.disconnect(connection)

    return render_template('index.html', content=html_tables, vpn=list, status=status, alerttype=alerttype)


# start application routes
@app.route('/')
def home():
    return index("","")

@app.route('/status/<alerttype>/<status>')
def status(alerttype,status):
    return index(status,alerttype)

@app.route('/revert/<type>/<name>')
def revert(type, name):

    # check if type is correct
    if type not in ['all', 'one']:
        status = 'Invalid revert type given.'
        alerttype = 'danger'
        return index(status,alerttype)

    # url decode to normal string
    name = urllib.unquote_plus(name)
    status = '{name} has been reverted, please allow 5 minutes to complete.'.format(name=name)
    alerttype = 'success'

    # connect to vmware
    obj_vmware = vmware()
    connection = obj_vmware.connect(VCENTER, USERNAME, PASSWORD)

    # revert VM
    if type == 'all':
        vms = obj_vmware.get_folder_vms(connection, name)

        if not vms:
            status = '{name} was not found and not reverted.'.format(name=name)
            alerttype = 'danger'
            return index(status,alerttype)

        for vm in vms:
            result = obj_vmware.revert_vm(connection, vm["name"])
    else:
        result = obj_vmware.revert_vm(connection, name)

    # check if a VM was reverted
    if not result:
        status = '{name} was not found and not reverted.'.format(name=name)
        alerttype = 'danger'


    # disconnect from vcenter
    obj_vmware.disconnect(connection)

    return redirect(url_for('status', alerttype=alerttype, status=status), code=302)


if __name__ == '__main__':
    app.run()
