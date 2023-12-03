from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, BooleanField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, Regexp
from .models import User

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Вход')
    remember_me = BooleanField('Remember Me')

class RegistrationFormVisitor(FlaskForm):
    full_name = StringField(
        'Имя:',
        validators=[DataRequired(message='Это поле обязательно для заполнения'), Length(min=1, max=50)],
        render_kw={"required": True}
    )
    email = StringField(
        'Почта:',
        validators=[
            DataRequired(message='Это поле обязательно для заполнения'), 
            Email(message='Некорректный адрес электронной почты')
        ],
        render_kw={"required": True}
    )
    password = PasswordField(
        'Пароль:',
        validators=[
            DataRequired(message='Это поле обязательно для заполнения.'), 
            Length(min=8, message='Пароль должен содержать минимум 8 символов.'),
            Regexp('^[A-Za-z0-9@#$%^&+=]{8,}$', message='Допустимы только латиница, цифры и специальные символы')
        ],
        render_kw={"required": True}
    )
    confirm_password = PasswordField('Подтвердите пароль:', validators=[DataRequired(), EqualTo('password', message='Пароли не совпадают')])
    submit = SubmitField('Зарегистрироваться')

class RegistrationFormOrganaizer(FlaskForm):
    full_name = StringField('Название', validators=[DataRequired(), Length(min=1, max=50)], render_kw={"required": True})
    short_description = StringField('Краткое описание', validators=[DataRequired(), Length(max=50)], render_kw={"placeholder": "киноклуб, галерея...", "required": True})
    full_description = TextAreaField('Полное описание', validators=[DataRequired()], render_kw={"placeholder": "расскажите о своем месте или сообществе", "required": True})
    address = StringField('Адрес', validators=[Optional(), Length(max=100)], render_kw={"placeholder": "укажите, если есть"})
    website = StringField('Сайт/соцсеть', validators=[DataRequired(), Length(max=100)], render_kw={"placeholder": "с примерами ваших мероприятий","required": True})
    
    profile_photo = FileField('Фото профиля', validators=[
        FileRequired(),
        FileAllowed(['jpg', 'png'], 'Images only!')
    ], render_kw={"id": "profile-photo-upload", "required": True})

    nickname = StringField('Никнейм:', validators=[DataRequired(), Length(min=3, max=30)], render_kw={"placeholder": "будет вашей ссылкой", "id": "nickname", "required": True})
    email = StringField('Почта:', validators=[DataRequired(), Email()], render_kw={"id": "email", "required": True})
    password = PasswordField('Пароль:', validators=[
        DataRequired(),
        Length(min=8),
        Regexp(regex="^[a-zA-Z0-9_!@#$%^&*]+$"),
    ], render_kw={"id": "password", "required": True})
    confirm_password = PasswordField('Подтвердите пароль:', validators=[
        DataRequired(),
        EqualTo('password')
    ], render_kw={"id": "confirm-password", "required": True})
    submit = SubmitField('подать заявку')

