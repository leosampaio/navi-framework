from pydispatch import dispatcher

from .core import Navi


def for_user(user_id):
    users_dict = Navi.context["users"]

    if user_id is None:
        user_id = 'any'

    if user_id in users_dict:
        return users_dict[user_id]
    else:
        users_dict[user_id] = {}
        users_dict[user_id]["user"] = user_id
        dispatcher.send(signal="did_create_new_user_context",
                        context=users_dict[user_id])
        return users_dict[user_id]


def for_user_metadata(user_id):
    users_dict = Navi.context["users_metadata"]

    if user_id is None:
        user_id = 'any'

    if user_id in users_dict:
        return users_dict[user_id]
    else:
        users_dict[user_id] = {}
        users_dict[user_id]["user"] = user_id
        return users_dict[user_id]


def general():
    return Navi.context


def clean_user_context(context):

    user_id = 'any'
    if 'user' in context:
        user_id = context['user']

    context = {}
    context["user"] = user_id


def clean_user_error_context(context):

    user_id = 'any'
    if 'user' in context:
        user_id = context['user']

    keys_to_remove = []
    for key in context:
        error_endings = ('missing', 'failure', 'unsupported', 'ambiguous')
        if isinstance(key, basestring) and key.endswith(error_endings):
            keys_to_remove.append(key)

    for k in keys_to_remove:
        context.pop(k)


def close_session_when_done():
    Navi.context["should_close_session"] = True
