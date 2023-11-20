from __future__ import annotations

from typing import List

import sqlalchemy
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase, relationship
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, request, jsonify
from marshmallow import Schema, fields, ValidationError
from flask_login import LoginManager

from werkzeug.security import generate_password_hash, check_password_hash

from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt

app = Flask(import_name='TODO list project')
app.config["SECRET_KEY"] = 'MY-SECRET-KEY'
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///sqlite.db"

login_manager = LoginManager()
login_manager.init_app(app)

db: SQLAlchemy = SQLAlchemy(app)

app.config['JWT_SECRET_KEY'] = 'your-secret-key'  # Replace 'your-secret-key' with your actual secret key
jwt = JWTManager(app)


class TODOEntry(Schema):
    list_id = fields.Integer()
    title = fields.String(required=True)
    description = fields.String(required=True)
    deadline_time = fields.DateTime(required=True)
    is_completed = fields.Boolean(required=True)


class TODOEntryOut(Schema):
    id = fields.Integer()
    list_id = fields.Integer()
    title = fields.String(required=True)
    description = fields.String(required=True)
    deadline_time = fields.String(required=True)
    is_completed = fields.Boolean(required=True)
    create_time = fields.String()


class UserSchema(Schema):
    id = fields.Int(dump_only=True)
    email = fields.Str(
        required=True  # , validate=validate.Email(error="Not a valid email address")
    )
    password = fields.Str(
        required=True  # , validate=[validate.Length(min=6, max=36)], load_only=True
    )


class UserSchemaOut(Schema):
    id = fields.Int(dump_only=True)
    email = fields.Str()


todo_list_schema = TODOEntry(many=True)


class TasksList(Schema):
    list = fields.Nested(TODOEntry(many=True))
    list_id = fields.Integer()


todo_schema_list = TODOEntryOut(many=True)


tasks_list = TasksList()
user_schema = UserSchema()
user_schema_out = UserSchemaOut()


from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


users_lists_access_table = sqlalchemy.Table(
    "users_lists_access",
    Base.metadata,
    sqlalchemy.Column("user_id", sqlalchemy.ForeignKey("users.id")),
    sqlalchemy.Column("list_id", sqlalchemy.ForeignKey("lists.id")),
)


class TODOlists(db.Model):
    __tablename__ = 'lists'
    id = sqlalchemy.Column(db.Integer, primary_key=True)
    users: Mapped[List[Users]] = relationship(
        secondary=users_lists_access_table, back_populates="lists"
    )


class Users(db.Model):
    __tablename__ = 'users'

    id = sqlalchemy.Column(db.Integer, primary_key=True)
    password = sqlalchemy.Column(db.String, nullable=False)
    email = sqlalchemy.Column(db.String, nullable=False)
    lists: Mapped[List[TODOlists]] = relationship(
        secondary=users_lists_access_table, back_populates="users"
    )


class Tasks(db.Model):
    __tablename__ = 'tasks'

    id = sqlalchemy.Column(db.Integer, primary_key=True)
    title = sqlalchemy.Column(db.String)
    description = sqlalchemy.Column(db.String)
    create_time = sqlalchemy.Column(db.String, default=sqlalchemy.sql.func.now())
    deadline_time = sqlalchemy.Column(db.String)
    is_completed = sqlalchemy.Column(db.Boolean, default=False)

    list_id = sqlalchemy.Column(db.Integer, sqlalchemy.ForeignKey('lists.id'))


def create_and_save_new_user(data: dict):
    new_user = Users(email=data.get('email'), password=generate_password_hash(data.get('password')))

    db.session.add(new_user)
    db.session.commit()
    return new_user


def login_user(password: str, user_pass: str):
    if check_password_hash(str(user_pass), password):
        return None
    else:
        return 'Wrong email-password pair'


def get_user_id(email):
    user = Users.query.filter(Users.email == email).first()
    if not user:
        raise Exception(f'no user with email {email}')
    return user.id


def get_list_id(task_id):
    task: Tasks = Tasks.query.filter(Tasks.id == task_id).first()
    return task.list_id


def check_list_access(list_id, user_id):
    todo_list: TODOlists = TODOlists.query.filter(TODOlists.id == list_id).first()
    if not todo_list:
        raise Exception(f'no list with id {list_id}')
    return todo_list.user_id == user_id


@app.route("/users", methods=["POST"])
def register():
    json_input = request.get_json()
    try:
        data = user_schema.load(json_input)
    except ValidationError as err:
        return {"error": err.messages}, 422
    user: Users = Users.query.filter(Users.email == data["email"]).first()
    if not user:
        user = create_and_save_new_user(data)
        message = f"Successfully created user: {user.email}"
    else:
        return {"error": "That email address is already in the database"}, 400

    data = user_schema_out.dump(user)
    data["message"] = message
    return data, 201


@app.route('/login', methods=["POST"])
def login():
    json_input = request.get_json()
    try:
        todo = user_schema.load(json_input)
    except ValidationError as err:
        return {"error": err.messages}, 422

    user = Users.query.filter(Users.email == todo.get('email')).first()
    if user is not None:
        logged_in = login_user(todo.get('password'), user.password)
    else:
        return {"error": f"User email {todo.get('email')} does not exist, please sign up and then log in."}, 400
    if logged_in is not None:
        return {"error": logged_in}, 400

    token = create_access_token(user.email)
    return jsonify(access_token=token), 200


@app.route('/lists', methods=["POST"])
@jwt_required()
def create_new_list():
    email = get_jwt().get('sub')
    json_input = request.get_json()
    try:
        todo = tasks_list.load(json_input)
    except ValidationError as err:
        return {"error": err.messages}, 422

    list_id = todo.get('list_id')
    if not TODOlists.query.filter(TODOlists.id == list_id).first():
        new_list = TODOlists(user_id=get_user_id(email))
        db.session.add(new_list)
        db.session.commit()
        list_id = new_list.id

    for task in todo.get('list'):
        task['list_id'] = list_id

    todo = [Tasks(**t) for t in todo.get('list')]
    db.session.bulk_save_objects(todo)
    db.session.commit()
    created_id = list_id

    return {"created_list_id": created_id}, 201


@app.route('/tasks/<todo_id>', methods=['GET'])
@jwt_required()
def get_entry(todo_id: int):
    list_id = get_list_id(task_id=todo_id)
    if not check_list_access(list_id=list_id, user_id=Users.query.filter(Users.email == get_jwt().get('sub')).first().id):
        return {"error": "no access"}, 401
    todo = Tasks.query.get(todo_id)
    return {'todo_list': todo_schema_list.dump([todo])}


@app.route('/lists/<list_id>', methods=['GET'])
@jwt_required()
def get_entry_list(list_id: int):
    if not check_list_access(list_id=list_id, user_id=Users.query.filter(Users.email == get_jwt().get('sub')).first().id):
        return {"error": "no access"}, 401
    todo = Tasks.query.filter(Tasks.list_id == list_id).all()
    return {'todo_list': todo_schema_list.dump(todo)}


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=8000)
