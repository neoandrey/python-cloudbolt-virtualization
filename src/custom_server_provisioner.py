"""
This is a working sample CloudBolt plug-in for you to start with. The run method is required,
but you can change all the code within it. See the "CloudBolt Plug-ins" section of the docs for
more info and the CloudBolt forge for more examples:
https://github.com/CloudBoltSoftware/cloudbolt-forge/tree/master/actions/cloudbolt_plugins
"""
#from pprint import pp
from pyVim.task import WaitForTask
from datetime import datetime, date,timedelta
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim, vmodl
import time 
from requests.auth import HTTPBasicAuth
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import traceback, json, os, operator, ssl,requests, math, getpass,smtplib,time,random,paramiko

from utilities.logger import ThreadLogger
from infrastructure.models import Server,User
from utilities.models import ConnectionInfo 
from resourcehandlers.vmware.models import VsphereResourceHandler
from resourcehandlers.vmware.pyvmomi_wrapper import get_connection
from utilities.mail import InvalidConfigurationException
from common.methods import set_progress

#import django.contrib.auth.models.User


logger = ThreadLogger(__name__)

VM_RESOURCE_HANDLER_ID_PROD = 1

host_exclusion_list =['192.168.10.173','192.168.10.186','192.168.10.187','192.168.10.188']

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
   cluster= "CLUSTER-A"
   osType=""
   ip = ""
   mask = ""
   gateway= ""
   vcenterAddress= ""
   vcenterUser= ""
   vcenterPassword= ""
   dnsList= []
   ownerEmail= ""
   senderEmail = "provisioner@APP"
   emailUser= ""
   emailPassword = ""
   emailServer = "smtp.gmail.com"
   requestURL= "Cloudbolt Special Server Request"
   emailport= 587
   useLDAP = False
   sendEmail= True
   domainUser = ""
   domainPassword = ""
   serverAdminName = ""
   serverAdminPassword = ""
   annotation = ""
   usedSpace = 0
   datastore = ""

   def get_datastore_name(self):
      return self.datastore  if self.datastore else self.diskList[0].split(':')[1]

   def get_fields(self):
     return [x for x in VMTemplate.__dict__.keys() if '_' not in x] 

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


def get_domain_from_ip(ip):
  vm_ip_to_domain_map    =  {'192.42': 'TEST.TESTDOMAIN.COM','192.25': 'TEST.TESTDOMAIN.COM','192.24': 'TEST.TESTDOMAIN.COM', '192.89': 'TESTDOMAIN.COM', '192.254': 'TEST.TESTDOMAIN.COM', '192.89': 'TESTDOMAIN.COM', '192.16':'TESTDOMAIN.COM', '192.38':'TESTDOMAIN.COM','192.37':'TESTDOMAIN.COM' }
  ip_prefix = ip.split('.')[0]+'.'+ip.split('.')[1]
  return vm_ip_to_domain_map[ip_prefix]

def wait_for_task(task):
    """ wait for a vCenter task to finish """
    task_done = False
    while not task_done:
        if task.info.state == 'success':
            return task.info.result

        if task.info.state == 'error':
            logger.info("there was an error")
            logger.info(task.info.error)
            task_done = True

requests.packages.urllib3.disable_warnings()
context = ssl._create_unverified_context()
test_url = ''
prod_url = ''
proxies = {'http': '', 'https': ''}

class TeamsChangeLoggerSectionsFact():
   name  = ''
   value = ''
   def __init__(self,name,value):
       self.name     = name
       self.value    = value

   def get_fields(self):
     return [x for x in TeamsChangeLoggerSectionsFact.__dict__.keys() if '_' not in x]

   def to_json(self):
     json_object    = {}
     for  i in  self.get_fields():
        json_object[i] =getattr(self, i)
     return json_object
     
class TeamsChangeLoggerSection():
   activityTitle    = ''
   activitySubtitle = ''
   activityImage    = ''
   facts            = []
   markdown         = True

   def __init__(self,activityTitle=None,activitySubtitle=None,activityImage=None, facts =None, markdown=True):
       self.activityTitle     = activityTitle
       self.activitySubtitle  = activitySubtitle
       self.activityImage     = activityImage
       self.facts   	      = facts 
       self.markdown   	      = markdown

   def get_fields(self):
     return [x for x in TeamsChangeLoggerSection.__dict__.keys() if '_' not in x]

   def to_json(self):
     json_object ={}
     for  i in self.get_fields(): 
        if i=='facts':
            json_object['facts'] = [fact.to_json() for fact  in self.facts]
        else:
            json_object[i] =getattr(self, i)
     return json_object


class  TeamsChangeLogger():
   type            = 'MessageCard'
   context         = 'https://schema.org/extensions'
   themeColor      = '0076D7'
   summary         = ''
   sections        = []
   potentialAction = []
   url             = ''

   def __init__(self, type='MessageCard', context='https://schema.org/extensions', themeColor="0076D7", summary="", sections=None, potentialAction=None, url=None):
       self.type              = type
       self.context           = context
       self.themeColor        = themeColor
       self.summary   	      = summary 
       self.sections   	      = sections
       self.potentialAction   = potentialAction
       self.url               = url

   def get_fields(self):
     return [x for x in TeamsChangeLogger.__dict__.keys() if '_' not in x]

   def to_json(self):
     json_object ={}
     for  i in self.get_fields(): 
         if i == 'type':
            json_object['@type'] =getattr(self, i)
         elif i == 'context':
            json_object['@context'] =getattr(self, i)
         elif i == 'sections':
            json_object['sections'] =[section.to_json() for section in self.sections]
         elif i == 'potentialAction' and self.potentialAction:
            json_object['potentialAction'] =[action.to_json() for action in self.potentialAction]
         elif  i !="url":
            json_object[i] =getattr(self, i)
     return json.dumps(json_object)
    
   def run_post(self):
    json_data = self.to_json()
    logger.info('data: '+json_data)
    requests.post(self.url, json_data,verify=False, proxies=proxies)
    #session = requests.Session()
    #session.trust_env = False
    #print('data: '+json_data)
    #session.post(self.url, json_data,verify=False)


class TeamsChangePotentialAction():
   type    = ''
   name    = ''
   inputs  = []
   actions = []
   targets = []

   def __init__(self,type='',name='',targets='',inputs='',actions=''):
      self.type     = type
      self.name     = name
      self.targets  = targets
      self.inputs   = inputs
      self.actions  = actions

   def get_fields(self):
     return [x for x in TeamsChangePotentialAction.__dict__.keys() if '_' not in x]

   def to_json(self):
     json_object    = {}
     for  i in  self.get_fields():
        if i == 'type':
            json_object['@type'] =getattr(self, i)
        elif i == 'targets' and self.targets:
            json_object['targets'] =[target.to_json() for target in self.targets]
        elif i == 'inputs' and self.inputs:
            json_object['inputs'] =[input.to_json() for input in self.inputs]
        elif i == 'actions' and self.actions:
            json_object['actions'] =[action.to_json() for action in self.actions]
        else:
            json_object[i] =getattr(self, i)
     return json_object


class TeamsChangePotentialActionElement():
  type   =''
  name   = ''
  target = ''
  
  def __init__(self,type,name,target):
    self.type    = type
    self.name    = name
    self.target  = target

  def get_fields(self):
    return [x for x in TeamsChangePotentialActionElement.__dict__.keys() if '_' not in x]

  def to_json(self):
    json_object    = {}
    for  i in  self.get_fields():
        if i == 'type':
            json_object['@type'] =getattr(self, i)
        else:
            json_object[i] =getattr(self, i)
    return json_object

class TeamsChangePotentailInput():
  type        = ''
  id          = ''
  isMultiline = False
  isMultiSelect = False
  title       = ''
  choices     = []
  
  def __init__(self,type,id,isMultiline, isMultiSelect, title,choices):
      self.type          = type
      self.id            = id
      self.isMultine     = isMultiline
      self.isMultiSelect = isMultiSelect
      self.title         = title
      self.choices       = choices

  def get_fields(self):
    return [x for x in TeamsChangePotentailInput.__dict__.keys() if '_' not in x]

  def to_json(self):
    json_object    = {}
    for  i in  self.get_fields():
        if i == 'type':
            json_object['@type'] =getattr(self, i)
        else:
            json_object[i] =getattr(self, i)
    return json_object

class TeamsChangePotentailInputChoices():
  display     = ''
  value       = ''
  
  def __init__(self,display,value):
    self.display    = display
    self.value        = value
  def get_fields(self):
    return [x for x in TeamsChangePotentailInputChoices.__dict__.keys() if '_' not in x]
  
  def to_json(self):
    json_object    = {}
    for  i in  self.get_fields():
        json_object[i] =getattr(self, i)
    return json_object

class TeamsChangePotentailActionTarget():
   os     = 'default'
   uri    = ''

   def __init__(self,os,uri):
      self.os    = os
      self.uri   = uri

   def get_fields(self):
     return [x for x in TeamsChangePotentailActionTarget.__dict__.keys() if '_' not in x]

   def to_json(self):
     json_object    = {}
     for  i in  self.get_fields():
        json_object[i] =getattr(self, i)
     return json_object


