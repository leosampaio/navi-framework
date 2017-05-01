import logging
import os
import inspect
from importlib import import_module

from telegram.ext import (Updater, MessageHandler, CommandHandler,
                          Filters)
from telegram import Bot, ParseMode

from navi.core import Navi


class Telegram(object):

    def __init__(self, key):
        self.key = key

    def start(self):
        """Start Telegram Pooling (for development)"""

        self.updater = Updater(self.key)
        self.bot = Bot(token=self.key)

        Navi.db.set_secret_for_key('telegram_key', self.key)
        Navi.context["telegram_key"] = self.key

        # iterate over command functions and try to import each
        ext_functions = Navi.db.get_all_extension_functions(
            'telegram_commands')
        for (key, comm_module_name, comm_func_name) in ext_functions:
            try:
                comm_module = import_module(comm_module_name)
                comm_func = getattr(comm_module, comm_func_name)
                tg_comm_handler = CommandHandler(key, comm_func)
                self.updater.dispatcher.add_handler(tg_comm_handler)
            except Exception as e:
                raise e

        # get entry point funtion
        (ep_module_name, ep_func_name) = Navi.db.get_extension_func_for_key(
            'telegram', 'entry_point')

        # and try to import and register with telegram
        try:
            ep_module = import_module(ep_module_name)
            entry_point = getattr(ep_module, ep_func_name)
            tg_msg_handler = MessageHandler(Filters.text,
                                            entry_point)
            self.updater.dispatcher.add_handler(tg_msg_handler)
        except Exception as e:
            raise e

        self.updater.start_polling()
        self.updater.idle()


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
            Navi.context["telegram_user"] = update.message.chat_id
            reply_message = func(message, Navi.context)
            if reply_message is not None:
                reply(bot, update.message.chat_id, reply_message)
            return reply_message

        Navi.db.extension_set_func_for_key('telegram', func, 'entry_point')
        print("registering {} for telegram entry point".format(func.__name__))
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
            Navi.context["telegram_user"] = update.message.chat_id

            reply_message = func(message, Navi.context)
            if reply_message is not None:
                reply(bot, update.message.chat_id, reply_message)
            return reply_message

        Navi.db.extension_set_func_for_key('telegram_commands',
                                           func,
                                           command)
        print("registering {} for telegram command '{}'".format(
            func.__name__, command))
        return wrap_and_call

    return decorator
