import urllib3, ssl, pyVim
from pyVim import connect
from pyVmomi import vim
from pyVim.task import WaitForTask

# disable insecure request warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# disabled SSL certificate verification
context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
context.verify_mode = ssl.CERT_NONE

class vmware(object):

    def __init__(self):
        # disabled SSL certificate verification
        self.context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
        self.context.verify_mode = ssl.CERT_NONE

    def connect(self, vcenter, username, password):
        vcenter_ses = connect.Connect(vcenter, 443, username, password, sslContext=self.context)
        return vcenter_ses

    def disconnect(self, vcenter_ses):
        connect.Disconnect(vcenter_ses)

    def get_obj(self, content, vimtype, name):
        obj = None
        container = content.viewManager.CreateContainerView(
            content.rootFolder, vimtype, True)
        for c in container.view:
            if name:
                if c.name == name:
                    obj = c
                    break
            else:
                obj = c
                break

        return obj

    def get_current_snap_obj(self, snapshots, snapob):
        snap_obj = []
        for snapshot in snapshots:
            if snapshot.snapshot == snapob:
                snap_obj.append(snapshot)
            snap_obj = snap_obj + self.get_current_snap_obj(snapshot.childSnapshotList, snapob)
        return snap_obj


    def get_folder_vms(self, vcenter_ses, folder_name):
        content = vcenter_ses.RetrieveContent()
        cluster = self.get_obj(content, [vim.Folder], folder_name)

        if cluster:
            VMs = []
            for VM in cluster.childEntity:

            	# just place NoShow in your VM name for it not to display
                if "NoShow" in VM.name:
                    continue

                #grab MAC address for VM
                vm_obj = self.get_obj(content, [vim.VirtualMachine], VM.name)
                for dev in vm_obj.config.hardware.device:
                    if isinstance(dev, vim.vm.device.VirtualEthernetCard):
                        MacAddress = dev.macAddress

                #return object
                VMs += [{ "name": VM.name, "state": VM.runtime.powerState, "MAC": MacAddress }]

	    return VMs
        else:
            return None

    def revert_vm(self, vcenter_ses, vm_name):
        content = vcenter_ses.RetrieveContent()
        vm = self.get_obj(content, [vim.VirtualMachine], vm_name)

        if vm:
            current_snapref = vm.snapshot.currentSnapshot
            current_snap_obj = self.get_current_snap_obj(vm.snapshot.rootSnapshotList, current_snapref)

            current_snap_obj[0].snapshot.RevertToSnapshot_Task()

            return True
        else:
            return None

    def poweroff_folder(self, vcenter_ses, folder_name):
        content = vcenter_ses.RetrieveContent()
        cluster = self.get_obj(content, [vim.Folder], folder_name)

        if cluster:
            for vm in cluster.childEntity:
                if vm.runtime.powerState == vim.VirtualMachinePowerState.poweredOn:
                    vm.PowerOff()

