import uuid
import json

import requests

from hstest import FlaskTest, dynamic_test, wrong, correct, SQLTest, StageTest


class ServerTest(FlaskTest):
    use_database = False
    source = 'task'
    existing_user = f"{uuid.uuid4()}@mail.ru"

    @dynamic_test
    def test_register_201(self):
        hw = requests.post(self.get_url('/users'), json={
            "email": f"{self.existing_user}",
            "password": "132"
        })

        try:
            json.loads(hw.content)
        except Exception:
            return wrong(f'Response for {hw.request} on {hw.url} should be in json format')

        if hw.status_code != 201:
            return wrong('Response code of successful POST method should be 201')

        if 'message' not in hw.json():
            return wrong('Register endpoint should return "message" field about successful user registration')

        return correct()

    @dynamic_test
    def test_register_duplicate_email_400(self):
        self.duplicate_user = f"{uuid.uuid4()}@mail.ru"
        hw = requests.post(self.get_url('/users'), json={
            "email": f"{self.duplicate_user}",
            "password": "132"
        })
        hw = requests.post(self.get_url('/users'), json={
            "email": f"{self.duplicate_user}",
            "password": "132"
        })

        try:
            json.loads(hw.content)
        except Exception:
            return wrong(f'Response for {hw.request} on {hw.url} should be in json format')

        if hw.status_code != 400:
            return wrong('Response code of unsuccessful POST method in cause of wring input should be 400')

        if 'error' not in hw.json():
            return wrong('Register endpoint should return "error" field in case of unsuccessful user registration')

        if hw.json().get('error').lower() != 'email address is already in use':
            return wrong("Register endpoint should return an error message 'email address is already in use'")

        return correct()

    @dynamic_test
    def test_login_200(self):
        hw = requests.post(self.get_url('/login'), json={
            "email": f"{self.existing_user}",
            "password": "132"
        })

        try:
            json.loads(hw.content)
        except Exception:
            return wrong(f'Response for {hw.request} on {hw.url} should be in json format')

        if hw.status_code != 200:
            return wrong('Response code of successful login method should be 200')

        if 'access_token' not in hw.json():
            return wrong('Login endpoint should return "access_token" field with jwt token')

        return correct()

    @dynamic_test
    def test_login_wrong_password_401(self):
        hw = requests.post(self.get_url('/login'), json={
            "email": f"{self.existing_user}",
            "password": "1322"
        })

        try:
            json.loads(hw.content)
        except Exception:
            return wrong(f'Response for {hw.request} on {hw.url} should be in json format')

        if hw.status_code != 401:
            return wrong('Response code of successful login method should be 401')

        if 'error' not in hw.json():
            return wrong('Login endpoint should return "error" field with error description')

        if 'wrong' not in hw.json().get('error').lower():
            return wrong('An "error" field should contain message about wrong email password combination')

        return correct()

    @dynamic_test
    def test_login_no_such_email_400(self):
        hw = requests.post(self.get_url('/login'), json={
            "email": f"{uuid.uuid4()}",
            "password": "132"
        })

        try:
            json.loads(hw.content)
        except Exception:
            return wrong(f'Response for {hw.request} on {hw.url} should be in json format')

        if hw.status_code != 400:
            return wrong('Response code of successful login method should be 400')

        if 'error' not in hw.json():
            return wrong('Login endpoint should return "error" field with error description')

        if 'exist' not in hw.json().get('error').lower():
            return wrong('An "error" field should contain message about non existing user with such an email')

        return correct()

    @dynamic_test
    def test_current_200(self):
        hw = requests.post(self.get_url('/login'), json={
            "email": f"{self.existing_user}",
            "password": "132"
        })

        token = hw.json().get('access_token')

        hw = requests.get(self.get_url('/current'), headers={'Authorization': f'Bearer {token}'})

        try:
            json.loads(hw.content)
        except Exception:
            return wrong(f'Response for {hw.request} on {hw.url} should be in json format')

        if hw.status_code == 422:
            return wrong('Check "access_token" field of "/login" endpoint. It should be a valid JWT token')

        if hw.status_code != 200:
            return wrong('Response code of successful GET method should be 200')

        if 'current_user_email' not in hw.json():
            return wrong('Current endpoint should return "current_user_email" field with token\'s user owner')

        return correct()

    @dynamic_test
    def test_current_422(self):
        hw = requests.post(self.get_url('/login'), json={
            "email": f"{self.existing_user}",
            "password": "132"
        })

        token = hw.json().get('access_token')

        hw = requests.get(self.get_url('/current'), headers={'Authorization': f'Bearer {token + "1"}'})
        try:
            json.loads(hw.content)
        except Exception:
            return wrong(f'Response for {hw.request} on {hw.url} should be in json format')

        if hw.status_code != 422:
            return wrong(
                'Response code of unsuccessful request of endpoint which require authorization method should be 422'
            )

        return correct()
