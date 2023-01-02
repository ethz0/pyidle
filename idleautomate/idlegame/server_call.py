#!/usr/bin/env python3
import hashlib
import json
import logging
import os
import requests

from base64 import b64decode

try:
    import idleautomate.idlegame.config as config
except:
    import config as config

from datetime import datetime
from argparse import ArgumentParser
from requests.exceptions import HTTPError

BOLD = '\033[1m'
ENDC = '\033[0m'
RED = '\033[31m'
GREEN = '\033[32m'
YELLOW = '\033[33m'
BLUE = '\033[34m'
CYAN = '\033[36m'

logger = logging.getLogger('idleautomate.window.window')

URL = 'https://master.idlechampions.com/~idledragons/'
URI = 'post.php'
CALL_URL = URL + URI

UserID = config.UserID
Hash = config.Hash

homedir = os.getenv("HOME")
cachedir = 'Library/Application Support/Steam/steamapps/common/IdleChampions/IdleDragonsMac.app/Contents/Resources/Data/StreamingAssets/downloaded_files/'
cachepath = f'{homedir}/{cachedir}'
cachefile = 'cached_definitions.json'

headers = {'user-agent': 'WinHttp.WinHttpRequest.5.1'}

### game specific data
instance_id = '0'
include_free_play_objectives = "true"
timestamp = '0'
request_id = '0'
network_id = '11'
mobile_client_version = config.ClientVersion
localization_aware = "true"
code = None
language_id = '1'
instance_key = '0'
mission_id = None
crusaders = None
patron_id = '0'
# game_instance_id 0 is foreground game 1-3 are background
game_instance_id = '0'
adventure_id = None
patron_tier = None
chest_type_id = None


getPlayServerForDefinitions = {
    'call': 'getPlayServerForDefinitions',
    'timestamp': timestamp,
    'request_id': request_id,
    'network_id': network_id,
    'mobile_client_version': mobile_client_version,
    'localization_aware': localization_aware
}


getuserdetails = {
    'call': 'getuserdetails',
    'language_id': language_id,
    'user_id': UserID,
    'hash': Hash,
    'instance_key': instance_key,
    'include_free_play_objectives': include_free_play_objectives,
    'timestamp': timestamp,
    'request_id': request_id,
    'network_id': network_id,
    'mobile_client_version': mobile_client_version,
    'localization_aware': localization_aware
}


getusergameinstance = {
    'call': 'getusergameinstance',
    'language_id': '1',
    'user_id': UserID,
    'hash': Hash,
    'language_id': '1',
    'include_free_play_objectives': include_free_play_objectives,
    'timestamp': timestamp,
    'request_id': request_id,
    'network_id': network_id,
    'mobile_client_version': mobile_client_version,
    'instance_id': '1',
    'game_instance_id': '0',
}


buysoftcurrencychest = {
    'call': 'buysoftcurrencychest',
    'language_id': '1',
    'user_id': UserID,
    'hash': Hash,
    'instance_key': '1',
    'timestamp': timestamp,
    'request_id': request_id,
    'network_id': network_id,
    'mobile_client_version': mobile_client_version,
    'localization_aware': localization_aware,
    'chest_type_id': chest_type_id, # 1: silver 2: gold
    'count': 100
}


opengenericchest = {
    'call': 'opengenericchest',
    'language_id': '1',
    'user_id': UserID,
    'hash': Hash,
    'instance_id': instance_id,
    'timestamp': timestamp,
    'request_id': request_id,
    'network_id': network_id,
    'mobile_client_version': mobile_client_version,
    'localization_aware': localization_aware,
    'chest_type_id': 1, # 1: silver 2: gold 282: electrum
    'count': 99,
    'gold_per_second': 0,
    'checksum': None,
    'pack_id': 0
}


redeemcoupon = {
    'call': 'redeemcoupon',
    'user_id': UserID,
    'hash': Hash,
    'code': code,
    'instance_id': '1',
    'timestamp': timestamp,
    'request_id': request_id,
    'language_id': '1',
    'network_id': network_id,
    'mobile_client_version': mobile_client_version,
    'localization_aware': localization_aware,
}


getallformationsaves = {
    'call': 'getallformationsaves',
    'user_id': UserID,
    'hash': Hash,
    'instance_id': '1',
    'timestamp': timestamp,
    'request_id': request_id,
    'language_id': '1',
    'network_id': network_id,
    'mobile_client_version': mobile_client_version,
    'localization_aware': localization_aware,
}


