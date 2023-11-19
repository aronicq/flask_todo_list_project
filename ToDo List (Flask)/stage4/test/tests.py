import uuid
import json

import requests
from requests import Response

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
            return wrong(f'Response should be in json format')

        if hw.status_code != 201:
            return wrong('Response code of successful POST method should be 201')

        if 'message' not in hw.json():
            return wrong('Register endpoint should return "message" field about successful user registration')

        return correct()

    @dynamic_test
    def test_post_list_201(self):
        hw = requests.post(self.get_url('/login'), json={
            "email": f"{self.existing_user}",
            "password": "132"
        })

        token = hw.json().get('access_token')
        headers = {'Authorization': f'Bearer {token}'}

        hw: Response = requests.post(
            self.get_url('/lists'),
            json={
                "list": [
                    dict(
                        title='title',
                        description='descr',
                        deadline_time='2001-01-01 12:00:00',
                        is_completed=False
                    ),
                    dict(
                        title='title',
                        description='descr',
                        deadline_time='2001-01-01 12:00:00',
                        is_completed=False
                    ),
                    dict(
                        title='title',
                        description='descr',
                        deadline_time='2001-01-01 12:00:00',
                        is_completed=False
                    )
                ]
            },
            headers=headers,
        )
        try:
            json.loads(hw.content)
        except Exception:
            return wrong(f'Response should be in json format')

        if hw.status_code != 201:
            return wrong('Response code of successful POST method should be 201')

        if 'created_list_id' not in hw.json():
            return wrong('Response body should contain id of created element in created_id files')

        return correct()

    @dynamic_test
    def test_get_list_200(self):
        hw = requests.post(self.get_url('/login'), json={
            "email": f"{self.existing_user}",
            "password": "132"
        })

        token = hw.json().get('access_token')
        headers = {'Authorization': f'Bearer {token}'}

        hw: Response = requests.post(
            self.get_url('/lists'),
            json={
                "list": [
                    dict(
                        title='title',
                        description='descr',
                        deadline_time='2001-01-01 12:00:00',
                        is_completed=False
                    )
                ]
            },
            headers=headers,
        )
        created_list_id = hw.json().get('created_list_id')

        hw = requests.get(self.get_url(f'/lists/{created_list_id}'), headers=headers)

        if len(hw.json().get('todo_list')) != 1:
            return wrong('Number of created elements in list is not correct')

        return correct()

    @dynamic_test
    def test_get_list_401(self):
        hw = requests.post(self.get_url('/login'), json={
            "email": f"{self.existing_user}",
            "password": "132"
        })

        token = hw.json().get('access_token')
        headers = {'Authorization': f'Bearer {token}'}

        hw: Response = requests.post(
            self.get_url('/lists'),
            json={
                "list": [
                    dict(
                        title='title',
                        description='descr',
                        deadline_time='2001-01-01 12:00:00',
                        is_completed=False
                    )
                ]
            },
            headers=headers,
        )
        created_list_id = hw.json().get('created_list_id')
        new_user = f"{uuid.uuid4()}@mail.com"
        hw = requests.post(self.get_url('/users'), json={
            "email": new_user,
            "password": "132"
        })
        hw = requests.post(self.get_url('/login'), json={
            "email": new_user,
            "password": "132"
        })
        token = hw.json().get('access_token')
        headers = {'Authorization': f'Bearer {token}'}

        hw = requests.get(self.get_url(f'/lists/{created_list_id}'), headers=headers)
        if hw.status_code != 401:
            return wrong('lists created by one user should no be accessible by others')

        return correct()

    @dynamic_test
    def test_post_append_201(self):
        hw = requests.post(self.get_url('/login'), json={
            "email": f"{self.existing_user}",
            "password": "132"
        })

        token = hw.json().get('access_token')
        headers = {'Authorization': f'Bearer {token}'}

        hw: Response = requests.post(
            self.get_url('/lists'),
            json={
                "list": [
                    dict(
                        title='title',
                        description='descr',
                        deadline_time='2001-01-01 12:00:00',
                        is_completed=False
                    )
                ]
            },
            headers=headers,
        )
        print('hw.json()', hw.json())
        created_list_id = hw.json().get('created_list_id')
        hw = requests.get(self.get_url(f'/lists/{created_list_id}'), headers=headers)

        if len(hw.json().get('todo_list')) != 1:
            return wrong('Wrong list length')

        hw: Response = requests.post(
            self.get_url('/lists'),
            json={
                "list": [
                    dict(
                        title='title',
                        description='descr',
                        deadline_time='2001-01-01 12:00:00',
                        is_completed=False
                    ),
                    dict(
                        title='title',
                        description='descr',
                        deadline_time='2001-01-01 12:00:00',
                        is_completed=False
                    ),
                    dict(
                        title='title',
                        description='descr',
                        deadline_time='2001-01-01 12:00:00',
                        is_completed=False
                    )
                ],
                "list_id": created_list_id
            },
            headers=headers,
        )
        print('hw.json() 2', hw.json())
        created_list_id = hw.json().get('created_list_id')
        hw = requests.get(self.get_url(f'/lists/{created_list_id}'), headers=headers)

        if len(hw.json().get('todo_list')) != 4:
            return wrong('Wrong list length')
        return correct()

