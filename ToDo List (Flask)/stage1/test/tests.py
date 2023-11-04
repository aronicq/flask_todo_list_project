import json
from requests import Response
import requests

from hstest import FlaskTest, dynamic_test, wrong, correct


class ServerTest(FlaskTest):
    use_database = False
    source = 'task'

    @dynamic_test
    def test_get_list_200(self):
        hw = requests.get(self.get_url('/'))
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
    def test_get_non_exiting_error(self):
        hw = requests.get(self.get_url('/1'))
        try:
            json.loads(hw.content)
        except Exception:
            return wrong(f'Response should be in json format')

        if hw.status_code != 200:
            return wrong('Response code of successfully GET method should be 200')

        if 'error' not in hw.json():
            return wrong('Response object should contain "error" key if requested index is not found')

        return correct()

    @dynamic_test
    def test_post_201(self):
        hw: Response = requests.post(self.get_url('/'), json={'name': 'task 1', 'time': '1h'})

        try:
            json.loads(hw.content)
        except Exception:
            return wrong(f'Response should be in json format')

        if hw.status_code != 201:
            return wrong('Response code of successfully POST method should be 201')

        if 'todo_list_length' not in hw.json():
            return wrong('Response object should contain "todo_list_length" key')
        if hw.json().get('todo_list_length') != 1:
            return wrong('Response should contain correct information about TODO list length')

        return correct()

    @dynamic_test
    def test_get_2_objects_200(self):
        requests.post(self.get_url('/'), json={'name': 'task 2', 'time': '3h'})

        hw: Response = requests.get(self.get_url('/'))
        try:
            json.loads(hw.content)
        except Exception:
            return wrong(f'Response should be in json format')

        if hw.status_code != 200:
            return wrong('Response code of successfully GET method should be 200')

        if 'todo_list' not in hw.json():
            return wrong('Response object should contain todo_list key')

        if len(hw.json().get('todo_list')) != 2:
            return wrong('Response should contain all TODO list entries')

        return correct()
