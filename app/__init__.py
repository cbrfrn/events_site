from flask import Flask, redirect, url_for, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from .database import db  # Импорт объекта SQLAlchemy из database.py
from flask_wtf.csrf import CSRFProtect
from flask_bootstrap import Bootstrap
from .models import User
from flask_login import LoginManager  # Импорт Flask-Login

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SECRET_KEY'] = b'\t\\\xf0\xa2~\xf1v\xe8OQ\xae\xf6\xb4\x00K\x17'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  

bcrypt = Bcrypt(app)
Bootstrap(app)
csrf = CSRFProtect(app)  # Инициализация CSRF-защиты
db.init_app(app)  # Инициализация SQLAlchemy с app

# Инициализация Flask-Login
login_manager = LoginManager(app)
login_manager.login_view = 'login'  # Указываем название функции входа

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@login_manager.unauthorized_handler
def unauthorized_callback():
    session['next'] = request.url
    session['show_login_modal'] = True
    return redirect(url_for('login'))

from app import routes  # Импорт маршрутов в конце файла