setcurrentobjective = {
    'call': 'setcurrentobjective',
    'user_id': UserID,
    'hash': Hash,
    'instance_id': '1',
    'timestamp': timestamp,
    'request_id': request_id,
    'language_id': '1',
    'network_id': network_id,
    'mobile_client_version': mobile_client_version,
    'localization_aware': localization_aware,
    'game_instance_id': game_instance_id,
    'adventure_id': adventure_id,
    'patron_id': patron_id,
    'patron_tier': patron_tier,
}


softreset = {
    'call': 'softreset',
    'user_id': UserID,
    'hash': Hash,
    'instance_id': '1',
    'timestamp': timestamp,
    'request_id': request_id,
    'language_id': '1',
    'network_id': network_id,
    'mobile_client_version': mobile_client_version,
    'localization_aware': localization_aware,
    'game_instance_id': game_instance_id,
}


startmission = {
    'call': 'startmission',
    'user_id': UserID,
    'hash': Hash,
    'instance_id': '1',
    'timestamp': timestamp,
    'request_id': request_id,
    'language_id': '1',
    'network_id': network_id,
    'mobile_client_version': mobile_client_version,
    'localization_aware': localization_aware,
    'mission_id': mission_id,
    'crusaders': crusaders,
}


def serverRequest(CALL_URL, params, headers):

    try:
        response = requests.post(CALL_URL, headers=headers, params=params)
        response.raise_for_status()
        return response
    except HTTPError as http_err:
        print(f'HTTP error occurred: {http_err}')
    except Exception as e:
        print(f'Unknown error occused: {e}')


def getServer():
    res = serverRequest(CALL_URL, getPlayServerForDefinitions, headers)
    server_detail = json.loads(res.text)
    if server_detail['success']:
        URL = server_detail['play_server']
        logging.debug(f"{CYAN}Using server: {URL}{ENDC}")
    return URL


def getUserDetails():
    res = serverRequest(CALL_URL, getuserdetails, headers)
    return json.loads(res.text)


def getUserDetails2(CALL_URL, headers):
    res = serverRequest(CALL_URL, getuserdetails, headers)
    return json.loads(res.text)


def getUserGameInstance():
    getusergameinstance['instance_id'] = instance_id
    getusergameinstance['game_instance_id'] = game_instance_id
    res = serverRequest(CALL_URL, getusergameinstance, headers)
    return json.loads(res.text)


def redeemCode(code):
    redeemcoupon['code'] = code
    redeemcoupon['instance_id'] = instance_id
    res = serverRequest(CALL_URL, redeemcoupon, headers)
    return json.loads(res.text)


def openChests(type, count=None):
    open_chest_salt = b64decode("YWxsdG9vZWFzdHl0b2JlbGlldmVpdHNub3RidXR0ZXI=")
    string_to_checksum = str(opengenericchest['gold_per_second']) + open_chest_salt
    opengenericchest['chest_type_id'] = type
    opengenericchest['checksum'] = hashlib.md5(string_to_checksum.encode('utf-8')).hexdigest()
    if count > 99:
        opengenericchest['count'] = 99
        res = serverRequest(CALL_URL, opengenericchest, headers)
        parseChests(res.text)
        count = count - 99
        openChests(type, count=count)
    elif count > 0:
        opengenericchest['count'] = count
        res = serverRequest(CALL_URL, opengenericchest, headers)
        parseChests(res.text)


def openChests2(type, CALL_URL, count=None, loot_list=[]):
    open_chest_salt = "alltooeastytobelieveitsnotbutter"
    string_to_checksum = str(opengenericchest['gold_per_second']) + open_chest_salt
    opengenericchest['chest_type_id'] = type
    opengenericchest['checksum'] = hashlib.md5(string_to_checksum.encode('utf-8')).hexdigest()
    if count > 99:
        opengenericchest['count'] = 99
        res = serverRequest(CALL_URL, opengenericchest, headers)
        loot = json.loads(res.text)
        loot_list = loot_list + loot['loot_details']
        count = count - 99
        return openChests2(type, CALL_URL, count=count, loot_list=loot_list)
    elif count > 0:
        opengenericchest['count'] = count
        res = serverRequest(CALL_URL, opengenericchest, headers)
        loot = json.loads(res.text)
        loot_list = loot_list + loot['loot_details']
        return loot_list


def buyChests(CALL_URL, type, count=None):
    buysoftcurrencychest['chest_type_id'] = type
    if count > 100:
        buysoftcurrencychest['count'] = 100
        res = serverRequest(CALL_URL, buysoftcurrencychest, headers)
        logging.debug(res.text)
        count = count - 100
        buyChests(CALL_URL, type, count=count)
    elif count > 0:
        buysoftcurrencychest['count'] = count
        res = serverRequest(CALL_URL, buysoftcurrencychest, headers)        
        logging.debug(res.text)


