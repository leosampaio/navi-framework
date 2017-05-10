from importlib import import_module

from tinydb import TinyDB, Query, where


class Register(object):

    def __init__(self, filepath):
        self.db = TinyDB(filepath)

    def set_handler_for_intent(self, handler, intent):
        handlers_db = self.db.table('handlers')
        entry = {
            'intent': intent.__name__,
            'module': handler.__module__,
            'class': handler.__name__
        }
        handlers_db.insert(entry)

    def get_handler_for_intent(self, intent_cls):
        handlers_db = self.db.table('handlers')
        entry = handlers_db.search(where('intent') == intent_cls.__name__)

        if len(entry) > 0:
            entry = entry[0]
        else:
            return (None, None)

        return (entry['module'], entry['class'])

    def extension_set_func_for_key(self, ext_name, func, key):
        """Set a function reference on a separate extension table

        :param: ext_name - name of extension (eg.: "telegram")
        :param: func - function reference
        :param: key - database unique key
        """

        ext_db = self.db.table(ext_name)
        entry = {
            'key': key,
            'module': func.__module__,
            'func': func.__name__
        }
        ext_db.insert(entry)

    def get_extension_func_for_key(self, ext_name, key):
        ext_db = self.db.table(ext_name)
        entry = ext_db.search(where('key') == key)

        if len(entry) > 0:
            entry = entry[0]
        else:
            return (None, None)

        return (entry['module'], entry['func'])

    def get_all_extension_functions(self, ext_name):
        ext_db = self.db.table(ext_name)
        entries = ext_db.all()
        functions = [(e['key'], e['module'], e['func']) for e in entries]
        return functions

    def set_secret_for_key(self, key, value):
        ext_db = self.db.table("secrets")
        entry = {
            'key': key,
            'value': value,
        }
        ext_db.insert(entry)

    def get_secret_for_key(self, key):
        ext_db = self.db.table("secrets")
        entry = ext_db.search(where('key') == key)

        if len(entry) > 0:
            entry = entry[0]
        else:
            return None

        return entry['value']

    def clean(self):
        self.db.purge_tables()
