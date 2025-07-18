import requests, sys, subprocess, os
import in_place, re
import urllib
from operator import itemgetter

from JWTAuth import JWTAuth


#API_SERVER_HOST = 'http://172.17.0.1:7601'
API_SERVER_HOST = 'https://vantage6.local'
API_SERVER_URL = API_SERVER_HOST + '/server/api'
#API_STORE_HOST = 'http://172.17.0.1:7602'
API_STORE_HOST = 'https://vantage6.local'
API_STORE_URL = API_STORE_HOST + '/store/api'

headers={
    'Content-type':'application/json', 
    'Accept':'application/json',
    'Server-Url': API_SERVER_URL    # workaround for "server_url"
}

store_headers={
    'Content-type':'application/json', 
    'Accept':'application/json',
    'Server-Url': API_SERVER_URL    # workaround for "server_url"
}

jwt_server_auth_root = JWTAuth(
    auth_url=f"{API_SERVER_URL}/token/user",
    api_payload={
        'username': 'root',
        'password': 'test',
    }
)

jwt_server_auth_user1 = JWTAuth(
    auth_url=f"{API_SERVER_URL}/token/user",
    api_payload={
        'username': 'user1',
        'password': 'User1User1!',
    }
)

def get(session, endpoint, data={}, params=""):
    getUrl = f"{session.url}{endpoint}"
    if len(params) > 0:
        getUrl += f"?{params}"
    response = session.get(getUrl, json=data)

    if response.status_code != 200:
        print(f"{response.status_code} ({response.text}) for get on {getUrl}")
        sys.exit(1)
        
    response = response.json()
    if 'data' in response:
        return response['data']
    else:
        return response

def post(session, endpoint, data={}, params=""):
    postUrl = f"{session.url}{endpoint}"
    if len(params) > 0:
        postUrl += f"?{params}"
    response = session.post(postUrl, json=data)

    if response.status_code != 200:
        print(f"{response.status_code} ({response.text}) for post on {postUrl}")
        sys.exit(1)
        
    response = response.json()
    if 'data' in response:
        return response['data']
    else:
        return response

    
def createIfNotExists(session, endpoint, data={}, params=""):
    getUrl = f"{session.url}/{endpoint}"
    if len(params) > 0:
        getUrl += f"?{params}"
    response = session.get(getUrl, json=data)

    if response.status_code != 200:
        print(f"{response.status_code} ({response.text}) for get on {getUrl}")
        sys.exit(1)
        
    if len(response.json()['data']) == 0:            
        response = session.post(session.url + endpoint, json=data)
        
        if response.status_code not in {200, 201}:
            print(f"response.status_code {response.status_code} ({response.text}) for post {endpoint} with {data}, but 200 (Ok) or 201 (Created) was expected")
            sys.exit(1)

        return response.json()
    else:
        return response.json()['data'][0]

def invalidateIfExists(session, endpoint, data={}, params=""):
    getUrl = f"{session.url}/{endpoint}"
    if len(params) > 0:
        getUrl += f"?{params}"
    print(f"getUrl: {getUrl}")
    response = session.get(getUrl, json=data)

    if response.status_code != 200:
        print(f"{response.status_code} ({response.text}) for get on {getUrl}")
        sys.exit(1)
        
    if len(response.json()['data']) != 0:            
        print(f"found algorithm, will invalidate using {session.url}{endpoint}/{response.json()['data'][0]['id']}/invalidate")
        response = session.post(f"{session.url}{endpoint}/{response.json()['data'][0]['id']}/invalidate", json=data)
        
        if response.status_code not in {200, 201}:
            print(f"response.status_code {response.status_code} ({response.text}) for post {endpoint} with {data}, but 200 (Ok) or 201 (Created) was expected")
            sys.exit(1)

        return response.json()
    else:
        return response.json()['data'][0]

def set_api_key(api_key, filename):
    with in_place.InPlace(filename) as file:
        print(f"editing {filename}, inserting api_key {api_key}")
        for line in file:
            line = re.sub('NODE_API_KEY=.*$', f"NODE_API_KEY={api_key}", line)
            file.write(line)
        file.close()

#
# provide session with headers and auth info so that this does not need te be repeated
#
server_session = requests.session()
server_session.headers = headers
server_session.auth = jwt_server_auth_root
server_session.url = API_SERVER_URL

store_session = requests.session()
store_session.headers = store_headers
store_session.auth = jwt_server_auth_root
store_session.url = API_STORE_URL

# make sure the test environment is up with clean volumes by running `just all-down-clean server-up`
# out, err = subprocess.Popen(['bash', '-l', "-c", "/home/jan/.cargo/bin/just all-down-clean server-up"], env={}).communicate()
# sys.exit(0)

