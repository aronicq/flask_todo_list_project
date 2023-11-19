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
            return wrong(f'Response should be in json format')

        if hw.status_code != 200:
            return wrong('Response code of successful GET method should be 200')

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
            return wrong('Response code of successful POST method should be 201')

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
        try:
            json.loads(hw.content)
        except Exception:
            return wrong(f'Response should be in json format')

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
            return wrong('Could not read database file.'
                         'Check if you use database for storage and its placed in special directory')
        if len(tables) < 1:
            return wrong('Database contains 0 tables')
        tablenames = ['list', 'todo', 'todolist', 'tasks', 'task']

        if not any([any(i.lower() in table.lower() for i in tablenames) for table in tables]):
            return wrong(
                f'Database has no table with relevant names.'
                f'Check name of table in database, it should reflect stored entities: tasks, todo list and so on'
            )

        all_entries = con.execute(f'select * from {tables[0]}').fetchall()

        if len(all_entries) > 0:
            return correct()
        else:
            return wrong(
                f'Database table {tables[0]} is empty after task creation.'
                f'Check if you use database for TODO list storage'
            )
