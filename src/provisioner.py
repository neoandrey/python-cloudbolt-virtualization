from json import JSONEncoder
from pyVmomi import vim
from pyVim.connect import SmartConnect, Disconnect
from pyVim.task import WaitForTask
from datetime import datetime
import argparse,traceback, json,   ssl,requests, math
import getpass

requests.packages.urllib3.disable_warnings()
context = ssl._create_unverified_context()

class VMTemplate():
   name  = "CBVM"
   nmCpu = 2
   memoryGb = 4
   diskList = []
   template = ""
   networkName= ""
   storageFormat="Thick"
   vmhost= ""
   hasCD = False,
   hasFloppy= False
   cluster= "NetApp-HCI-Cluster-01"
   osType=""
   ip = ""
   mask = ""
   gateway= ""
   vcenterAddress= ""
   vcenterUser= ""
   vcenterPassword= ""
   dnsList= []
   osDistribution= ""
   ownerEmail= ""
   senderEmail = "compumgr@interswitchgroup.com"
   emailUser= ""
   emailPassword = ""
   emailServer = ""
   requestURL= "Cloudbolt Special Server Request"
   emailport= 25
   useLDAP = False
   sendEmail= True
   domainUser = ""
   domainPassword = ""

   def get_datastore_name(self):
      return self.diskList[0].split(':')[1]


   def get_fields(self):
     return [x for x in VMTemplate.__dict__.keys() if '_' not in x] #['name','nmCpu','memoryGb','diskList','template','networkName','storageFormat','vmhost','hasCD','hasFloppy','cluster','osType','ip','mask','gateway','vcenterAddress','vcenterUser','vcenterPassword','dnsList','osDistribution','ownerEmail','senderEmail','emailUser','emailPassword','emailServer','requestURL','emailport','useLDAP','sendEmail']

   def init_config(self,json_data):
     for field in  self.get_fields():
        if field in json_data:
          setattr(self, field, json_data[field])
     return self

   def to_json(self):
     json_object ={}
     for  i in  dir(self): 
       if '_' not in  str(i) and i not in vars(VMTemplate()).keys() and str(i) not in ['toJson','default','iterencode','encode']:
         json_object[i] =getattr(self, i)
     return json.dumps(json_object) 

def main():
    parser = argparse.ArgumentParser(description="")

    parser.add_argument("-c",  "--config",        type=str,  default='', help="JSON input string")
    parser.add_argument("-f",  "--configfile",    type=str,  default='',      help="JSON input file")
    parser.add_argument("-v",  "--verbose",       type=int,  default=0, help="show debug")

    args                           = parser.parse_args()
    parameters ={}
    if  args.config:
        parameters['config']         = args.config
    elif  args.verbose:
        parameters['verbose']       = args.verbose
    elif  args.configfile:
        parameters['configfile']       = args.configfile
    #si = service_instance.connect(args)
    #print(parameters)
    vm_config_list = []

    if  'config' in parameters:

       vm_info= json.loads(parameters['config'])
       for cfg in vm_info:
          vm_config_list.append(cfg)
    elif  'configfile' in parameters:
       cfg_str =""
       with open( parameters['configfile'], "r") as cfg_file:
         cfg_str= cfg_file.read()
       #print(VMTemplate().get_fields())
       for field in  VMTemplate().get_fields():
        # print("field: "+field)
         cfg_str =  cfg_str.replace(field+":",'"{}":'.format(field))
       #print('cfg_str: {}'.format(cfg_str))
       vm_info = json.loads(cfg_str)
       if type(vm_info) is list:
         for cfg in vm_info:
           vm_template = VMTemplate().init_config(cfg)
           #print(vm_template)
           create_server(vm_template)
       else:
           vm_template = VMTemplate().init_config(vm_info)
           #print(vm_template)          
           create_server(vm_template)

def get_domain_from_ip(ip):
  vm_ip_to_domain_map    =  {'172.26': 'TEST.INTERSWITCH.COM','172.25': 'TEST.INTERSWITCH.COM','172.24': 'TEST.INTERSWITCH.COM', '172.35': 'INTERSWITCH.COM', '172.254': 'TEST.INTERSWITCH.COM', '172.35': 'INTERSWITCH.COM', '172.16':'INTERSWITCHNG.COM', '172.38':'INTERSWITCH.COM','172.37':'INTERSWITCHNG.COM' }
  ip_prefix = ip.split('.')[0]+'.'+ip.split('.')[1]
  return vm_ip_to_domain_map[ip_prefix]

