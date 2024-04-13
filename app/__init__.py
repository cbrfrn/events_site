from flask import Flask, redirect, url_for, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from .database import db  # Импорт объекта SQLAlchemy из database.py
from flask_wtf.csrf import CSRFProtect
from flask_bootstrap import Bootstrap
from .models import User, Event
from flask_login import LoginManager  # Импорт Flask-Login
import os
from flask_migrate import Migrate
from flask_babel import Babel, format_date
from jinja2 import Environment
from flask_apscheduler import APScheduler
from datetime import datetime


class Config(object):
    # Настройки планировщика
    SCHEDULER_API_ENABLED = True

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SECRET_KEY'] = b'\t\\\xf0\xa2~\xf1v\xe8OQ\xae\xf6\xb4\x00K\x17'
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024
app.config['BABEL_DEFAULT_LOCALE'] = 'ru'
app.config.from_object(Config())

bcrypt = Bcrypt(app)
Bootstrap(app)
csrf = CSRFProtect(app)  # Инициализация CSRF-защиты
db.init_app(app)  # Инициализация SQLAlchemy с app
migrate = Migrate(app, db)
babel = Babel(app)


# Инициализация Flask-Login
login_manager = LoginManager(app)
login_manager.login_view = 'login'  # Указываем название функции входа

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def format_date_filter(value, format='long'):
    if format == 'full':
        format="EEEE, d MMMM y"
    elif format == 'long':
        format="d MMMM"
    return format_date(value, format)

app.jinja_env.filters['format_date'] = format_date_filter

# Функция для удаления прошедших событий
def delete_past_events():
    with app.app_context():
        current_time = datetime.utcnow()
        
        # Сначала получаем события, которые должны быть удалены
        past_once_events = Event.query.filter(Event.event_type == 'once', Event.start_date < current_time).all()
        past_ongoing_events = Event.query.filter(Event.event_type == 'ongoing', Event.end_date < current_time).all()
        
        # Удаляем связанные файлы изображений
        for event in past_once_events + past_ongoing_events:
            if event.photo and event.photo != 'default_event.jpg':
                photo_path = os.path.join(app.config['UPLOAD_FOLDER'], event.photo)
                if os.path.exists(photo_path):
                    os.remove(photo_path)

        # Теперь удаляем сами события из базы данных
        Event.query.filter(Event.event_type == 'once', Event.start_date < current_time).delete(synchronize_session=False)
        Event.query.filter(Event.event_type == 'ongoing', Event.end_date < current_time).delete(synchronize_session=False)
        
        db.session.commit()

# Инициализация и конфигурация планировщика
scheduler = APScheduler()
scheduler.init_app(app)

# Задача для планировщика
@scheduler.task('cron', id='delete_past_events', hour=0, minute=0)
def scheduled_task():
    delete_past_events()

scheduler.start()

from app import routes  # Импорт маршрутов в конце файла