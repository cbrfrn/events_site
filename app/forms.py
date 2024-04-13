from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, BooleanField, DateTimeField, TimeField, SelectField, FileField, IntegerField 
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, Regexp, Optional, NumberRange
from .models import User

class LoginForm(FlaskForm):
    email = StringField('Почта', validators=[DataRequired(), Email()], render_kw={"placeholder": "Почта"})
    password = PasswordField('Пароль', validators=[DataRequired()], render_kw={"placeholder": "Пароль"})
    submit = SubmitField('Войти')
    remember_me = BooleanField('Remember Me')

class RegistrationFormVisitor(FlaskForm):
    full_name = StringField(
        'Имя:',
        validators=[DataRequired(message='Это поле обязательно для заполнения'), Length(min=1, max=60)],
        render_kw={"required": True, "placeholder": "Имя"}
    )
    email = StringField(
        'Почта:',
        validators=[
            DataRequired(message='Это поле обязательно для заполнения'), 
            Email(message='Некорректный адрес электронной почты')
        ],
        render_kw={"required": True, "placeholder": "Почта"}
    )
    password = PasswordField(
        'Пароль:',
        validators=[
            DataRequired(message='Это поле обязательно для заполнения'), 
            Length(min=8, message='Пароль должен содержать минимум 8 символов'),
            Regexp('^[A-Za-z0-9@#$%^&+=]{8,}$', message='Допустимы только латиница, цифры и специальные символы')
        ],
        render_kw={"required": True, "placeholder": "Пароль"}
    )
    confirm_password = PasswordField('Подтвердите пароль:', validators=[DataRequired(), EqualTo('password', message='Пароли не совпадают')], render_kw={"placeholder": "Подтвердите пароль"})
    submit = SubmitField('Зарегистрироваться')

class RegistrationFormOrganaizer(FlaskForm):
    full_name = StringField('Название', validators=[DataRequired(), Length(min=1, max=60)], render_kw={"required": True})
    short_description = StringField('Краткое описание', validators=[DataRequired(), Length(max=60)], render_kw={"placeholder": "киноклуб, галерея...", "required": True})
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


class SettingsForm(FlaskForm):
    full_name = StringField(
        'Имя:', 
        validators=[DataRequired(message='Это поле обязательно для заполнения'), Length(min=1, max=60)],
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
    new_password = PasswordField(
        'Новый пароль:', 
        validators=[
            Optional(), 
            Length(min=8, message='Пароль должен содержать минимум 8 символов.'),
            Regexp('^[A-Za-z0-9@#$%^&+=]{8,}$', message='Допустимы только латиница, цифры и специальные символы')
        ]
    )
    
    current_password = PasswordField('Текущий Пароль', validators=[Optional()])
    
    submit = SubmitField('Сохранить изменения')


class EditOrganaizerForm(FlaskForm):
    full_name = StringField('Название', validators=[DataRequired(), Length(min=1, max=60)])
    short_description = StringField('Краткое описание', validators=[DataRequired(), Length(max=60)], render_kw={"placeholder": "киноклуб, галерея..."})
    website = StringField('Сайт', validators=[Optional(), Length(max=100)])
    address = StringField('Адрес', validators=[Optional(), Length(max=100)])
    profile_photo = FileField('Фото профиля', validators=[Optional()])  # Optional, так как пользователь может не менять фото
    full_description = TextAreaField('Описание', validators=[DataRequired()], render_kw={"rows": 8})
    submit = SubmitField('Сохранить изменения')

class OrgSettingsForm(FlaskForm):
    nickname = StringField('Никнейм', validators=[DataRequired(), Length(min=2, max=30)])
    email = StringField('Электронная почта', validators=[DataRequired(), Email()])
    password = PasswordField('Новый пароль', validators=[Optional(), Length(min=8)])
    confirm_password = PasswordField('Подтвердите новый пароль', validators=[EqualTo('password')])
    current_password = PasswordField('Текущий пароль', validators=[DataRequired()])
    submit = SubmitField('Сохранить изменения')

class EventForm(FlaskForm):
    title = StringField('Название', validators=[DataRequired(), Length(min=1, max=100)])
    photo = FileField('Фото', validators=[FileAllowed(['jpg', 'png'], 'Только изображения!')])
    event_type = SelectField('Тип события', choices=[('once', 'Разовое'), ('ongoing', 'Длительное')], validators=[DataRequired()], id='event_type')    
    start_date = StringField('Дата начала', validators=[DataRequired()], id='start_date')
    end_date = StringField('Окончания', validators=[Optional()], id='end_date')    
    start_time = TimeField('Время начала')
    address = StringField('Адрес', validators=[DataRequired()])
    description = TextAreaField('Описание', validators=[DataRequired()])
    # price_option = SelectField('Вход', choices=[('Бесплатно', 'Бесплатно'), ('Donation', 'Donation'), ('number', 'Платно')], validators=[DataRequired()])
    # price = IntegerField('Стоимость', validators=[Optional(), NumberRange(min=0)])
    price = StringField('Вход', validators=[DataRequired()], render_kw={"placeholder": "укажите стоимость или условия входа"})
    submit = SubmitField('Сохранить')