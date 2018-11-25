import rocksdb
from pyndn import Name


class Storage:
    def __init__(self, filename="server_cache.db"):
        self.db = rocksdb.DB(filename, rocksdb.Options(create_if_missing=True))

    @staticmethod
    def convert_name(name):
        if isinstance(name, Name):
            name = name.toUri()
        if isinstance(name, str):
            name = bytes(name, "utf-8")
        if not isinstance(name, bytes):
            raise TypeError
        return name

    def put(self, name, data):
        name = Storage.convert_name(name)
        self.db.put(name, data)

    def get(self, name):
        # Return None if not exists
        name = Storage.convert_name(name)
        return self.db.get(name)

    def delete(self, name):
        name = Storage.convert_name(name)
        self.db.delete(name)

    def exists(self, name):
        return self.get(name) is not None

    def append(self, name, data):
        name = Storage.convert_name(name)
        self.db.put(name, self.db.get(name) + data)