def log_change_to_teams(url, vm_template):
    changeLogger        = TeamsChangeLogger()
    changeLogger.url    =  url
    owner  = vm_template.ownerEmail.split('@')[0].split('.')[0]+' '+vm_template.ownerEmail.split('@')[0].split('.')[1]
    template = vm_template.template
    if 'UBUNTU_18.04'.lower() in template.lower():
       template = 'Ubuntu 18.04 LTS'
    elif 'Redhat8.4'.lower()  in template.lower():
       template = 'Redhat 8.4'
    elif 'WINDOWS-2016'.lower()  in template.lower():
       template = 'WINDOWS 2016'
    elif 'WINDOWS-2016'.lower()  in template.lower():
       template = 'WINDOWS 2016'
    elif 'UBUNTU_20.04'.lower()  in template.lower():
       template = 'UBUNTU 20.04'
    owner       = owner
    server_name = vm_template.name
    template= template
    changeLogger.summary= '{o} has just created a new server: {s}'.format(o=owner, s=server_name)
    changeLogger.themeColor = '#cbc1de'
    changeLogger.sections= []
    changeLoggerSection = TeamsChangeLoggerSection()
    changeLoggerSection.activityTitle =changeLogger.summary
    changeLoggerSection.activitySubtitle ='Using the {t} CloudBolt Blueprint'.format(t=template)
    changeLoggerSection.activityImage='1'
    changeLoggerSection.facts = []
    fact1=TeamsChangeLoggerSectionsFact('Server Name',server_name)
    changeLoggerSection.facts.append(fact1) 
    fact2=TeamsChangeLoggerSectionsFact('IP Address',vm_template.ip)
    changeLoggerSection.facts.append(fact2) 
    fact3=TeamsChangeLoggerSectionsFact('Size',str(vm_template.usedSpace))
    changeLoggerSection.facts.append(fact3) 
    fact4=TeamsChangeLoggerSectionsFact('CPU',str(vm_template.nmCpu  )+' vcpu(s)')
    changeLoggerSection.facts.append(fact4)
    fact5=TeamsChangeLoggerSectionsFact('Memory',str(int(vm_template.memoryGb))+' GB')
    changeLoggerSection.facts.append(fact5)
    fact6=TeamsChangeLoggerSectionsFact('EPG',vm_template.networkName )
    changeLoggerSection.facts.append(fact6)
    fact7=TeamsChangeLoggerSectionsFact('Custodian',vm_template.ownerEmail)
    changeLoggerSection.facts.append(fact7)
    fact8=TeamsChangeLoggerSectionsFact('Date',str(datetime.now().strftime("%Y-%m-%d at %H:%M:%S")))
    changeLoggerSection.facts.append(fact8)
    changeLogger.sections.append(changeLoggerSection)
    changeLogger.potentialAction = list()
    action = TeamsChangePotentialAction()
    action.type = 'ActionCard'
    action.name=  'Add a comment'
    action.inputs = list()
    action.inputs.append(TeamsChangePotentailInput("TextInput","comment", False,False,"Add a comment here",None))
    action.actions = list()
    action.actions.append(TeamsChangePotentialActionElement("HttpPOST", "Add comment","https://docs.microsoft.com/outlook/actionable-messages"))
    action.targets = None
    changeLogger.potentialAction.append(action)
    changeLogger.run_post()

def create_server(vm_config):

    si  =None 
   
    try:
        rh=VsphereResourceHandler.objects.get(id=VM_RESOURCE_HANDLER_ID_PROD)
        si                      = get_connection(rh.ip, rh.port, rh.serviceaccount, rh.servicepasswd, ssl_verification=False)
    except Exception as e:
       traceback.print_exc()
       
    if si:
      content = si.RetrieveContent()
      vmList = get_vim_objects('vm')
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
              if vm_config.diskList:
                datastore = [ds for ds  in datastore_list if  ds.name.lower() == vm_config.get_datastore_name().lower()]
                datastore = datastore[0] if datastore else None
              else:
                datastore_to_space_dict ={}
                for ds  in datastore_list:
                    ds_info             = get_datastore_info(ds)
                    datastore_to_space_dict[ds_info['name']] = ds_info['free_space']
                    ds_name_to_space_map    = sorted(datastore_to_space_dict.items(), key=operator.itemgetter(1))
                    for k, v in ds_name_to_space_map:
                        if v > vm_config.usedSpace:
                            datastore = k
                dtsr= [ds for ds  in datastore_list if  ds.name.lower() ==datastore.lower()]
                datastore = dtsr[0] if dtsr else None
              if datastore:
                vm_config.datastore = datastore.name
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
                  if not vm_config.serverAdminPassword or vm_config.serverAdminPassword =="" :
                    ident.guiUnattended.password.value = 'openSesame411!'
                  else:
                    ident.guiUnattended.password.value = 'openSesame411!'

                  ident.guiUnattended.password.plainText = True  #the password passed over is not encrypted 
                  ident.userData = vim.vm.customization.UserData()
                  ident.userData.computerName = vim.vm.customization.FixedName()
                  ident.userData.computerName.name = vm_config.name.replace('_','-')
                  if not vm_config.serverAdminName or vm_config.serverAdminName == "":
                    ident.userData.fullName = "admin_user"
                  else:
                    ident.userData.fullName = vm_config.serverAdminName
                  ident.userData.orgName = "Neocrystals limited"
                  if (vm_config.domainUser and vm_config.domainUser !="" and vm_config.domainUser.lower !="defaut" ) and  (vm_config.domainPassword and vm_config.domainPassword !="" and vm_config.domainPassword.lower !="defaut" ):
                    ident.identification = vim.vm.customization.Identification(joinDomain  = get_domain_from_ip(vm_config.ip),domainAdmin = vm_config.domainUser+'@'+ get_domain_from_ip(vm_config.ip),domainAdminPassword = vim.vm.customization.Password(value=vm_config.domainPassword, plainText=True) )
                  else:
                    ident.identification = vim.vm.customization.Identification()

                
                customspec = vim.vm.customization.Specification(nicSettingMap=[adaptermap], globalIPSettings=globalip, identity=ident)    
                vmconf = get_config_spec(vm_config)

                # Creating relocate spec and clone spec
                resource_pool = cluster.resourcePool
                if resource_pool:
                  relocateSpec = vim.vm.RelocateSpec(pool=resource_pool)
                  relocateSpec.datastore = datastore  
                  #cloneSpec = vim.vm.CloneSpec(powerOn=True, template=False, location=relocateSpec, customization=None, config=vmconf)
                  cloneSpec = vim.vm.CloneSpec(powerOn=True, template=False, location=relocateSpec, customization=customspec, config=vmconf)
                  logger.info("Creating  server...")
                  task = vm_template.Clone(folder=vm_template.parent, name=vm_config.name, spec=cloneSpec)
                  wait_for_task(task)
                  logger.info("{} server has been successfully created.".format(vm_config.name))
                  vmList = get_vim_objects('vm')
                  new_vm = [vm  for vm in vmList if vm.name.lower() == vm_config.name.lower()]
                  new_vm = new_vm[0] if new_vm else None   
                  if new_vm:
                    if new_vm.runtime.powerState == vim.VirtualMachine.PowerState.poweredOn:
                        WaitForTask(new_vm.PowerOff())
                    if vm_config.diskList:
                        add_disks(new_vm,vm_config, host)
                    if vm_config.networkName:
                        update_nic(new_vm,vm_config, host)
                    set_attribute(new_vm,vm_config, content)
                    if new_vm.runtime.powerState == vim.VirtualMachine.PowerState.poweredOff:
                        WaitForTask(new_vm.PowerOn())
                    logger.info("guestID: {}".format(new_vm.guest.guestId))
                    try:
                        if   new_vm.summary.config.guestFullName  == 'Ubuntu Linux (64-BIZ-INTELt)':
                            if not vm_config.serverAdminName:
                                vm_config.serverAdminName = 'admin'
                            if not vm_config.serverAdminPassword:
                                vm_config.serverAdminPassword = 'openSesame411!'
                            set_ubuntu2004_ip(vm_config)
                    except:
                        logger.info("Checking for Ubuntu20.04 provisioning")

                    send_notification(vm_config)
                    log_change_to_teams(prod_url,vm_config)  
                else:
                  logger.info("The Resource Pool of host {h} was not found.".format(h=host.name))
                  raise Exception("The Resource Pool of host {h} was not found.".format(h=host.name))
              else: 
                logger.info('Datastore {d} is not connected to host {h} '.format(d=vm_config.get_datastore_name(),h=vm_config.vmhost))
                raise Exception('Datastore {d} is not connected to host {h} '.format(d=vm_config.get_datastore_name(),h=vm_config.vmhost))
            else:
              logger.info('Host {h} does not exist in cluster {c} '.format(h=vm_config.vmhost,c=vm_config.cluster))
              raise Exception('Host {h} does not exist in cluster {c} '.format(h=vm_config.vmhost,c=vm_config.cluster))
          else:
            logger.info('Cluster {} does not exist'.format(vm_config.cluster))
            raise Exception('Cluster {} does not exist'.format(vm_config.cluster))
        else:
          logger.info('{} server already exists. Please change the name of the new server'.format(vm_config.name))
          raise Exception('{} server already exists. Please change the name of the new server'.format(vm_config.name))
      else:
        logger.info('{} template does not exist'.format(vm_config.template) )
        raise Exception('{} template does not exist'.format(vm_config.template) )

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
                        logger.info("we don't support this many disks")
                        return -1
                if isinstance(device, vim.vm.device.VirtualSCSIController):
                    controller = device
            if controller is None:
                logger.info("Disk SCSI controller not found!")
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
                logger.info("%sGB disk has been extended to %sGB for %s" % (int(capacity_in_kb/(1024*1024*1024)), disk_size, vm.config.name))
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
              logger.info("%sGB disk added to %s" % (disk_size, vm.config.name))
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
            dvs_port_connection.SERVICESUuid = network.config.distributedVirtualSERVICES.uuid
            nicspec.device.backing = vim.vm.device.VirtualEthernetCard.DistributedVirtualPortBackingInfo()
            nicspec.device.backing.port = dvs_port_connection

            nicspec.device.connectable = vim.vm.device.VirtualDevice.ConnectInfo()
            nicspec.device.connectable.startConnected = True
            nicspec.device.connectable.allowGuestControl = True
            device_change.append(nicspec)
            spec.deviceChange  = device_change
            break
    WaitForTask(vm.ReconfigVM_Task(spec=spec))
    logger.info("%s server has been added to the %s network" % (vm.config.name,network_port_group.name))
    return 0

