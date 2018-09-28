import json
import os
import random

import requests
from bs4 import BeautifulSoup

from constants import *
from util import load_file

path = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))


class InstagramParser:

    def __init__(self):
        self.__devices = load_file(path + '/devices.json')

    @staticmethod
    def __parse_json(html):
        soup = BeautifulSoup(html.text, 'html.parser')
        body = soup.find('body')

        script_tag = body.find('script')
        raw_string = script_tag.text.strip().replace('window._sharedData =', '').replace(';', '')

        json_text = json.loads(raw_string)
        try:
            root = json_text['entry_data']['PostPage'][0]['graphql']['shortcode_media']

            typename = root['__typename']

            if typename == type_image:
                return InstagramParser.__image_create(root)

            elif typename == type_video:
                return InstagramParser.__video_create(root)

            elif typename == type_sidecar:
                raw_content = root['edge_sidecar_to_children']['edges']
                content = list()
                for media in raw_content:
                    root_node = media['node']
                    typename = root_node['__typename']
                    if typename == type_image:
                        content.append(InstagramParser.__image_create(root_node))
                    elif typename == type_video:
                        content.append(InstagramParser.__video_create(root_node))
                    else:
                        continue
                return content
        except KeyError:
            if json_text['entry_data']['ProfilePage']:
                return None

    @staticmethod
    def __video_create(raw_video):
        raw_video = raw_video['video_url']
        return Media(raw_video, type_video, 0, 0)

    @staticmethod
    def __image_create(raw_image):
        raw_images = raw_image['display_resources']
        list_images_source = list(
            Media(
                image['src'], type_image,
                image['config_width'],
                image['config_height']) for image in raw_images)
        ready_image_source = max(list_images_source, key=lambda x: x.size)
        return ready_image_source

    def get_content_by_url(self, src):
        session = requests.session()
        agent = random.choice(self.__devices)
        html = session.get(src, allow_redirects=True, timeout=20, headers={'User-Agent': agent})
        return InstagramParser.__parse_json(html)


class Media:
    def __init__(self, src, type_content, config_width, config_height):
        self.src = src
        self.config_width = config_width
        self.config_height = config_height
        self.size = config_height + config_width
        self.type_content = type_content


i = InstagramParser()
i.get_content_by_url('https://www.instagram.com/p/BoKCOvmAWuY/?hl=ru')
