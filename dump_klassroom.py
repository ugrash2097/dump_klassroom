import requests
import logging
import pprint
import sys
import re


logging.basicConfig(level=logging.INFO)


class Student:
    def __init__(self, student, users):
        logging.info('Student __init__')
        self.first_name = student['first_name']
        self.last_name = student['last_name']
        self.family = ', '.join([f'{v}: {users[k]["name"]}' for k, v in student['members'].items()])
    
    def __str__(self):
        return f'{self.first_name} {self.last_name} ({self.family})'


class Klass:
    def __init__(self, klass, users):
        logging.info('Klass __init__')
        self.created_at = klass['created_at']
        self.id = klass['id']
        self.level = klass['level']
        self.name = klass['natural_name']
        self.school = klass['school']['name']
        self.students = [Student(s, users) for s in klass['students'].values()]

    def __str__(self):
        students_list = "\n".join([str(s) for s in self.students])
        return f'{self.name} {self.school} ({self.level})\n{students_list}'


class KlassRoom:
    def __init__(self):
        logging.info('__init__')
        self.web_url = "web.klassroom.fr"
        self.api_url = "api2.klassroom.co"
        self.session = requests.session()
        self.web_device = None
        self.app_id = None
        self.auth_token = 'null'
        self.users = {}
        self.klasses = {}

    def post_data(self):
        return {'auth_token': self.auth_token,
                'device': self.web_device,
                'app_id': self.app_id,
                'version': '4.0',
                'culture': 'fr',
                'gmt_offset': '-120',
                'tz': 'Europe/Paris',
                'dst': 'true'}

    def init_klassroom_session(self):
        logging.info('init_klassroom_session')
        response = self.session.get(f'https://{self.web_url}/')
        self.web_device = self.session.cookies['klassroom_device']
        self.app_id = re.search(r'api_key:"([0-9a-f]+)",', response.text).group(1)
        logging.info(f'web_device: {self.web_device}')
        logging.info(f'app_id: {self.app_id}')

    def app_connect(self):
        post_data = self.post_data()
        response = self.session.post(f'https://{self.api_url}/app.connect',
                                     data=post_data)
        if 'klasses' in response.json():
            self.klasses = response.json()['klasses']
            self.users = response.json()['users']

    def auth(self, phone, password):
        post_data = {'phone': phone,
                     'password': password}
        post_data.update(self.post_data())
        response = self.session.post(f'https://{self.api_url}/auth.basic',
                                     data=post_data)
        self.auth_token = response.json()['auth_token']


if __name__ == '__main__':
    kr = KlassRoom()
    kr.init_klassroom_session()
    kr.app_connect()
    kr.auth(*sys.argv[1:3])
    kr.app_connect()
    for klass_key, klass in kr.klasses.items():
        kklass = Klass(klass, kr.users)
        print(kklass)