def set_attribute(vm, vm_config, content):
  cfm= content.customFieldsManager
  fields = content.customFieldsManager.field
  for field in fields:
      if  'custodian' in field.name.lower():
         cfm.SetField(entity=vm, key=field.key, value=vm_config.ownerEmail +' ('+datetime.now().strftime("%Y-%m-%d %H:%M:%S")+')')

def get_config_spec(vm_config):
    config = vim.vm.ConfigSpec()
    config.annotation = vm_config.annotation #vm_config.annotation
    config.memoryMB = 1024 *  int(vm_config.memoryGb)
    config.name = vm_config.name
    config.numCPUs = vm_config.nmCpu
    files = vim.vm.FileInfo()
    files.vmPathName = "["+vm_config.get_datastore_name()+"]"
    config.files = files
    config.swapPlacement = 'vmDirectory'
    config.numCoresPerSocket = math.floor(int(vm_config.nmCpu)/2)
    if hasattr(config,'createDate'):
        config.createDate= datetime.now()
    config.tools =vim.vm.ToolsConfigInfo(syncTimeWithHost= False,toolsUpgradePolicy    = vim.vm.ToolsConfigInfo.UpgradePolicy.upgradeAtPowerCycle)
    return config

def  generate_options_for_templates(**kwargs):     
     opts  = []
     vm_list = get_vim_objects('vm')
     for vm in vm_list:
          if vm.config.template:
             opts.append((vm.name,vm.name))
     return opts

def  generate_options_for_network(**kwargs):     
     app_opts  = [('Default','Default')]
     for  key, value  in prod_options['purpose_network'].items():
        displayed_value= value.split('|')[-1]
        app_opts.append((str(value), str(displayed_value)))
     return app_opts
     
def generate_options_for_customization(**kwargs):
    opts =[]
    opts.append(('None','None'))
    opts.append(('Standard','Standard'))
    opts.append(('Detailed','Detailed'))
    return opts
    
def generate_options_for_vcpus(**kwargs):
    opts =[]
    cpu_range=range(2,18,2)
    for  cpu in cpu_range:
        opts.append((cpu,cpu))
    return opts

def generate_options_for_memory(**kwargs):
    opts =[]
    mem_range=range(2,38,2)
    for  mem in mem_range:
        opts.append((mem,mem))
    return opts
       
def generate_options_for_join_domain(**kwargs):
    opts =[]
    opts.append(('No','No'))
    opts.append(('Yes','Yes'))
    return opts

