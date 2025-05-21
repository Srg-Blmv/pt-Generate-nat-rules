import requests
import json
import random
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

    else:
        print("auth fail")
        exit()
# GET DNAT RULES


def get_nat_rules():
    url = f"https://{mgmt_ip}:443/api/v2/ListNatRules"

    payload = {
        "deviceGroupId": global_gr_id,
        "precedence": f"{precedence}",
        "offset": 0,
        "limit": 100000
    }

    response = requests.request("POST", url, json=payload, headers=headers, cookies=cookies, verify=False)

    if response.status_code == 200:

        data = response.json()
        ########  ЕСЛИ НУЖНО УДАЛИТЬ SNAT то необходимо заменить "dnat" на "snat"
        nat_rules = [obj["id"] for obj in data["items"] if obj["name"].startswith(prefix_name_nat_rule)]
        return nat_rules
    else:
        print(f"Error: {response.status_code} - {response.text}")



def main():
    auth()
    nat_rules = get_nat_rules()
    url_remove_rule = f"https://{mgmt_ip}:443/api/v2/DeleteNatRule"

    for id in nat_rules:
        payload = json.dumps({
            "id": id,
        })
        try:
            response = requests.request("POST", url_remove_rule, headers=headers, data=payload,cookies=cookies,  verify=False)
            print(f"id: {id},  code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")




mgmt_ip = "192.168.1.100"
mgmt_login =  "admin"
mgmt_pass = "xxXX1234$"
prefix_name_nat_rule = "dnat"   # dnat  or snat 
precedence = "pre"            # post or pre

main()