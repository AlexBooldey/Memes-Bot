import json
import sys


def load_file(filename):
    try:
        with open(filename) as json_data_file:
            file_data = json.load(json_data_file)
        json_data_file.close()
    except FileNotFoundError as e:
        print(e)
        sys.exit(0)
    return file_data


class Post:
    def __init__(self, media):
        self.media = media
        self.description = None
