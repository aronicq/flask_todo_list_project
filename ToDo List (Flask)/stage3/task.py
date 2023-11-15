import sqlalchemy
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
    title = fields.String(required=True)
    description = fields.String(required=True)
    deadline_time = fields.DateTime(required=True)
    is_completed = fields.Boolean(required=True)


class TODOEntryOut(Schema):
    id = fields.Integer()
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


todo_schema = TODOEntry()
todo_schema_list = TODOEntryOut(many=True)


user_schema = UserSchema()


class Users(db.Model):
    __tablename__ = 'users'

    id = sqlalchemy.Column(db.Integer, primary_key=True)
    password = sqlalchemy.Column(db.String, nullable=False)
    email = sqlalchemy.Column(db.String, nullable=False)


class TODOlist(db.Model):
    __tablename__ = 'todolist'

    id = sqlalchemy.Column(db.Integer, primary_key=True)
    title = sqlalchemy.Column(db.String)
    description = sqlalchemy.Column(db.String)
    create_time = sqlalchemy.Column(db.String, default=sqlalchemy.sql.func.now())
    deadline_time = sqlalchemy.Column(db.String)
    is_completed = sqlalchemy.Column(db.Boolean, default=False)


class Session:
    def __init__(self):
        self._user_email = None

    @property
    def user_email(self):
        return self._user_email

    @user_email.setter
    def user_email(self, user_email):
        self._user_email = user_email


session = Session()


def create_and_save_new_user(data: dict):
    new_user = Users(email=data.get('email'), password=generate_password_hash(data.get('password')))

    db.session.add(new_user)
    db.session.commit()
    session.user_email = new_user.email
    return new_user


def login_user(email: str, password: str, user: Users):
    print(user.password, password)
    if check_password_hash(user.password, password):
        session.user_email = email
        return None
    else:
        return 'Wrong password'


@app.route("/register", methods=["POST"])
def register():
    json_input = request.get_json()
    try:
        data = user_schema.load(json_input)
    except ValidationError as err:
        return {"errors": err.messages}, 422
    user: Users = Users.query.filter(Users.email == data["email"]).first()
    if not user:
        user = create_and_save_new_user(data)
        message = f"Successfully created user: {user.email}"
    else:
        print('user', user.email, user.id)
        return {"errors": "That email address is already in the database"}, 400

    data = user_schema.dump(user)
    data["message"] = message
    return data, 201


@app.route('/tasks', methods=["POST"])
def create_entry():
    json_input = request.get_json()
    try:
        todo = todo_schema.load(json_input)
    except ValidationError as err:
        return {"errors": err.messages}, 422
    todo = TODOlist(**todo)
    db.session.add(todo)
    db.session.commit()
    created_id = todo.id

    return {"created_id": created_id}, 201


@app.route('/tasks/<todo_id>', methods=['GET'])
def get_entry(todo_id: int):
    todo = TODOlist.query.filter(id == todo_id).first()
    return {'todo_list': todo_schema_list.dump(todo)}


@app.route('/tasks', methods=['GET'])
def get_entry_list():
    return {'todo_list': todo_schema_list.dump(TODOlist.query.all())}


@app.route('/login', methods=["POST"])
def login():
    json_input = request.get_json()
    try:
        todo = user_schema.load(json_input)
    except ValidationError as err:
        return {"errors": err.messages}, 422

    user = Users.query.filter(Users.email == todo.get('email')).first()
    logged_in = None
    if user is not None:
        logged_in = login_user(todo.get('email'), todo.get('password'), user)
    else:
        return {"error": f"User email {todo.get('email')} does not exist, please sign up and then log in."}
    if logged_in is not None:
        return {"error": logged_in}

    token = create_access_token(user.email)
    return jsonify(access_token=token), 200


@app.route('/current')
@jwt_required()
def get_current_user():
    return get_jwt()
    # return {"current_user_email": session.user_email}


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=8000)
