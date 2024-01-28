import json


def singleton(class_):
    instances = {}

    def getinstance(*args, **kwargs):
        if class_ not in instances:
            instances[class_] = class_(*args, **kwargs)
        return instances[class_]
    return getinstance


@singleton
class Config:
    def __init__(self):
        with open('config.json') as f:
            self.data = json.load(f)

    def get(self, section):
        return self.data[section]
