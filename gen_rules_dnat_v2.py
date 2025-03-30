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
        dst_objects = [obj["id"] for obj in data["addresses"] if obj["name"].startswith("dst")]
        trans_objects = [obj["id"] for obj in data["addresses"] if obj["name"].startswith("trans")]
        return dst_objects, trans_objects
    else:
        print(f"Error: {response.status_code} - {response.text}")
        exit()


def get_zones():
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
        print(zone)
        return(zone)
    else:
        print(f"Error: {response.status_code} - {response.text}")
        exit()


def main():
    # Создавать будем 1:1  поэтому создавайте сети одинаковые, если dst 16 то транслируемую тоже 16 будь добр
    auth()
    zone = get_zones()
    dst_objects, trans_objects = get_ip()

    url = f"https://{mgmt_ip}/api/v2/CreateNatRule"
    for x in range(len(dst_objects)):

        payload = json.dumps({
            "deviceGroupId": f"{global_gr_id}",
            "precedence": f"{precedence}",
            "position": x+1,
            "enabled": True,
            "name": f"dnat_{x}",
            "description": "",
            "srcTranslationType": "NAT_SOURCE_TRANSLATION_TYPE_NONE",
            "dstTranslationType": "NAT_DESTINATION_TRANSLATION_TYPE_ADDRESS_POOL",
            "srcTranslationAddrType": "NAT_SOURCE_TRANSLATION_ADDRESS_TYPE_NONE",
            "sourceZone": {
                "kind":"RULE_KIND_LIST",
                "objects": {
                    "array":
                        zone
                } 
            },
            "destinationZone": {
                "kind": "RULE_KIND_LIST",
                "objects": {
                    "array":
                        zone
                }
            },
            "sourceAddr": {
                "kind": "RULE_KIND_ANY",
                    "objects": {}
            },
            "destinationAddr": {
                "kind":"RULE_KIND_LIST",
                "objects": {
                    "array":[
                        dst_objects[x]
                    ]
                }
            },
            "service": {
                "kind":"RULE_KIND_ANY",
                "objects": {}
            },
            "dstTranslatedAddress": [
                trans_objects[x]
            ],
            "dstTranslatedPort": 0
            })

        
        #print(payload)

        try:
            response = requests.post(url, headers=headers, json=json.loads(payload), verify=False, cookies=cookies)
            response.raise_for_status()
            print(x, response.json())
        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")




mgmt_ip = "192.168.1.100"
mgmt_login =  "admin"
mgmt_pass = "xxXX1234$"
zone_name = "Trusted"
precedence   = "pre"        # pre or post

main()