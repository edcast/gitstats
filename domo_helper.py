import requests  # used for http request
import json #import the json module

from pydomo import *
from pydomo.users import CreateUserRequest
from pydomo.groups import CreateGroupRequest
from pydomo.datasets import DataSetRequest, Policy
from pydomo.datasets import PolicyFilter, FilterOperator, PolicyType
from requests.auth import HTTPBasicAuth

def get_domo_client(client_id, client_secret, api_host):
  return Domo(client_id, client_secret, api_host=api_host, use_https=True, request_timeout=120)

def get_access_token(client_id, client_secret, api_host):
  auth = HTTPBasicAuth(client_id, client_secret)
  try:
    response = requests.post(url='https://{0}/oauth/token?grant_type=client_credentials'.format(api_host), auth=auth, timeout=60)
    return json.loads(response.text)['access_token']
  except Exception as exception_message:
    print(exception_message)
    raise Exception(exception_message)

def record_exist(details, attr, record):
  exist = False
  record_id = ''
  for detail in details:
    if detail[attr] == record:
      exist = True
      record_id = detail['id']
      break
  return exist, record_id

#############################################################################
######################## User Helper ########################################
#############################################################################

def list_user(domo_client, offset, limit=500):
  return domo_client.users.list(limit, offset)

def user_exist(domo_client, email):
  offset = 0
  user_id = ''
  user_list = list_user(domo_client, offset)
  exist = False
  while len(user_list) > 0:
    exist, user_id = record_exist(user_list, 'email', email)
    if exist:
      print("{0} User Exist!".format(email))
      break
    offset += 500
    user_list = list_user(domo_client, offset)
  return exist, user_id

def create_user(domo_client, args={}):
  exist, user_id = user_exist(domo_client, args['email'])
  if not exist:
    user_request = CreateUserRequest()
    user_request.name = args['name']
    user_request.email = args['email']
    user_request.role = 'Participant'
    send_invite = False

    # Create a User
    user = domo_client.users.create(user_request, send_invite)
    user_id = user['id']
    print("Created User '{}'".format(user['name']))
  return user_id

#############################################################################
######################## Group Helper #######################################
#############################################################################

def list_group(domo_client, offset, limit=500):
  return domo_client.groups.list(limit, offset)

def list_user_in_group(domo_client, group_id, offset, limit=500):
  return domo_client.groups.list_users(group_id, limit, offset)

def group_exist(domo_client, name):
  offset = 0
  group_id = ''
  group_list = list_group(domo_client, offset)
  exist = False
  while len(group_list) > 0:
    exist, group_id = record_exist(group_list, 'name', name)
    if exist:
      print("{0} Group Exist!".format(name))
      break
    offset += 500
    group_list = list_group(domo_client, offset)
  return exist, group_id

def user_exist_in_group(domo_client, group_id, user_id):
  offset = 0
  user_list = list_user_in_group(domo_client, group_id, offset)
  exist = False
  while len(user_list) > 0:
    if user_id in user_list:
      exist = True
      print("{0} User Exist in the Group!".format(user_id))
      break
    offset += 500
    user_list = list_user_in_group(domo_client, group_id, offset)
  return exist, user_id

def add_user_to_group(domo_client, args={}):
  exist, user_id = user_exist_in_group(domo_client, args['group_id'], args['user_id'])
  if not exist:
    domo_client.groups.add_user(args['group_id'], user_id)
    print("User Added to the Group!")

def remove_user_from_group(domo_client, args={}):
  exist, user_id = user_exist_in_group(domo_client, args['group_id'], args['user_id'])
  if exist:
    domo_client.groups.remove_user(args['group_id'], user_id)
    print("User Removed from the Group!")

def create_group(domo_client, name):
  exist, group_id = group_exist(domo_client, name)
  if not exist:
    group_request = CreateGroupRequest()
    group_request.name = name
    group_request.active = True
    group_request.default = False

    # Create a Group
    group = domo_client.groups.create(group_request)
    group_id = group['id']
    print("Created Group '{}'".format(group['name']))
  return group_id

