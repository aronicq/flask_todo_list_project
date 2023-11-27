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
    def test_get_list_403(self):
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
        if hw.status_code != 403:
            return wrong('lists created by one user should no be accessible by others')

        if 'error' not in hw.json():
            return wrong('Response object should contain "error" key if endpoint not permitted')

        if hw.json().get('error').lower() != 'no access':
            return wrong("Response message for non-accessible endpoint should be 'no access'")

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
        created_list_id = hw.json().get('created_list_id')
        hw = requests.get(self.get_url(f'/lists/{created_list_id}'), headers=headers)

        if len(hw.json().get('todo_list')) != 4:
            return wrong('Wrong list length')
        return correct()

    @dynamic_test
    def test_delete_list_200(self):
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
        created_list_id = hw.json().get('created_list_id')

        hw = requests.get(self.get_url(f'/lists/{created_list_id}'), headers=headers)
        task_id = hw.json().get('todo_list')[0].get('id')

        hw: Response = requests.delete(self.get_url(f'/tasks?task_id={task_id}'), headers=headers)
        print(hw.json())
        try:
            json.loads(hw.content)
        except Exception:
            return wrong(f'Response should be in json format')

        if hw.status_code != 200:
            return wrong('Response code of successful DELETE method should be 200')

        if 'task_id' not in hw.json():
            return wrong('Response object for successfully DELETE should contain task_id of deleted task')

        hw = requests.get(self.get_url(f'/tasks/{task_id}'), headers=headers)

        try:
            json.loads(hw.content)
        except Exception:
            return wrong(f'Response should be in json format')

        if hw.status_code != 403:
            return wrong('Response code of successful POST method should be 201')

        if 'error' not in hw.json():
            return wrong('Response object should contain "error" key if requested task is accessible')

        if hw.json().get('error').lower() != 'no access':
            return wrong("Response message on trying to GET the deleted task should be 'no access'")

        return correct()

    @dynamic_test
    def test_delete_list_422(self):
        hw = requests.post(self.get_url('/login'), json={
            "email": f"{self.existing_user}",
            "password": "132"
        })

        token = hw.json().get('access_token')
        headers = {'Authorization': f'Bearer {token}'}

        hw: Response = requests.delete(self.get_url(f'/tasks'), headers=headers)
        try:
            json.loads(hw.content)
        except Exception:
            return wrong(f'Response should be in json format')

        if hw.status_code != 422:
            return wrong('Response code of DELETE method with no passed task_id should be 422')

        if 'error' not in hw.json():
            return wrong('Response object should contain "error" key if no id is passed')

        if hw.json().get('error').lower() != 'no task_id param passed':
            return wrong("Response message on trying to DELETE without task_id 'no task_id param passed'")

        return correct()

    @dynamic_test
    def test_delete_list_403(self):
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
        task_id = hw.json().get('todo_list')[0].get('id')

        hw: Response = requests.delete(self.get_url(f'/tasks?task_id={task_id + 1}'), headers=headers)
        print(hw.json())
        try:
            json.loads(hw.content)
        except Exception:
            return wrong(f'Response should be in json format')

        if hw.status_code != 403:
            return wrong('Response code of successful DELETE method should be 200')

        if 'error' not in hw.json():
            return wrong('Response object should contain "error" key if task is not accessible')

        if hw.json().get('error').lower() != 'no access':
            return wrong("Response message for non-accessible task_id should be 'no access'")

        return correct()
