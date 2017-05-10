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


def general():
    return Navi.context
