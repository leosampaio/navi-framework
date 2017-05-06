from importlib import import_module
import os

from register import Register


class Navi(object):
    """The navi object is used to initialize your bot, wire up all your
    modules together with navi's modules
    """

    context = {}

    def __init__(self, bot_module,
                 intent_modules=None,
                 handler_modules=None,
                 interface_modules=None):
        """Initialize Navi instance with your bot modules

        :param bot_module: required. specifies your bot's main module

        :param intent_modules: if provided, these modules are used instead 
        of the default module `intents`

        :param handler_modules: if provided, these modules are used instead 
        of the default module `handlers`

        :param interface_modules: if provided, these modules are used instead 
        of the default module `interfaces`
        """

        self.bot_module = bot_module

        Navi.dbfilename = "{}/../register.db".format(
            os.path.dirname(bot_module.__file__))
        Navi.db = Register(Navi.dbfilename)
        Navi.db.clean()
        Navi.context["should_close_session"] = False

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

    def start(self, messaging_platforms=[], conversational_platforms=[],
              speech_platforms=[]):
        """Start bot in development mode, if available for chosen messaging
        platform.
        """

        for platform in conversational_platforms:
            platform.start()

        for platform in messaging_platforms:
            platform.start()

        for platform in speech_platforms:
            platform.start()


def get_handler_for(intent):
    try:
        (module_name, handler_class) = Navi.db.get_handler_for_intent(
            intent.__class__)

        module = import_module(module_name)
        Handler = getattr(module, handler_class)
        return Handler()
    except:
        return None


def entity_from_entities_or_context(entity_name, entities, context):
    a = [entities.get(entity_name, None), context.get(entity_name, None)]
    return next((item for item in a if item is not None), None)


def set_can_close_session():
    Navi.context["should_close_session"] = True


def should_close_session():
    return Navi.context["should_close_session"]


def set_session_was_closed():
    Navi.context["is_session_open"] = False
    Navi.context["should_close_session"] = False


def open_session():
    Navi.context["is_session_open"] = True


def is_session_open():
    return Navi.context["is_session_open"]