def wait_for_task(task):
    """ wait for a vCenter task to finish """
    task_done = False
    while not task_done:
        if task.info.state == 'success':
            return task.info.result

        if task.info.state == 'error':
            print("there was an error")
            print(task.info.error)
            task_done = True

def create_server(vm_config):

    if vm_config.vcenterUser is None or vm_config.vcenterUser=="":
       vm_config.vcenterUser = input("Please type username: ")
    if vm_config.vcenterPassword is None or vm_config.vcenterPassword=="":
       vm_config.vcenterPassword = getpass.getpass(prompt="Please type password: ")
  
    if vm_config.domainUser is None or vm_config.domainUser=="":
      vm_config.domainUser= input("Please type domain username: ")
    if vm_config.domainPassword is None or vm_config.domainPassword =="":
      vm_config.domainPassword  = getpass.getpass(prompt="Please type password for domain user: ")
    si  =None
    try:
       si = SmartConnect(host=vm_config.vcenterAddress, user=vm_config.vcenterUser,pwd=vm_config.vcenterPassword,port=443,sslContext=context)
    except Exception as e:
       traceback.print_exc()
    if si:
      content = si.RetrieveContent()
      vmObjView = content.viewManager.CreateContainerView(content.rootFolder,[vim.VirtualMachine],True)
      vmList = vmObjView.view
      vmObjView.Destroy()
      host = None
      vm_template = [vm  for vm in vmList if vm.name.lower() == vm_config.template.lower()]
      vm_template = vm_template[0] if vm_template else None
      if vm_template:
        vm_exists = [vm  for vm in vmList if vm.name.lower() == vm_config.name.lower() ]
        if not vm_exists:
          datacenter = None
          cluster = None
          cluster_list = None
          datastore = None
          for child in content.rootFolder.childEntity:
            datacenter           = child
            hostFolder           = datacenter.hostFolder
            cluster_list         = hostFolder.childEntity
          cluster =[cluster for cluster in cluster_list  if  cluster.name.lower() == vm_config.cluster.lower() ]
          cluster = cluster[0]  if cluster else None
          if cluster:
            host_list =  cluster.host if   hasattr(cluster, 'host') else []
            host = [vmHost for vmHost  in host_list if  vmHost.name.lower() == vm_config.vmhost.lower()]
            host = host[0] if host else None
            if host:
              datastore_list =  host.datastore if   hasattr(host, 'datastore') else []
              datastore = [ds for ds  in datastore_list if  ds.name.lower() == vm_config.get_datastore_name().lower()]
              datastore = datastore[0] if datastore else None
              if datastore:
                adaptermap = vim.vm.customization.AdapterMapping()
                adaptermap.adapter = vim.vm.customization.IPSettings()
                adaptermap.adapter.ip = vim.vm.customization.FixedIp()
                adaptermap.adapter.ip.ipAddress = vm_config.ip 
                adaptermap.adapter.subnetMask =vm_config.mask
                adaptermap.adapter.gateway =vm_config.gateway
                globalip = vim.vm.customization.GlobalIPSettings(dnsServerList=vm_config.dnsList)
                # Hostname settings
                
                ident = None
                if  'linux' in vm_config.osType.lower() or 'centos' in vm_config.osType.lower() or 'ubuntu' in vm_config.osType.lower() or 'redhat' in vm_config.osType.lower() :
                  ident = vim.vm.customization.LinuxPrep(domain=vm_config.name, hostName=vim.vm.customization.FixedName(name=vm_config.name))
                elif 'windows' in vm_config.osType.lower():
                  ident = vim.vm.customization.Sysprep()
                  ident.guiUnattended = vim.vm.customization.GuiUnattended()
                  ident.guiUnattended.autoLogon = False
                  ident.guiUnattended.password  = vim.vm.customization.Password()
                  ident.guiUnattended.password.value = 'W1nd0w$123'
                  ident.guiUnattended.password.plainText = True  #the password passed over is not encrypted 
                  ident.userData = vim.vm.customization.UserData()
                  ident.userData.computerName = vim.vm.customization.FixedName()
                  ident.userData.computerName.name = vm_config.name
                  ident.userData.fullName = "isw_user"
                  ident.userData.orgName = "INTERSWITCH LIMITED"
                  ident.identification = vim.vm.customization.Identification(joinDomain  = get_domain_from_ip(vm_config.ip),domainAdmin = vm_config.domainUser+'@'+ get_domain_from_ip(vm_config.ip),domainAdminPassword = vim.vm.customization.Password(value=vm_config.domainPassword, plainText=True) )
                
                # Putting all these pieces together in a custom spec
                customspec = vim.vm.customization.Specification(nicSettingMap=[adaptermap], globalIPSettings=globalip, identity=ident)
                
                vmconf = get_config_spec(vm_config)

                # Creating relocate spec and clone spec
                resource_pool = cluster.resourcePool
                if resource_pool:
                  relocateSpec = vim.vm.RelocateSpec(pool=resource_pool)
                  relocateSpec.datastore = datastore
                  #cloneSpec = vim.vm.CloneSpec(powerOn=True, template=False, location=relocateSpec, customization=None, config=vmconf)
                  cloneSpec = vim.vm.CloneSpec(powerOn=True, template=False, location=relocateSpec, customization=customspec, config=vmconf)
                  print("Creating  server...")
                  task = vm_template.Clone(folder=vm_template.parent, name=vm_config.name, spec=cloneSpec)
                  
                  wait_for_task(task)
                  print("{} server has been successfully created.".format(vm_config.name))
                  vmObjView = content.viewManager.CreateContainerView(content.rootFolder,[vim.VirtualMachine],True)
                  vmList = vmObjView.view
                  vmObjView.Destroy()
                  new_vm = [vm  for vm in vmList if vm.name.lower() == vm_config.name.lower()]
                  new_vm = new_vm[0] if new_vm else None   
                  if new_vm:
                    WaitForTask(new_vm.PowerOff())
                    add_disks(new_vm,vm_config, host)
                    update_nic(new_vm,vm_config, host)
                    set_attribute(new_vm,vm_config, content) 
                    WaitForTask(new_vm.PowerOn())
                    #send_notification()  
                  

                else:
                  print("The Resource Pool of host {h} was not found.".format(h=host.name))
              else: 
                print('Datastore {d} is not connected to host {h} '.format(d=vm_config.get_datastore_name(),h=vm_config.vmhost))
            else:
              print('Host {h} does not exist in cluster {c} '.format(h=vm_config.vmhost,c=vm_config.cluster))
          else:
            print('Cluster {} does not exist'.format(vm_config.cluster))
        else:
          print('{} server already exists. Please change the name of the new server'.format(vm_config.name))
      else:
        print('{} template does not exist'.format(vm_config.template) )