prod_options = {"purpose": ["APPLICATION-1", "APPLICATION-2", "APPLICATION-3", "APPLICATION-4", "APPLICATION-5", "APPLICATION-6", "APPLICATION-7", "APPLICATION-8", "TEST", "OTHERS", "APPLICATION-9", "APPLICATION-10", "BIZ-INTEL", "ELK-DB", "ETL-DB", "APP-4_DB", "APPLICATION-3-DB", "MONGO-DB", "APPLICATION-6-DB", "APPLICATION-7-DB", "APPLICATION-11-DB", "APPLICATION-9-DB", "APPLICATION-9-REDIS", "APPLICATION-12-DB", "APPLICATION-10-DB", "ORACLE-DB", "DATABASE", "BACKEND", "JUMP", "APPLICATION-12"], "purpose_network": {"APPLICATION-1": "VIRT-NET|APPLICATIONS|APPLICATION-1", "APPLICATION-21":"VIRT-NET|APPLICATIONS|APPLICATION-2","APPLICATION-22":"VIRT-NET|APPLICATIONS|APPLICATION-2-ENDPOINT", "APPLICATION-3": "VIRT-NET|APPLICATIONS|APPLICATION-3", "APPLICATION-4": "VIRT-NET|APPLICATIONS|APPLICATION-4", "APPLICATION-5": "VIRT-NET|APPLICATIONS|APPLICATION-5", "APPLICATION-6": "VIRT-NET|APPLICATIONS|APPLICATION-6", "APPLICATION-71": "VIRT-NET|APPLICATIONS|APPLICATION-7", "APPLICATION-71":  "VIRT-NET|APPLICATIONS|APPLICATION-7_SERVICES", "APPLICATION-8": "VIRT-NET|APPLICATIONS|APPLICATION-8", "TEST1": "VIRT-NET-DEV|APP|TEST_ENV",  "TEST2": "VIRT-NET-DEV|APP|TEST2", "OTHERS1":"VIRT-NET|APPLICATIONS|APP-POOL","OTHERS2": "VIRT-NET|APPLICATIONS|SHARED-SERVICES", "OTHERS3":"VIRT-NET|APPLICATIONS|APP-SERVICES", "APPLICATION-9": "VIRT-NET|APPLICATIONS|APPLICATION-9", "APPLICATION-101": "VIRT-NET|APPLICATIONS|APPLICATION-10", "APPLICATION-102": "VIRT-NET|APPLICATIONS|APPLICATION-10-ENDPOINT", "BIZ-INTEL1":"VIRT-NET|BIZ-INTEL-DATA|BIZ-INTEL-DATA","BIZ-INTEL2":  "VIRT-NET|BIZ-INTEL-DATA|BIZ-INTEL-ETL", "BIZ-INTEL3": "VIRT-NET|BIZ-INTEL-DATA|BIZ-INTEL-TABLEAU", "ELK-DB": "VIRT-NET|DATABASE|ELK-DB", "ETL-DB": "VIRT-NET|DATABASE|ETL-DB", "APP-4_DB": "VIRT-NET|DATABASE|APP-4_DB", "APPLICATION-3-DB": "VIRT-NET|DATABASE|APPLICATION-3-DB", "MONGO-DB": "VIRT-NET|DATABASE|MONGO-DB", "APPLICATION-6-DB": "VIRT-NET|DATABASE|APPLICATION-6-DB", "APPLICATION-7-DB": "VIRT-NET|DATABASE|APPLICATION-7-DB", "APPLICATION-11-DB": "VIRT-NET|DATABASE|APPLICATION-11-DB", "APPLICATION-9-DB": "VIRT-NET|DATABASE|APPLICATION-9-DB", "APPLICATION-9-REDIS": "VIRT-NET|DATABASE|APPLICATION-9-REDIS", "APPLICATION-12-DB": "VIRT-NET|DATABASE|APPLICATION-12-DB", "APPLICATION-10-DB": "VIRT-NET|DATABASE|APPLICATION-10-DB", "ORACLE-DB": "VIRT-NET|DATABASE|ORACLE-DB", "DATABASE": "VIRT-NET|DATABASE|ENDPOINT-DB", "BACKEND1": "VIRT-NET|BACKEND|BACKEND-ARCH","BACKEND2": "VIRT-NET|BACKEND|BACKEND-SERVICES","BACKEND3":  "VIRT-NET|BACKEND|APPLICATION-9_WEB", "JUMP": "VIRT-NET|STANDALONE_JUMP|SECURE_JUMP", "APPLICATION-121":"VIRT-NET|SERVICES|APP-1-SERVICES", "APPLICATION-122":"VIRT-NET|SERVICES|APP-2-SERVICES"}, "network_subnet_map": {"VIRT-NET-DEV|APP|TEST_192.235.10.0": "192.235.10.0/24","VIRT-NET-DEV|APP|SANDBOX_BND":  "192.42.42.0/24", "VIRT-NET-DEV|APP|TEST_DEV": "192.42.42.0/24", "VIRT-NET-DEV|APP|TEST_ENV": "192.123.20.0/24", "VIRT-NET-DEV|APP|TEST2": ["192.42.40.0/24", "192.42.41.0/24", "192.42.42.0/23"], "VIRT-NET|APPLICATIONS|APP-POOL":  ["192.89.15.0/24", "192.89.14.0/22", "192.89.8.0/24", "192.89.9.0/22", "192.89.10.0/22"], "VIRT-NET|APPLICATIONS|APPLICATION-1":   ["192.89.15.0/24", "192.89.14.0/22", "192.89.8.0/24", "192.89.9.0/22", "192.89.10.0/22"], "VIRT-NET|APPLICATIONS|BIZ-INTEL-DATA-TEST": ["192.42.40.0/24", "192.42.41.0/24", "192.42.42.0/23"], "VIRT-NET|APPLICATIONS|APPLICATION-2": ["192.89.15.0/24", "192.89.14.0/22", "192.89.8.0/24", "192.89.9.0/22", "192.89.10.0/22"], "VIRT-NET|APPLICATIONS|APPLICATION-2-ENDPOINT": ["192.89.15.0/24", "192.89.14.0/22", "192.89.8.0/24", "192.89.9.0/22", "192.89.10.0/22"], "VIRT-NET|APPLICATIONS|APPLICATION-3": "192.21.21.0/27", "VIRT-NET|APPLICATIONS|APPLICATION-4": ["192.89.15.0/24", "192.89.14.0/22", "192.89.8.0/24", "192.89.9.0/22", "192.89.10.0/22"], "VIRT-NET|APPLICATIONS|APPLICATION-5": "192.38.1.0/24", "VIRT-NET|APPLICATIONS|APP-SERVICES": ["192.89.15.0/24", "192.89.14.0/22", "192.89.8.0/24", "192.89.9.0/22", "192.89.10.0/22"], "VIRT-NET|APPLICATIONS|APPLICATION-6": ["192.89.15.0/24", "192.89.14.0/22", "192.89.8.0/24", "192.89.9.0/22", "192.89.10.0/22"], "VIRT-NET|APPLICATIONS|APPLICATION-7": ["192.89.15.0/24", "192.89.14.0/22", "192.89.8.0/24", "192.89.9.0/22", "192.89.10.0/22"], "VIRT-NET|APPLICATIONS|APPLICATION-7_SERVICES": ["192.89.15.0/24", "192.89.14.0/22", "192.89.8.0/24", "192.89.9.0/22", "192.89.10.0/22"], "VIRT-NET|APPLICATIONS|APPLICATION-9": ["192.89.15.0/24", "192.89.14.0/22", "192.89.8.0/24", "192.89.9.0/22", "192.89.10.0/22"], "VIRT-NET|APPLICATIONS|SHARED-SERVICES": ["192.89.15.0/24", "192.89.14.0/22", "192.89.8.0/24", "192.89.9.0/22", "192.89.10.0/22"], "VIRT-NET|APPLICATIONS|APPLICATION-10": ["192.89.15.0/24", "192.89.14.0/22", "192.89.8.0/24", "192.89.9.0/22", "192.89.10.0/22"], "VIRT-NET|APPLICATIONS|APPLICATION-10-ENDPOINT": ["192.89.15.0/24", "192.89.14.0/22", "192.89.8.0/24", "192.89.9.0/22", "192.89.10.0/22"], "VIRT-NET|BACKUP|BACKUP_1": "10.100.111.0/24", "VIRT-NET|BIZ-INTEL-DATA|BIZ-INTEL-DATA": "192.37.1.0/24", "VIRT-NET|BIZ-INTEL-DATA|BIZ-INTEL-ETL": "192.37.1.0/24", "VIRT-NET|BIZ-INTEL-DATA|BIZ-INTEL-TABLEAU": "192.37.1.0/24", "VIRT-NET|BIZ-INTELG-DATA|DATA": "192.168.10.0/24", "VIRT-NET|BIZ-INTELG-DATA|HCI_MGMT_NODE": "192.168.10.0/24", "VIRT-NET|DATABASE|ENDPOINT-DB": "192.38.1.0/24", "VIRT-NET|DATABASE|ELK-DB": "192.38.1.0/24", "VIRT-NET|DATABASE|ETL-DB": "192.38.1.0/24", "VIRT-NET|DATABASE|APP-4_DB": "192.38.1.0/24", "VIRT-NET|DATABASE|APPLICATION-3-DB": "192.38.1.0/24", "VIRT-NET|DATABASE|MONGO-DB": "192.38.1.0/24", "VIRT-NET|DATABASE|APPLICATION-6-DB": "192.38.1.0/24", "VIRT-NET|DATABASE|APPLICATION-7-DB": "192.38.1.0/24", "VIRT-NET|DATABASE|APPLICATION-11-DB": "192.38.1.0/24", "VIRT-NET|DATABASE|APPLICATION-9-DB": "192.38.1.0/24", "VIRT-NET|DATABASE|APPLICATION-9-REDIS": "192.38.1.0/24", "VIRT-NET|DATABASE|APPLICATION-12-DB": "192.38.1.0/24", "VIRT-NET|DATABASE|APPLICATION-10-DB": "192.38.1.0/24", "VIRT-NET|DATABASE|ORACLE-DB": "192.38.1.0/24", "VIRT-NET|BACKEND|MAPR-TEST-DATA": "192.123.10.0/24", "VIRT-NET|BACKEND|BACKEND-ARCH": "192.123.10.0/24", "VIRT-NET|BACKEND|BACKEND-SERVICES": "192.123.10.0/24", "VIRT-NET|BACKEND|APPLICATION-9_WEB": "192.123.10.0/24", "VIRT-NET|EXTERNAL|POWERCARD_DB_EPG": "192.123.0.0/24", "VIRT-NET|EXTERNAL|APPLICATION-9-VERVE": "192.123.0.0/24", "VIRT-NET|STANDALONE_JUMP|SECURE_JUMP": "192.21.21.0/24", "VIRT-NET|SERVICES|APP-1-SERVICES": "192.123.0.0/24", "VIRT-NET|SERVICES|APP-2-SERVICES": "192.123.0.0/24"}, "network_subnet_gateway": {"VIRT-NET-DEV|APP|SANDBOX_BND":  "192.42.42.1", "VIRT-NET-DEV|APP|TEST_DEV": "192.42.42.1", "VIRT-NET-DEV|APP|TEST_ENV": "192.123.20.1", "VIRT-NET-DEV|APP|TEST2": ["192.42.40.1", "192.42.42.1"], "VIRT-NET|APPLICATIONS|APP-POOL":  ["192.89.15.1", "192.89.8.1"], "VIRT-NET|APPLICATIONS|APPLICATION-1":   ["192.89.15.1", "192.89.8.1"], "VIRT-NET|APPLICATIONS|BIZ-INTEL-DATA-TEST": ["192.42.40.1", "192.42.41.1", "192.42.42.0/23"], "VIRT-NET|APPLICATIONS|APPLICATION-2": ["192.89.15.1", "192.89.8.1"], "VIRT-NET|APPLICATIONS|APPLICATION-2-ENDPOINT": ["192.89.15.1", "192.89.8.1"], "VIRT-NET|APPLICATIONS|APPLICATION-3": "192.21.21.1", "VIRT-NET|APPLICATIONS|APPLICATION-4": ["192.89.15.1", "192.89.8.1"], "VIRT-NET|APPLICATIONS|APPLICATION-5": "192.38.1.1", "VIRT-NET|APPLICATIONS|APP-SERVICES": ["192.89.15.1", "192.89.8.1"], "VIRT-NET|APPLICATIONS|APPLICATION-6": ["192.89.15.1", "192.89.8.1"], "VIRT-NET|APPLICATIONS|APPLICATION-7": ["192.89.15.1", "192.89.8.1"], "VIRT-NET|APPLICATIONS|APPLICATION-7_SERVICES": ["192.89.15.1", "192.89.8.1"], "VIRT-NET|APPLICATIONS|APPLICATION-9": ["192.89.15.1", "192.89.8.1"], "VIRT-NET|APPLICATIONS|SHARED-SERVICES": ["192.89.15.1", "192.89.8.1"], "VIRT-NET|APPLICATIONS|APPLICATION-10": ["192.89.15.1", "192.89.8.1"], "VIRT-NET|APPLICATIONS|APPLICATION-10-ENDPOINT": ["192.89.15.1", "192.89.8.1"], "VIRT-NET|BACKUP|BACKUP_1": "10.100.111.1", "VIRT-NET|BIZ-INTEL-DATA|BIZ-INTEL-DATA": "192.37.1.1", "VIRT-NET|BIZ-INTEL-DATA|BIZ-INTEL-ETL": "192.37.1.1", "VIRT-NET|BIZ-INTEL-DATA|BIZ-INTEL-TABLEAU": "192.37.1.1", "VIRT-NET|BIZ-INTELG-DATA|DATA": "192.168.10.1", "VIRT-NET|BIZ-INTELG-DATA|HCI_MGMT_NODE": "192.168.10.1", "VIRT-NET|DATABASE|ENDPOINT-DB": "192.38.1.1", "VIRT-NET|DATABASE|ELK-DB": "192.38.1.1", "VIRT-NET|DATABASE|ETL-DB": "192.38.1.1", "VIRT-NET|DATABASE|APP-4_DB": "192.38.1.1", "VIRT-NET|DATABASE|APPLICATION-3-DB": "192.38.1.1", "VIRT-NET|DATABASE|MONGO-DB": "192.38.1.1", "VIRT-NET|DATABASE|APPLICATION-6-DB": "192.38.1.1", "VIRT-NET|DATABASE|APPLICATION-7-DB": "192.38.1.1", "VIRT-NET|DATABASE|APPLICATION-11-DB": "192.38.1.1", "VIRT-NET|DATABASE|APPLICATION-9-DB": "192.38.1.1", "VIRT-NET|DATABASE|APPLICATION-9-REDIS": "192.38.1.1", "VIRT-NET|DATABASE|APPLICATION-12-DB": "192.38.1.1", "VIRT-NET|DATABASE|APPLICATION-10-DB": "192.38.1.1", "VIRT-NET|DATABASE|ORACLE-DB": "192.38.1.1", "VIRT-NET|BACKEND|MAPR-TEST-DATA": "192.123.10.1", "VIRT-NET|BACKEND|BACKEND-ARCH": "192.123.10.1", "VIRT-NET|BACKEND|BACKEND-SERVICES": "192.123.10.1", "VIRT-NET|BACKEND|APPLICATION-9_WEB": "192.123.10.1", "VIRT-NET|EXTERNAL|POWERCARD_DB_EPG": "192.123.0.2", "VIRT-NET|EXTERNAL|APPLICATION-9-VERVE": "192.123.0.2", "VIRT-NET|STANDALONE_JUMP|SECURE_JUMP": "192.21.21.1", "VIRT-NET|SERVICES|APP-1-SERVICES": "192.123.0.2", "VIRT-NET|SERVICES|APP-2-SERVICES": "192.123.0.2"}, "blueprint_options": {"WINDOWS2016-NANO": {"server_name": "NW16.1", "vcpus": "1", "memory": "1", "vm_deploy_template": "WIN2016", "application_type": "DEV-SERVER", "network": "VIRT-NET-DEV|APP|TEST_192.235.10.0", "additional_disk_count": 0}, "WINDOWS2016-MICRO": {"server_name": "MCW16.1", "vcpus": "2", "memory": "2", "vm_deploy_template": "WIN2016", "application_type": "DEV-SERVER", "network": "VIRT-NET-DEV|APP|TEST_192.235.10.0", "additional_disk_count": 0}, "WINDOWS2016-MINI": {"server_name": "MNW16.1", "vcpus": "2", "memory": "4", "vm_deploy_template": "WIN2016", "application_type": "DEV-SERVER", "network": "VIRT-NET-DEV|APP|TEST_192.235.10.0", "additional_disk_count": 0}, "WINDOWS2016-STANDARD": {"server_name": "SW16.1", "vcpus": "4", "memory": "6", "vm_deploy_template": "WIN2016", "application_type": "DEV-SERVER", "network": "VIRT-NET-DEV|APP|TEST_192.235.10.0", "additional_disk_count": 1}, "WINDOWS2016-APP-1": {"server_name": "MGW16.1", "vcpus": "4", "memory": "8", "vm_deploy_template": "WIN2016", "application_type": "DEV-SERVER", "network": "VIRT-NET-DEV|APP|TEST_192.235.10.0", "additional_disk_count": 1}, "WINDOWS2016-GIGA": {"server_name": "GW16.1", "vcpus": "8", "memory": "12", "vm_deploy_template": "WIN2016", "application_type": "DEV-SERVER", "network": "VIRT-NET-DEV|APP|TEST_192.235.10.0", "additional_disk_count": 2}, "WINDOWS2016-TERA": {"server_name": "TW16.1", "vcpus": "16", "memory": "24", "vm_deploy_template": "WIN2016", "application_type": "DEV-SERVER", "network": "VIRT-NET-DEV|APP|TEST_192.235.10.0",
"additional_disk_count": 2}, "WINDOWS2016-PETA": {"server_name": "PW16.1", "vcpus": "16", "memory": "32", "vm_deploy_template": "WIN2016", "application_type": "DEV-SERVER", "network": "VIRT-NET-DEV|APP|TEST_192.235.10.0", "additional_disk_count": 3}, "WINDOWS2016-ZETTA": {"server_name": "ZW16.1", "vcpus": "20", "memory": "64", "vm_deploy_template": "WIN2016", "application_type": "DEV-SERVER", "network": "VIRT-NET-DEV|APP|TEST_192.235.10.0", "additional_disk_count": 3}, "WINDOWS2019-NANO": {"server_name": "NW19.1", "vcpus": "1", "memory": "1", "vm_deploy_template": "WIN2019", "application_type": "DEV-SERVER", "network": "VIRT-NET-DEV|APP|TEST_192.235.10.0", "additional_disk_count": 0}, "WINDOWS2019-MICRO": {"server_name": "MCW19.1", "vcpus": "2", "memory": "2", "vm_deploy_template": "WIN2019", "application_type": "DEV-SERVER", "network": "VIRT-NET-DEV|APP|TEST_192.235.10.0", "additional_disk_count": 0}, "WINDOWS2019-MINI": {"server_name": "MNW19.1", "vcpus": "2", "memory": "4", "vm_deploy_template": "WIN2019", "application_type": "DEV-SERVER", "network": "VIRT-NET-DEV|APP|TEST_192.235.10.0", "additional_disk_count": 0}, "WINDOWS2019-STANDARD": {"server_name": "SW19.1", "vcpus": "4", "memory": "6", "vm_deploy_template": "WIN2019", "application_type": "DEV-SERVER", "network": "VIRT-NET-DEV|APP|TEST_192.235.10.0", "additional_disk_count": 1}, "WINDOWS2019-APP-1": {"server_name": "MGW19.1", "vcpus": "4", "memory": "8", "vm_deploy_template": "WIN2019", "application_type": "DEV-SERVER", "network": "VIRT-NET-DEV|APP|TEST_192.235.10.0", "additional_disk_count": 1}, "WINDOWS2019-GIGA": {"server_name": "GW19.1", "vcpus": "8", "memory": "12", "vm_deploy_template": "WIN2019", "application_type": "DEV-SERVER", "network": "VIRT-NET-DEV|APP|TEST_192.235.10.0", "additional_disk_count": 2}, "WINDOWS2019-TERA": {"server_name": "TW19.1", "vcpus": "16", "memory": "24", "vm_deploy_template": "WIN2019", "application_type": "DEV-SERVER", "network": "VIRT-NET-DEV|APP|TEST_192.235.10.0", "additional_disk_count": 2}, "WINDOWS2019-PETA": {"server_name": "PW19.1", "vcpus": "16", "memory": "32", "vm_deploy_template": "WIN2019", "application_type": "DEV-SERVER", "network": "VIRT-NET-DEV|APP|TEST_192.235.10.0", "additional_disk_count": 3}, "WINDOWS2019-ZETTA": {"server_name": "ZW19.1", "vcpus": "20", "memory": "64", "vm_deploy_template": "WIN2019", "application_type": "DEV-SERVER", "network": "VIRT-NET-DEV|APP|TEST_192.235.10.0", "additional_disk_count": 3}, "UBUNTU18.04-NANO": {"server_name": "NU18.1", "vcpus": "1", "memory": "1", "vm_deploy_template": "UBU18", "application_type": "DEV-SERVER", "network": "VIRT-NET-DEV|APP|TEST_192.235.10.0", "additional_disk_count": 0}, "UBUNTU18.04-MICRO": {"server_name": "MCU18.1", "vcpus": "2", "memory": "2", "vm_deploy_template": "UBU18", "application_type": "DEV-SERVER", "network": "VIRT-NET-DEV|APP|TEST_192.235.10.0", "additional_disk_count": 0}, "UBUNTU18.04-MINI": {"server_name": "MNU18.1", "vcpus": "2", "memory": "4", "vm_deploy_template": "UBU18", "application_type": "DEV-SERVER", "network": "VIRT-NET-DEV|APP|TEST_192.235.10.0", "additional_disk_count": 0}, "UBUNTU18.04-STANDARD": {"server_name": "SU18.1", "vcpus": "4", "memory": "6", "vm_deploy_template": "UBU18", "application_type": "DEV-SERVER", "network": "VIRT-NET-DEV|APP|TEST_192.235.10.0", "additional_disk_count": 1}, "UBUNTU18.04-APP-1": {"server_name": "MEU18.1", "vcpus": "4", "memory": "8", "vm_deploy_template": "UBU18", "application_type": "DEV-SERVER", "network": "VIRT-NET-DEV|APP|TEST_192.235.10.0", "additional_disk_count": 1}, "UBUNTU18.04-GIGA": {"server_name": "GU18.1", "vcpus": "8", "memory": "12", "vm_deploy_template": "UBU18", "application_type": "DEV-SERVER", "network": "VIRT-NET-DEV|APP|TEST_192.235.10.0", "additional_disk_count": 2}, "UBUNTU18.04-TERA": {"server_name": "TU18.1", "vcpus": "16", "memory": "24", "vm_deploy_template": "UBU18", "application_type": "DEV-SERVER", "network": "VIRT-NET-DEV|APP|TEST_192.235.10.0", "additional_disk_count": 2}, "UBUNTU18.04-PETA": {"server_name": "PU18.1", "vcpus": "16", "memory": "32", "vm_deploy_template": "UBU18", "application_type": "DEV-SERVER", "network": "VIRT-NET-DEV|APP|TEST_192.235.10.0", "additional_disk_count": 3}, "UBUNTU18.04-ZETTA": {"server_name": "ZU18.1", "vcpus": "20", "memory": "64", "vm_deploy_template": "UBU18", "application_type": "DEV-SERVER", "network": "VIRT-NET-DEV|APP|TEST_192.235.10.0", "additional_disk_count": 3}, "REDHAT8.4-NANO": {"server_name": "NR8.1", "vcpus": "1", "memory": "1", "vm_deploy_template": "RED8.4", "application_type": "DEV-SERVER", "network": "VIRT-NET-DEV|APP|TEST_192.235.10.0", "additional_disk_count": 0}, "REDHAT8.4-MICRO": {"server_name": "MCR8.1", "vcpus": "2", "memory": "2", "vm_deploy_template": "RED8.4", "application_type": "DEV-SERVER", "network": "VIRT-NET-DEV|APP|TEST_192.235.10.0", "additional_disk_count": 0}, "REDHAT8.4-MINI": {"server_name": "MNR8.1", "vcpus": "2", "memory": "4", "vm_deploy_template": "RED8.4", "application_type": "DEV-SERVER", "network": "VIRT-NET-DEV|APP|TEST_192.235.10.0", "additional_disk_count": 0}, "REDHAT8.4-STANDARD": {"server_name": "SR8.1", "vcpus": "4", "memory": "6", "vm_deploy_template": "RED8.4", "application_type": "DEV-SERVER", "network": "VIRT-NET-DEV|APP|TEST_192.235.10.0", "additional_disk_count": 1}, "REDHAT8.4-APP-1": {"server_name": "MER8.1", "vcpus": "4", "memory": "8", "vm_deploy_template": "RED8.4", "application_type": "DEV-SERVER", "network": "VIRT-NET-DEV|APP|TEST_192.235.10.0", "additional_disk_count": 1}, "REDHAT8.4-GIGA": {"server_name": "GR8.1", "vcpus": "8", "memory": "12", "vm_deploy_template": "RED8.4", "application_type": "DEV-SERVER", "network": "VIRT-NET-DEV|APP|TEST_192.235.10.0", "additional_disk_count": 2}, "REDHAT8.4-TERA": {"server_name": "TR8.1", "vcpus": "16", "memory": "24", "vm_deploy_template": "RED8.4", "application_type": "DEV-SERVER", "network": "VIRT-NET-DEV|APP|TEST_192.235.10.0", "additional_disk_count": 2}, "REDHAT8.4-PETA": {"server_name": "PR8.1", "vcpus": "16", "memory": "32", "vm_deploy_template": "RED8.4", "application_type": "DEV-SERVER", "network": "VIRT-NET-DEV|APP|TEST_192.235.10.0", "additional_disk_count": 3}, "REDHAT8.4-ZETTA": {"server_name": "ZR8.1", "vcpus": "20", "memory": "64", "vm_deploy_template": "RED8.4", "application_type": "DEV-SERVER", "network": "VIRT-NET-DEV|APP|TEST_192.235.10.0", "additional_disk_count": 3}}, "class_options": {"NANO": "NANO: CPUs= 1, Memory= 1GB, Extra Drives= none", "MICRO": "MICRO: CPUs= 2, Memory= 2GB, Extra Drives= none", "MINI": "MINI: CPUs= 2, Memory= 4GB, Extra Drivess= none", "STANDARD": "STANDARD: vCPUs= 4, Memory= 6GB, Extra Drives= 1", "APP-1": "APP-1: CPUs= 4, Memory= 8GB, Extra Drivess= 1", "GIGA": "GIGA: CPUs= 8, Memory= 12GB, Extra Drives= 2", "TERA": "TERA: CPUs= 16, Memory= 24GB, Extra Drives= 2", "PETA": "PETA: CPUs= 16, Memory= 32GB, Extra Drives= 3", "ZETTA": "ZETTA: CPUs= 20, Memory= 64GB, Extra Drives= 3"}}

