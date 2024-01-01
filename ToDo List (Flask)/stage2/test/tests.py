import json
from typing import List

from requests import Response
import requests

from hstest import FlaskTest, dynamic_test, wrong, correct, SQLTest, StageTest


class ServerTest(FlaskTest):
    use_database = False
    source = 'task'

    @dynamic_test
    def test_get_list_200(self):
        hw = requests.get(self.get_url('/tasks'))
        try:
            json.loads(hw.content)
        except Exception:
            return wrong(f'Response for {hw.request} on {hw.url} should be in json format')

        if hw.status_code != 200:
            return wrong('Response code of successful GET method should be 200')

        if 'todo_list' not in hw.json():
            return wrong('Response object should contain todo_list key')

        return correct()

    @dynamic_test
    def test_get_task_404(self):
        hw = requests.get(self.get_url('/tasks/1000'))
        try:
            json.loads(hw.content)
        except Exception:
            return wrong(f'Response for {hw.request} on {hw.url} should be in json format')

        if hw.status_code != 404:
            return wrong('Response code for not existing task for GET method should be 404')
        if "error" not in hw.json():
            return wrong('Unsuccessful request should return a JSON with an error description under the "error" key')
        if hw.json().get("error").lower() != "task not found":
            return wrong('get for not existing task should return error message "Task not found"')

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
            return wrong(f'Response for {hw.request} on {hw.url} should be in json format')

        if hw.status_code != 201:
            return wrong('Response code of successful POST method should be 201')

        if 'created_id' not in hw.json():
            return wrong('Response body should contain id of created element in created_id files')

        return correct()

    @dynamic_test
    def test_put_201(self):
        hw: Response = requests.post(self.get_url('/tasks'), json=dict(
            title='title',
            description='descr',
            deadline_time='2001-01-01 12:00:00',
            is_completed=False
        ))

        created_id = hw.json().get('created_id')
        hw: Response = requests.put(self.get_url('/tasks'), json=dict(
            id=created_id,
            is_completed=True
        ))

        if hw.status_code != 200:
            return wrong('Response code of successful PUT method should be 200')

        if not hw.json().get('task').get('is_completed'):
            return wrong('Completed state should have been changed')

        return correct()

    @dynamic_test
    def test_put_404(self):
        hw: Response = requests.post(self.get_url('/tasks'), json=dict(
            title='title',
            description='descr',
            deadline_time='2001-01-01 12:00:00',
            is_completed=False
        ))

        created_id = hw.json().get('created_id')
        hw: Response = requests.put(self.get_url('/tasks'), json=dict(
            id=created_id + 1,
            is_completed=True
        ))

        if hw.status_code != 404:
            return wrong('status code for update of non-existing task should return 404')

        if "error" not in hw.json():
            return wrong('Unsuccessful request should return a JSON with an error description under the "error" key')

        if hw.json().get("error").lower() != "task not found":
            return wrong('PUT for not existing task should return error message "Task not found"')

        return correct()

    @dynamic_test
    def test_post_422(self):
        hw: Response = requests.post(self.get_url('/tasks'), json=dict(name='1'))

        try:
            json.loads(hw.content)
        except Exception:
            return wrong(f'Response for {hw.request} on {hw.url} should be in json format')

        if hw.status_code != 422:
            return wrong('Response code of wrong schema for POST method should be 422')

        if {'title', 'description', 'deadline_time', 'is_completed'}.difference(set(hw.json().get('error'))):
            return wrong('response message should provide missing or incorrect fields title, deadline_time, is_completed')

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
        try:
            json.loads(hw.content)
        except Exception:
            return wrong(f'Response for {hw.request} on {hw.url} should be in json format')

        if hw.status_code != 200:
            return wrong('Response code of successful GET method should be 200')

        if 'todo_list' not in hw.json():
            return wrong('Response object should contain todo_list key')
        if len(hw.json().get('todo_list')) - length_before != 1:
            return wrong('POST method should add entries unconditionally')

        return correct()


class Test(StageTest):

    @dynamic_test
    def test_sqlite(self):
        import sqlite3
        con = sqlite3.connect("instance/sqlite.db")
        tables: tuple = con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchone()

        if tables is None:
            return wrong('''Could not read database file.
                            Check if you use database for storage and its placed in special directory''')

        all_entries = con.execute(f'select * from {tables[0]}').fetchall()

        if len(all_entries) > 0:
            return correct()
        else:
            return wrong(
                f'Database table {tables[0]} is empty after task creation.'
                f'Check if you use database for TODO list storage'
            )