def add_disks(vm, vm_config, host):
    spec = vim.vm.ConfigSpec()
    disk_index = 0
    disk_to_datastore_list = []
    processed_disk_list =[]
    for disk_def  in vm_config.diskList:
       size    = disk_def.split(':')[0]
       ds_name = disk_def.split(':')[1]
       disk_to_datastore_list.append((size,ds_name))
    
    for disk_mapping  in  disk_to_datastore_list:
        disk_file_name        =     None
        disk_index            +=1
        disk_size             =  disk_mapping[0]
        datastore_name        =  disk_mapping[1]     
        datastore_list =  host.datastore if   hasattr(host, 'datastore') else []
        datastore = [ds for ds  in datastore_list if  ds.name.lower() == datastore_name.lower()]
        datastore = datastore[0] if datastore else None
        if datastore:
            unit_number = 0
            controller = None
            capacity_in_kb = 0
            disk_mode = None
            disk_key = 0
            controller_key = 0
            for device in vm.config.hardware.device:
                if  hasattr(device.backing, 'fileName'):
                    disk_file_name = device.backing.fileName
                    unit_number = int(device.unitNumber) + 1
                    capacity_in_kb = device.capacityInKB
                    disk_mode = device.backing.diskMode
                    disk_key  = device.key
                    controller_key = device.controllerKey
                    # unit_number 7 reserved for scsi controller
                    if unit_number == 7:
                        unit_number += 1
                    if unit_number >= 16:
                        print("we don't support this many disks")
                        return -1
                if isinstance(device, vim.vm.device.VirtualSCSIController):
                    controller = device
            if controller is None:
                print("Disk SCSI controller not found!")
                return -1
            
            if disk_index == unit_number and disk_file_name not in processed_disk_list:
              new_disk_kb = int(disk_size) * 1024 * 1024
              if new_disk_kb > capacity_in_kb:
                dev_changes = []
                disk_spec = vim.vm.device.VirtualDeviceSpec()
                disk_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.edit
                disk_spec.device = vim.vm.device.VirtualDisk()
                disk_spec.device.key = disk_key
                disk_spec.device.backing = vim.vm.device.VirtualDisk.FlatVer2BackingInfo()
                disk_spec.device.backing.fileName = disk_file_name
                disk_spec.device.backing.diskMode = disk_mode
                disk_spec.device.controllerKey = controller_key
                disk_spec.device.unitNumber =unit_number
                disk_spec.device.capacityInKB = new_disk_kb
                dev_changes.append(disk_spec)
                spec = vim.vm.ConfigSpec()
                spec.deviceChange = dev_changes
                WaitForTask(vm.ReconfigVM_Task(spec=spec))
                print("%sGB disk has been extended to %sGB for %s" % (capacity_in_kb, disk_size, vm.config.name))
                processed_disk_list.append(disk_file_name)
            else:
              dev_changes = []
              new_disk_kb = int(disk_size) * 1024 * 1024
              disk_spec = vim.vm.device.VirtualDeviceSpec()
              disk_spec.fileOperation = "create"
              disk_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
              disk_spec.device = vim.vm.device.VirtualDisk()
              disk_spec.device.backing = vim.vm.device.VirtualDisk.FlatVer2BackingInfo()
              disk_spec.device.backing.diskMode = 'persistent'
              disk_spec.device.unitNumber = unit_number
              disk_spec.device.capacityInKB = new_disk_kb
              disk_spec.device.backing.datastore = datastore
              disk_spec.device.controllerKey = controller.key
              dev_changes.append(disk_spec)
              spec.deviceChange = dev_changes
              WaitForTask(vm.ReconfigVM_Task(spec=spec))
              print("%sGB disk added to %s" % (disk_size, vm.config.name))
    return 0

