import logging
import os
import inspect
import time
from importlib import import_module
import logging
import functools
import threading

from pydispatch import dispatcher

from navi.core import Navi
from navi.speech import snowboywrapper
from navi import context as ctx


logger = logging.getLogger(__name__)


class SnowboyHotwordDetector(object):

    def __init__(self, names, models, sensitivity=None):
        self.names = names
        self.models = models
        self.sensitivity = sensitivity

    def start(self):

        dispatcher.connect(self.terminate_detector,
                           signal="hotword_terminate_detector",
                           sender=dispatcher.Any)
        dispatcher.connect(self.start_detector,
                           signal="hotword_start_detector",
                           sender=dispatcher.Any)

        if self.sensitivity is None:
            self.sensitivity = [0.5] * len(self.models)

        self.callbacks = [
            functools.partial(self._activated_by_hotword, name)
            for name in self.names
        ]

        self.detector = snowboywrapper.HotwordDetector(
            self.models, sensitivity=self.sensitivity)

        # connect hotword detector with speech recognition
        dispatcher.connect(self._did_finish_recog,
                           signal="did_finish_speech_recognition")
        dispatcher.connect(self._did_finish_recog,
                           signal="did_timeout")
        dispatcher.connect(self._did_finish_recog,
                           signal="did_fail")
        dispatcher.connect(self._did_finish_recog,
                           signal="did_not_understand")
        dispatcher.connect(self._did_start_recog,
                           signal="did_start_speech_recognition")

        self.should_detect = True
        self._run_detector()

    def terminate_detector(self):
        self.should_detect = False
        self.detector.terminate()

    def start_detector(self):
        self.should_detect = True
        self._run_detector()

    def _run_detector(self):
        t = threading.Thread(
            target=lambda: self.detector.start(
                detected_callback=self.callbacks,
                interrupt_check=self._interrupt_check,
                sleep_time=0.03)
        )
        t.daemon = True
        t.start()

    def _interrupt_check(self):
        return not self.should_detect

    def _activated_by_hotword(self, name):
        signal = "hotword_activation_{}".format(name)
        logger.info("sent {} signal".format(signal))
        dispatcher.send(signal=signal, sender=self, name=name)

    def _did_finish_recog(self):
        self.start_detector()

    def _did_start_recog(self):
        self.terminate_detector()


def hotword_activation(name):

    def decorator(func):
        def wrap_and_call(*kvars, **kwargs):
            func()

        signal = "hotword_activation_{}".format(name)
        dispatcher.connect(wrap_and_call, signal=signal,
                           sender=dispatcher.Any)
        logger.info(
            "registering {} for {}".format(func.__name__, signal))
        return wrap_and_call

    return decorator


def hotword_activation_with_audio_session(name):

    def decorator(func):
        def wrap_and_call(*kvars, **kwargs):
            if ctx.is_audio_session_open(): return
            ctx.open_audio_session()
            while ctx.is_audio_session_open():
                func(*kvars, **kwargs)

        signal = "hotword_activation_{}".format(name)
        dispatcher.connect(wrap_and_call, signal=signal,
                           sender=dispatcher.Any)
        logger.info(
            "registering {} for {}".format(func.__name__, signal))
        return wrap_and_call

    return decorator