email_suffix = "@virt-net-group.com"

def generate_options_for_purpose(**kwargs):
    opts = []
    for opt in prod_options['purpose']:
        opts.append((str(opt), str(opt)))
    return opts

def get_blueprint_parameters():
    return prod_options['blueprint_options']

def generate_options_for_quantity(**kwargs):
    app_opts = []
    for i in range(1, 5):
         app_opts.append((str(i), str(i)))
    return app_opts
    
def  generate_options_for_class(**kwargs):
    app_opts = []
    for key, value  in prod_options['class_options'].items():
        app_opts.append((str(key), str(value)))
    return app_opts

def get_vm_server_name(new_vm_name,current_index):
    similarly_named_vm_list = []
    servers = get_vim_objects('vm')
    index_suffix = str(current_index)
    used_index_list = []
    new_name = ''
    similarly_named_vm_list = []
    server_name_list = [server.name.lower() for server in servers]
    new_vm_name=new_vm_name.lower()
    for vm_name in server_name_list:
      if new_vm_name  in vm_name and (vm_name.replace(new_vm_name,'')).isdigit():
        similarly_named_vm_list.append(vm_name)
    if not similarly_named_vm_list:
       index_suffix= str(1).rjust(15-len(new_vm_name),'0')
       new_name = new_vm_name+index_suffix
    else:
       for vm_name in similarly_named_vm_list:
           suffix = vm_name.replace(new_vm_name, '')
           if(suffix != ''):
             used_index_list.append(int(suffix))
       last_used_index = 0
       next_index = 0
       logger.info(used_index_list)
       if len(used_index_list) > 0:
           last_used_index = int(max(used_index_list))
           next_index = last_used_index+1
       else:
           next_index = current_index
       index_suffix= str(next_index).rjust(15-len(new_vm_name),'0')
       new_name = new_vm_name+index_suffix
    return new_name

