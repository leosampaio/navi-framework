import logging
import os
import inspect
from importlib import import_module
from enum import Enum
import logging
from pydispatch import dispatcher

import speech_recognition as sr

from navi.core import Navi, NaviEntryPoint, NaviRequest, NaviResponse
from navi import context
from .sounds import play_ding, play_dong, play_ding_dong

logger = logging.getLogger(__name__)


class NaviSpeechRecognition(NaviEntryPoint):

    class Services(Enum):
        google = 0
        wit = 1
        bing = 2
        ibm = 4

    class Status(Enum):
        unknown = 0
        success = 1
        failure = 2
        timeout = 3

    def __init__(self, name, service, tts_script, key=None, language="en-us",
                 username=None, credentials_json=None):
        super(NaviSpeechRecognition, self).__init__(name)

        self.key = key
        self.credentials_json = credentials_json
        self.service = service
        self.language = language
        self.username = username
        NaviSpeechRecognition.tts_script = tts_script

        if self.credentials_json:
            with open(credentials_json, "r") as file:
                self.credentials_json = file.read()

    def start(self):

        Navi.context["speech_key"] = self.key
        Navi.context["credentials_json"] = self.credentials_json
        Navi.context["speech_service"] = self.service
        Navi.context["speech_language"] = self.language
        Navi.context["speech_username"] = self.username

        # check if hooks have any custom hooks and add our sound effects if not
        if len(dispatcher.getReceivers(signal="did_not_understand_sound")) == 0:
            dispatcher.connect(self._did_finish_recog,
                               signal="did_not_understand_sound")
        if len(dispatcher.getReceivers(signal="did_fail_sound")) == 0:
            dispatcher.connect(self._did_finish_recog,
                               signal="did_fail")
        if len(dispatcher.getReceivers(signal="did_timeout_sound")) == 0:
            dispatcher.connect(self._did_timeout_recog,
                               signal="did_timeout_sound")
        if len(dispatcher.getReceivers(
                signal="did_finish_speech_recognition_sound")) == 0:
            dispatcher.connect(self._did_finish_recog,
                               signal="did_finish_speech_recognition_sound")
        if len(dispatcher.getReceivers(
                signal="did_start_speech_recognition_sound")) == 0:
            dispatcher.connect(self._did_start_recog,
                               signal="did_start_speech_recognition_sound")

        dispatcher.connect(self._graceful_stop,
                           signal="graceful_stop")

    def _did_start_recog(self):
        play_ding()

    def _did_finish_recog(self):
        play_dong()

    def _did_timeout_recog(self):
        play_ding_dong()

    def _graceful_stop(self):
        play_ding_dong()

    def build_request(self, *kvars, **kwargs):
        return NaviSpeechRecognitionRequest(
            kwargs.setdefault("user_id", "speech")
        )

    def build_response(self, *kvars, **kwargs):
        return NaviSpeechRecognitionResponse()


class NaviSpeechRecognitionRequest(NaviRequest):

    def __init__(self, user_id):
        dispatcher.send(signal="did_start_speech_recognition",
                        sender=dispatcher.Any)
        dispatcher.send(signal="did_start_speech_recognition_sound")
        (status, message) = _listen_and_convert_to_text()

        user_context = context.for_user(user_id)

        if status == NaviSpeechRecognition.Status.failure:
            dispatcher.send(signal="did_fail", context=user_context)
            dispatcher.send(signal="did_fail_sound")
        elif status == NaviSpeechRecognition.Status.timeout:
            dispatcher.send(signal="did_timeout", context=user_context)
            dispatcher.send(signal="did_timeout_sound")
            return
        elif status == NaviSpeechRecognition.Status.unknown:
            dispatcher.send(signal="did_not_understand",
                            context=user_context)
            dispatcher.send(signal="did_not_understand_sound")
        elif status == NaviSpeechRecognition.Status.success:
            dispatcher.send(signal="did_finish_speech_recognition",
                            status=status,
                            message=message,
                            context=user_context)

        super(NaviSpeechRecognitionRequest, self).__init__(message, user_id)


class NaviSpeechRecognitionResponse(NaviResponse):

    def reply(self, message):
        say(message)


def say(message):

    from subprocess import call
    message = "\"{}\"".format(message.encode('utf-8'))
    try:
        command = NaviSpeechRecognition.tts_script.format(message)
        logger.info("running {}".format(command))
        call(command, shell=True)
    except Exception as e:
        logger.error(str(e))


