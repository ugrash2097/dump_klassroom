import requests
import logging
import pprint
import json
import sys
import re
import os


logging.basicConfig(level=logging.INFO)

WEB_HOST = "web.klassroom.fr"
API_HOST = "api2.klassroom.co"
WEB_URL = f"https://{WEB_HOST}/"
AUTH_URL = f"https://{API_HOST}/auth.basic"
CONNECT_URL = f"https://{API_HOST}/app.connect"


class User:
    def __init__(self, user_data, klassroom):
        logging.debug("Users __init__")
        self.klassroom = klassroom
        self._user_data = user_data
        logging.debug(f"Got {self.name}")

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


class Klassroom:
    def __init__(self, phone, password):
        # Initialize base properties
        logging.debug('Klassroom __init__')
        self.session = requests.session()
        self.web_device = None
        self.app_id = None
        self._auth_data = None
        self._klassroom_data = None
        self.users = {}
        self.klasses = {}

        # Initialize credentials
        self.phone = phone
        self.password = password

        # Initialize session
        self.init_session()
        self.authenticate()
        self.connect()
        self.get_users()
        self.get_klasses()


    def get_users(self):
        self.users = {k: User(v, self) for k, v in self._klassroom_data["users"].items()}

    def get_klasses(self):
        self.klasses = {k: Klass(v, self) for k, v in self._klassroom_data["klasses"].items()}

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
                'gmt_offset': '-120',
                'tz': 'Europe/Paris',
                'dst': 'true'}

    def init_session(self):
        logging.debug('Klassroom init_session')
        response = self.session.get(WEB_URL)
        self.web_device = self.session.cookies['klassroom_device']
        logging.debug(f'Got web_device: {self.web_device}')
        self.app_id = re.search(r'api_key:"([0-9a-f]+)",', response.text).group(1)
        logging.debug(f'Got app_id: {self.app_id}')

    def authenticate(self):
        logging.debug('Klassroom authenticate')
        post_data = {'phone': self.phone,
                     'password': self.password}
        post_data.update(self.post_data)
        response = self.session.post(AUTH_URL, data=post_data)
        self._auth_data = response.json()

    def connect(self):
        logging.debug('Klassroom connect')
        response = self.session.post(CONNECT_URL, data=self.post_data)
        self._klassroom_data = response.json()

    def pretty_print(self):
        print 

    
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

class Klass:
    def __init__(self, klass, klassroom):
        # Initialize base
        logging.debug('Klass __init__')
        self.klassroom = klassroom
        self._klass_data = klass
        self.students = {}
        self.get_students()
        logging.debug(f'Got {self.name} {self.school_name} ({self.level})')

    def get_students(self):
        logging.debug('Klass get_students')
        self.students = {k: Student(v, self) for k, v in self._klass_data['students'].items()}

    @property
    def school_name(self):
        try:
            return self._klass_data["school"]["name"]
        except KeyError:
            return None

    @property
    def level(self):
        try:
            return self._klass_data["level"]
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

    
if __name__ == '__main__':
    kr = Klassroom(*sys.argv[1:3])
    print(f'Web Device: {kr.web_device}')
    print(f'AppId: {kr.app_id}')
    print('\nUsers:\n------')
    for user in kr.users.values():
        print(user.name)
    print('\nKlasses:\n--------')
    for klass in kr.klasses.values():
        print(f'\n{klass.name} {klass.organization} ({klass.level})')
        for student in klass.students.values():
            print(f'- {student.name} ({student.gender} / {student.dob})')
            for link, member in student.family:
                print(f'    {link}: {member.name}')

    # def __getattr__(self, name):
    #     try:
    #         return self._klass_data[name]
    #     except KeyError:
    #         raise AttributeError



# def get_post_history(self):
#     post_data = {'id': self.id,
#                     'filter': 'all',
#                     'type': 'post',
#                     'from': '0'}
#     print(post_data)
#     post_data.update(self.klassroom.post_data())
#     response = self.klassroom.session.post(f'https://{self.klassroom.api_url}/klass.history',
#                                             data=post_data)
#     self.posts = response.json()
#     with open(f'history_{self.id}.json', 'w') as f:
#         json.dump(response.json(), f, indent=2)
    

# def __str__(self):
#     students_list = "\n".join([str(s) for s in self.students])
#     return f'{self.name} {self.school} ({self.level})\n{students_list}'
    # for key, post in kklass.posts['posts'].items():
    #     logging.debug(f'Post {key}')
    #     try:
    #         os.mkdir(f'{klass_key}/{key}')
    #     except:
    #         pass
    #     with open(f'{klass_key}/{key}/index.html', 'w') as f:
    #         f.write(post['text'])
    #     for attachment in post['attachments'].values():
    #         r = kr.session.get(attachment['url'], stream=True)
    #         logging.debug(f'Downloading {klass_key}/{key}/{attachment["name"]}')
    #         with open(f'{klass_key}/{key}/{attachment["name"]}', 'w') as a:
    #             for chunk in r.iter_content(chunk_size=8096):
    #                 a.write(chunk)
            
