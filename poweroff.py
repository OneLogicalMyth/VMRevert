import sys, os
# set root directory so crontab runs
sys.path.append('/var/www/VMRevert')
os.chdir('/var/www/VMRevert')

from vmware import vmware
from pfsense import pfsense
import pandas as pd
from requests import Session
from re import findall
from argparse import ArgumentParser
import datetime
import urllib3
import json
from os.path import abspath, exists
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


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
PFUSER = config.get('pfuser', None)
PFPASS = config.get('pfpass', None)
PFURL = config.get('pfurl', None)

# login to pfsense check how many VPN clients we have connected
p = pfsense(PFURL)
s = p.login(PFUSER,PFPASS)

# if 0 connected power everything off
clients = p.get_vpnclients(s)

users = []
if clients:
    for c in clients:
        for u in c["clients"]:
            # sometimes you get an error that will keep the VMs powered on...
            if u["username"] != '[error]':
                users.append(u["username"])

# check if we have users and if not shutdown all VMs
if users:
    print "The following people are still connected"
    print json.dumps(users,indent=4)

else:
    print "No clients connected to VPN powering off"
    vm = vmware()
    con = vm.connect(VCENTER,USERNAME,PASSWORD)

    for f in FOLDERS:
        vm.poweroff_folder(con, f['name'])
