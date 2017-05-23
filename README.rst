
.. image:: https://raw.githubusercontent.com/leosampaio/navi-framework/master/navi/resources/logo/navi_framework_v1_thin.png
    :width: 50%

|

Navi Framework's README
=======================
|License| |Python|
    .. |License| image:: https://img.shields.io/pypi/l/Django.svg
    .. |Python| image:: https://img.shields.io/badge/python-2.7-blue.svg

Navi is an open and free high-level framework that aims to make
building smart chatbots and personal assistants easy, friction-less and fun. 

In general terms, think about how awesome would it if you could build your own Siri, Alexa or
Google Assistant in a *free*, *open* and *controlled-by-you* way. Navi integrates all
necessary services into a consistent and fluid architecture to help you reach that goal.

Currently, Navi is compatible with **Python 2.7**, but support for Python > 3 is planned.


Guiding Principles
------------------

*   **Fun.**
    Working with the Navi framework should be a fun experience. It should make
    the design of a smart assistant easy to do, to test and to understand and explain

*   **User friendly.**
    Navi is designed to get you from idea to prototype fast by 
    offering consistent, coeherent and well-documented API's

*   **Modular.**
    Bots and assistants created with Navi should be easily shareable in parts
    or wholes. This way developers can build a community and grow together

*   **Extensible**
    Integrating new messaging and conversational platforms to Navi
    should be an easy task and done constantly.


Install
----------------------------

To install only the core of navi, use::

    pip install navi

But the best part of navi lies within its service extensions, we currently support
*Telegram Messaging*; *Snowboy Hotword Detection*; 
*Wit.ai Natural Language Processing*; and *Speech Recognition* services from many providers. 
Install the required dependencies for each by including the name of your desired extension with
the install command, like so::

    pip install navi[SpeechRecognition, HotwordDetection, Telegram, Wit]


Documentation
----------------------------

Head over to the complete documentation, including some great guides, at `navi-framework.readthedocs.io <http://navi-framework.readthedocs.io>`_