def  update_nic(vm, vm_config, host):   
    device_change = []
    spec = vim.vm.ConfigSpec()
    portgroup_list= host.network if hasattr(host,'network') else []
    network_port_group  = [port_group for port_group in portgroup_list  if port_group.name == vm_config.networkName ]
    network_port_group = network_port_group[0] if network_port_group else portgroup_list[0]
    for device in vm.config.hardware.device:
        if isinstance(device, vim.vm.device.VirtualEthernetCard):
            nicspec = vim.vm.device.VirtualDeviceSpec()
            nicspec.operation = vim.vm.device.VirtualDeviceSpec.Operation.edit
            nicspec.device = device
            nicspec.device.wakeOnLanEnabled = True
            
            network = network_port_group
            dvs_port_connection = vim.dvs.PortConnection()
            dvs_port_connection.portgroupKey = network.key
            dvs_port_connection.switchUuid = network.config.distributedVirtualSwitch.uuid
            nicspec.device.backing = vim.vm.device.VirtualEthernetCard.DistributedVirtualPortBackingInfo()
            nicspec.device.backing.port = dvs_port_connection

            nicspec.device.connectable = vim.vm.device.VirtualDevice.ConnectInfo()
            nicspec.device.connectable.startConnected = True
            nicspec.device.connectable.allowGuestControl = True
            device_change.append(nicspec)
            spec.deviceChange  = device_change
            break
    WaitForTask(vm.ReconfigVM_Task(spec=spec))
    print("%s server has been added to the %s network" % (vm.config.name,network_port_group.name))
    return 0

def set_attribute(vm, vm_config, content):
  cfm= content.customFieldsManager
  fields = content.customFieldsManager.field
  for field in fields:
      if  'custodian' in field.name.lower():
         cfm.SetField(entity=vm, key=field.key, value=vm_config.ownerEmail +' ('+datetime.now().strftime("%Y-%m-%d %H:%M:%S")+')')

def get_config_spec(vm_config):
    config = vim.vm.ConfigSpec()
    config.annotation = "Created by "+vm_config.ownerEmail +' on '+datetime.now().strftime("%Y-%m-%d at %H:%M:%S") #vm_config.annotation
    config.memoryMB = 1024 *  int(vm_config.memoryGb)
    config.name = vm_config.name
    config.numCPUs = vm_config.nmCpu
    files = vim.vm.FileInfo()
    files.vmPathName = "["+vm_config.get_datastore_name()+"]"
    config.files = files
    config.swapPlacement = 'vmDirectory'
    config.numCoresPerSocket = math.floor(int(vm_config.nmCpu)/2)
    #config.memoryReservationLockedToMax=False
    #config.memoryHotAddEnabled= False
    #config.cpuHotAddEnabled=False
    config.createDate= datetime.now()
    config.tools =vim.vm.ToolsConfigInfo(syncTimeWithHost= False,toolsUpgradePolicy    = vim.vm.ToolsConfigInfo.UpgradePolicy.upgradeAtPowerCycle)
    return config


if __name__ == "__main__":
      main()