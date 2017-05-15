import logging
import os
import inspect
import time
from importlib import import_module
import logging

from pydispatch import dispatcher

from navi.core import Navi, is_session_open, open_session
from navi.speech import snowboywrapper


logger = logging.getLogger(__name__)


class SnowboyHotwordDetector(object):

    def __init__(self, model):
        self.model = model

    def start(self):

        dispatcher.connect(self._terminate_detector,
                           signal="hotword_terminate_detector",
                           sender=dispatcher.Any)
        dispatcher.connect(self._start_detector,
                           signal="hotword_start_detector",
                           sender=dispatcher.Any)
        self.detector = snowboywrapper.HotwordDetector(
            self.model, sensitivity=0.5)

        self._start_detector()

    def _terminate_detector(self):
        self.detector.terminate()

    def _start_detector(self):
        self.detector.start(detected_callback=self._activated_by_hotword,
                            sleep_time=0.03)

    def _activated_by_hotword(self):
        dispatcher.send(signal="hotword_activation", sender=self)


def hotword_activation(func):
    """Link a function with a hotword activation event

    usage: 
    ```
        >>> from navi.speech.hotword import hotword_activation
        >>> @hotword_activation
        >>> @speech_entry_point
        >>> def take_care_of_messages(message, context):
        >>>     ...
    ```

    """

    def decorator(func):
        def wrap_and_call(*kvars, **kwargs):
            open_session()
            dispatcher.send(signal="hotword_terminate_detector",
                            sender=dispatcher.Any)
            while is_session_open():
                func(*kvars, **kwargs)
            dispatcher.send(signal="hotword_start_detector",
                            sender=dispatcher.Any)

        dispatcher.connect(wrap_and_call, signal="hotword_activation",
                           sender=dispatcher.Any)
        logger.info(
            "registering {} for hotword_activation".format(func.__name__))
        return wrap_and_call

    return decorator(func)
