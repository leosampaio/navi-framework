"""Here is where your many intents may live. An intent is an action a user 
wants acomplished. It is created by inheriting from the `Intent` base class
and declaring each of your `Entity` s
"""

from navi.intents import Intent, Entity


class DoSomethingAwesomeIntent(Intent):

    awesomeness_level = Entity()
    type_of_awesome = Entity()