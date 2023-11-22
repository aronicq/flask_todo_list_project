from __future__ import annotations

from enum import Enum
from typing import List, Optional

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

app.config['JWT_SECRET_KEY'] = 'your-secret-key'
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


class Base(DeclarativeBase):
    pass


class SharedStateEnum(str, Enum):
    SHARED = 'SHARED'
    AUTHOR = 'AUTHOR'


class UsersListsAccessTable(db.Model):
    __tablename__ = "users_lists_access"

    user_id: Mapped[int] = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id"), primary_key=True)
    list_id: Mapped[int] = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("lists.id"), primary_key=True)
    access_type: Mapped[Optional[str]] = sqlalchemy.Column(sqlalchemy.String, default=SharedStateEnum.SHARED)

    list: Mapped[TODOlists] = relationship(back_populates="users")
    user: Mapped[Users] = relationship(back_populates="lists")


class TODOlists(db.Model):
    __tablename__ = 'lists'
    id: Mapped[int] = sqlalchemy.Column(db.Integer, primary_key=True)
    users: Mapped[List[UsersListsAccessTable]] = relationship(
        back_populates="list"
    )


class Users(db.Model):
    __tablename__ = 'users'

    id: Mapped[int] = sqlalchemy.Column(db.Integer, primary_key=True)
    password: Mapped[str] = sqlalchemy.Column(db.String, nullable=False)
    email: Mapped[str] = sqlalchemy.Column(db.String, nullable=False)
    lists: Mapped[List[UsersListsAccessTable]] = relationship(
        back_populates="user"
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


def check_list_shared_access(list_id, user_id):
    todo_list = UsersListsAccessTable.query.filter(UsersListsAccessTable.list_id == list_id)\
        .filter(UsersListsAccessTable.user_id == user_id).all()
    if not todo_list:
        return f'no access to list with id {list_id}'
    return None


def check_list_author_access(list_id, user_id):
    todo_list = UsersListsAccessTable.query.filter(UsersListsAccessTable.list_id == list_id)\
        .filter(UsersListsAccessTable.user_id == user_id)\
        .filter(UsersListsAccessTable.access_type == SharedStateEnum.AUTHOR).all()
    if not todo_list:
        return f'no access to list with id {list_id}'
    return None


@app.route("/users", methods=["GET"])
def get_user_by_email():
    if 'email' not in request.args:
        return {"error": "no email passed"}, 422
    email = request.args['email']
    return {"user_id": get_user_id(email)}


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


class TasksListAccess(Schema):
    user_id = fields.Integer()
    list_id = fields.Integer()


tasks_list_access = TasksListAccess()


@app.route('/access', methods=['POST'])
@jwt_required()
def share_access():
    json_input = request.get_json()
    try:
        access_params = tasks_list_access.load(json_input)
    except ValidationError as err:
        return {"error": err.messages}, 422

    list_id = access_params.get('list_id')
    user_id = access_params.get('user_id')
    if not TODOlists.query.get(list_id):
        return {"error": f"no list with such id"}, 400
    if not Users.query.get(user_id):
        return {"error": "no user with such id"}, 400

    access_error = check_list_author_access(
        list_id=list_id,
        user_id=Users.query.filter(Users.email == get_jwt().get('sub')).first().id,
    )
    if access_error:
        return {"error": access_error}, 403

    access = UsersListsAccessTable(
        access_type=SharedStateEnum.SHARED, user_id=user_id, list_id=list_id,
    )
    db.session.add(access)
    try:
        db.session.commit()
    except sqlalchemy.exc.IntegrityError as e:
        return {"error": "this user already has access to the list"}

    return {"shared_list_id": list_id}, 201


@app.route('/access', methods=['DELETE'])
@jwt_required()
def revoke_access():
    json_input = request.get_json()
    try:
        access_params = tasks_list_access.load(json_input)
    except ValidationError as err:
        return {"error": err.messages}, 422

    list_id = access_params.get('list_id')
    user_id = access_params.get('user_id')

    if not TODOlists.query.get(list_id):
        return {"error": f"no list with such id"}, 400
    if not Users.query.get(user_id):
        return {"error": "no user with such id"}, 400

    access_error = check_list_author_access(
        list_id=list_id,
        user_id=Users.query.filter(Users.email == get_jwt().get('sub')).first().id,
    )
    if access_error:
        return {"error": access_error}, 403

    UsersListsAccessTable.query.filter(UsersListsAccessTable.list_id == list_id)\
        .filter(UsersListsAccessTable.user_id == user_id).delete()

    db.session.commit()
    return {"deleted_id": user_id}, 200


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
    todo_list = TODOlists.query.filter(TODOlists.id == list_id).first()
    if not todo_list:
        todo_list = TODOlists()
        access = UsersListsAccessTable(extra_data=SharedStateEnum.AUTHOR, user_id=get_user_id(email), list=todo_list)
        db.session.add(todo_list)
        db.session.add(access)
        db.session.commit()

    else:
        access_error = check_list_author_access(
            list_id=list_id,
            user_id=Users.query.filter(Users.email == get_jwt().get('sub')).first().id,
        )
        if access_error:
            return {"error": access_error}, 403

    list_id = todo_list.id
    todo_list = []
    for t in todo.get('list'):
        todo_list.append(
            Tasks(
                title=t.get('title'),
                description=t.get('description'),
                deadline_time=t.get('deadline_time'),
                list_id=list_id,
            )
        )
    db.session.bulk_save_objects(todo_list)
    db.session.commit()
    created_id = list_id

    return {"created_list_id": created_id}, 201


@app.route('/tasks/<todo_id>', methods=['GET'])
@jwt_required()
def get_entry(todo_id: int):
    list_id = get_list_id(task_id=todo_id)

    access_error = check_list_shared_access(
        list_id=list_id,
        user_id=Users.query.filter(Users.email == get_jwt().get('sub')).first().id,
    )
    if access_error:
        return {"error": access_error}, 403
    todo = Tasks.query.get(todo_id)
    return {'todo_list': todo_schema_list.dump([todo])}


@app.route('/lists/<list_id>', methods=['GET'])
@jwt_required()
def get_entry_list(list_id: int):
    access_error = check_list_shared_access(
        list_id=list_id,
        user_id=Users.query.filter(Users.email == get_jwt().get('sub')).first().id,
    )
    if access_error:
        return {"error": access_error}, 403
    todo = Tasks.query.filter(Tasks.list_id == list_id).all()
    return {'todo_list': todo_schema_list.dump(todo)}


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=8000)
