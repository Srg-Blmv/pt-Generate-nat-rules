import requests
import json
import ipaddress
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

global_gr_id = ""
cookies = ""
headers = {"Content-Type": "application/json"}

def auth():
    global global_gr_id, cookies

    url = f"https://{mgmt_ip}/api/v2/Login"
    
    payload = {
        "login": mgmt_login,
        "password": mgmt_pass
    }
    
    response_auth = requests.post(url, json=payload, headers=headers, verify=False)
    if response_auth.status_code == 200:
        print("auth ok")
        url =  f"https://{mgmt_ip}/api/v2/GetDeviceGroupsTree"
        r = requests.post(url, headers=headers, verify=False, cookies=response_auth.cookies)
        cookies = response_auth.cookies
        # ПОЛУЧАЕМ ID глобальной группы
        global_gr_id = r.json()['groups'][0]['id']
        # Пример 1 группы в глобальной:
        # global_gr_id = (r.json()['groups'][0].get("subgroups")[0].get('id'))
        # Или заберите нужное ID через web api интерфейс: https://IP_MGMT/apidoc/v2/ui/#tag/device-groups/POST/api/v2/GetDeviceGroupsTree

    else:
        print("auth fail")
        exit()


def send_ip(net,name):
    url_create_ip  = f"https://{mgmt_ip}/api/v2/CreateNetworkObject"
    x = 0
    for ip in ipaddress.ip_network(net).hosts():
        payload = json.dumps({
          "name": f"{name}_{ip}",
          "deviceGroupId": global_gr_id,
          "description": "",
          "value": {
          "inet": {
              "inet": f"{ip}/32"
          }
        }})

        try:
            response = requests.post(url_create_ip, headers=headers, json=json.loads(payload), verify=False, cookies=cookies)
            response.raise_for_status()
            print(payload)
            x = x + 1
            #print(x, response.text)
        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")



mgmt_ip = "192.168.1.100"
mgmt_login =  "admin"
mgmt_pass = "xxXX1234$"
dst_network = '11.11.224.0/27'
translated_net = '48.0.224.0/27'



auth()
send_ip(dst_network, "dst")
send_ip(translated_net, "trans")

### Для генерации src ip
# src_net = '10.0.224.0/27'
# send_ip(src_net, "src")