# verify access to the server API
response = get(server_session, '/user')

# 2. get/create organization and collaboration
test_org = createIfNotExists(server_session, "/organization", data={'name': 'TestOrg'}, params='name=TestOrg')

test_collab = createIfNotExists(server_session, "/collaboration", 
                                data={'name': 'TestCollab',
                                      'organization_ids': [test_org['id']],
                                      'encrypted': 0},
                                params="name=TestCollab")

# nodes_endpoint = test_collab['nodes']

# nodes = session.get(API_SERVER + nodes_endpoint)
# print(f"nodes: {nodes.json()['data']}")

# create node
#node_name = f"{test_collab['name']} - {test_org['name']}"
#node_data = {
#    'collaboration_id': test_collab['id'],
#    'name': node_name,
#    'organization_id': test_org['id']
#    }
#created_node = createIfNotExists(server_session, "/node", data=node_data, 
#                params=f"name={node_name}&organization_id={test_org['id']}&collaboration_id={test_collab['id']}")

# replace the API key in the .env file
#print(f"node created, api_key: {created_node['api_key']}")
#if 'api_key' in created_node:
#    set_api_key(created_node['api_key'], '.env')

# get roles
roles = get(server_session, "/role")

roleids_for_user1 = itemgetter('Researcher', 'Organization Admin', 'Collaboration Admin')({r['name']: r['id'] for r in roles})

user1 = createIfNotExists(server_session, "/user", data={
        'email': "UserOne@vantage6.local",
        'firstname': 'User',
        'lastname': 'One',
        'organization_id': test_org['id'],
        'password': 'User1User1!',
        'roles': roleids_for_user1,
        'rules': [],
        'username': 'user1'
    }, params="username=user1")

#
# create the algorithm store
#
created_store = createIfNotExists(server_session, '/algorithmstore', data={
        'algorithm_store_url': f"{API_STORE_URL}",
        'collaboration_id': test_collab['id'],
        'name': 'TestStore',
        'server_url': f"{API_SERVER_URL}"
        #'force': true,
    }, params = 'name=TestStore')

store_roles = get(store_session, '/role')

store_roleids_for_user1 = itemgetter(
    'Developer', 'Store Manager', 'Server Manager', 'Algorithm Manager', 'Reviewer'
    )({r['name']: r['id'] for r in store_roles})

registered_reviewer = createIfNotExists(store_session, '/user', data={
        'roles': store_roleids_for_user1,
        'username': 'user1'
    }, params="username=user1")

invalidateIfExists(store_session, '/algorithm', params=f"name={urllib.parse.quote_plus('OMOP Cohort diagnostics (debug)')}")

pending_algorithm = createIfNotExists(store_session, '/algorithm', data={
  "name": "OMOP Cohort diagnostics (debug)",
  "description": "Debig version of OMOP Cohort Diagnostics",
  "image": "registry.vantage6.local/omop-cohort-diagnostics-debug",
  "vantage6_version": "4.6",
  "code_url": "https://mygitrepo.org",
  "documentation_url": "https://thehyve.nl",
  "partitioning": "horizontal",
  "functions": [
  {
    "name": "cohort_diagnostics_central",
    "databases": [
      {
        "name": "OMOP CDM Database",
        "description": "Database to use for the OHDSI Cohort Diagnostics"
      }
    ],
    "ui_visualizations": [],
    "arguments": [
      {
        "type": "string",
        "description": "The cohort definitions to use for the analysis.",
        "name": "cohort_definitions"
      },
      {
        "type": "string_list",
        "description": "The cohort names.",
        "name": "cohort_names"
      },
      {
        "type": "json",
        "description": "The meta cohorts output.",
        "name": "meta_cohorts"
      },
      {
        "type": "json",
        "description": "The settings for the temporal covariate analysis.",
        "name": "temporal_covariate_settings"
      },
      {
        "name": "diagnostics_settings",
        "type": "json",
        "description": "The settings for the diagnostics."
      },
      {
        "name": "organizations_to_include",
        "type": "organization_list",
        "description": "The organizations to include in the analysis."
      }
    ],
    "description": "Create a cohort diagnostics report for a set of cohorts.",
    "type": "central"
  }
],
}, params="name=OMOP Cohort diagnostics (debug)")

review = createIfNotExists(store_session, '/review', data={
        'algorithm_id': pending_algorithm['id'],
        'reviewer_id': registered_reviewer['id']
    }, params=f"algorithm_id={pending_algorithm['id']}&reviewer_id={registered_reviewer['id']}")

store_session.auth = jwt_server_auth_user1
approval = post(store_session, f"/review/{review['id']}/approve")
