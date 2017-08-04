from enum import Enum
import uuid
import logging

from pydispatch import dispatcher

from navi.core import (Navi, get_handler_for, get_intent_and_fill_slots)
from navi import context as ctx
from navi.intents import Intent
from navi import responses


logger = logging.getLogger(__name__)


class ConversationalResponse(object):

    def __init__(self,
                 intent=None,
                 entities={},
                 ready=False,
                 confidence=0,
                 original_res={}):
        self.intent = intent
        self.entities = entities
        self.ready = ready
        self.confidence = confidence
        self.original_res = original_res

    def __str__(self):
        return ("ConversationalResponse: "
                "\n\tintent: \t{}\n\tentities: \t{}"
                "\n\tconfidence: \t{}\n\tready to send: \t{}"
                ).format(self.intent,
                         self.entities,
                         self.confidence,
                         self.ready)


class ConversationalPlatform(Enum):
    wit_ai = 0


def parse_message(message,
                  context,
                  platform=ConversationalPlatform.wit_ai,
                  confidence_threshold=0.1):

    if not message:
        return _parsing_error(message, context)

    # check if there is an open session and start one if not
    if not context.setdefault("session_started", False):
        session = str(uuid.uuid1())
        context["session_number"] = session
        context["session_started"] = True
    session = context["session_number"]  # get current open session

    # reference to conversational platform of choice
    chosen_platform = None
    if platform == ConversationalPlatform.wit_ai:
        chosen_platform = ctx.general()['wit_ai']

    # every platform parser is a python generator
    response = chosen_platform.parser(session, message, context)

    logger.info("Parser response: %s", response)

    if response.confidence < confidence_threshold:
        return _parsing_error(message, context)

    if response.ready:
        ctx.clean_user_error_context(context)
        if ctx.should_close_session(context):
            ctx.clean_user_context(context)
            ctx.set_session_was_closed(context)
        return response.messages

    intent_name = None
    if response.intent is None:
        if 'intent' in context:
            intent_name = context['intent']
        else:
            return _parsing_error(message, context)
    else:
        intent_name = response.intent
        context['intent'] = intent_name

    intent = get_intent_and_fill_slots(intent_name,
                                       response.entities,
                                       context)

    handler = get_handler_for(intent)
    handler.context = context

    if handler is None:
        logger.warning("No handler for intent %s",
                       type(intent).__name__)
        return _parsing_error(message, context)

    # 1. Resolve
    resolve_responses = handler.resolve(intent, context)
    (must_ask, messages) = _parse_resolve_result(resolve_responses,
                                                 intent, context)

    # keep getting responses until we can handle the intent
    if must_ask:
        if len(messages) > 0:
            return messages[0]
        else:
            return ""

    # 2. Confirm
    confirm_response = handler.confirm(intent, context)
    (is_ready, message) = _parse_confirm_result(confirm_response, intent,
                                                context)

    if not is_ready:
        if message:
            return message
        else:
            return ""

    # 3. Handle
    handle_response = handler.handle(intent, context)
    message = _parse_handle_result(handle_response, intent,
                                   context)

    ctx.clean_user_error_context(context)
    ctx.clean_user_context(context)
    ctx.set_session_was_closed(context)

    if message:
        return message
    else:
        return ""


def _parsing_error(message, context):

    ctx.clean_user_error_context(context)
    ctx.clean_user_context(context)
    ctx.set_session_was_closed(context)

    message = responses.get(for_key="parsing_error")
    if message is None:
        return "parsing_error"

    return message


def _get_resolve_result_into_context(resolve_responses, intent, context):

    must_ask_user_for_more_info = False

    # iterate over resolve responses and include data on context
    for entity_name, resolve_response in resolve_responses.iteritems():
        if resolve_response == Intent.ResolveResponse.missing:
            context_key = "{}_missing".format(entity_name)
            context[context_key] = True
            must_ask_user_for_more_info = True
        elif resolve_response == Intent.ResolveResponse.unsupported:
            context_key = "{}_unsupported".format(entity_name)
            context[context_key] = True
            must_ask_user_for_more_info = True
        elif resolve_response == Intent.ResolveResponse.ambiguous:
            context_key = "{}_ambiguous".format(entity_name)
            context[context_key] = True
            must_ask_user_for_more_info = True
        elif resolve_response == Intent.ResolveResponse.not_required:
            context_key = "{}".format(entity_name)
            context[context_key] = None
        elif resolve_response == Intent.ResolveResponse.ready:
            context_key = "{}".format(entity_name)
            context[context_key] = (
                getattr(intent, entity_name))

    return (context, must_ask_user_for_more_info)