def get_datastore_info(datastore):
    ds_info = {}
    try:
        ds_info['summary'] = datastore.summary
        ds_info['free_space'] = ds_info['summary'].freeSpace
        ds_info['name'] = ds_info['summary'].name
    except Exception as error:
        logger.warning("Unable to access summary for datastore: {d}".format(d=datastore.name))
        logger.warning("error: {e}:".format(e=error))
        pass
    return ds_info

def get_disk_info(disk_list,vm_host_name=None):
    vm_disk_map             = []
    vm_datastore            = None
    host                    =get_vim_objects('host',vm_host_name)
    datastores              = host.datastore if   hasattr(host, 'datastore') else []
    datastore_to_space_dict ={}
    for ds  in datastores:
        ds_info             = get_datastore_info(ds)
        datastore_to_space_dict[ds_info['name']] = ds_info['free_space']
    ds_name_to_space_map    = sorted(datastore_to_space_dict.items(), key=operator.itemgetter(1))
    disks = [int(disk) for disk in disk_list ]
    vm_size                 = sum(disks)
    for k, v in ds_name_to_space_map:
        if v > vm_size:
            vm_datastore = k
    if vm_datastore:
        for i in disk_list:
            vm_disk_map.append('{size}:{datastore}'.format(size=i,datastore=vm_datastore))
    return vm_disk_map

def get_vim_objects(obj_type, object_value=None):
    object_list                = []
    vmObjView                  = []
    rh                         = VsphereResourceHandler.objects.get(id=VM_RESOURCE_HANDLER_ID_PROD)
    try:
        si                      = get_connection(rh.ip, rh.port, rh.serviceaccount, rh.servicepasswd, ssl_verification=False)
    except Exception as e:
        traceback.print_exc()

    if si:
        content                 = si.RetrieveContent()
    if obj_type.lower()         == 'host':
        vmObjView               = content.viewManager.CreateContainerView(content.rootFolder,[vim.HostSystem],True)
    elif obj_type.lower()       == 'datastore':
        vmObjView          	    = content.viewManager.CreateContainerView(content.rootFolder,[vim.Datastore],True)
    elif obj_type.lower()        == 'vm':
        vmObjView          	    = content.viewManager.CreateContainerView(content.rootFolder,[vim.VirtualMachine],True)
    elif obj_type.lower()        == 'cluster':
        vmObjView          	    = content.viewManager.CreateContainerView(content.rootFolder,[vim.ClusterComputeResource],True)
    elif obj_type.lower()        == 'dvs':
        vmObjView          	    = content.viewManager.CreateContainerView(content.rootFolder,[vim.DistributedVirtualSERVICES],True)
    elif obj_type.lower()        == 'prtgrp':
        vmObjView          	    = content.viewManager.CreateContainerView(content.rootFolder,[vim.Network],True)
    object_list           	    = vmObjView.view
    vmObjView.Destroy()
    if not object_value:
       return object_list
    else:
        objs = [objs  for objs in object_list if objs.name.lower() == object_value.lower()]
        obj = objs[0] if objs else None
        return obj
    
 
def get_vim_contents(id=1):
    contents                   = None
    rh                         = VsphereResourceHandler.objects.get(id=id)
    try:
        si                      = get_connection(rh.ip, rh.port, rh.serviceaccount, rh.servicepasswd, ssl_verification=False)
    except Exception as e:
        traceback.print_exc()
    if si:
        contents                 = si.RetrieveContent()
    return contents
    


def get_host_info(host):
    host_info = {}
    MBFACTOR = float(1 << 20)
    try:
        host_info['summary'] = host.summary
        host_info['stats'] = host_info['summary'].quickStats
        host_info['hardware'] = host.hardware
        host_info['cpu_usage'] = host_info['stats'].overallCpuUsage
        host_info['memory_capacity_in_mb'] = host_info['hardware'].memorySize/MBFACTOR
        host_info['memory_usage'] = host_info['stats'].overallMemoryUsage
        host_info['memory_percentage'] =  ((float(host_info['memory_usage']) / host_info['memory_capacity_in_mb']) * 100.0)
        host_info['name'] = host.name
    except Exception as error:
        logger.warning("Unable to access information for host: {h}".format(h=host.name))
        logger.warning("error: {e}:".format(e=error))
        pass
    return host_info

def get_server_host():
    host_list               = get_vim_objects('host')
    host_cpu_map            = {}
    host_mem_map            = {}
    total_map               = {}
    sorted_total_map        = {}
    for host  in  host_list:
        host_info = get_host_info(host)
        if 'name'  in host_info and  host_info['name'] not in host_exclusion_list:
            name = host_info['name']
            host_mem_map[name]= host_info['memory_percentage']
            host_cpu_map[name]= host_info['cpu_usage']
            sorted_mem_map_list = sorted(host_mem_map.items(), key=operator.itemgetter(1))
            sorted_mem_map ={}
            for k,v in sorted_mem_map_list:       
              sorted_mem_map[k] = v
              sorted_cpu_map_list = sorted(host_cpu_map.items(), key=operator.itemgetter(1))
            sorted_cpu_map ={}
            for k,v in sorted_cpu_map_list:
              sorted_cpu_map[k] = [v][0]
    for host in host_list: 
        host_info = get_host_info(host)
        if 'name'  in host_info and  host_info['name'] not in host_exclusion_list:
            host_name = host_info['name']
            total_map[host_name]=sorted_mem_map[host_name]+sorted_cpu_map[host_name] 
    sorted_total_map = sorted(total_map.items(), key=operator.itemgetter(1))
    #logger.info('sorted_total_map:{}'.format(sorted_total_map))
    return sorted_total_map[0][0]	

