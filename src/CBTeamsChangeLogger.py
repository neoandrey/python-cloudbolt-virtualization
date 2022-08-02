from common.methods import set_progress
import requests, ssl, json

requests.packages.urllib3.disable_warnings()
context = ssl._create_unverified_context()
test_url = 'put-webhook-url-here' 
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
    print('data: '+json_data)
    requests.post(self.url, json_data,verify=False, proxies=proxies)

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


def log_change_to_teams(url, server, owner, template, network):
    changeLogger        = TeamsChangeLogger()
    changeLogger.url    =  url 
    owner       = owner
    server_name = server.hostname
    template= template
    changeLogger.summary= '{o} has just created a new server {s}'.format(o=owner, s=server_name)
    changeLogger.themeColor = '#cbc1de'
    changeLogger.sections= []
    changeLoggerSection = TeamsChangeLoggerSection()
    changeLoggerSection.activityTitle =changeLogger.summary
    changeLoggerSection.activitySubtitle ='Using the {t} CloudBolt Blueprint'.format(t=template)
    changeLoggerSection.activityImage='https://th.bing.com/th/id/OIP.0cD0ygr5ZxVug57NmOF5GQHaHa?pid=ImgDet&rs=1'
    changeLoggerSection.facts = []
    fact1=TeamsChangeLoggerSectionsFact('Server Name',server.hostname)
    changeLoggerSection.facts.append(fact1) 
    fact2=TeamsChangeLoggerSectionsFact('IP Address',server.ip)
    changeLoggerSection.facts.append(fact2) 
    fact3=TeamsChangeLoggerSectionsFact('Size',str(server.disk_size))
    changeLoggerSection.facts.append(fact3) 
    fact4=TeamsChangeLoggerSectionsFact('CPU',server.cpu_cnt)
    changeLoggerSection.facts.append(fact4)
    fact5=TeamsChangeLoggerSectionsFact('Memory',str(server.mem_size))
    changeLoggerSection.facts.append(fact5)
    fact6=TeamsChangeLoggerSectionsFact('EPG',network)
    changeLoggerSection.facts.append(fact6)
    fact7=TeamsChangeLoggerSectionsFact('Custodian',owner)
    changeLoggerSection.facts.append(fact7)
    fact8=TeamsChangeLoggerSectionsFact('Date',str(server.add_date))
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


server = Server.objects.first()
owner = 'Mobolaji Aina'
network = 'VMNetwork'
template = 'Ubuntu 18.04 LTS'
log_change_to_teams(test_url, server, owner, template, network)

