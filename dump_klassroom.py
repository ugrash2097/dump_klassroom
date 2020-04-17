import requests
import logging
import sys
import re


logging.basicConfig(level=logging.INFO)


class KlassRoom:
    def __init__(self):
        logging.info('__init__')
        self.web_url = "web.klassroom.fr"
        self.api_url = "api2.klassroom.co"
        self.session = requests.session()
        self.web_device = None
        self.app_id = None
        self.auth_token = 'null'

    def post_data(self):
        return {'device': self.web_device,
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
        post_data = {'auth_token': self.auth_token}
        post_data.update(self.post_data())
        response = self.session.post(f'https://{self.api_url}/app.connect',
                                     data=post_data)
        return response.json()

    def auth(self, phone, password):
        post_data = {'phone': phone,
                     'password': password,
                     'auth_token': self.auth_token}
        post_data.update(self.post_data())
        response = self.session.post(f'https://{self.api_url}/auth.basic',
                                     data=post_data)
        return response.json()


if __name__ == '__main__':
    kr = KlassRoom()
    kr.init_klassroom_session()
    print(kr.app_connect())
    print(kr.auth(*sys.argv[1:3]))
    print(kr.app_connect())
