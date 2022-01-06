import datetime
import json
import logging
import os
import pprint
import re
import sys

import requests

import urllib3
urllib3.disable_warnings()


logging.basicConfig(level=logging.INFO)

WEB_HOST = "www.klass.ly"
API_HOST = "api2.klassroom.co"
WEB_URL = f"https://{WEB_HOST}/"
AUTH_URL = f"https://{API_HOST}/auth.basic"
CONNECT_URL = f"https://{API_HOST}/app.connect"
HISTORY_URL = f"https://{API_HOST}/klass.history"


class User:
    def __init__(self, user_data, klassroom):
        logging.debug("Users __init__")
        self.klassroom = klassroom
        self._user_data = user_data
        logging.info(f"Got {self.name}")

    @property
    def name(self):
        try:
            return self._user_data["name"]
        except KeyError:
            return None

    @property
    def id(self):
        try:
            return self._user_data["id"]
        except KeyError:
            return None

    @property
    def main_image_url(self):
        try:
            return self._user_data["main_image_url"]
        except KeyError:
            return None

    @property
    def thumb_image_url(self):
        try:
            return self._user_data["thumb_image_url"]
        except KeyError:
            return None


class Klassroom:
    def __init__(self, phone, password):
        # Initialize base properties
        logging.debug('Klassroom __init__')
        self.session = requests.session()
        self.session.proxies = None #{'http': '10.0.0.165:8080', 'https': '10.0.0.165:8080'}
        self.session.verify = False
        self.session.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:95.0) Gecko/20100101 Firefox/95.0'}
        self.web_device = None
        self.app_id = None
        self._auth_data = None
        self._klassroom_data = None
        self.users = {}
        self.klasses = {}
        self.klassroomauth = 'delete'

        # Initialize credentials
        self.phone = phone
        self.password = password

        # Initialize session
        self.frontpage()
        self.connect()
        self.authenticate()
        self.frontpage()
        self.connect()
        self.get_klasses()


    def get_users(self):
        self.users = {k: User(v, self)
                      for k, v
                      in self._klassroom_data["users"].items()}

    def get_klasses(self):
        self.klasses = {k: Klass(v, self)
                        for k, v
                        in self._klassroom_data["klasses"].items()}

    @property
    def auth_token(self):
        if self._auth_data is not None:
            return self._auth_data['auth_token']
        else:
            return 'null'

    @property
    def post_data(self):
        return {'auth_token': self.auth_token,
                'device': self.web_device,
                'app_id': self.app_id,
                'version': '4.0',
                'culture': 'fr',
                'gmt_offset': '-60',
                'tz': 'Europe/Paris',
                'dst': 'true'}

    def frontpage(self):
        logging.info(WEB_URL)
        r = self.session.get(WEB_URL)
        self.klassroomauth = re.search(r'klassroomauth=([0-9a-z]+)"', r.text).group(1)
        logging.info(f'klassroomauth : {self.klassroomauth}')
        self.web_device = self.session.cookies['klassroom_device']
        logging.info(f'Got web_device: {self.web_device}')
        bundel_url = re.search(r'js/_react/dist/bundle.*.js', r.text).group(0)
        response = self.session.get(WEB_URL + bundel_url)
        self.app_id = re.search(r'APP_ID:"([0-9a-f]+)",', response.text).group(1)
        logging.info(f'Got app_id: {self.app_id}')

        logging.info(f'{WEB_URL}_data/klassroomauth?klassroomauth={self.klassroomauth}')
        self.session.get(f'{WEB_URL}_data/klassroomauth?klassroomauth={self.klassroomauth}')


    def authenticate(self):
        logging.info('Klassroom authenticate')
        post_data = {'phone': self.phone,
                     'password': self.password}
        post_data.update(self.post_data)
        response = self.session.post(AUTH_URL, data=post_data)
        self._auth_data = response.json()
        self.session.cookies["klassroom_token"] = self.auth_token

    def connect(self):
        logging.info('Klassroom connect')
        response = self.session.post(CONNECT_URL, data=self.post_data)
        self._klassroom_data = response.json()

    
class Student:
    def __init__(self, student, klass):
        logging.debug('Student __init__')
        self.klass = klass
        self._student_data = student        

    @property
    def family(self):
        return [(v, self.klass.klassroom.users[k]) for k, v in self._student_data['members'].items()]

    @property
    def gender(self):
        try:
            return self._student_data['gender']  
        except KeyError:
            return None

    @property
    def dob(self):
        try:
            return self._student_data['dob']  
        except KeyError:
            return None

    @property
    def name(self):
        try:
            return f"{self._student_data['first_name']} {self._student_data['last_name']}"
        except KeyError:
            return None

    @property
    def main_image_url(self):
        try:
            return self._student_data["main_image_url"]
        except KeyError:
            return None

    @property
    def thumb_image_url(self):
        try:
            return self._student_data["thumb_image_url"]
        except KeyError:
            return None


