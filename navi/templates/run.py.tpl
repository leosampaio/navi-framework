import os

from navi.core import Navi
from navi.messaging.telegram_platform import Telegram
from navi.conversational.wit_ai import WitConversationalPlatform
from navi.speech.recognition import NaviSpeechRecognition
from navi.speech.hotword import SnowboyHotwordDetector

import $bot_name
import config
import secret.config

if __name__ == "__main__":
    """Setup your environment, create objects for tour services of choice,
    and add them to the lists navi expects on `start`

      telegram only needs your bot token to get running
        >>> telegram_messaging = Telegram(secret.config.TELEGRAM["key"])  

      wit will also need your app token
        >>> wit_platform = WitConversationalPlatform(secret.config.WIT["key"])

      we support multiple speech recognition platforms, specify your platform,
      your token and your language (if supported by the platform)
        >>> speech_recog = NaviSpeechRecognition(
        >>>      NaviSpeechRecognition.Services.bing,
        >>>      secret.config.BING["key"],
        >>>      language="en-US"
        >>> )

      hotword detection is performed by snowboy, it only needs your recognition
      model. Create one at https://snowboy.kitt.ai
        >>> hotword_detect = SnowboyHotwordDetector(hotword_model_file)

    """

    bot = Navi($bot_name)

    # bot.start(messaging_platforms=[telegram_messaging],
    #           conversational_platforms=[wit_platform],
    #           speech_platforms=[speech_recog, hotword_detect])
