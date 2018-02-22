import colorsys
import json
import logging

from botocore.vendored import requests
import random

# Setup logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

API_URL = 'http://71.60.35.26:5000/api/v2'

endpoints = []
state = {}


class Endpoint(object):
    def __init__(self, name: str):
        self.endpointId = name
        self.manufacturerName = "Barry McAndrews"
        self.friendlyName = name
        self.description = "RGB LED Strip"
        self.displayCategories = ["LIGHT"]
        self.cookie = {}

        with open("capabilities.json") as json_file:
            self.capabilities = json.load(json_file)


def get_endpoints():
    global endpoints
    if len(endpoints) == 0:
        resp = requests.get(API_URL + '/channels')
        for channel in resp.json():
            found = False
            for endpoint in endpoints:
                found |= (channel['device'] == endpoint['friendlyName'])
            if not found:
                endpoints.append(Endpoint(channel['device']).__dict__)
    return endpoints


def set_power_state(endpoint_id: str, value: str):
    if value.lower() == 'on':
        with open('color-presets.json') as json_file:
            options = json.load(json_file)
            choice = options[random.randint(0, len(options))]
            choice['devices'] = [endpoint_id]
            requests.post(API_URL + '/presets', json=choice)
    else:
        update_state()
        if endpoint_id in state:
            logger.error(state[endpoint_id])
            requests.delete(API_URL + '/presets/' + str(state[endpoint_id]['id']))


def get_power_state(endpoint_id):
    return "ON" if endpoint_id in state else "OFF"


def set_color(endpoint_id, value):
    b, g, r = colorsys.hsv_to_rgb(value['hue'], value['saturation'], value['brightness'])
    r = int(r * 100)
    g = int(g * 100)
    b = int(b * 100)
    color = {
        "name": "Alexa-" + str(r) + str(g) + str(b),
        "devices": [endpoint_id],
        "payload": {
            "type": "levels",
            "red": r,
            "green": g,
            "blue": b
        }
    }
    logger.error(color)
    requests.post(API_URL + '/presets', json=color)


def get_color(endpoint_id):
    if endpoint_id in state:
        if state[endpoint_id]['payload']['type'] == 'levels':
            h, s, b = colorsys.rgb_to_hsv(state[endpoint_id]['payload']['red'],
                                          state[endpoint_id]['payload']['green'],
                                          state[endpoint_id]['payload']['blue'])
            return {"hue": h * 360.0, "saturation": s, "brightness":  b / 100.0}
        else:
            return {"hue": 0.0, "saturation": 0.0, "brightness": 1.0}
    else:
        return {"hue": 0.0, "saturation": 0.0, "brightness": 0.0}


def get_connectivity(endpoint_id):
    try:
        for ep in get_endpoints():
            if ep['endpointId'] == endpoint_id:
                return "OK"
        return "UNREACHABLE"
    except requests.ConnectionError:
        return "UNREACHABLE"


def update_state():
    # state type: Dict[device -> Payload]
    global state

    state = {}
    resp = requests.get(API_URL + '/presets')
    for preset in resp.json():
        for device in preset['devices']:
            if device not in state:
                state[device] = preset
