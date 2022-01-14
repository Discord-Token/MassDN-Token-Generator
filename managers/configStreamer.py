import json 

config = json.loads(open("data/config.json", "r").read())

def getValue(key):
    return config.get(key)
