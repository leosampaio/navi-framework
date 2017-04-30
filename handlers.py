import abc

from navi.core import Navi


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

    @abc.abstractmethod
    def resolve(self, intent, context={}):
        """Check if all needed parameters are set. Complain if not.

        :param intent: an intent object of type TVSeriesEpisodeIntent
        :param context: a dictionary describing current context
        :rtype: A :class: `TVSeriesEpisodeIntentResolveResponse`
        """
        pass

    def confirm(self, intent, context={}):
        """Optional. Perform any final validation of the intent parameters
        and to verify that you are ready to handle the intent

        :param intent: an intent object of type TVSeriesEpisodeIntent
        :param context: a dictionary describing current context
        """
        pass

    @abc.abstractmethod
    def handle(self, intent, context={}):
        """Execute intended action and return result

        :param intent: an intent object of type TVSeriesEpisodeIntent
        :param context: a dictionary describing current context
        :rtype: A :class: `TVSeriesEpisodeIntentHandleResponse`
        """
        pass


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
        print("registering {} for {}".format(Cls.__name__, intent.__name__))
        Navi.db.set_handler_for_intent(Cls, intent)
        return Cls

    return class_decorator
