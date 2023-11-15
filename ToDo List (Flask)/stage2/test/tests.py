import json
from requests import Response
import requests

from hstest import FlaskTest, dynamic_test, wrong, correct


class ServerTest(FlaskTest):
    use_database = False
    source = 'task'

    @dynamic_test
    def test_get_list_200(self):
        hw = requests.get(self.get_url('/tasks'))
        try:
            json.loads(hw.content)
        except Exception:
            return wrong(f'Response should be in json format')

        if hw.status_code != 200:
            return wrong('Response code of successfully GET method should be 200')

        if 'todo_list' not in hw.json():
            return wrong('Response object should contain todo_list key')

        return correct()

    @dynamic_test
    def test_post_201(self):
        hw: Response = requests.post(self.get_url('/tasks'), json=dict(
            title='title',
            description='descr',
            deadline_time='2001-01-01 12:00:00',
            is_completed=False
        ))

        try:
            json.loads(hw.content)
        except Exception:
            return wrong(f'Response should be in json format')

        if hw.status_code != 201:
            return wrong('Response code of successfully POST method should be 201')

        if 'created_id' not in hw.json():
            return wrong('Response body should contain id of created element in created_id files')

        return correct()

    @dynamic_test
    def test_post_422(self):
        hw: Response = requests.post(self.get_url('/tasks'), json=dict(name='1'))

        try:
            json.loads(hw.content)
        except Exception:
            return wrong(f'Response should be in json format')

        if hw.status_code != 422:
            return wrong('Response code of wrong schema for POST method should be 422')

        return correct()

    @dynamic_test
    def test_get_2_objects_200(self):
        hw: Response = requests.get(self.get_url('/tasks'))
        length_before = len(hw.json().get('todo_list'))

        requests.post(
            self.get_url('/tasks'),
            json=dict(
                title='title',
                description='descr',
                deadline_time='2001-01-01 12:00:00',
                is_completed=False
            )
        )

        hw: Response = requests.get(self.get_url('/tasks'))
        print('hw.json()', hw.json())
        try:
            json.loads(hw.content)
        except Exception:
            return wrong(f'Response should be in json format')

        if hw.status_code != 200:
            return wrong('Response code of successfully GET method should be 200')

        if 'todo_list' not in hw.json():
            return wrong('Response object should contain todo_list key')
        if len(hw.json().get('todo_list')) - length_before != 1:
            return wrong('POST method should add entries unconditionally')

        return correct()
