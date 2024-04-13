from .database import db
from datetime import datetime
from flask_login import UserMixin


# Определение отношения многие ко многим между посетителями и организаторами
subscriptions = db.Table('subscriptions',
    db.Column('visitor_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('organaizer_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)

# Модель Пользователя
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    type = db.Column(db.String(10), nullable=False) # 'visitor', 'organaizer', 'admin'
    
    # Дополнительные поля для организаторов
    nickname = db.Column(db.String(30), unique=True)
    profile_photo = db.Column(db.String(255), nullable=True, default='default_user.jpg')
    address = db.Column(db.String(100), nullable=True)
    website = db.Column(db.String(100))
    short_description = db.Column(db.String(100))
    full_description = db.Column(db.Text)
    is_confirmed = db.Column(db.Boolean, default=False)

    # Для организаторов: Список посетителей, подписанных на организатора
    subscribed_visitors = db.relationship(
        'User', secondary=subscriptions,
        primaryjoin=id == subscriptions.c.organaizer_id,
        secondaryjoin=id == subscriptions.c.visitor_id,
        backref=db.backref('subscribed_organaizers', lazy='dynamic'), lazy='dynamic')

    # Связь с событиями (для организаторов)
    events = db.relationship('Event', backref='organaizer', lazy=True, cascade='all, delete-orphan')

# Модель События
class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    photo = db.Column(db.String(255), nullable=True, default='default_event.jpg')
    event_type = db.Column(db.String(10), nullable=False)  # 'once', 'ongoing'
    start_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    end_date = db.Column(db.DateTime)
    start_time = db.Column(db.Time)
    address = db.Column(db.String(100), nullable=False)
    organaizer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.String(50), nullable=True)

