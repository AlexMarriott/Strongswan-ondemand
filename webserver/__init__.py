from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

import uuid

db = SQLAlchemy()


def create_app():
    app = Flask(__name__)
    app.secret_key = uuid.uuid4().hex

    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
    db.init_app(app)
    login_manager = LoginManager()  # Create a Login Manager instance
    login_manager.init_app(app)  # configure it for login
    from models import User
    import logging
    logging.basicConfig(filename='error.log', level=logging.DEBUG)

    @login_manager.user_loader
    def load_user(user_id):  # reload user object from the user ID stored in the session
        # since the user_id is just the primary key of our user table, use it in the query for the user
        return User.query.get(int(user_id))

    return app
