import uuid
import time
from enum import Enum


class ResponseName(Enum):
    DISCOVER = "Discover.Response"
    RESPONSE = "Response"
    STATE_REPORT = "StateReport"
    ACCEPT_GRANT = "AcceptGrant.Response"


RESPONSE_NAMESPACES = {
    ResponseName.DISCOVER: "Alexa.Discovery",
    ResponseName.RESPONSE: "Alexa",
    ResponseName.STATE_REPORT: "Alexa",
    ResponseName.ACCEPT_GRANT: "Alexa.Authorization"
}


class ContextName(Enum):
    POWER_STATE = "powerState"
    COLOR = "color"
    CONNECTIVITY = "connectivity"


CONTEXT_NAMESPACES = {
    ContextName.POWER_STATE: "Alexa.PowerController",
    ContextName.COLOR: "Alexa.ColorController",
    ContextName.CONNECTIVITY: "Alexa.EndpointHealth"
}


def get_utc_timestamp(seconds=None):
    return time.strftime("%Y-%m-%dT%H:%M:%S.00Z", time.gmtime(seconds))


def get_uuid():
    return str(uuid.uuid4())


class Response(object):
    def __init__(self, response_name: ResponseName):
        self.context = None
        self.event = {
            "header": {
                "namespace": RESPONSE_NAMESPACES[response_name],
                "name": response_name.value,
                "payloadVersion": "3",
                "messageId": get_uuid()
            },
            "payload": {}
        }

    def add_context(self, context_name: ContextName, value):
        if self.context is None:
            self.context = {"properties": []}
        self.context["properties"].append({
            "namespace": CONTEXT_NAMESPACES[context_name],
            "name": context_name.value,
            "value": value,
            "timeOfSample": get_utc_timestamp(),
            "uncertaintyInMilliseconds": 500
        })

    def add_correlation_token(self, correlation_token):
        self.event["header"]["correlationToken"] = correlation_token

    def add_endpoint(self, endpoint_id):
        self.event["endpoint"] = {
            "scope": {
                "type": "BearerToken",
                "token": "access-token-from-Amazon"
            },
            "endpointId": endpoint_id
        }

    def add_payload(self, payload):
        self.event["payload"] = payload

    def as_dict(self):
        d = self.__dict__
        if self.context is None:
            del d['context']
        return d


