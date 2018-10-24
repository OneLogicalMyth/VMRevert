import urllib, json
from pfsense import pfsense
from os.path import abspath, exists

# check if the config.json file is present
f_config = abspath("config.json")
if not exists(f_config):
    print "config.json not found"
    sys.exit()

# first load the configuration
with open(f_config, 'r') as json_data:
    config = json.load(json_data)

# place config into vars
PFUSER = config.get('pfuser', None)
PFPASS = config.get('pfpass', None)
PFURL = config.get('pfurl', None)


class tables(object):

    def __init__(self):
        p = pfsense(PFURL)
        s = p.login(PFUSER,PFPASS)
        self.arp_table = p.get_arptable(s)
        self.vpn_users = p.get_vpnclients(s)

    def create_vpnlist(self):
        html = ""
        for user in self.vpn_users:
            if user["clients"]:
                for u in user["clients"]:
                    if u["username"] != '[error]':
                        html += '<li class="list-group-item"><div class="d-flex w-100 justify-content-between"><h5 class="mb-1">{username}</h5></div><p class="mb-1">Connected since {since}.</p></li>'.format(username=u["username"],since=u["connected_since"])

        if not html:
           return '<li class="list-group-item list-group-item-warning">No Connections</li>'

        return html

    def create_table(self, folder_name, title, type, vms):

        # build type
        if type == 'all':
            revert_display = 'Revert All'
            revert_path = '/revert/all/'
        else:
            revert_display = 'Revert'
            revert_path = '/revert/one/{urlname}'

        # build table
        TableHead = '<div class="d-flex justify-content-between flex-wrap flex-md-nowrap align-items-center pb-2 mb-3 border-bottom"><h1 class="h2">{title}</h1></div>'.format(title=title)
        TableBody = '<div class="table-responsive"><table class="table table-striped table-sm"><thead><tr><th>Name</th><th>IP Address</th><th>Power State</th><th>Actions</th></tr></thead><tbody>'
        i = 0
        for vm in vms:

            IP = self.arp_table.loc[self.arp_table["MAC address"].str.match(vm["MAC"].lower())]
            if IP["IP address"].values:
                IP = IP["IP address"].values[0]
            else:
                IP = ""

            # build type
            if type == 'all':
                revert_display = 'Revert All'
                revert_path = '/revert/all/' + urllib.quote_plus(folder_name)
            else:
                revert_display = 'Revert'
                revert_path = '/revert/one/' + urllib.quote_plus(vm["name"])

            if vm["state"] == 'poweredOn':
                state = '<i data-feather="thumbs-up" style="color: green;"></i>'
            elif vm["state"] == 'poweredOff':
                state = '<i data-feather="thumbs-down" style="color: red;"></i>'


            TableBody += '<tr><td>{name}</td><td>{mac}</td><td>{state}</td><td><a href="{path}" class="badge badge-info">{display}</a></td></tr>'.format(path=revert_path,display=revert_display,name=vm["name"],state=state,mac=IP)
        TableFooter = '</tbody></table></div>'

        return TableHead + TableBody + TableFooter

