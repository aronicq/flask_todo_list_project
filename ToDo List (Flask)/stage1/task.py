import json

from flask import Flask, request

app = Flask(import_name='TODO list project')


todo_list = []


@app.route('/', methods=["POST"])
def create_entry():
    todo_list.append(json.loads(request.data))
    return {"todo_list_length": len(todo_list)}, 201


@app.route('/<todo_id>', methods=['GET'])
def get_entry(todo_id: int):
    todo_id = int(todo_id)
    if len(todo_list) <= todo_id:
        return {'error': 'list out of range'}
    return {'todo_list': [todo_list[todo_id]]}


@app.route('/', methods=['GET'])
def get_entry_list():
    return {'todo_list': todo_list}


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