def get_os_type(template):
    vm_list = get_vim_objects('vm')
    template = [vm.name for vm in vm_list  if vm.name.lower() == template.lower()]
    template = template[0]
    if 'centos' in  template.lower() or  'ubuntu' in  template.lower() or  'red' in  template.lower() or 'fedora' in  template.lower() or   'mandriva' in  template.lower() or   'unix' in  template.lower() or   'suse' in  template.lower():
        return 'linux'
    else:
        return 'windows'

def get_free_ip_info(network):   
    logger = ThreadLogger(__name__)
    ip = None
    connection_info = ConnectionInfo.objects.get(name='jump_server')
    jump_server   = connection_info.ip
    jump_username = connection_info.username
    jump_password = connection_info.password
    jump_port= connection_info.port
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    server = jump_server
    username=jump_username
    password =  jump_password  
    timeout  =  45
    infoblox_subnet = None
    original_infoblox_subnet = prod_options['network_subnet_map'][network]	
    if original_infoblox_subnet:
        ips =[]
        count = 5
        while not ips and count >0:
            if type(original_infoblox_subnet) == list:
                infoblox_subnet = random.choice(original_infoblox_subnet)
            else:
                infoblox_subnet =original_infoblox_subnet 
            logger.info("subnet: {}".format(infoblox_subnet))
            cmd_to_execute = f"powershell  -executionpolicy bypass  -Command  get-FreeIPList {infoblox_subnet.split('.')[0]}.{infoblox_subnet.split('.')[1]}.{infoblox_subnet.split('.')[2]}"
            logger.info('Running command: {}'.format(cmd_to_execute))

            ssh_client.connect(server, username=username, password=password, port=jump_port, timeout=timeout)
            ssh_stdin, ssh_stdout, ssh_stderr = ssh_client.exec_command(cmd_to_execute)
            ip_list = []
            for line in iter(lambda: ssh_stdout.readline(2048), ""):
               line = str(line.replace('\r\n',',').replace('\n',''))
               if not line.endswith('.1') or not line.endswith('.2'):
                ip_list.append(line)
            ips = ''.join(ip_list).split(',')
            logger.info('ips: {}'.format(ips))
            existing_ips = [server.ip for server in Server.objects.all() ]
            count-=1
            ips = [ip for ip in ips if ip not in  existing_ips]
            
        if isinstance(ips, list):
            ip=  random.choice(ips)
            logger.info("The IP address would be set to {}".format(ip))
    else:
        logger.info("No subnet could be found for the {} network".format(network))
        raise Exception("No subnet could be found for the {} network".format(network))

    return  ip

def get_subnet_info(network, ip):
    network_info  = prod_options['network_subnet_gateway'][network]
    gateway = None
    mask    = None
    dns_list = []
    octets = ip.split('.')
    domain_user = None
    domain_password = None
    ip_subnet =   (octets[0]+'.'+octets[1]+'.'+octets[2]) 
    if type(network_info)  != list:
        gateway = network_info
        mask    = '255.255.255.0'
    else:
        for gtw in network_info:
            if octets[2] == gtw.split('.')[2]:
                gateway = gtw
    if not gateway:
        if  ip_subnet  == '192.42.41':
            gateway = '192.42.40.1'
        elif ip_subnet  in ['192.89.15','192.89.14']:
            gateway = '192.89.15.1'
        elif ip_subnet  in ['192.89.8','192.89.9','192.89.10']:
            gateway = '192.89.8.1'
        else:
            gateway = octets[0]+'.'+octets[1]+'.'+octets[2]+'.1'
    if  ip_subnet  in ['192.89.15','192.89.14','192.42.41']:
        mask = "255.255.235.0"
    elif  ip_subnet  in ['192.89.8','192.89.9','192.89.10']:
        mask = "255.255.252.0"
    else:
        mask = "255.255.255.0"
    
    if ip_subnet  in ['192.89.15','192.89.14','192.89.8','192.89.9','192.89.10','192.38.1','192.123.0','192.123.15','192.123.10','192.123.25','192.16.11','192.123.30','192.168.10','192.31.2','192.36.1']:
        dns_list=['192.123.15.7','192.123.15.9']
        connection_info = ConnectionInfo.objects.get(name='neocrystalsinc_dns')
        domain_user = connection_info.username
        domain_password = connection_info.password
    elif ip_subnet  in ['192.16.10','192.16.110','192.37.1']:
        dns_list= ['192.16.10.2','192.16.10.42','192.16.10.62']
        connection_info = ConnectionInfo.objects.get(name='neocrystalsinc_dns_2')
        domain_user = connection_info.username
        domain_password = connection_info.password
    elif ip_subnet  in ['192.123.10','192.42.40','192.42.41','192.42.42','192.235.10']:
        dns_list = ['192.42.40.10','192.123.20.10']
        connection_info = ConnectionInfo.objects.get(name='test_neocrystalsinc_dns')
        domain_user = connection_info.username
        domain_password = connection_info.password

    return {'gateway':gateway,'mask': mask,'dns':dns_list,'user':domain_user,'pass':domain_password}

def  set_ubuntu2004_ip(vm_config):   
    logger = ThreadLogger(__name__)
    ip = None
    connection_info = ConnectionInfo.objects.get(name='jump_server')
    jump_server   = connection_info.ip
    jump_username = connection_info.username
    jump_password = connection_info.password
    jump_port= connection_info.port
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    server = jump_server
    username=jump_username
    password =  jump_password  
    timeout  =  300
    
    vm_name = vm_config.name
    vm_ip = vm_config.ip
    vm_subnetmask = vm_config.mask
    vm_gateway = vm_config.gateway
    vm_dns_list= vm_config.dnsList
    vm_user = vm_config.serverAdminName
    vm_password = vm_config.serverAdminPassword
    dns_string  =""
    if type(vm_dns_list) ==list:
        for dns in vm_dns_list:
            dns_string+=dns+','
        dns_string = dns_string[:-1]
    else:
        dns_string = vm_dns_list
    cmd_to_execute = f"powershell -executionpolicy bypass  -file  E:\powershell\Set-Ubuntu20.04IP.ps1 {vm_name} {vm_ip} {vm_subnetmask} {vm_gateway} {dns_string} {vm_user} {vm_password}"
    logger.info('Running command: {}'.format(cmd_to_execute))

    ssh_client.connect(server, username=username, password=password, port=jump_port, timeout=timeout)
    ssh_stdin, ssh_stdout, ssh_stderr = ssh_client.exec_command(cmd_to_execute)
    response = []
    for line in iter(lambda: ssh_stdout.readline(2048), ""):
       line = str(line.replace('\r\n',',').replace('\n',''))
       if not line.endswith('.1') or not line.endswith('.2'):
        response.append(line)
    logger.info('response: {}'.format(response))


    for line in iter(lambda: ssh_stderr.readline(2048), ""):
       line = str(line.replace('\r\n',',').replace('\n',''))
       if not line.endswith('.1') or not line.endswith('.2'):
        response.append(line)
    logger.info('error: {}'.format(response))
  
    return  response
def get_mail_body(vm_config):
   owner = vm_config.ownerEmail
   first_name = owner.split('@')[0]
   excluded_props = ['storageFormat','hasCD','hasFloppy','vcenterAddress','vcenterUser','vcenterPassword','ownerEmail','senderEmail','emailUser','emailPassword','emailServer','emailPort','annotation']
   excluded_props =  [prop.lower() for prop in excluded_props]
   owner_first_name = first_name
   body = []
   body.append('<div style="width: 100%; font-family:Arial, Times New Roman, Calibri;">')
   body.append('<div style="width: 100%;" align="justify">')
   body.append('Hello, {o}.<br/>'.format(o=owner_first_name))
   body.append('<br/>')
   body.append('Trust this meets you well.<br/>')
   body.append('<br/>')
   body.append('A server with the following details has been created based on your request:')
   body.append('<br />')
   body.append('<table>')
   body.append('<thead><tr ><th style="text-align:left" > {server_name} Server Details </th></tr><thead>'.format(server_name=vm_config.name.capitalize()))
   body.append('<tr><td><strong>No.</strong></td><td><strong>Server Property</strong></td> <td><strong>Value</strong></td></tr>')
   index=1
   prop_list = ['name','nmCpu','memoryGb','diskList','template','networkName','vmhost','cluster','osType','ip','mask','gateway','dnsList','requestURL','serverAdminName','serverAdminPassword','usedSpace','datastore']
   for prop in prop_list:
      value = getattr(vm_config,prop)
      if prop.lower() not in excluded_props:
        if prop == 'diskList':
            fin_val = ""
            indy = 1
            if type(value) == list:
                for val  in  value:
                    sub_val  = val.split(':')
                    sub_val1 = sub_val[0]	 
                    fin_val+='{indy}. {sub_val1} GB <br/>'.format(indy=indy,sub_val1=sub_val1)
                    indy+=1
            else:
                if not value:
                    value = '1. {}GB'.format(int((vm_config.usedSpace)/(1024*1024)))
                else:
                    sub_val  = value.split(':')
                    sub_val1 = sub_val[0]
                    fin_val = '{indy}. {sub_val1} GB <br/>'.format(indy=indy,sub_val1=sub_val1)
                    value = fin_val
        elif prop =='dnsList':
            fin_val = ''
            indy = 1
            if type(value) == list:
                for val  in  value:
                    sub_val  = val.split(',')
                    sub_val1 = sub_val[0] 
                    fin_val+='{indy}. {sub_val1} <br/>'.format(indy=indy,sub_val1=sub_val1)
                    indy+=1
            else:
                sub_val  = value.split(',')
                sub_val1 = sub_val[0] 
                fin_val+='{indy}. {sub_val1} <br/>'.format(indy=indy,sub_val1=sub_val1)
                value = fin_val
        elif prop =='usedSpace':
            value = '{}'.format(int((vm_config.usedSpace)/(1024*1024)))

        style =  'style="background-color: #e6f2ff;"' if index %2 == 0 else ''
        body.append('<tr {style} ><td>{index}</td><td> {prop} </td>  <td>{value}</td></tr>'.format(style=style,index=index,prop=prop,value=value))
        index+=1
   body.append('</table><br />')
   body.append('<br/>')
   body.append('Please consult the Technical Support team if you have any issues accessing your server(s).<br /><br />')
   body.append('Best regards,<br /><br />')
   body.append('Technical Support - CloudBolt Platform <br /><br />')
   body.append('</div><table border="0px" style="border:none"><tbody><tr>')
   body.append('<td  style="width:  50%;border:none" align="left">')
   body.append('<img src="cid:image1"  alt="VIRT-NET Logo"/>')
   body.append('</td>')
   body.append('<td  style="width:  50%; border:none" text-align="right">')
   body.append('</td>')
   body.append('</tr></tbody></table>')
   body.append('</div>')
   body.append('</body>')
   body.append('</html>')
   return  ''.join(body)

