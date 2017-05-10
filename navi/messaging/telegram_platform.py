import logging
import os
import inspect
from importlib import import_module
import logging
import time

from telegram.ext import (Updater, MessageHandler, CommandHandler,
                          Filters)
from telegram import Bot, ParseMode
from pydispatch import dispatcher

from navi.core import Navi
from navi import context as ctx

logger = logging.getLogger(__name__)


class Telegram(object):

    def __init__(self, key):
        self.key = key

    def start(self):
        """Start Telegram Pooling (for development)"""

        # initialize
        self.updater = Updater(self.key)
        self.bot = Bot(token=self.key)

        # set context
        ctx.general()["telegram"] = {}
        ctx.general()["telegram"]["key"] = self.key
        ctx.general()["telegram"]["bot"] = self.bot

        # set handlers
        tg_msg_handler = MessageHandler(Filters.text,
                                        self._send_entry_point_signal)
        tg_comm_handler = MessageHandler(Filters.command,
                                         self._send_command_signal)
        self.updater.dispatcher.add_handler(tg_msg_handler)
        self.updater.dispatcher.add_handler(tg_comm_handler)

        # start pooling
        self.updater.start_polling()
        while True:
            time.sleep(1)

    def _send_entry_point_signal(self, bot, update):
        dispatcher.send(signal="telegram_entry_point", sender=self,
                        bot=bot, update=update)

    def _send_command_signal(self, bot, update):
        command = update.message.text.split(' ', 1)[0][1:]
        signal = "telegram_command_{}".format(command)
        logger.info("Sent {} signal".format(signal))
        dispatcher.send(signal=signal, sender=self,
                        bot=bot, update=update)

def reply(bot, user, message):
    """Reply to user infered by context dict."""

    bot.sendMessage(
        chat_id=user,
        text=message,
        parse_mode=ParseMode.MARKDOWN
    )


def telegram_entry_point(func):
    """Link a method with telegram's entry point

    usage: 
    ```
        >>> from navi.messaging.telegram_platform import telegram_entry_point
        >>> @telegram_entry_point
        >>> def take_care_of_messages(message, context):
        >>>     ...
    ```

    """

    def decorator(func):
        def wrap_and_call(bot, update):
            message = update.message.text
            context = ctx.for_user(update.message.chat_id)
            dispatcher.send(signal="did_receive_text_message")
            reply_message = func(message, context)
            dispatcher.send(signal="did_generate_text_reply")
            if reply_message is not None:
                if isinstance(reply_message, list):
                    for message in reply_message:
                        reply(bot, update.message.chat_id, message)
                else:
                    reply(bot, update.message.chat_id, reply_message)
            return reply_message

        dispatcher.connect(wrap_and_call, signal="telegram_entry_point",
                           sender=dispatcher.Any)
        logger.info(
            "registering {} for entry point".format(func.__name__))
        return wrap_and_call

    return decorator(func)


def telegram_command(command):
    """Link a method with a telegram command (a `/command` type of message)

    usage: 
    ```
        >>> from navi.messaging.navi_telegram import telegram_command
        >>> @telegram_command('hello')
        >>> def say_hello(message, context):
        >>>     ...
    ```

    """

    def decorator(func):
        def wrap_and_call(bot, update):
            message = update.message.text
            context = ctx.for_user(update.message.chat_id)
            dispatcher.send(signal="did_receive_text_message")
            reply_message = func(message, context)
            dispatcher.send(signal="did_generate_text_reply")
            if reply_message is not None:
                reply(bot, update.message.chat_id, reply_message)
            return reply_message

        dispatcher.connect(wrap_and_call,
                           signal="telegram_command_{}".format(command),
                           sender=dispatcher.Any)
        logger.info("registering {} for command '{}'".format(
            func.__name__, command))
        return wrap_and_call

    return decorator
