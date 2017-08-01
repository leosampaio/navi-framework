import abc
from enum import Enum
import traceback

from pydispatch import dispatcher


class IntentClassWatcher(type):

    def __init__(cls, name, bases, clsdict):
        if len(cls.mro()) > 2:

            entities = [i for i in clsdict if isinstance(
                clsdict[i], Entity)]

            for entity in entities:
                clsdict[entity].defined_intent_name = name

            signal = "intent_class_{}".format(name)
            dispatcher.connect(cls.get_class, signal=signal)

        super(IntentClassWatcher, cls).__init__(name, bases, clsdict)


class Intent(object):
    """Base class for Intent representation.
    An intent is a user-desired action to be acomplished.
    Each intent is built by an `Interface` and sent over to the corresponding
    `IntentHandler`.
    """

    __metaclass__ = IntentClassWatcher

    def __init__(self, **kwargs):
        entities = [i for i in dir(self) if isinstance(
            getattr(self, i), Entity)]
        for entity_name in entities:
            setattr(self, entity_name, kwargs.get(entity_name))

    @classmethod
    def get_class(cls):
        return cls

    class ResolveResponse(Enum):
        """Base Intent Resolving Response.
        The resolve stage is where the intent handler may request for missing
        information.
        """
        not_required = 0
        missing = 1
        unsupported = 2
        ambiguous = 3
        ready = 4

    class ConfirmResponse(Enum):
        unspecified = 4
        unsupported = 5
        failure = 6
        ready = 7

    class HandleResponse(object):

        class Status(Enum):
            """Defines possible handling status for a handle response"""
            unspecified = 8
            in_progress = 9
            success = 10
            failure = 11

        def __init__(self, status, response_dict):
            self.status = status
            self.response_dict = response_dict


class Entity(object):

    def __init__(self, def_name=None):
        if def_name == None:
            (filename, line_number, function_name,
             text) = traceback.extract_stack()[-2]
            def_name = text[:text.find('=')].strip()
        self.defined_name = def_name

    def __repr__(self):
        return "{}_{}".format(self.defined_intent_name, self.defined_name)


class FulfilledIntent(Intent):
    pass
