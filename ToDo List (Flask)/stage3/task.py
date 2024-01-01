import sqlalchemy
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, request, jsonify
from marshmallow import Schema, fields, ValidationError

from werkzeug.security import generate_password_hash, check_password_hash

from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt

app = Flask(import_name='TODO list project')
app.config["SECRET_KEY"] = 'MY-SECRET-KEY'
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///sqlite.db"


db: SQLAlchemy = SQLAlchemy(app)

app.config['JWT_SECRET_KEY'] = 'your-secret-key'
jwt = JWTManager(app)


class UserSchema(Schema):
    id = fields.Int(dump_only=True)
    email = fields.Str(
        required=True
    )
    password = fields.Str(
        required=True
    )


class UserSchemaOut(Schema):
    id = fields.Int(dump_only=True)
    email = fields.Str()


user_schema = UserSchema()
user_schema_out = UserSchemaOut()


class Users(db.Model):
    __tablename__ = 'users'

    id = sqlalchemy.Column(db.Integer, primary_key=True)
    password = sqlalchemy.Column(db.String, nullable=False)
    email = sqlalchemy.Column(db.String, nullable=False)


def create_and_save_new_user(data: dict):
    new_user = Users(email=data.get('email'), password=generate_password_hash(data.get('password')))

    db.session.add(new_user)
    db.session.commit()
    return new_user


def login_user(password: str, user_password: str):
    if check_password_hash(str(user_password), password):
        return None
    else:
        return 'Wrong email-password pair'


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
        return {"error": 'email address is already in use'}, 400

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
        return {"error": logged_in}, 401

    token = create_access_token(user.email)
    return jsonify(access_token='token'), 200


@app.route('/current')
@jwt_required()
def get_current_user():
    return {"current_user_email": get_jwt().get('sub')}


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=8000)
