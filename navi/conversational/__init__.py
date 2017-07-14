from enum import Enum
import uuid
import logging

from pydispatch import dispatcher

from navi.core import (Navi, get_handler_for)
from navi import context as ctx
from navi.intents import Intent


logger = logging.getLogger(__name__)


class ConversationalResponse(object):

    def __init__(self,
                 action=None,
                 entities={},
                 messages=[],
                 ready=False,
                 confidence=0,
                 original_res={}):
        self.action = action
        self.entities = entities
        self.messages = messages
        self.ready = ready
        self.confidence = confidence
        self.original_res = original_res

    def __str__(self):
        return ("ConversationalResponse: "
                "\n\taction: \t{}\n\tentities: \t{}"
                "\n\tmessages: \t{}\n\tready to send: \t{}"
                ).format(self.action,
                         self.entities,
                         self.messages,
                         self.ready)


class ConversationalPlatform(Enum):
    wit_ai = 0


def parse_message(message,
                  context,
                  platform=ConversationalPlatform.wit_ai,
                  confidence_threshold=0.1):

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
    parser = chosen_platform.parser(session, message, context)

    for response in parser:

        logger.info("Parser response: %s", response)

        if response.confidence < confidence_threshold:
            return _parsing_error(message, context)

        if response.ready:
            ctx.clean_user_error_context(context)
            if ctx.should_close_session(context):
                ctx.clean_user_context(context)
                ctx.set_session_was_closed(context)
            return response.messages

        if response.action is None:
            return response.messages

        signal = "action_{}".format(response.action)
        logger.info("Sent {} signal".format(signal))
        disp_responses = dispatcher.send(signal=signal,
                                         sender=dispatcher.Any,
                                         message=message,
                                         entities=response.entities,
                                         context=context)

        if not disp_responses:
            logger.warning("No callback for action %s",
                           response.action)
            return _parsing_error(message, context)

        (_, intent) = disp_responses[0]

        handler = get_handler_for(intent)
        if handler is None:
            logger.warning("No handler for intent %s",
                           type(intent).__name__)
            return _parsing_error(message, context)

        # 1. Resolve
        resolve_responses = handler.resolve(intent)
        (context, must_ask) = _get_resolve_result_into_context(
            resolve_responses,
            intent, context)

        # keep getting responses until we can handle the intent
        if must_ask:
            continue

        # 2. Confirm
        confirm_response = handler.confirm(intent)
        (context, is_ready) = _get_confirm_result_into_context(
            confirm_response, context)

        if not is_ready:
            continue

        # 3. Handle
        handle_response = handler.handle(intent)
        context = _get_handle_result_into_context(handle_response,
                                                  context)

        continue


def _parsing_error(message, context):

    ctx.clean_user_error_context(context)
    ctx.clean_user_context(context)
    ctx.set_session_was_closed()

    signal = "parsing_error"
    disp_responses = dispatcher.send(signal=signal,
                                     sender=dispatcher.Any,
                                     message=message,
                                     context=context)

    if not disp_responses:
        logger.info("No parsing error treatment found")
        return ""
    else:
        (_, message) = disp_responses[0]
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