def send_mail(email_subject, email_body, receiver):
	import smtplib
	from email.mime.text import MIMEText
	from email.mime.multipart import MIMEMultipart
	port = 25
	smtp_server      = "192.16.10.116"
	login              = "cbolt@virt-net-group.com"  
	password           = ""
	sender_email       = "cbolt@virt-net-group.com"
	receiver_email     = receiver
	message            = MIMEMultipart("relative")
	message["Subject"] = email_subject
	message["From"] = sender_email
	message["To"] = receiver_email
	message["BCC"] = "compute@virt-net-group.com"
	html = email_body
	part1 = MIMEText(html, "html")
	message.attach(part1)
	fp1 = open('/opt/files/VIRT-NET_icon.jpg', 'rb')
	msgImage1 = MIMEImage(fp1.read())
	fp1.close()
	msgImage1.add_header('Content-ID', '<image1>')
	message.attach(msgImage1)

	with smtplib.SMTP(smtp_server, port) as server:
		server.sendmail(
			sender_email, receiver_email, message.as_string()
		)
		server.quit()

def send_notification(vm_config):
    set_progress("Preparing email notification.")
    owner         = vm_config.ownerEmail
    name          = owner.split('@')[0]
    first_name    = name.split('.')[0]
    surname       = name.split('.')[1]
    email_body    = get_mail_body(vm_config)
    email_subject = '{server} Server Creation from {template} template for {owner}'.format(server=vm_config.name, template=vm_config.template, owner = owner)
    to_address    = first_name+'.'+surname+email_suffix

    set_progress("sending email nofication to " +first_name+' '+surname+"("+to_address+") ")
    #set_progress("Dictionary of keyword args passed to this plug-in: {}".format(kwargs.items()))
    try:
        send_mail(email_subject, email_body, to_address)
    except InvalidConfigurationException:
        logger.debug('Cannot connect to email (SMTP) server')
    return "SUCCESS", "Email has been successfully sent", ""


def run(job, *args, **kwargs):
    set_progress("Reviewing order and determining its requirements...")
    #set_progress("Dictionary of keyword args passed to this plug-in: {}".format(kwargs.items()))
    templates                =   '{{ templates }}'    
    customization            =    str('{{ customization }}')
    vm_name                  =    str('{{ name }}')
    server_class             =    str('{{ class }}')
    quantity                 =    int('{{ quantity }}')
    network                  =    str('{{ network }}')
    purpose                  =    network.split('|')[-1]
    vcpus                    =    str('{{ vcpus }}')
    memory                   =    str('{{ memory }}')
    size_of_disk_1           =    str('{{ size_of_disk_1 }}')
    size_of_disk_2           =    str('{{ size_of_disk_2 }}')
    size_of_disk_3           =    str('{{ size_of_disk_3 }}')
    size_of_disk_4           =    str('{{ size_of_disk_4 }}')
    size_of_disk_5           =    str('{{ size_of_disk_5 }}')
    join_domain              =    str('{{ join_domain }}')
    server_admin_name        =    str('{{ server_admin_name }}')
    server_admin_password    =    str('{{ server_admin_password }}')

    vms = get_vim_objects('vm')
    nic = None
    source_vm_template = [vm for vm in vms  if  vm.name.lower() ==templates.lower() ]
    source_vm_template = source_vm_template[0]
    if not network or network.strip().lower() =="default" or  network.strip() =="":
        for device in source_vm_template.config.hardware.device:
            if isinstance(device,vim.vm.device.VirtualVmxnet3):
                nic = device
    for i in range(0, (quantity)):
        vm_template                  = VMTemplate()
        vm_template.name             = (get_vm_server_name(vm_name,(i))).upper().replace('_','-')
        vm_template.diskList         = []
        vm_template.vmhost           = get_server_host()
        vm_template.osType           = get_os_type(templates)
        nic                          = None
        portgroups = get_vim_objects('prtgrp')
        if network and  network.lower().strip()!='default':
            vm_template.networkName         = network
        else:
            if hasattr(nic,'backing'):
                pg = [prtgrp for prtgrp in  portgroups if  hasattr(prtgrp,'key') and  prtgrp.key== nic.backing.port.portgroupKey]
                pg = pg[0]
                network = pg.name
            else:
                network='VIRT-NET-DEV|APP|TEST2'
            if network.lower()  =='vm_network':
                network='VIRT-NET-DEV|APP|TEST2'
            vm_template.networkName         = network
        vm_template.ip                  = get_free_ip_info(network)
        subnet_info                     = get_subnet_info(network,  vm_template.ip )
        vm_template.mask                = subnet_info['mask'] 
        vm_template.gateway             = subnet_info['gateway']
        vm_template.dnsList             = subnet_info['dns']
        if  join_domain.lower()         == "yes":
            vm_template.domainUser      = subnet_info['user'] if subnet_info['user'] else None
            vm_template.domainPassword  = subnet_info['pass'] if subnet_info['pass'] else None
        owner                           = str(job.owner).split(' ')
        first_name                      = owner[0]
        surname                         = owner[1]
        vm_template.ownerEmail          = first_name+'.'+surname+email_suffix
        vm_template.senderEmail         = "cbolt@virt-net-group.com"
        vm_template.template            = templates

        if customization.strip().lower() == 'none':
            logger.info('No Customization: ')
            vm      = [vm for vm in get_vim_objects('vm') if  vm.name.lower() ==templates.lower()]
            vm      = vm[0]
            vm_space_usage = 0
            for device in vm.config.hardware.device:
                if type(device).__name__ == 'vim.vm.device.VirtualDisk':
                    vm_space_usage  += int(device.deviceInfo.summary.strip().replace('KB','').replace(',','')) if device.deviceInfo.summary else 0
            vm_template.usedSpace   = vm_space_usage
            vm_template.diskList    = None
        elif customization.strip().lower() == 'standard':
            logger.info('Standard Customization: ')

            class_option_list          = prod_options['class_options']
            class_option               = class_option_list[server_class.upper()]
            prop_list                  = [x.split('=')[1].strip().replace('GB','') for x in class_option.split(':')[1].split(',')]
            vcpus                      = int(prop_list[0])
            memory                     = int(prop_list[1])
            disk_count                 = str(prop_list[2]).strip()
            disk_count                 = 0 if not disk_count else int(disk_count)
            vm_template.nmCpu          = vcpus
            vm_template.memoryGb       = memory
            disk_unit_size             = 60
            logger.info([disk_unit_size]*disk_count)
            vm_template.diskList       = get_disk_info([disk_unit_size]*disk_count,vm_template.vmhost)

        elif  customization.strip().lower()    == 'detailed':
            logger.info('Detailed Customization: ')
            vm_template.nmCpu          = int(vcpus)
            vm_template.memoryGb       = int(memory)
            disk_list= []
            logger.info('Sizes of disks: {},{},{},{},{}'.format(size_of_disk_1,size_of_disk_2,size_of_disk_3,size_of_disk_4,size_of_disk_5))
            if  int(size_of_disk_1.strip()) > 0:
                disk_list.append(size_of_disk_1)
            if int(size_of_disk_2.strip()) > 0:
                disk_list.append(size_of_disk_2)
            if int(size_of_disk_3.strip()) > 0:
                disk_list.append(size_of_disk_3)
            if int(size_of_disk_4.strip()) > 0:
                disk_list.append(size_of_disk_4)
            if int(size_of_disk_5.strip()) > 0:
                disk_list.append(size_of_disk_5)
            vm_template.diskList = get_disk_info(disk_list,vm_template.vmhost)

            if server_admin_name is not None and server_admin_name.lower() !="default" and server_admin_name.lower() !="none"  :
                vm_template.serverAdminName = server_admin_name

            if server_admin_password is not None and server_admin_password.lower() !="default" and server_admin_password.lower() !="none" :
                vm_template.serverAdminPassword = server_admin_password
               
        vm_template.annotation = 'Created by '+vm_template.ownerEmail +' on '+datetime.now().strftime("%Y-%m-%d at %H:%M:%S")+' for '+purpose+' via Cloudbolt.' if purpose and purpose.lower() != 'default' else 'Created by '+vm_template.ownerEmail +' on '+datetime.now().strftime("%Y-%m-%d at %H:%M:%S")+' via Cloudbolt.'
        create_server(vm_template)
    if True:
        return "SUCCESS", "The server request has been successfully processed", ""