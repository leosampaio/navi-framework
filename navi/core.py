from importlib import import_module
import abc
import os
import logging
import threading
import signal
import sys
import inspect

from pydispatch import dispatcher

from .notebook import Notebook

logger = logging.getLogger('navi')


class Navi(object):
    """The navi object is used to initialize your bot, wire up all your
    modules together with navi's modules
    """

    context = {}
    _responses = {}

    def __init__(self, bot_module,
                 intent_modules=None,
                 handler_modules=None,
                 interface_modules=None,
                 response_modules=None,
                 debug=False):
        """Initialize Navi instance with your bot modules

        :param bot_module: required. specifies your bot's main module

        :param intent_modules: if provided, these modules are used instead 
        of the default module `intents`

        :param handler_modules: if provided, these modules are used instead 
        of the default module `handlers`

        :param interface_modules: if provided, these modules are used instead 
        of the default module `interfaces`
        """

        if debug:
            logger.propagate = False
            logger.setLevel(logging.DEBUG)
            formatter = logging.Formatter(
                '%(asctime)s %(name)s \n%(levelname)-10s  %(message)s')
            ch = logging.StreamHandler()
            ch.setLevel(logging.DEBUG)
            ch.setFormatter(formatter)
            logger.addHandler(ch)

        self.bot_module = bot_module
        self.bot_path = os.path.dirname(inspect.getfile(bot_module))
        Notebook._set_db(os.path.join(self.bot_path, 'notebook.db'))

        Navi.context["should_close_session"] = False
        Navi.context["users"] = {}
        Navi.context["users_metadata"] = {}

        if intent_modules == None:
            import_module('.intents', bot_module.__name__)
        else:
            for module in intent_modules:
                try:
                    import module
                except ImportError:
                    raise ImportError(
                        "Can't import intent module {}".format(module))

        if handler_modules == None:
            import_module('.handlers', bot_module.__name__)
        else:
            for module in handler_modules:
                try:
                    import module
                except ImportError:
                    raise ImportError(
                        "Can't import handler module {}".format(module))

        if interface_modules == None:
            import_module('.interfaces', bot_module.__name__)
        else:
            for module in interface_modules:
                try:
                    import module
                except ImportError:
                    raise ImportError(
                        "Can't import interface module {}".format(module))

        if response_modules == None:
            import_module('.responses', bot_module.__name__)
        else:
            for module in response_modules:
                try:
                    import module
                except ImportError:
                    raise ImportError(
                        "Can't import conversational module {}".format(module))

        dispatcher.connect(self._new_user_context_created,
                           signal="did_create_new_user_context")

    def start(self, messaging_platforms=[], conversational_platforms=[],
              speech_platforms=[]):
        """Start bot in development mode, if available for chosen messaging
        platform.
        """

        self.threads = []

        for platform in conversational_platforms:
            t = threading.Thread(target=platform.start)
            t.daemon = True
            self.threads.append(t)
            t.start()

        for platform in messaging_platforms:
            t = threading.Thread(target=platform.start)
            t.daemon = True
            self.threads.append(t)
            t.start()

        for platform in speech_platforms:
            t = threading.Thread(target=platform.start)
            t.daemon = True
            self.threads.append(t)
            t.start()

        self.idle()

    def idle(self):
        def signal_handler(signal, frame):
            logger.info("Exiting...")
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        while True:
            signal.pause()

    def _new_user_context_created(self, context):
        context["session_started"] = False
        context["should_close_session"] = False


def get_handler_for(intent):
    signal = "handler_for_{}".format(type(intent).__name__)
    logger.info("Sent {} signal".format(signal))
    responses = dispatcher.send(signal=signal, sender=dispatcher.Any,
                                intent=intent)
    if len(responses) > 0:
        (_, handler) = responses[0]
        return handler
    else:
        return None

def get_intent_and_fill_slots(name, entities, context):
    signal = "intent_class_{}".format(name)
    logger.info("Sent {} signal".format(signal))
    responses = dispatcher.send(signal=signal, sender=dispatcher.Any)

    if len(responses) > 0:
        (_, IntentClass) = responses[0]
        combined_dictionary = dict(entities, **context)
        return IntentClass(**combined_dictionary)
    else:
        return None


def entity_from_entities_or_context(entity_name, entities, context):
    a = [entities.get(entity_name, None), context.get(entity_name, None)]
    return next((item for item in a if item is not None), None)


def find_in_either(entity_name, entities, context):
    a = [entities.get(entity_name, None), context.get(entity_name, None)]
    return next((item for item in a if item is not None), None)


def _set_can_close_session():
    Navi.context["should_close_session"] = True


def _should_close_session():
    return Navi.context["should_close_session"]


def _set_session_was_closed():
    Navi.context["is_session_open"] = False
    Navi.context["should_close_session"] = False


def _open_session():
    Navi.context["is_session_open"] = True


def _is_session_open():
    return Navi.context["is_session_open"]


class NaviEntryPoint(object):

    __metaclass__ = abc.ABCMeta

    def __init__(self, name):
        self.name = name
        logger.info("registering entry point '{}'".format(name))
        signal = "entry_point_named_{}".format(name)
        dispatcher.connect(self._get_self_reference, signal=signal,
                           sender=dispatcher.Any)

    def _get_self_reference(self):
        return self

    @abc.abstractmethod
    def build_request(self, *kvars, **kwargs):
        pass

    @abc.abstractmethod
    def build_response(self, *kvars, **kwargs):
        pass

    @abc.abstractmethod
    def start(self):
        pass


class NaviRequest(object):

    __metaclass__ = abc.ABCMeta

    def __init__(self, message, user_id):
        self.message = message
        self.user_id = user_id


class NaviResponse(object):

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def reply(self, message):
        pass


def entry_point(entry_point_name):

    def decorator(func):
        def wrap_and_call(*kvars, **kwargs):

            # get assigned entry point object
            signal = "entry_point_named_{}".format(entry_point_name)
            disp_responses = dispatcher.send(signal=signal,
                                             sender=dispatcher.Any)

            (_, entry_point_obj) = disp_responses[0]

            # create general req and res objects
            request = entry_point_obj.build_request(*kvars, **kwargs)
            response = entry_point_obj.build_response(*kvars, **kwargs)

            import context as ctx
            context = ctx.for_user(request.user_id)
            metadata = ctx.for_user_metadata(request.user_id)
            metadata['response'] = response

            reply_message = func(request.message, context)

            if reply_message is not None:
                if isinstance(reply_message, list):
                    for message in reply_message:
                        response.reply(message)
                else:
                    response.reply(reply_message)
            return reply_message

        callback_signal = "cb_for_entry_point_{}".format(entry_point_name)
        dispatcher.connect(wrap_and_call,
                           signal=callback_signal,
                           sender=dispatcher.Any)
        logger.info("registering {} for entry point '{}'".format(
            func.__name__, entry_point_name))
        return wrap_and_call

    return decorator
