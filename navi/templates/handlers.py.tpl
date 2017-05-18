"""You may declare your handlers here. Handlers are a special kind of class
that should inherit from `IntentHandler` provide the 3 sets of handling 
methods: resolve, confirm and handle.

Handlers should also be registered with one or more `Intent`
"""

from navi.handlers import IntentHandler, handler_for_intent
from navi.intents import Intent

from .intents import DoSomethingAwesomeIntent


@handler_for_intent(DoSomethingAwesomeIntent)
class AwesomenessHandler(IntentHandler):

    def resolve_awesomeness_level(self, entity):
        """Checks the status of each entity inside our intent before proceding
        with the action. The response is sent back through the conversational
        interface of choice and handled accordingly

        Should return an `Intent.ResolveResponse`, which can be one of:
            Intent.ResolveResponse.ready
            Intent.ResolveResponse.missing
            Intent.ResolveResponse.not_required
            Intent.ResolveResponse.unsupported
            Intent.ResolveResponse.ambiguous

        You don't need to implement a resolve method for each entity.
        By default, unimplemented resolve methods return .not_required
        """
        return Intent.ResolveResponse.ready

    def confirm(self, intent):
        """Before actually executing the action, this is your last chance to
        check the environment (eg. making sure you have access to required 
        service). 


        Should return an `Intent.ConfirmResponse`, which can be one of:
            Intent.ConfirmResponse.unspecified
            Intent.ConfirmResponse.unsupported
            Intent.ConfirmResponse.failure
            Intent.ConfirmResponse.ready
        """
        return Intent.ConfirmResponse.ready

    def handle(self, intent):
        """Finally, this is where you should execute the intended action. 
        After performing and concluding the task, you should return a
        `Intent.HandleResponse` object that states the task status and keeps
        a dictionary of the results you want exposed to the conversational
        interface.

        Intent.HandleResponse.Status can be one of:
            Intent.HandleResponse.Status.unspecified
            Intent.HandleResponse.Status.in_progress
            Intent.HandleResponse.Status.success
            Intent.HandleResponse.Status.failure
        """
        result = {'awesome_thing': "The Navi Framework"}
        response = Intent.HandleResponse(Intent.HandleResponse.Status.success,
                                         result)
        return response
