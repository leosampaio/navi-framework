import random
from importlib import import_module

from wit import Wit
from navi.core import Navi


class WitConversationalPlatform(object):

    def __init__(self, key):
        self.key = key

    def start(self):
        self.client = Wit(access_token=self.key)

        Navi.context['wit_client'] = self.client
        Navi.context["wit_context"] = {}
        Navi.context["wit_context"]["session_started"] = False


def parse_message(message, context):
    if not Navi.context["wit_context"]["session_started"]:
        Navi.context["wit_context"]["session"] = random.randint(0, 1000000000)
        Navi.context["wit_context"]["session_started"] = True

    client = Navi.context['wit_client']
    session = Navi.context["wit_context"]["session"]
    converse_result = client.converse(session,
                                      message,
                                      Navi.context["wit_context"])

    if converse_result['type'] == 'action':
        action_name = converse_result['action']
        (module_name, func_name) = Navi.db.get_extension_func_for_key(
            'wit_actions',
            action_name
        )
        try:
            module = import_module(module_name)
            func = getattr(module, func_name)
            return func(message, converse_result['entities'], Navi.context)
        except Exception as e:
            print(str(e))
    elif converse_result['type'] == 'msg':
        return converse_result['msg']


def did_finish_session():
    Navi.context["wit_context"]["session_started"] = False


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
        Navi.db.extension_set_func_for_key('wit_actions',
                                           func,
                                           action)
        print("registering {} for wit.ai action '{}'".format(
            func.__name__, action))
        return func

    return decorator
