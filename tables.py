import urllib

class tables(object):

    def __init__(self):
        pass

    def create_table(self, folder_name, title, type, vms):

        # build type
        if type == 'all':
            revert_display = 'Revert All'
            revert_path = '/revert/all/'
        else:
            revert_display = 'Revert'
            revert_path = '/revert/one/{urlname}'

        # build table
        TableHead = '<div class="row"><div class="col-sm-12 col-lg-12"><h4><strong>AD Lab - Hack Boxes</strong></h4><table class="display"><thead><tr><th>VM Name</th><th>Current State</th><th>Actions</th></tr></thead>'
        TableBody = ''
        i = 0
        for vm in vms:

            # build type
            if type == 'all':
                revert_display = 'Revert All'
                revert_path = '/revert/all/' + urllib.quote_plus(folder_name)
            else:
                revert_display = 'Revert'
                revert_path = '/revert/one/' + urllib.quote_plus(vm["name"])


            if i  == 0:
                row = 'odd'
                i = 1
            else:
                row = 'even'
                i = 0

            TableBody += '<tr class="{row}"><td>{name}</td><td>{state}</td><td><a href="{path}">{display}</a></td></tr>'.format(path=revert_path,display=revert_display,name=vm["name"],state=vm["state"],row=row)
        TableFooter = '</table></div></div>'

        return TableHead + TableBody + TableFooter

