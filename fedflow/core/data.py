
__all__ = [
    "FedData"
]

import json
import os


class FedData(object):

    def __init__(self, name):
        super(FedData, self).__init__()
        self.name = name
        self.files = {}
        self.attrs = {}

    def save(self, path):
        os.makedirs(path)
        with open(os.path.join(path, "attrs.json"), "w") as f:
            f.write(json.dumps(self.attrs, indent=4))
        self.__save_file(self.files, path)

    @classmethod
    def load(cls, path):
        if not os.path.exists(path):
            raise ValueError(f"{path} not exists")
        fd = FedData()
        with open(os.path.join(path, "attrs.json"), "r") as f:
            fd.attrs = json.loads(f.read())
        cls.__load_file(fd.files, path)
        return fd

    @classmethod
    def __save_file(cls, file_dict, path):
        for k, v in file_dict.items():
            if isinstance(v, dict):
                cls.__save_file(v, os.path.join(k))
            elif isinstance(v, bytes):
                with open(os.path.join(path, k), "wb") as f:
                    f.write(v)
            else:
                raise ValueError(f"Error data type")

    @classmethod
    def __load_file(cls, file_dict, path):
        for name in os.listdir(path):
            _path = os.path.join(path, name)
            if os.path.isdir(_path):
                file_dict[name] = {}
                cls.__load_file(file_dict[name], _path)
            else:
                with open(_path, "rb") as f:
                    data = f.read()
                file_dict[name] = data
