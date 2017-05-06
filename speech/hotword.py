import logging
import os
import inspect
import time
from importlib import import_module
import logging

from navi.core import Navi, is_session_open, open_session
from navi.speech.snowboy import snowboydecoder


logger = logging.getLogger(__name__)


class SnowboyHotwordDetector(object):

    def __init__(self, model):
        self.model = model

    def start(self):

        # get entry point funtion
        (ep_module_name, ep_func_name) = Navi.db.get_extension_func_for_key(
            'hotword', 'activation')

        # and try to import and register
        activation_function = lambda x: None
        try:
            ep_module = import_module(ep_module_name)
            activation_function = getattr(ep_module, ep_func_name)
        except Exception as e:
            raise e

        detector = snowboydecoder.HotwordDetector(self.model, sensitivity=0.5)
        Navi.context["hotword_detector"] = detector

        detector.start(detected_callback=activation_function,
                       interrupt_check=_interrupt_callback,
                       sleep_time=0.03)

interrupted = False


def _set_is_interrupted(is_interrupted):
    global interrupted
    interrupted = is_interrupted


def _interrupt_callback():
    global interrupted
    return interrupted


def hotword_activation(speech_decorator):
    """Link a method with telegram's entry point

    usage: 
    ```
        >>> from navi.speech.hotword import hotword_activation
        >>> @hotword_activation(speech_entry_point)
        >>> def take_care_of_messages(message, context):
        >>>     ...
    ```

    """

    def decorator(func):
        def wrap_and_call(*kvars, **kwargs):
            open_session()
            Navi.context["hotword_detector"].terminate()
            while is_session_open():
                snowboydecoder.play_audio_file()
                speech_decorator(func)(*kvars, **kwargs)

        Navi.db.extension_set_func_for_key('hotword', func, 'activation')
        logger.info("registering {} for hotword_activation".format(func.__name__))
        return wrap_and_call

    return decorator
