import abc
from enum import Enum

from pydispatch import dispatcher


class IntentClassWatcher(type):

    def __init__(cls, name, bases, clsdict):
        if len(cls.mro()) > 2:
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
        unspecified = 0
        unsupported = 1
        failure = 2
        ready = 3

    class HandleResponse(object):

        class Status(Enum):
            """Defines possible handling status for a handle response"""
            unspecified = 0
            in_progress = 1
            success = 2
            failure = 3

        def __init__(self, status, response_dict):
            self.status = status
            self.response_dict = response_dict


class Entity(object):
    pass


class FulfilledIntent(Intent):
    pass