def parseChests(res):
    gilded = 0
    s_speed = 0
    m_speed = 0
    l_speed = 0
    h_speed = 0

    with open (cachepath + cachefile) as cfile:
        cdata = json.load(cfile)

    data = json.loads(res)

    if data['success'] == True:
        print(f"Remaining: {data['chests_remaining']}") 
        for result in data['loot_details']:
            if 'gilded' in result:
                if result['gilded'] == True:
                    for buff in cdata['hero_defines']:
                        if result['hero_id'] == buff['id']:
                            name = buff['name']
                        for loot in cdata['loot_defines']:
                            if result['hero_id'] == loot['hero_id'] and result['slot_id'] == loot['slot_id']:
                                item_name = loot['name']
                    print(f"Shiny: {name} - slot {result['slot_id']} - {item_name} - {result['enchant_level']}")
                    gilded += 1
            elif 'add_inventory_buff_id' in result:
                for buff in cdata['buff_defines']:
                    if result['add_inventory_buff_id'] == buff['id']:
                        if buff['id'] == 74:
                            s_speed += 1
                        if buff['id'] == 75:
                            m_speed += 1
                        if buff['id'] == 76:
                            l_speed += 1
                        if buff['id'] == 77:
                            h_speed += 1
    else:
        logging.debug('Failed Call')

    if gilded > 0:
        print(f'Found {gilded} Shinies')
    if s_speed > 0:
        print(f'Found {s_speed} Small Speed Potions')
    if m_speed > 0:
        print(f'Found {m_speed} Medium Speed Potions')
    if l_speed > 0:
        print(f'Found {l_speed} Large Speed Potions')
    if h_speed > 0:
        print(f'Found {h_speed} Huge Speed Potions')


def parseChests2(loot_data):

    loot = {
        'gilded': 0,
        'gilded_list': [],
        's_speed': 0,
        'm_speed': 0,
        'l_speed': 0,
        'h_speed': 0,
        't_blacksmith': 0,
        's_blacksmith': 0,
        'm_blacksmith': 0,
        'l_blacksmith': 0,
        't_bounty': 0,
        's_bounty': 0,
        'm_bounty': 0,
        'l_bounty': 0,
    }

    with open (cachepath + cachefile) as cfile:
        cdata = json.load(cfile)

    for ld in loot_data:
        if 'gilded' in ld:
            if ld['gilded'] == True:
                for buff in cdata['hero_defines']:
                    if ld['hero_id'] == buff['id']:
                        name = buff['name']
                    for cld in cdata['loot_defines']:
                        if ld['hero_id'] == cld['hero_id'] and ld['slot_id'] == cld['slot_id']:
                            item_name = cld['name']
                logger.info(f"Shiny: {name} - slot {ld['slot_id']} - {item_name} - {ld['enchant_level']}")
                loot['gilded_list'].append(ld)
                loot['gilded'] += 1
        elif 'add_inventory_buff_id' in ld:
            for buff in cdata['buff_defines']:
                if ld['add_inventory_buff_id'] == buff['id']:
                    if buff['id'] == 17:
                        loot['t_bounty'] += 1
                    if buff['id'] == 18:
                        loot['s_bounty'] += 1
                    if buff['id'] == 19:
                        loot['m_bounty'] += 1
                    if buff['id'] == 20:
                        loot['l_bounty'] += 1                    
                    if buff['id'] == 31:
                        loot['t_blacksmith'] += 1
                    if buff['id'] == 32:
                        loot['s_blacksmith'] += 1
                    if buff['id'] == 33:
                        loot['m_blacksmith'] += 1
                    if buff['id'] == 34:
                        loot['l_blacksmith'] += 1                    
                    if buff['id'] == 74:
                        loot['s_speed'] += 1
                    if buff['id'] == 75:
                        loot['m_speed'] += 1
                    if buff['id'] == 76:
                        loot['l_speed'] += 1
                    if buff['id'] == 77:
                        loot['h_speed'] += 1                    

    # if gilded > 0:
    #     print(f'Found {gilded} Shinies')
    # if s_speed > 0:
    #     print(f'Found {s_speed} Small Speed Potions')
    # if m_speed > 0:
    #     print(f'Found {m_speed} Medium Speed Potions')
    # if l_speed > 0:
    #     print(f'Found {l_speed} Large Speed Potions')
    # if h_speed > 0:
    #     print(f'Found {h_speed} Huge Speed Potions')
    logging.debug(loot)


