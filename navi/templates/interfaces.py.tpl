"""The interfaces file is a collection of functions that guide your 
communication with navi's supported conversational, messaging and speech
services
"""


from navi.messaging.telegram_platform import (telegram_entry_point,
                                              telegram_command)
from navi.conversational import wit_ai
from navi.speech.recognition import message_from_speech
from navi.speech.hotword import hotword_activation
from navi.core import get_handler_for, entity_from_entities_or_context

from .intents import DoSomethingAwesomeIntent


@telegram_entry_point
def did_receive_amazing_message(message, context):
    """This entry point is where all your telegram text messages are forwarded
    to. It expects you to return a text reply, which is exactly what we do by
    using wit to parse the message and get a reply back
    """
    reply = wit_ai.parse_message(message, context)
    return reply


@telegram_command('do_a_magic_trick')
def did_receive_start(message, context):
    """If you want some quick interactions, register a telegram command
    that your users can access by sending '/command_name' 
    (eg. '/do_a_magic_trick'). It also expects you to return a text reply, here
    we are simply returing one straight away.
    """
    return "Hello!"


@hotword_activation
@message_from_speech
def did_get_speech(message, context):
    """Here we are registering this function for two things at the same 
    time. 

    `@hotword_activation` tells navi this function should be called when
    a voice hotword activation is triggered. 

    And `@message_from_speech` registers this function as a voice recognition 
    trigger and handler. It means that anyone that calls this function will
    activate the voice recognition module and have the result transcribed on 
    the message parameter. It expects a string as return value, which will 
    be spoken back to the user. As in the telegram entry_point, we are using
    wit's parsing to provide a response back
    """
    reply = wit_ai.parse_message(message, context)
    return reply


@wit_ai.wit_action('do_something_awesome')
def do_something_awesome(message, entities, context):
    """When using wit.ai, you define actions on their platform. Navi will link
    your wit actions to the functions you register using the `@wit_action` 
    decorator. 

    On this method you should build your intent and return it. To 
    do so, you can use the entities extracted on the last sent message and/or
    the current context, both are simple key-value dictionaries. On this 
    example we use the helper method `entity_from_entities_or_context` that
    tries to get the value from either the entities or the context dictionary.
    """
    aws_level = entity_from_entities_or_context("awesomeness_level",
                                            entities,
                                            context)
    aws_type = entity_from_entities_or_context("type_of_awesome",
                                              entities,
                                              context)
    intent = DoSomethingAwesomeIntent(awesomeness_level=aws_level,
                                      type_of_awesome=aws_type)
    return intent
