import json

import sqlalchemy
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, request
from marshmallow import Schema, fields, ValidationError

app = Flask(import_name='TODO list project')

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///sqlite.db"
db: SQLAlchemy = SQLAlchemy(app)


class TODOEntry(Schema):
    title = fields.String(required=True)
    description = fields.String(required=True)
    deadline_time = fields.DateTime(required=True)
    is_completed = fields.Boolean(required=True)


class TODOEntryUpdate(Schema):
    id = fields.Integer(required=True)
    is_completed = fields.Boolean(required=True)


class TODOEntryOut(Schema):
    id = fields.Integer()
    title = fields.String(required=True)
    description = fields.String(required=True)
    deadline_time = fields.String(required=True)
    is_completed = fields.Boolean(required=True)
    create_time = fields.String()


class TODOlist(db.Model):
    __tablename__ = 'todolist'

    id = sqlalchemy.Column(db.Integer, primary_key=True)
    title = sqlalchemy.Column(db.String)
    description = sqlalchemy.Column(db.String)
    create_time = sqlalchemy.Column(db.String, default=sqlalchemy.sql.func.now())
    deadline_time = sqlalchemy.Column(db.String)
    is_completed = sqlalchemy.Column(db.Boolean, default=False)


todo_schema = TODOEntry()
todo_schema_list = TODOEntryOut(many=True)
todo_update = TODOEntryUpdate()


@app.route('/tasks', methods=["POST"])
def create_entry():
    json_input = request.get_json()
    try:
        todo = todo_schema.load(json_input)
    except ValidationError as err:
        return {"error": err.messages}, 422
    todo = TODOlist(**todo)
    db.session.add(todo)
    db.session.commit()
    created_id = todo.id

    return {"created_id": created_id}, 201


@app.route('/tasks/<todo_id>', methods=['GET'])
def get_entry(todo_id: int):
    todo = TODOlist.query.filter(TODOlist.id == todo_id).first()
    return {'todo_list': todo_schema_list.dump(todo)}


@app.route('/tasks', methods=['PUT'])
def change_entry():
    json_input = request.get_json()
    try:
        todo = todo_update.load(json_input)
    except ValidationError as err:
        return {"error": err.messages}, 422
    todo_object: TODOlist = TODOlist.query.filter(TODOlist.id == todo.get('id')).first()
    todo_object.is_completed = todo.get('is_completed')
    db.session.commit()
    return {'todo_list': todo_schema_list.dump([todo_object])}


@app.route('/tasks', methods=['GET'])
def get_entry_list():
    return {'todo_list': todo_schema_list.dump(TODOlist.query.all())}


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=8000)
