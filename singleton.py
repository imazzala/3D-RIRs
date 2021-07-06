import numpy as np

class Singleton:
    _shared_state = {}

    def __init__(self):
        self.__dict__ = self._shared_state


class Database(Singleton):

    def __init__(self):
        Singleton.__init__(self)

    def get(self):
        return self._data

    def change(self, data):
        self.load(data)

    def hasData(self):
        return hasattr(self, "_data")

    def load(self, data):
        self._data = data
        