import requests
import random
import ipaddress
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


mgmt_ip = "192.168.1.100"
mgmt_login =  "admin"
mgmt_pass = "xxXX1234$"
url = f"https://{mgmt_ip}/api/v2/Login"


payload = {
    "login": mgmt_login,
    "password": mgmt_pass
}
headers = {"Content-Type": "application/json"}

response_auth = requests.post(url, json=payload, headers=headers, verify=False)
if response_auth.status_code == 200:
  print("auth ok")
  url =  f"https://{mgmt_ip}/api/v2/GetDeviceGroupsTree"
  r = requests.post(url, headers=headers, verify=False, cookies=response_auth.cookies)
  global_gr_id = r.json()['groups'][0]['id']



# ---------------------  GET IP ----------------------
url = f"https://{mgmt_ip}:443/api/v2/ListNetworkObjects"



payload = {
    "deviceGroupId": global_gr_id,
    "objectKinds": ["OBJECT_NETWORK_KIND_IPV4_ADDRESS"],
    "offset": 0,
    "limit": 100000
}

response = requests.request("POST", url, json=payload, headers=headers, cookies=response_auth.cookies, verify=False)

if response.status_code == 200:
    data = response.json()
    #print(data)
    dest_src_objects = [obj["id"] for obj in data["addresses"] if obj["name"].startswith("dst") or obj["name"].startswith("trans")]
else:
    print(f"Error: {response.status_code} - {response.text}")


##### ОН УДАЛИТЬ С ПРЕФИКОМ dst и trans еcли надо src то меняй тут:   .startswith("dst") or  obj["name"].startswith("trans") 

# ---------------  DEL rules  ----------------

for i in dest_src_objects:
    url = f"https://{mgmt_ip}:443/api/v2/DeleteNetworkObject"
    payload = {
        "id": i
    }
    response = requests.request("POST", url, json=payload,  headers=headers, cookies=response_auth.cookies, verify=False)
    if response.status_code == 200:
        print(f"del: {i}")
    else:
        print(f"Error: {response.status_code} - {response.text} - ID RULE: {i}")
