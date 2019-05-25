import os
from pyndn import Name
from typing import Union
try:
    import rocksdb
except ImportError:
    import pyrocksdb as rocksdb


class IStorage:
    def put(self, name, data):
        # type: (Union[Name, str, bytes], bytes) -> None
        """
        Put data into storage.
        :param name: Name of data.
        :param data: Data.
        """
        pass

    def get(self, name):
        # type: (Union[Name, str, bytes]) -> bytes
        """
        Get data from storage.
        Return None if not exists.
        :param name: Name of data.
        :return Data or None.
        """
        pass

    def delete(self, name):
        # type: (Union[Name, str, bytes]) -> None
        """
        Delete specified data.
        :param name: Name of data.
        """
        pass

    def exists(self, name):
        # type: (Union[Name, str, bytes]) -> bool
        """
        Tell whether specified data exist in storage.
        :param name: Name of data.
        :return: If exist or not.
        """
        pass

    def append(self, name, data):
        # type: (Union[Name, str, bytes], bytes) -> None
        """
        Append data to the end of existing data.
        Create a new item if not existing.
        :param name: Name of data.
        :param data: Data to append.
        """
        pass

    def enum(self, prefix):
        """
        Enumerate all data under prefix.
        :param prefix: Prefix of names.
        :return: An iterator used to enumerate.
        """
        pass


class RocksdbStorage(IStorage):
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
        name = self.convert_name(name)
        self.db.put(name, data)

    def get(self, name):
        name = self.convert_name(name)
        return self.db.get(name)

    def delete(self, name):
        name = self.convert_name(name)
        self.db.delete(name)

    def exists(self, name):
        return self.get(name) is not None

    def append(self, name, data):
        name = self.convert_name(name)
        self.db.put(name, self.db.get(name) + data)

    class Iter:
        def __init__(self, prefix, impl):
            self.prefix = prefix
            if isinstance(self.prefix, bytes):
                self.prefix = self.prefix.decode("utf-8")
            if isinstance(self.prefix, str):
                self.prefix = Name(self.prefix)
            self.impl = impl

        def __next__(self):
            ret = next(self.impl)
            name = Name(ret.decode("utf-8"))
            if not self.prefix.isPrefixOf(name):
                raise StopIteration

    def enum(self, prefix):
        prefix_bytes = self.convert_name(prefix)
        it = self.db.iterkeys()
        it.seek(prefix_bytes)
        return self.Iter(prefix, it)


class RocksdbStorageV2(IStorage):
    def __init__(self, filename="server_cache.db"):
        self.db = rocksdb.DB()
        options = rocksdb.Options()
        options.create_if_missing = True
        self.db.open(options, filename)

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
        name = self.convert_name(name)
        self.db.put(rocksdb.WriteOptions(), name, data)

    def get(self, name):
        name = self.convert_name(name)
        blob = self.db.get(rocksdb.ReadOptions(), name)
        if blob.status.ok():
            return blob.data
        else:
            return None

    def delete(self, name):
        name = self.convert_name(name)
        self.db.delete(rocksdb.WriteOptions(), name)

    def exists(self, name):
        return self.get(name) is not None

    def append(self, name, data):
        name = self.convert_name(name)
        self.db.put(rocksdb.WriteOptions(), name, self.db.get(name) + data)

    class Iter:
        def __init__(self, prefix, impl):
            self.prefix = prefix
            if isinstance(self.prefix, bytes):
                self.prefix = self.prefix.decode("utf-8")
            if isinstance(self.prefix, str):
                self.prefix = Name(self.prefix)
            self.impl = impl

        def __next__(self):
            ret = next(self.impl)
            name = Name(ret.decode("utf-8"))
            if not self.prefix.isPrefixOf(name):
                raise StopIteration

    def enum(self, prefix):
        raise NotImplementedError


class FilesysStorage(IStorage):
    def __init__(self, dirname="server_cache"):
        self.dir = dirname
        os.makedirs(self.dir, exist_ok=True)

    def convert_name(self, name):
        if isinstance(name, Name):
            name = name.toUri()
        elif isinstance(name, bytes):
            name = name.decode("utf-8")
        elif not isinstance(name, str):
            raise TypeError
        if name[0] == "/":
            name = name[1:]
        if name[0] == "/" or name.find(".") >= 0:
            raise ValueError
        return os.path.join(self.dir, name)

    def put(self, name, data):
        name = self.convert_name(name)
        os.makedirs(os.path.dirname(name), exist_ok=True)
        with open(name, "wb") as f:
            f.write(data)

    def get(self, name):
        name = self.convert_name(name)
        if not os.path.exists(name):
            return None
        with open(name, "rb") as f:
            ret = f.read()
        return ret

    def delete(self, name):
        raise NotImplementedError

    def exists(self, name):
        name = self.convert_name(name)
        return os.path.exists(name)

    def append(self, name, data):
        name = self.convert_name(name)
        os.makedirs(os.path.dirname(name), exist_ok=True)
        with open(name, "ab") as f:
            f.write(data)

    def enum(self, prefix):
        raise NotImplementedError