#############################################################################
######################## PDP Helper #########################################
#############################################################################

def list_pdp(domo_client, dataset_id):
  return domo_client.datasets.list_pdps(dataset_id)

def pdp_exist(domo_client, name, dataset_id):
  pdp_id = ''
  pdp_list = list_pdp(domo_client, dataset_id)
  exist = False
  if len(pdp_list) > 0:
    exist, pdp_id = record_exist(pdp_list, 'name', name)
    if exist:
      print("{0} PDP Exist!".format(name))
  return exist, pdp_id

def create_pdp(domo_client, name, dataset_id, group_ids):
  exist, pdp_id = pdp_exist(domo_client, name, dataset_id)
  if not exist:
    pdp_request = Policy()
    pdp_request.name = name
    pdp_request.filters = []
    pdp_request.type = PolicyType.USER
    pdp_request.users = []
    pdp_request.groups = group_ids

    pdp = domo_client.datasets.create_pdp(dataset_id, pdp_request)
    print("Created a Personalized Data Policy (PDP): {}, id: {}".format(pdp['name'], pdp['id']))

#############################################################################
######################## Dataset Helper #####################################
#############################################################################

def list_dataset(domo_client, offset, limit=50):
  access_token = get_access_token(domo_client['client_id'], domo_client['client_secret'], domo_client['api_host'])
  response = requests.get(
    url='https://{0}/v1/datasets?sort=name&offset={1}&limit={2}'.format(domo_client['api_host'], offset, limit),
    headers={"Authorization": "Bearer %s" % access_token, "Accept": "application/json", "Content-Type": "application/json"},
    timeout=60
  )
  return json.loads(response.text)

def get_datasets(domo_client, name):
  offset = 0
  dataset_ids = set()
  dataset_list = list_dataset(domo_client, offset)
  while len(dataset_list) > 0:
    for dataset_detail in dataset_list:
      if name in dataset_detail['name']:
        dataset_ids.add(dataset_detail['id'])
    offset += 50
    dataset_list = list_dataset(domo_client, offset)
  return dataset_ids

def create_dataset(domo_client, name):
  url = "https://{0}/v1/json".format(domo_client['api_host'])
  payload = json.dumps({
    "name": name
  })
  access_token = get_access_token(domo_client['client_id'], domo_client['client_secret'], domo_client['api_host'])
  headers = {
    'Content-Type': 'application/json',
    'Authorization': "Bearer {0}".format(access_token)
  }
  response = requests.request("POST", url, headers=headers, data=payload)
  return json.loads(response.text)

def import_data(domo_client, dataset_id, payload):
  url = "https://{0}/v1/json/{1}/data".format(domo_client["api_host"], dataset_id)
  access_token = get_access_token(domo_client['client_id'], domo_client['client_secret'], domo_client['api_host'])
  headers = {
    'Content-Type': 'application/json',
    'Authorization': "Bearer {0}".format(access_token)
  }
  requests.request("PUT", url, headers=headers, data=payload)

def enable_pdp(dataset_id, domo_client={}):
  domo = get_domo_client(domo_client['client_id'], domo_client['client_secret'], domo_client['api_host'])
  dataset = domo.datasets.get(dataset_id)
  if dataset['pdpEnabled']:
    print("Already, PDP Enabled for the Dataset {0}".format(dataset_id))
    return
  try:
    access_token = get_access_token(domo_client['client_id'], domo_client['client_secret'], domo_client['api_host'])
    response = requests.put(
      url='https://{0}/v1/datasets/{1}'.format(domo_client['api_host'], dataset_id),
      headers={"Authorization": "Bearer %s" % access_token, "Accept": "application/json", "Content-Type": "application/json"},
      data = json.dumps({ "pdpEnabled": True }),
      timeout=60
    )
    print("PDP Enabled for the Dataset {0}".format(dataset_id))
  except Exception as exception_message:
    print(exception_message)
    raise Exception(exception_message)
