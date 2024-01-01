import json
from requests import Response
import requests

from hstest import FlaskTest, dynamic_test, wrong, correct


class ServerTest(FlaskTest):
    use_database = False
    source = 'task'

    @dynamic_test
    def test_get_empty_list_200(self):
        hw = requests.get(self.get_url('/tasks'))
        try:
            json.loads(hw.content)
        except Exception:
            return wrong(f'Response for {hw.request} on {hw.url} should be in json format')

        if hw.status_code != 200:
            return wrong('Response code of successful GET method should be 200')

        if 'todo_list' not in hw.json():
            return wrong('Response object should contain todo_list key')

        if len(hw.json().get('todo_list')) != 0:
            return wrong('Response object should contain empty todo_list before any tasks are created')

        return correct()

    @dynamic_test
    def test_get_non_exiting_error(self):
        hw = requests.get(self.get_url('/tasks/1'))
        try:
            json.loads(hw.content)
        except Exception:
            return wrong(f'Response for {hw.request} on {hw.url} should be in json format')

        if hw.status_code != 404:
            return wrong('Response code of successful GET method should be 200')

        if 'error' not in hw.json():
            return wrong('Response object should contain "error" key if requested index is not found')

        if hw.json().get('error').lower() != 'task not found':
            return wrong("Response message should be 'task not found'")

        return correct()

    @dynamic_test
    def test_post_201(self):
        hw: Response = requests.post(self.get_url('/tasks'), json={'name': 'task 1', 'time': '1h'})

        try:
            json.loads(hw.content)
        except Exception:
            return wrong(f'Response for {hw.request} on {hw.url} should be in json format')

        if hw.status_code != 201:
            return wrong('Response code of successful POST method should be 201')

        if 'todo_list_length' not in hw.json():
            return wrong('Response object should contain "todo_list_length" key')
        if hw.json().get('todo_list_length') != 1:
            return wrong('Response should contain correct information about TODO list length')

        return correct()

    @dynamic_test
    def test_get_liat_with_2_objects_200(self):
        requests.post(self.get_url('/tasks'), json={'name': 'task 2', 'time': '3h'})

        hw: Response = requests.get(self.get_url('/tasks'))
        try:
            json.loads(hw.content)
        except Exception:
            return wrong(f'Response for {hw.request} on {hw.url} should be in json format')

        if hw.status_code != 200:
            return wrong('Response code of successful GET method should be 200')

        if 'todo_list' not in hw.json():
            return wrong('Response object should contain todo_list key')

        if isinstance(hw.json().get('todo_list'), (list, tuple)):
            return wrong('Response field todo_list should contain list of TODO entries')

        if len(hw.json().get('todo_list')) != 2:
            return wrong('Response should contain all TODO list entries')

        return correct()

    @dynamic_test
    def test_get_task_200(self):
        hw: Response = requests.post(self.get_url('/tasks'), json={'name': 'task 1', 'time': '1h'})

        hw = requests.get(self.get_url(f'/tasks/{hw.json().get("todo_list_length") - 1}'))

        try:
            json.loads(hw.content)
        except Exception:
            return wrong(f'Response for {hw.request} on {hw.url} should be in json format')

        if hw.status_code != 200:
            return wrong('Response code of successful POST method should be 201')

        if 'task' not in hw.json():
            return wrong('Response object should contain "task" key')
        if not isinstance(hw.json().get('task'), dict):
            return wrong('Response shout contain the created task object under "task" key')

        return correct()