def _get_confirm_result_into_context(confirm_response, context):

    is_ready = False

    if confirm_response == Intent.ConfirmResponse.ready:
        context["ready"] = True
        is_ready = True
    elif confirm_response == Intent.ConfirmResponse.failure:
        context["failure"] = True
    elif confirm_response == Intent.ConfirmResponse.unsupported:
        context["unsupported"] = True

    return (context, is_ready)


def _get_handle_result_into_context(handle_response, context):

    if handle_response.status == Intent.HandleResponse.Status.success:
        context["handled"] = True
    elif handle_response.status == Intent.HandleResponse.Status.failure:
        context["failure"] = True
    elif handle_response.status == Intent.HandleResponse.Status.in_progress:
        context["in_progress"] = True
    context.update(handle_response.response_dict)

    return context


def _parse_resolve_result(resolve_responses, intent, context):

    must_ask_user_for_more_info = False
    messages = []

    # iterate over resolve responses and include data on context
    for entity_name, resolve_response in resolve_responses.iteritems():
        entity = getattr(intent.__class__, entity_name)
        message = responses.get(for_intent_entity=entity,
                                for_status=resolve_response)

        if (resolve_response == Intent.ResolveResponse.missing or
                resolve_response == Intent.ResolveResponse.unsupported or
                resolve_response == Intent.ResolveResponse.ambiguous):
            messages.append(message)
            must_ask_user_for_more_info = True
        elif (resolve_response == Intent.ResolveResponse.not_required or
              resolve_response == Intent.ResolveResponse.ready):
            context_key = "{}".format(entity_name)
            context[context_key] = (
                getattr(intent, entity_name))

    return (must_ask_user_for_more_info, messages)


def _parse_confirm_result(confirm_response, intent, context):

    is_ready = False
    message = responses.get(for_intent=intent.__class__,
                            for_status=confirm_response)

    if confirm_response == Intent.ConfirmResponse.ready:
        context["ready"] = True
        is_ready = True
    elif confirm_response == Intent.ConfirmResponse.failure:
        context["failure"] = True
    elif confirm_response == Intent.ConfirmResponse.unsupported:
        context["unsupported"] = True

    try:
        message = message.format(**context)
    except (Exception):
        pass

    return (is_ready, message)


def _parse_handle_result(handle_response, intent, context):

    message = responses.get(for_intent=intent.__class__,
                            for_status=handle_response.status)

    if handle_response.status == Intent.HandleResponse.Status.success:
        context["handled"] = True
    elif handle_response.status == Intent.HandleResponse.Status.failure:
        context["failure"] = True
    elif handle_response.status == Intent.HandleResponse.Status.in_progress:
        context["in_progress"] = True
    context.update(handle_response.response_dict)

    try:
        message = message.format(**handle_response.response_dict)
    except (KeyError):
        try:
            message = message.format(**context)
        except (KeyError):
            pass

    return message


def action(action):
    """Link a method with an action

    usage: 
    ```
        >>> from navi.conversational import action
        >>> @action('find_music')
        >>> def find_music(message, entities, context):
        >>>     ...
    ```

    """

    def decorator(func):
        signal = "action_{}".format(action)
        dispatcher.connect(func, signal=signal,
                           sender=dispatcher.Any)
        logger.info("registering {} for action '{}'".format(
            func.__name__, action))
        return func

    return decorator


def parsing_error(func):

    def decorator(func):
        signal = "parsing_error"
        dispatcher.connect(func, signal=signal,
                           sender=dispatcher.Any)
        logger.info("registering {} for parsing error".format(
            func.__name__))
        return func

    return decorator(func)
