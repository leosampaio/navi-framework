import abc
from enum import Enum


class Intent(object):
    """Base class for Intent representation.
    An intent is a user-desired action to be acomplished.
    Each intent is built by an `Interface` and sent over to the corresponding
    `IntentHandler`.
    """

    class IntentResolveResponse(object):
        """Base Intent Resolving Response.
        The resolve stage is where the intent handler may request for missing
        information.
        """
        pass

    class IntentHandleResponse(object):
        """Base Intent Handling Response.
        Represents a response from the Intent Handler to the Interface
        """

        class IntentHandlingStatus(Enum):
            """Defines possible handling status for a handle response"""
            unspecified = 1
            in_progress = 3
            success = 4
            failure = 5

        status = IntentHandlingStatus.unspecified
