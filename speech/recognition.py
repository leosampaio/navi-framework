import logging
import os
import inspect
from importlib import import_module
from enum import Enum

import speech_recognition as sr

from navi.core import Navi


class NaviSpeechRecognition(object):

    class Services(Enum):
        google = 0
        wit = 1
        bing = 2
        ibm = 4

    def __init__(self, service, key, language="en-us", username=None):
        self.key = key
        self.service = service
        self.language = language
        self.username = username

    def start(self):

        Navi.db.set_secret_for_key('speech_key', self.key)
        Navi.context["speech_key"] = self.key
        Navi.context["speech_service"] = self.service
        Navi.context["speech_language"] = self.language
        Navi.context["speech_username"] = self.username


def say(message):
    """TEMPORARY MACOS DEPENDENCY. HARDCODED VOICE AND COMMAND"""
    from subprocess import call
    command = ["say", "-v", "Luciana"] + message.split()
    call(command)


def speech_entry_point(func):
    """Link a method with speech recognition's entry point

    usage: 
    ```
        >>> from navi.speech.recognition import speech_entry_point
        >>> @speech_entry_point
        >>> def take_care_of_messages(message, context):
        >>>     ...
    ```

    """

    def decorator(func):
        def wrap_and_call(*kvars, **kwargs):
            message = _listen_and_convert_to_text()
            reply_message = func(message, Navi.context)
            print("Reply: {}".format(reply_message))
            if reply_message is not None:
                if isinstance(reply_message, list):
                    for rmessage in reply_message:
                        say(rmessage)
                else:
                    say(reply_message)
            return reply_message

        Navi.db.extension_set_func_for_key('speech', func, 'entry_point')
        print("registering {} for speech entry point".format(func.__name__))
        return wrap_and_call

    return decorator(func)


def _listen_and_convert_to_text():
    r = sr.Recognizer()
    audio = None
    with sr.Microphone(sample_rate=16000, chunk_size=1024) as source:
        print("Invoked Speech Recognition")
        try:
            audio = r.listen(source)
        except Exception as e:
            print(e)

    service = Navi.context["speech_service"]
    key = Navi.context["speech_key"]
    language = Navi.context["speech_language"]

    username = None
    try:
        username = Navi.context["speech_username"]
    except:
        pass
    

    try:
        if service == NaviSpeechRecognition.Services.google:
            text = r.recognize_google_cloud(audio, credentials_json=key,
                                            language=language)
        elif service == NaviSpeechRecognition.Services.wit:
            text = r.recognize_wit(audio, key=key)
        elif service == NaviSpeechRecognition.Services.bing:
            text = r.recognize_bing(audio, key=key, language=language)
        elif service == NaviSpeechRecognition.Services.ibm:
            text = r.recognize_ibm(audio,
                                   username=username,
                                   key=key, language=language)
        return text.encode('utf-8')
    except sr.UnknownValueError:
        print("{} could not understand audio".format(service))
    except sr.RequestError as e:
        print("Could not request results from {} service; {}".format(service,
                                                                     e))
    return None