# def startMission():
#     crusaders = 1
#     mission_id = 1
#     res = serverRequest(CALL_URL, startmission, headers)
#     print(res.text)


def writeToFile(data, name):
    file = name + '.json'
    with open(file, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


if __name__ == '__main__':

    parser = ArgumentParser(description="Select options.")
    parser.add_argument("--type", 
                        nargs="*",
                        type=str,
                        default=['s'],  
                        choices=['s', 'g'],
                        help="Chest type")
    parser.add_argument('-c', type = str,
                        help = 'Code redeem')
    parser.add_argument('-bs', type = str,
                        help = 'Buy silver chests')
    parser.add_argument('-bg', type = str,
                        help = 'Buy gold chests')
    # parser.add_argument('-o', type = str,
    #                     help = 'Open chests')
    parser.add_argument('-list', action="store_true",
                        help = 'List chests')      
    parser.add_argument('-o2', action="store_true",
                        help = 'Open chests')      
    parser.add_argument("-end", action="store_true",
                        help="End Game")  
    parser.add_argument("-g", action="store_true",
                        help="Get Formations")
    parser.add_argument("-wf", action="store_true",
                        help="Write JSON files")                             
    # parser.add_argument("-v", action="store_true",
    #                     help="verbose")                        
    parser.add_argument("-d", action="store_true",
                        help="debug")

    args = parser.parse_args()

    start_time = datetime.now()

    if args.d:
        logging.basicConfig(level=logging.DEBUG,
                            format="%(asctime)s - %(levelname)s - %(message)s")

    URL = getServer()
    CALL_URL = URL + URI

    userdetails = getUserDetails()

    if args.wf:
        writeToFile(userdetails, 'userdetails')

    if userdetails['success'] == True:
        instance_id = userdetails['details']['instance_id']

        gamedetails = getUserGameInstance()
        if args.wf:
            writeToFile(gamedetails, 'gamedetails')

        if gamedetails['success'] == True:
            game_instance_id = gamedetails['details']['game_instance_id']
            adventure_id = gamedetails['details']['current_adventure_id']

        if args.c:
            with open (cachepath + cachefile) as cfile:
                cdata = json.load(cfile)

            result = redeemCode(args.c)

            if result['success'] == True:
                if 'loot_details' in result.keys():
                    for res in result['loot_details']:
                        print(res)
                elif 'failure_reason' in result.keys():
                    print(f"Failed: {result['failure_reason']}")
            else:
                print('success false')

        if args.list:
            with open (cachepath + cachefile) as cfile:
                cdata = json.load(cfile)
            opengenericchest['instance_id'] = instance_id
            for k,v in userdetails['details']['chests'].items():
                if v != 0:
                    for c in cdata['chest_type_defines']:
                        if c['id'] == int(k):
                            if v > 1:
                                print(f"{k} - {v} {c['name_plural']}")
                            else:
                                print(f"{k} - {v} {c['name']}")

        if args.o2:
            with open (cachepath + cachefile) as cfile:
                cdata = json.load(cfile)
            opengenericchest['instance_id'] = instance_id
            for k,v in userdetails['details']['chests'].items():
                if v != 0:
                    # do not open non-electrum, 282 is electrum
                    if k in ['1', '2']:
                    # if k != '282':
                        for c in cdata['chest_type_defines']:
                            if c['id'] == int(k):
                                if v > 1:
                                    print(f"Opening {v} {c['name_plural']}")
                                else:
                                    print(f"Opening {v} {c['name']}")
                                loot = openChests2(k, CALL_URL, count=v)
                        print(f"{GREEN}{loot}{ENDC}")
                        parseChests2(loot)

        if args.bs:
            type = 1
            buyChests(type, count=int(args.bs))

        if args.bg:
            type = 2
            buyChests(type, count=int(args.bg))

        if args.g:
            getallformationsaves['instance_id'] = instance_id
            res = serverRequest(CALL_URL, getallformationsaves, headers)
            if args.wf:
                writeToFile(res.text, 'getallformationsaves')

        # softreset code 
        if args.end:
            softreset['instance_id'] = instance_id
            print(f'instance_id: {instance_id}')
            softreset['game_instance_id'] = game_instance_id
            res = serverRequest(CALL_URL, softreset, headers)
            softreset = json.loads(res.text)
            if softreset['success'] == True:
                print(f"success: {softreset['reset_details']['new_resets_number']}")   

    else:
        print("failure")
        print(userdetails.text)

    end_time = datetime.now()
    print(f'\nruntime: {end_time - start_time}')
