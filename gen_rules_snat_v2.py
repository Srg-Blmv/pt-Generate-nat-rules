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
        payload = {}
        url =  f"https://{mgmt_ip}/api/v2/GetDeviceGroupsTree"
        r = requests.post(url, headers=headers, json=payload, verify=False, cookies=response_auth.cookies)
        cookies = response_auth.cookies
        # ПОЛУЧАЕМ ID глобальной группы
        global_gr_id = r.json()['groups'][0]['id']
        # Пример 1 группы в глобальной:
        # global_gr_id = (r.json()['groups'][0].get("subgroups")[0].get('id'))
        # Или заберите нужное ID через web api интерфейс: https://IP_MGMT/apidoc/v2/ui/#tag/device-groups/POST/api/v2/GetDeviceGroupsTree

    else:
        print("auth fail")
        exit()



    # Забираем IP которые начинаются в dst и trans
def get_ip():
    # ---------------------  GET IP ----------------------
    url = f"https://{mgmt_ip}:443/api/v2/ListNetworkObjects"



    payload = {
        "deviceGroupId": global_gr_id,
        "objectKinds": ["OBJECT_NETWORK_KIND_IPV4_ADDRESS"],
        "offset": 0,
        "limit": 100000
    }
    response = requests.request("POST", url, json=payload, headers=headers, cookies=cookies, verify=False)

    if response.status_code == 200:
        data = response.json()
        #print(data)
        src_objects = [obj["id"] for obj in data["addresses"] if obj["name"].startswith("src")]
        trans_objects = [obj["id"] for obj in data["addresses"] if obj["name"].startswith("trans")]
        return src_objects, trans_objects
    else:
        print(f"Error: {response.status_code} - {response.text}")
        exit()


def get_zones(zone_name):
    # ---------------------  GET ZONES ----------------------
    url = f"https://{mgmt_ip}:443/api/v2/ListZones"

    payload = {
        "offset": 0,
        "limit": 100
    }
    response = requests.request("POST", url, json=payload,  headers=headers, cookies=cookies, verify=False)

    if response.status_code == 200:
        data = response.json()
        zone = [item["id"] for item in data["zones"] if  item["name"].startswith(zone_name)]
        return(zone)
    else:
        print(f"Error: {response.status_code} - {response.text}")
        exit()





# Создавать будем 1:1  поэтому создавайте сети одинаковые, если dst 16 то транслируемую тоже 16 будь добр
def main():
    auth()
    src_objects, trans_objects = get_ip()
    src_zone = get_zones(src_zone_name)
    dst_zone = get_zones(dst_zone_name)
    url = f"https://{mgmt_ip}/api/v2/CreateNatRule"

    for x in range(len(src_objects)):
        payload = json.dumps({
            "deviceGroupId": f"{global_gr_id}",
            "precedence":f"{precedence}",
            "position": x,
            "enabled": True,
            "name": f"src_{x}",
            "description": "",
            "srcTranslationType": "NAT_SOURCE_TRANSLATION_TYPE_DYNAMIC_IP_PORT",
            "dstTranslationType": "NAT_DESTINATION_TRANSLATION_TYPE_NONE",
            "srcTranslationAddrType": "NAT_SOURCE_TRANSLATION_ADDRESS_TYPE_TRANSLATED",
            "sourceZone": {
                "kind":"RULE_KIND_LIST",
                "objects": {
                    "array":
                        src_zone
                } 
            },
            "destinationZone": {
                "kind": "RULE_KIND_LIST",
                "objects": {
                    "array":
                        dst_zone
                }
            },
            "sourceAddr": {
                "kind":"RULE_KIND_LIST",
                "objects": {
                "array":[
                        src_objects[x]
                    ]
            }
            },            
            "destinationAddr": {
                "kind": "RULE_KIND_ANY",
                "objects": {}
            },
            "service": {
                "kind": "RULE_KIND_ANY",
                "objects": {}
            },
            "srcTranslatedPort": {
                "portRange": {
                    "from": 1,
                    "to": 65535
                }
            },
        "srcTranslatedAddress":[
                trans_objects[x]
            ],
        })

        try:
            response = requests.post(url, headers=headers, json=json.loads(payload), verify=False, cookies=cookies)
            response.raise_for_status()
            print(x, response.json())
        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")



mgmt_ip = "192.168.1.100"
mgmt_login =  "admin"
mgmt_pass = "xxXX1234$"
src_zone_name = "Trusted"
dst_zone_name = "Untrusted"
precedence   = "pre"

main()