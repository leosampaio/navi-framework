import logging
import os
import inspect
import time
from importlib import import_module
import logging

from pydispatch import dispatcher

from navi.core import Navi
from navi.speech import snowboywrapper
from navi import context as ctx


logger = logging.getLogger(__name__)


class SnowboyHotwordDetector(object):

    def __init__(self, names, models):
        self.names = names
        self.models = models

    def start(self):

        dispatcher.connect(self._terminate_detector,
                           signal="hotword_terminate_detector",
                           sender=dispatcher.Any)
        dispatcher.connect(self._start_detector,
                           signal="hotword_start_detector",
                           sender=dispatcher.Any)

        sensitivity = [0.5]*len(self.models)

        self.callbacks = []
        for (model, name) in zip(self.models, self.names):
            self.callbacks.append(lambda: self._activated_by_hotword(name))

        self.detector = snowboywrapper.HotwordDetector(
            self.models, sensitivity=sensitivity)

        self._start_detector()

    def _terminate_detector(self):
        self.detector.terminate()

    def _start_detector(self):
        self.detector.start(detected_callback=self.callbacks,
                            sleep_time=0.03)

    def _activated_by_hotword(self, name):
        signal = "hotword_activation_{}".format(name)
        dispatcher.send(signal=signal, sender=self, name=name)


def hotword_activation(name):
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
            ctx.open_audio_session()
            dispatcher.send(signal="hotword_terminate_detector",
                            sender=dispatcher.Any)
            while ctx.is_audio_session_open():
                func(*kvars, **kwargs)
            dispatcher.send(signal="hotword_start_detector",
                            sender=dispatcher.Any)

        signal = "hotword_activation_{}".format(name)
        dispatcher.connect(wrap_and_call, signal=signal,
                           sender=dispatcher.Any)
        logger.info(
            "registering {} for hotword_activation".format(func.__name__))
        return wrap_and_call

    return decorator
