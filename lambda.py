import logging
import json

import api
from response import Response, ResponseName, ContextName
from validation import validate_message

# Setup logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)


# ------------------------------------------------ #
# Handlers                                         #
# ------------------------------------------------ #

def handle_power_controller(request):
    request_name = request["directive"]["header"]["name"]
    endpoint_id = request["directive"]["endpoint"]["endpointId"]

    value = "ON" if request_name == "TurnOn" else "OFF"
    api.set_power_state(endpoint_id, value)

    response = Response(ResponseName.RESPONSE)
    response.add_context(ContextName.POWER_STATE, value)
    response.add_correlation_token(request["directive"]["header"]["correlationToken"])
    response.add_endpoint(endpoint_id)
    return response


def handle_color_controller(request):
    endpoint_id = request["directive"]["endpoint"]["endpointId"]
    value = request["directive"]["payload"]["color"]

    api.set_color(endpoint_id, value)

    response = Response(ResponseName.RESPONSE)
    response.add_context(ContextName.COLOR, value)
    response.add_correlation_token(request["directive"]["header"]["correlationToken"])
    response.add_endpoint(endpoint_id)
    return response


def handle_state_request(request):
    endpoint_id = request["directive"]["endpoint"]["endpointId"]
    value = api.get_connectivity(endpoint_id)

    api.update_state()

    response = Response(ResponseName.STATE_REPORT)
    response.add_endpoint(endpoint_id)
    response.add_context(ContextName.CONNECTIVITY, {
        "value": value
    })
    if value == "OK":
        response.add_context(ContextName.POWER_STATE, api.get_power_state(endpoint_id))
        response.add_context(ContextName.COLOR, api.get_color(endpoint_id))
    return response


def handle_authentication(request):
    return Response(ResponseName.ACCEPT_GRANT)


def handle_discovery(request):
    response = Response(ResponseName.DISCOVER)
    response.add_payload({
        "endpoints": api.get_endpoints()
    })
    return response


DIRECTIVE_HANDLERS = {
    "TurnOn": handle_power_controller,
    "TurnOff": handle_power_controller,
    "SetColor": handle_color_controller,
    "ReportState": handle_state_request,
    "AcceptGrant": handle_authentication,
    "Discover": handle_discovery,
}


# ------------------------------------------------ #
# Main Lambda Handler                              #
# ------------------------------------------------ #

def lambda_handler(request, context):
    try:
        logger.info("Directive:")
        logger.info(json.dumps(request, indent=4, sort_keys=True))
        directive_name = request["directive"]["header"]["name"]

        if get_directive_version(request) != "3":
            raise ValueError("API must be version 3")

        logger.info("Received v3 directive!")
        response = DIRECTIVE_HANDLERS[directive_name](request).as_dict()

        logger.info("Response:")
        logger.info(json.dumps(response, indent=4, sort_keys=True))

        logger.info("Validate v3 response")
        validate_message(request, response)
        return response

    except KeyError as error:
        logger.info("Directive: " + str(directive_name) + " not supported.")
        logger.error(error)

    except ValueError as error:
        logger.error(error)
        raise


def get_directive_version(request):
    try:
        return request["directive"]["header"]["payloadVersion"]
    except KeyError:
        try:
            return request["header"]["payloadVersion"]
        except KeyError:
            return "-1"


def handle_non_discovery(request):
    request_namespace = request["directive"]["header"]["namespace"]
    request_name = request["directive"]["header"]["name"]
    endpoint_id = request["directive"]["endpoint"]["endpointId"]

    if request_namespace == "Alexa.PowerController":
        if request_name == "TurnOn":
            value = "ON"
        else:
            value = "OFF"

        api.set_power_state(endpoint_id, value)

        response = {
            "context": {
                "properties": [
                    {
                        "namespace": "Alexa.PowerController",
                        "name": "powerState",
                        "value": value,
                        # "timeOfSample": get_utc_timestamp(),
                        "uncertaintyInMilliseconds": 500
                    }
                ]
            },
            "event": {
                "header": {
                    "namespace": "Alexa",
                    "name": "Response",
                    "payloadVersion": "3",
                    # "messageId": get_uuid(),
                    "correlationToken": request["directive"]["header"]["correlationToken"]
                },
                "endpoint": {
                    "scope": {
                        "type": "BearerToken",
                        "token": "access-token-from-Amazon"
                    },
                    "endpointId": endpoint_id
                },
                "payload": {}
            }
        }
        return response

    elif request_namespace == "Alexa":
        if request_name == "ReportState":
            response = {
                "context": {
                    "properties": [
                        {
                            "namespace": "Alexa.EndpointHealth",
                            "name": "connectivity",
                            "value": {
                                "value": api.get_connectivity(endpoint_id)
                            },
                            # "timeOfSample": get_utc_timestamp(),
                            "uncertaintyInMilliseconds": 500
                        }
                    ]
                },
                "event": {
                    "header": {
                        "namespace": "Alexa",
                        "name": "StateReport",
                        "payloadVersion": "3",
                        # "messageId": get_uuid(),
                        "correlationToken": request["directive"]["header"]["correlationToken"]
                    },
                    "endpoint": {
                        "scope": {
                            "type": "BearerToken",
                            "token": "access-token-from-Amazon"
                        },
                        "endpointId": endpoint_id
                    },
                    "payload": {}
                }
            }
            return response

