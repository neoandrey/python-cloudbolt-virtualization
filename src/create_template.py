from json import JSONEncoder
from pyVmomi import vim
from pyVim.connect import SmartConnect, Disconnect
from pyVim.task import WaitForTask
from datetime import datetime
import argparse,traceback, json,   ssl,requests, math
import getpass
import operator

requests.packages.urllib3.disable_warnings()
context = ssl._create_unverified_context()

def get_datastore_info(datastore):
    ds_info  = {}
    try:
        ds_info['object'] = datastore
        ds_info['summary'] = datastore.summary
        ds_info['capacity'] =   ds_info['summary'] .capacity
        ds_info['free_space'] =   ds_info['summary'] .freeSpace
        ds_info['uncommitted_space'] = ds_info['summary'].uncommitted
        ds_info['free_space_percentage'] = (float(ds_info['free_space']) / ds_info['capacity']) * 100
        ds_info['name'] = ds_info['summary'].name
    except Exception as error:
        print("Unable to access summary for datastore: {d}".format(d=datastore.name))
        print("error: {e}:".format(e=error))
        pass
    return ds_info

class VMConfig():
   name  = "CBVM"
   sourceVM   = "CBVM"
   cluster= "CLUSTER-A"
   host  = None
   vcenterAddress= ""
   vcenterUser= ""
   vcenterPassword= ""

   def get_datastore_name(self):
      return self.diskList[0].split(':')[1]

   def get_fields(self):
     return [x for x in VMConfig.__dict__.keys() if '_' not in x] #['name','nmCpu','memoryGb','diskList','template','networkName','storageFormat','vmhost','hasCD','hasFloppy','cluster','osType','ip','mask','gateway','vcenterAddress','vcenterUser','vcenterPassword','dnsList','osDistribution','ownerEmail','senderEmail','emailUser','emailPassword','emailServer','requestURL','emailport','useLDAP','sendEmail']

   def init_config(self,json_data):
     for field in  self.get_fields():
        if field in json_data:
          setattr(self, field, json_data[field])
     return self

   def to_json(self):
     json_object ={}
     for  i in  dir(self): 
       if '_' not in  str(i) and i not in vars(VMConfig()).keys() and str(i) not in ['toJson','default','iterencode','encode']:
         json_object[i] =getattr(self, i)
     return json.dumps(json_object) 

def create_template(vm_config):

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
      ds_name_to_space_map = []
      vm_size = 0
      resource_pool = None
      source_vm = [vm  for vm in vmList if vm.name.lower() == vm_config.sourceVM.lower()]
      source_vm = source_vm[0] if source_vm else None
      if source_vm:
        vm_exists = [vm  for vm in vmList if vm.name.lower() == vm_config.name.lower() ]
        if  not vm_exists:
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
                resource_pool  = cluster.resourcePool
                for ds in datastore_list:
                    d_store_info = get_datastore_info(ds)
                    ds_name_to_space_map[d_store_info['name']] = int(d_store_info['free_space'])/(1024*1024*1024)
                config = source_vm.config
                devices = config.hardware.device
                for device in devices:
                    if isinstance(device, vim.vm.device.VirtualDisk):
                        disk_kb = device.capacityInKB
                        vm_size+=(disk_kb /(1024*1024))
                ds_name_to_space_map = sorted(ds_name_to_space_map.items(), key=operator.itemgetter(1))
                for k,v in ds_name_to_space_map:
                  if  v > vm_size:
                    datastore = k
                    break          
                if resource_pool:
                   relocateSpec = vim.vm.RelocateSpec(pool=resource_pool)
                   relocateSpec.datastore = datastore
                   clonespec = vim.vm.CloneSpec(powerOn=False, template=True, location = relocateSpec)
                   print("cloning VM...")
                   task = source_vm.Clone(folder=source_vm.parent, name=vm_config.name, spec=clonespec)
                   WaitForTask(task)
                   print("VM cloned.")
        else:
            print("A virtual machine with the name: {} already exists".format(vm_config.name))
      else:
        print("A source vm with name: {} does not exist".format(vm_config.sourceVM))
if __name__ == "__main__":
      create_template()