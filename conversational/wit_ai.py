import uuid
from importlib import import_module
import logging

from pydispatch import dispatcher
from wit import Wit

from navi.core import (Navi, get_handler_for,
                       set_can_close_session, should_close_session,
                       set_session_was_closed)
from navi.intents import Intent


logger = logging.getLogger(__name__)


class WitConversationalPlatform(object):

    def __init__(self, key):
        self.key = key

    def start(self):

        self.client = Wit(access_token=self.key)
        Navi.context['wit_client'] = self.client
        Navi.context["wit_context"] = {}
        Navi.context["wit_context"]["session_started"] = False
        Navi.context["wit_messages"] = {}

        # register hooks for messaging shortcomings
        dispatcher.connect(self._set_did_not_understand,
                           signal="did_not_understand")
        dispatcher.connect(self._set_failed_request,
                           signal="did_fail")
        dispatcher.connect(self._invalidate_context,
                           signal="did_timeout")

    def _set_did_not_understand(self):
        Navi.context["wit_context"]["unknown"] = True
        Navi.context["wit_context"]["has_used_error_state"] = False

    def _set_failed_request(self):
        Navi.context["wit_context"]["failed_request"] = True
        Navi.context["wit_context"]["has_used_error_state"] = False

    def _invalidate_context(self):
        close_session(Navi.context)


def close_session(context):
    context["wit_context"] = {}
    context["wit_context"]["session_started"] = False
    set_session_was_closed()


def close_session_when_done():
    set_can_close_session()


def _remove_error_state():
    Navi.context["wit_context"].pop("unknown", None)
    Navi.context["wit_context"].pop("failed_request", None)
    Navi.context["wit_context"].pop("has_used_error_state", None)


def wit_action(action):
    """Link a method with a wit action (as defined using the 'stories' feature)

    usage: 
    ```
        >>> from navi.conversational.wit_ai import wit_action
        >>> @wit_action('find_music')
        >>> def find_music(message, entities, context):
        >>>     ...
    ```

    """

    def decorator(func):
        signal = "wit_action_{}".format(action)
        dispatcher.connect(func, signal=signal,
                           sender=dispatcher.Any)
        logger.info("registering {} for action '{}'".format(
            func.__name__, action))
        return func

    return decorator


def parse_message(message, context):
    if not context.setdefault("wit_context", {}).setdefault("session_started",
                                                            False):
        session = str(uuid.uuid1())
        context["wit_context"]["session"] = session
        context["wit_context"]["session_started"] = True
        context["wit_messages"][session] = []
    if context["wit_context"].get("has_used_error_state", None) == False:
        context["wit_context"]["has_used_error_state"] = True
    elif context["wit_context"].get("has_used_error_state", None) == True:
        _remove_error_state()

    logger.info("Context Before Converse: %s", context)
    client = context['wit_client']
    session = context["wit_context"]["session"]
    converse_result = client.converse(session,
                                      message,
                                      context["wit_context"])
    logger.info("Converse Result: %s", converse_result)
    if converse_result['type'] == 'action':

        entities = _simplify_entities_dict(converse_result['entities'])
        action_name = converse_result['action']

        signal = "wit_action_{}".format(action_name)
        logger.info("Sent {} signal".format(signal))
        disp_responses = dispatcher.send(signal=signal, sender=dispatcher.Any,
                                         message=message,
                                         entities=entities,
                                         context=context["wit_context"])
        (_, intent) = disp_responses[0]

        handler = get_handler_for(intent)
        if handler is None:
            logger.warning("No handler for intent %s", type(intent).__name__)
            return parse_message("", context["wit_context"])

        # 1. Resolve
        resolve_responses = handler.resolve(intent)
        (context, must_ask) = _get_resolve_result_into_context(
            resolve_responses,
            intent, context)

        if must_ask:  # recusivelly call parse until a message is returned
            return parse_message("", context)

        # 2. Confirm
        confirm_response = handler.confirm(intent)
        (context, is_ready) = _get_confirm_result_into_context(
            confirm_response, context)

        if not is_ready:
            return parse_message("", context)

        # 3. Handle
        handle_response = handler.handle(intent)
        context = _get_handle_result_into_context(handle_response, context)

        return parse_message("", context)

    if converse_result['type'] == 'msg':
        if ((context["wit_messages"][session][-1]
             if len(context["wit_messages"][session]) != 0
             else None) == converse_result['msg']):
            # if message is repeated, wit is on a loop
            messages = context["wit_messages"][session]
            context["wit_messages"][session] = []
            return messages

        context["wit_messages"][session].append(converse_result['msg'])
        return parse_message("", context)

    if converse_result['type'] == 'stop':
        try:
            if should_close_session():
                close_session(context)
            messages = context["wit_messages"][session]
            context["wit_messages"][session] = []
            return messages
        except Exception as e:
            logger.exception(e)


def _simplify_entities_dict(entities_dict):
    entities = {
        key: value[0]['value'] for (key, value) in entities_dict.iteritems()
    }
    return entities


def _get_resolve_result_into_context(resolve_responses, intent, context):

    must_ask_user_for_more_info = False

    # iterate over resolve responses and include data on context
    for entity_name, resolve_response in resolve_responses.iteritems():
        if resolve_response == Intent.ResolveResponse.missing:
            context_key = "{}_missing".format(entity_name)
            context["wit_context"][context_key] = True
            must_ask_user_for_more_info = True
        elif resolve_response == Intent.ResolveResponse.unsupported:
            context_key = "{}_unsupported".format(entity_name)
            context["wit_context"][context_key] = True
            must_ask_user_for_more_info = True
        elif resolve_response == Intent.ResolveResponse.ambiguous:
            context_key = "{}_ambiguous".format(entity_name)
            context["wit_context"][context_key] = True
            must_ask_user_for_more_info = True
        elif resolve_response == Intent.ResolveResponse.not_required:
            context_key = "{}".format(entity_name)
            context["wit_context"][context_key] = None
        elif resolve_response == Intent.ResolveResponse.ready:
            context_key = "{}".format(entity_name)
            context["wit_context"][context_key] = (
                getattr(intent, entity_name))

    return (context, must_ask_user_for_more_info)


def _get_confirm_result_into_context(confirm_response, context):

    is_ready = False

    if confirm_response == Intent.ConfirmResponse.ready:
        context["wit_context"]["ready"] = True
        is_ready = True
    elif confirm_response == Intent.ConfirmResponse.failure:
        context["wit_context"]["failure"] = True
    elif confirm_response == Intent.ConfirmResponse.unsupported:
        context["wit_context"]["unsupported"] = True

    return (context, is_ready)


def _get_handle_result_into_context(handle_response, context):

    if handle_response.status == Intent.HandleResponse.Status.success:
        context["wit_context"]["handled"] = True
    elif handle_response.status == Intent.HandleResponse.Status.failure:
        context["wit_context"]["failure"] = True
    elif handle_response.status == Intent.HandleResponse.Status.in_progress:
        context["wit_context"]["in_progress"] = True
    context["wit_context"].update(handle_response.response_dict)

    return context
