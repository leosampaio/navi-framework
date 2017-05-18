import abc
import logging

from pydispatch import dispatcher

from navi.core import Navi
from navi.intents import Entity, Intent

logger = logging.getLogger("__name__")


class IntentHandler(object):
    """Intent Handler Protocol. Must be subclassed.
    Responsible for executing the user-desired action.

    The handling is composed of three stages:

    * 1. Resolve
    Verify required parameters and if they are well specified enough
    to complete the desired task

    * 2. Confirm
    Perform any final validation of the intent parameters
    and verify that you are ready to handle the intent

    * 3. Handle
    Execute intended action and return result
    """

    __metaclass__ = abc.ABCMeta

    def resolve(self, intent):
        """Check if all needed parameters are set. Complain if not.

        :param intent: an intent object of type TVSeriesEpisodeIntent
        :param context: a dictionary describing current context
        :rtype: A resolve response
        """

        resolve_responses = {}

        entities = [i for i in dir(intent.__class__) if isinstance(
            getattr(intent.__class__, i), Entity)]
        for entity_name in entities:
            try:
                method_name = "resolve_{}".format(entity_name)
                method = getattr(self, method_name)
                resolution = method(getattr(intent, entity_name))
                resolve_responses[entity_name] = resolution
                logger.info("{}: {}".format(entity_name, resolution))
            except Exception as e:
                print(str(e))
                resolution = Intent.ResolveResponse.not_required
                resolve_responses[entity_name] = resolution
                logger.info("{}: {}".format(
                    entity_name,
                    Intent.ResolveResponse.not_required))

        return resolve_responses

    def confirm(self, intent):
        """Optional. Perform any final validation of the intent parameters
        and to verify that you are ready to handle the intent

        :param intent: an intent object of type TVSeriesEpisodeIntent
        """
        return Intent.ConfirmResponse.ready

    @abc.abstractmethod
    def handle(self, intent):
        """Execute intended action and return result

        :param intent: an intent object of type TVSeriesEpisodeIntent
        :rtype: A dictionary with all values that the developer wants exposed
        to the interface regarding the task handling
        """
        pass

    @classmethod
    def create(cls):
        """IntentHandler Factory to be called on 'handler_for_intent' 
        dispatcher message
        """
        return cls()


def handler_for_intent(intent):
    """Similar to flask's decorator, this should allow us to link `Intents` 
    with their handlers

    usage: 
    ```
        >>> @handler_for_intent(WatchTVSeriesEpisodeIntent)
        >>> class TVSeriesEpisodeHandler(IntentHandler):
        >>>     ...
    ```

    """

    def class_decorator(Cls):
        logger.info("registering {} for {}".format(
            Cls.__name__, intent.__name__))
        signal = "handler_for_{}".format(intent.__name__)
        dispatcher.connect(Cls.create, signal=signal)
        return Cls

    return class_decorator
