from vmware import vmware
import pandas as pd
from requests import Session
from re import findall
from argparse import ArgumentParser
import datetime
import urllib3
import sys, json
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


class pfsense(object):

    def __init__(self,url):
        self.openvpn_status_url = url + '/status_openvpn.php'
        self.url = url

    def get_csrf(self,content):
        csrf_token = findall('name=\'__csrf_magic\'\s*value="([^"]+)"', content)[0]
        return csrf_token

    def get_vpnclients(self,pfsession):
        response = pfsession.get(self.openvpn_status_url, verify=False)
        df = pd.read_html(response.text)[2]
        df1 = df[df['Common Name'] != '[error]']
        df2 = df1[df1['Common Name'] != 'Status: Actions:']
        if len(df2) > 0:
            out = []
            for c in df2['Common Name'].tolist():
                out += [c.split(' ')[0]]
            return out
        else:
           return None

    def login(self,username,password):
        pfsession = Session()
        response = pfsession.get(self.url, verify=False)
        csrf_token = self.get_csrf(response.text)
        login_payload = {
                        '__csrf_magic': csrf_token,
                        'usernamefld': username,
                        'passwordfld': password,
                        'login': 'Sign+In'
                        }
        pfsession.post(self.url, data=login_payload, verify=False)

        check_login = pfsession.get(self.url, verify=False)
        login_user  = findall('class="fa fa-sign-out" title="(.*?)"', check_login.text)
        if len(login_user) == 1:
            return pfsession
        else:
            return bool(0)


# login to pfsense check how many VPN clients we have connected
p = pfsense(PFURL)
s = p.login(PFUSER,PFPASS)

# if 0 connected power everything off
clients = p.get_vpnclients(s)
if clients:
    print "The following people are still connected"
    print clients
else:
    print "No clients connected to VPN powering off"
    vm = vmware()
    con = vm.connect(VCENTER,USERNAME,PASSWORD)

    for f in FOLDERS:
        vm.poweroff_folder(con, f['name'])
