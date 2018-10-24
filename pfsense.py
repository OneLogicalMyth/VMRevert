from bs4 import BeautifulSoup
import pandas as pd
from requests import Session
from re import findall
from argparse import ArgumentParser
import datetime
import urllib3
import json
from os.path import abspath, exists
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class pfsense(object):

    def __init__(self,url):
        self.alias_edit_url = url + '/firewall_aliases_edit.php'
        self.alias_list_url = url + '/firewall_aliases.php'
        self.openvpn_status_url = url + '/status_openvpn.php'
        self.arptable_url = url + '/diag_arp.php'
        self.url = url

    def merge_dicts(self,*dict_args):
        result = {}
        for dictionary in dict_args:
            result.update(dictionary)
        return result

    def get_csrf(self,content):
        csrf_token = findall('name=\'__csrf_magic\'\s*value="([^"]+)"', content)[0]
        return csrf_token

    def apply_changes(self,pfsession):
        response = pfsession.get(self.alias_list_url, verify=False)
        csrf_token = self.get_csrf(response.text)
        apply_payload = {
                        '__csrf_magic': csrf_token,
                        'apply': 'Apply changes',
                        'tab': 'ip'
                        }
        response = pfsession.post(self.alias_list_url, data=apply_payload, verify=False)
        return response.status_code

    def get_vpnclients(self,pfsession):
        response = pfsession.get(self.openvpn_status_url, verify=False)
        soup = BeautifulSoup(response.text, 'html.parser')
        data = []
        divs = soup.findAll('div', attrs={'class':'panel panel-default'})

        for div in divs:
            if div.has_attr('id'):
                continue #VPN user tables have no id attr

            title = div.find('h2', attrs={'class':'panel-title'}).text
            if title == 'Client Instance Statistics':
                continue

            table_body = div.find('tbody')
            rows = table_body.find_all('tr')

            clients = []
            for row in rows:
                if row.has_attr('id'):
                    cols = row.find_all('td')
                    cols = [ele.text.strip() for ele in cols]
                    username = cols[0].split('\t')[0]
                    EXT_IP = cols[1]
                    VPN_IP = cols[2]
                    ConnectedSince = cols[3]
                    up_down = cols[4].split(' / ')

                    clients += [{
                                  "username": username,
                                  "ext_ip": EXT_IP,
                                  "vpn_ip": VPN_IP,
                                  "connected_since": ConnectedSince,
                                  "bytes_s": up_down[0],
                                  "bytes_r": up_down[1]
                               }]

            data += [{"vpn_name": title, "clients": clients}]
        return data


    def get_arptable(self, pfsession):
        response = pfsession.get(self.arptable_url, verify=False)
        df = pd.read_html(response.text)[0]
        return df

    def add_alias(self,pfsession,alias,address,detail):
        alias_data = self.get_alias(pfsession,alias)
        descr_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        next_id = str(len(alias_data['address_ip']))
        alias_data['address_ip'].append((u'address' + next_id,u'' + address))
        alias_data['address_detail'].append((u'detail' + next_id,u'' + detail))
        addresses = dict(alias_data['address_ip'])
        details = dict(alias_data['address_detail'])
        alias_payload_base = {
                             '__csrf_magic': alias_data['csrf'],
                             'origname': alias_data['alias_name'],
                             'name': alias_data['alias_name'],
                             'id': alias,
                             'tab': 'ip',
                             'descr': 'Last updated on the ' + descr_date,
                             'type': 'host',
                             'save': 'Save',
                             }
        alias_payload = self.merge_dicts(alias_payload_base,addresses,details)
        response = pfsession.post(self.alias_edit_url, data=alias_payload, verify=False)
        return response.status_code

    def get_alias(self,pfsession,alias):
        response = pfsession.get(self.alias_edit_url + '?id=' + alias, verify=False)
        alias_name = findall('name="origname".*?value="([^"]+)', response.text)[0]
        addresses  = findall('name="(address\d+)".*?value="([^"]+)', response.text)
        details = findall('name="(detail\d+)".*?value="([^"]+)', response.text)
	csrf_token = self.get_csrf(response.text)
        results = {
                  'alias_name': alias_name,
                  'address_ip': addresses,
                  'address_detail': details,
                  'csrf': csrf_token
                  }
        return results

    def del_alias(self,pfsession,alias,username):
        alias_data = self.get_alias(pfsession,alias)
        descr_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        address_tmp = dict(alias_data['address_ip'])
        detail_tmp = dict(alias_data['address_detail'])
        details = {}
        addresses = {}
        count = 0
        # loop values to remove IPs matching the username
        for field, value in detail_tmp.iteritems():
            if not value.startswith(username + '|'):
                id = findall('\d+$', field)[0]
                addresses['address' + str(count)] = address_tmp['address' + str(id)]
                details['detail' + str(count)] = detail_tmp[field]
                count += 1
        alias_payload_base = {
                             '__csrf_magic': alias_data['csrf'],
                             'origname': alias_data['alias_name'],
                             'name': alias_data['alias_name'],
                             'id': alias,
                             'tab': 'ip',
                             'descr': 'Last updated on the ' + descr_date,
                             'type': 'host',
                             'save': 'Save',
                             }
        alias_payload = self.merge_dicts(alias_payload_base,addresses,details)
        response = pfsession.post(self.alias_edit_url, data=alias_payload, verify=False)
        return response.status_code

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