class Klass:
    def __init__(self, klass, klassroom):
        # Initialize base
        logging.debug('Klass __init__')
        self.klassroom = klassroom
        self._klass_data = klass
        self.students = {}
        self.get_students()
        self.posts = {}
        self.get_post_history()
        logging.info(f'Got {self.name} {self.school_name} ({self.level})')

    def get_students(self):
        logging.info('Klass get_students')
        self.students = {k: Student(v, self)
                         for k, v
                         in self._klass_data['students'].items()}

    @property
    def school_name(self):
        try:
            return self._klass_data["school"]["name"]
        except KeyError:
            return None

    @property
    def id(self):
        try:
            return self._klass_data["id"]
        except KeyError:
            return None

    @property
    def level(self):
        try:
            return self._klass_data["level"]
        except KeyError:
            return None

    @property
    def key(self):
        try:
            return self._klass_data["key"]
        except KeyError:
            return None

    @property
    def name(self):
        try:
            return self._klass_data["natural_name"]
        except KeyError:
            return None

    @property
    def organization(self):
        try:
            return self._klass_data["organization"]
        except KeyError:
            return None

    def get_post_history(self):
        min_date = ''
        post_data = {'id': self.id,
                     'filter': 'all',
                     'type': 'post',
                     'from': '0'}
        post_data.update(self.klassroom.post_data)
        finished = False
        while not finished:
            response = self.klassroom.session.post(HISTORY_URL, data=post_data)
            try:
                min_date = min([post["date"] for post in response.json()["posts"].values()])
            except:
                break
            self.posts.update({k: Post(p, self)
                               for k, p
                               in response.json()["posts"].items()})
            logging.info(f'mindate : {min_date}')
            post_data['from'] = f'{min_date - 1}'


class Attachment:
    def __init__(self, attachment, post):
        # Initialize base
        logging.debug('Attachment __init__')
        self.post = post
        self._attachment_data = attachment




    @property
    def thumb_url(self):
        try:
            return self._attachment_data["thumb_url"]
        except KeyError:
            return None

    @property
    def url(self):
        try:
            return self._attachment_data["url"]
        except KeyError:
            return None

    @property
    def name(self):
        try:
            return self._attachment_data["name"]
        except KeyError:
            return None

    def is_image(self):
        try:
            return self._attachment_data["type"] == "image"
        except KeyError:
            return False

    def download(self):
        session = self.post.klass.klassroom.session
        filename = os.path.join(self.post.klass.name, self.post.date.strftime("%d-%m-%Y_%H-%M-%S-") + self.name)
        filefullpath = os.path.join('/mnt/KlassLy/', self.post.klass.name, self.post.date.strftime("%d-%m-%Y_%H-%M-%S-") + self.name)
        if os.path.exists(filefullpath):
            logging.info(f'Skip {filename}')
            return
        if self.url.endswith('m3u8'):
            r = session.get(self.url)
            reso_url = ""
            for line in r.content.splitlines():
                if line.endswith(b'm3u8'):
                    if not line.startswith(b'https'):
                        line = b'https://www.klass.ly/_data' + line
                    reso_url = line
            logging.info(f"reso_url : {reso_url}")
            with open(filefullpath, 'wb') as a:
                r = session.get(reso_url)
                for line in r.content.splitlines():
                    if line.endswith(b'ts'):
                        logging.info(f'Reading {line}...')
                        a.write(session.get(line).content)
            os.utime(filefullpath, (self.post.date.timestamp(), self.post.date.timestamp()))
            logging.info(f'video downloaded : {filename}')

        else:
            if 'data.klassroom.co/img/' in self.url:
                new_url = self.url.replace('https://data.klassroom.co/img/', 'https://www.klass.ly/_data/img/')
                headers = {'Host': 'www.klass.ly', 'Sec-Fetch-Dest': 'image', 'Sec-Fetch-Mode': 'no-cors', 'Sec-Fetch-Site': 'same-origin', 'Pragma': 'no-cache', 'Cache-Control': 'no-cache', 'Accept': 'image/avif,image/webp,*/*'}
                r = session.get(new_url, cookies=session.cookies.get_dict(), headers=headers) 
            else:
                try:
                    r = session.get(self.url)
                except:
                    logging.info(self._attachment_data)
                    logging.info(self.post._post_data)
                    return
            if r.status_code == 200:
                with open(filefullpath, 'wb') as a:
                    a.write(r.content)
                logging.info(f'file downloaded : {filename}')
            else:
                logging.error(f'{r.status_code} : {new_url}')



class Post:
    def __init__(self, post, klass):
        # Initialize base
        logging.debug('Post __init__')
        self.klass = klass
        self._post_data = post
        self.attachments = {}
        self.get_attachments()

    @property
    def text(self):
        try:
            return self._post_data["text"]
        except KeyError:
            return None

    @property
    def date(self):
        try:
            return datetime.datetime.fromtimestamp(self._post_data["date"] / 1000)
        except KeyError:
            return None

    def get_attachments(self):
        self.attachments = {k: Attachment(a, self)
                            for k, a 
                            in self._post_data['attachments'].items()}
      
    
if __name__ == '__main__':
    kr = Klassroom(*sys.argv[1:3])
    for klass in kr.klasses.values():
        logging.info(f'Classe : {klass.name}')
        os.makedirs(os.path.join('/mnt/KlassLy', klass.name), exist_ok=True)
        for post in klass.posts.values():
            for attachment in post.attachments.values():
                attachment.download()

