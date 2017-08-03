from tinydb import TinyDB, Query, where


class Notebook(object):

    db = None

    @classmethod
    def _set_db(self, filepath):
        Notebook.db = TinyDB(filepath)

    @classmethod
    def clear(self):
        Notebook.db.purge_tables()

    @classmethod
    def close(self):
        Notebook.db.close()


class UserNotebook(object):

    def __init__(self, user_id):
        self.id = user_id

    def add_entry(self, key, entry):
        db = Notebook.db.table(str(self.id))
        obj = {
            'label': key,
            'entry': entry,
        }
        db.insert(obj)

    def get_entry(self, key):
        db = Notebook.db.table(str(self.id))
        entry = db.search(Query().label == key)

        if len(entry) > 0:
            entry = entry[0]
        else:
            return None

        return entry['entry']


def get_notebook_for_user(user):
    return UserNotebook(user)
