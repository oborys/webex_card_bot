import requests
from requests.exceptions import Timeout
import base64
import json


DEF_TIMEOUT = 10
USER_DNA = "devnetuser"
PASSWORD_DNA = "Cisco123!"
dnac_url = "https://sandboxdnac.cisco.com/"

# Will be provided during the workshop
Meraki_API_Key = ''
organizationId = ''
###
requests.packages.urllib3.disable_warnings()

def merakiPostOperation(mailCard):
    # Create a new dashboard administrator for Test network
    HTTP_Request_header = {
    'X-Cisco-Meraki-API-Key': Meraki_API_Key,
    'Content-Type': 'application/json'
    }
    
    baseUrl = 'https://api.meraki.com/api/v1'
    API_Resource = "{}/organizations/{}/admins".format(baseUrl,organizationId)
    
    payload = json.dumps({
    "name": "Test role",
    "email": mailCard,
    "orgAccess": "none",
    "tags": [
        {
        "tag": "west",
        "access": "read-only"
        }
    ]
    })

    createRole = requests.post(API_Resource, data=payload, headers=HTTP_Request_header, timeout=DEF_TIMEOUT)
    print(createRole.text)
    return(createRole.text)


def SimpleAPIoperation(dnac_url):
    postUrlDNA = dnac_url + "api/system/v1/auth/token"
    usrPasDna = USER_DNA + ":" + PASSWORD_DNA
    basicDNA = base64.b64encode(usrPasDna.encode()).decode()
    headers = {"Authorization": "Basic %s" % basicDNA,
                "Content-Type": "application/json;"}
    body_json = ""

    try:
        response = requests.post(postUrlDNA, data=body_json, headers=headers, verify=False, timeout=DEF_TIMEOUT)
    except Timeout as e:
        raise Timeout(e)
    tokenDNA = response.json()['Token']
    urlSimpleDNA = dnac_url + "api/v1/network-device/"

    headers = {'x-auth-token': tokenDNA}
    try:
        response = requests.get(urlSimpleDNA, headers=headers, verify=False)
        #print (response.json())
        deviceInfo = ''
        for device in response.json()['response']:
            deviceInfo += 'Type: ' + device['description'] + '  IP: ' + device['managementIpAddress'] + ' MAC:  ' + device['macAddress'] + '\n'
        print('DeviceInfo ', deviceInfo)
        return (response.json(), deviceInfo)
        if response.status_code != 200:
            print('Error status_code != 200')
    except Timeout as e:
        raise Timeout(e)

# if __name__ == "__main__":
#     merakiPostOperation('test_mail')
#     SimpleAPIoperation(dnac_url)