def message_from_speech(func):
    """Link a method with speech recognition's entry point

    usage:
    ```
        >>> from navi.speech.recognition import message_from_speech
        >>> @message_from_speech
        >>> def take_care_of_messages(message, context):
        >>>     ...
    ```

    """

    def decorator(func):
        def wrap_and_call(*kvars, **kwargs):
            dispatcher.send(signal="did_start_speech_recognition",
                            sender=dispatcher.Any)
            dispatcher.send(signal="did_start_speech_recognition_sound")
            (status, message) = _listen_and_convert_to_text()

            user_context = context.for_user(kwargs.setdefault("user"))

            if status == NaviSpeechRecognition.Status.failure:
                dispatcher.send(signal="did_fail", context=user_context)
                dispatcher.send(signal="did_fail_sound")
            elif status == NaviSpeechRecognition.Status.timeout:
                dispatcher.send(signal="did_timeout", context=user_context)
                dispatcher.send(signal="did_timeout_sound")
                return
            elif status == NaviSpeechRecognition.Status.unknown:
                dispatcher.send(signal="did_not_understand",
                                context=user_context)
                dispatcher.send(signal="did_not_understand_sound")
            elif status == NaviSpeechRecognition.Status.success:
                dispatcher.send(signal="did_finish_speech_recognition",
                                status=status,
                                message=message,
                                context=user_context)

            reply_message = func(message, user_context)
            logger.info("Reply: {}".format(reply_message))
            if reply_message is not None:
                if isinstance(reply_message, list):
                    for rmessage in reply_message:
                        say(rmessage)
                else:
                    say(reply_message)
            return reply_message

        logger.info(
            "registering {} for speech recog".format(func.__name__))
        return wrap_and_call

    return decorator(func)


def _listen_and_convert_to_text():
    r = sr.Recognizer()
    r.pause_threshold = 0.5
    audio = None
    with sr.Microphone(sample_rate=8000, chunk_size=1024) as source:
        logger.info("Invoked Speech Recognition")
        try:
            audio = r.listen(source, timeout=5)
        except sr.WaitTimeoutError:
            return (NaviSpeechRecognition.Status.timeout, None)
        except Exception as e:
            logger.exception(e)

    logger.info("Sending audio clip for recognition")

    dispatcher.send(signal="did_finish_speech_recognition_sound")
    service = Navi.context["speech_service"]
    key = Navi.context["speech_key"]
    language = Navi.context["speech_language"]

    username = Navi.context.get("speech_username")
    credentials_json = Navi.context.get("credentials_json")

    try:
        if service == NaviSpeechRecognition.Services.google:
            text = r.recognize_google_cloud(audio,
                                            credentials_json=credentials_json,
                                            language=language)
        elif service == NaviSpeechRecognition.Services.wit:
            text = r.recognize_wit(audio, key=key)
        elif service == NaviSpeechRecognition.Services.bing:
            text = r.recognize_bing(audio, key=key, language=language)
        elif service == NaviSpeechRecognition.Services.ibm:
            text = r.recognize_ibm(audio,
                                   username=username,
                                   key=key, language=language)
        logger.info("Speech Recognition: %s", text.encode('utf-8'))
        return (NaviSpeechRecognition.Status.success, text.encode('utf-8'))
    except sr.UnknownValueError:
        logger.info("{} could not understand audio".format(service))
        return (NaviSpeechRecognition.Status.unknown, None)
    except sr.RequestError as e:
        logger.info(
            "Could not request results from {} service; {}".format(service, e))
    return (NaviSpeechRecognition.Status.failure, None)


def start_speech_recognition_hook(func):
    """Link a method with speech recognition's start speech hook

    usage:
    ```
        >>> from navi.speech.recognition import start_speech_recognition_hook
        >>> @start_speech_recognition_hook
        >>> def play_bing():
        >>>     ...
    ```

    """

    def decorator(func):

        dispatcher.connect(func, signal="did_start_speech_recognition")
        logger.info(
            "registering {} for speech started hook".format(func.__name__))

    return decorator(func)


def finish_speech_recognition_hook(func):
    """Link a method with speech recognition's finish speech hook

    usage:
    ```
        >>> from navi.speech.recognition import finish_speech_recognition_hook
        >>> @finish_speech_recognition_hook
        >>> def play_bong():
        >>>     ...
    ```

    """

    def decorator(func):

        dispatcher.connect(func, signal="did_finish_speech_recognition")
        logger.info(
            "registering {} for speech finished hook".format(func.__name__))

    return decorator(func)


def timeout_out_speech_recognition_hook(func):
    """Link a method with speech recognition's timeout speech hook

    usage:
    ```
        >>> from navi.speech.recognition import fail_speech_recognition_hook
        >>> @fail_speech_recognition_hook
        >>> def play_puonpuon():
        >>>     ...
    ```

    """

    def decorator(func):

        dispatcher.connect(func, signal="did_timeout")
        logger.info(
            "registering {} for speech finished hook".format(func.__name__))

    return decorator(func)
