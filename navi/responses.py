import random

from pydispatch import dispatcher

from .core import Navi


def _build_key(for_intent=None,
               for_intent_entity=None,
               for_status=None,
               for_key=None):

    if not for_key and not for_intent and not for_intent_entity:
        raise ValueError("You cannot add a response without specifying "
                         "a key, intent or intent entity")

    if for_key:
        return "response_{}".format(for_key)

    if for_intent_entity:
        if not for_status:
            raise ValueError("You cannot add a response to an entity without "
                             "specifying a status")
        return "response_intent_{}_entity_{}_status_{}".format(
            for_intent_entity.defined_intent_name,
            for_intent_entity.defined_name,
            for_status.value)

    if for_intent:
        if not for_status:
            raise ValueError("You cannot add a response to an intent without "
                             "specifying a status")
        return "response_intent_{}_status_{}".format(for_intent.__name__,
                                                     for_status.value)


def add(responses,
        for_intent=None,
        for_intent_entity=None,
        for_status=None,
        for_key=None):

    res = Navi._responses
    key = _build_key(for_intent=for_intent,
                     for_intent_entity=for_intent_entity,
                     for_status=for_status,
                     for_key=for_key)

    if key not in res:
        res[key] = []

    if not isinstance(responses, list):
        responses = [responses]

    res[key].extend(responses)


def get(for_intent=None,
        for_intent_entity=None,
        for_status=None,
        for_key=None):

    res = Navi._responses
    key = _build_key(for_intent=for_intent,
                     for_intent_entity=for_intent_entity,
                     for_status=for_status,
                     for_key=for_key)

    if key not in res:
        return None

    responses = res[key]

    return random.choice(responses).decode('utf-8')
