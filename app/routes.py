from . import app, db, bcrypt
from flask import render_template, flash, redirect, url_for, jsonify, request, get_flashed_messages, session
import sqlalchemy
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from werkzeug.utils import secure_filename
from urllib.parse import urlparse
from .forms import RegistrationFormVisitor, RegistrationFormOrganaizer, LoginForm
from .models import User, Event, subscriptions
import os
from flask_login import login_user, logout_user, login_required, current_user



@app.context_processor
def context_processor():
    return dict(
        login_form=LoginForm(),
        register_form=RegistrationFormVisitor()
    )

@app.route('/')
def home():
    return render_template('index.html', title='Главная страница')

@app.route('/visitor/<int:user_id>')
def visitor(user_id):
    # Логика для проверки, существует ли посетитель с таким ID
    # Если нет, то возвращаем 404 страницу
    # Например: if not is_valid_visitor(user_id): abort(404)
    return render_template('visitor.html', title='Страница посетителя', user_id=user_id)

@app.route('/event/<int:event_id>')
def event(event_id):
    # Логика для получения данных о событии
    return render_template('event.html', title='Страница события', event_id=event_id)

@app.route('/all_of_us')
def all_of_us():
    return render_template('all_of_us.html', title='Все организаторы')

@app.route('/create')
def create():
    return render_template('create.html', title='Создание события')

@app.route('/about')
def about():
    return render_template('about.html', title='О проекте')

@app.route('/<nickname>')
def organaizer(nickname):
    organaizer = User.query.filter_by(nickname=nickname, type='organaizer').first()
    if organaizer is None:
        return redirect(url_for('home'))  # или render_template('404.html'), если у вас есть такой шаблон
    return render_template('organaizer.html', title='Страница организатора', nickname=nickname)

@app.route('/register_organaizer', methods=['GET', 'POST'])
def register_organaizer():
    form = RegistrationFormOrganaizer()
    if form.validate_on_submit():
        
        # Приведение никнейма и почты к нижнему регистру
        nickname = form.nickname.data.lower()
        email = form.email.data.lower()

        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(full_name=form.full_name.data, email=email,
                    password=hashed_password, type='organaizer',
                    nickname=nickname, short_description=form.short_description.data,
                    full_description=form.full_description.data, address=form.address.data or None,
                    website=form.website.data or None, is_confirmed=False)

        # Обработка загруженного файла
        if form.profile_photo.data:
            file = form.profile_photo.data
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            user.profile_photo = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        else:
            user.profile_photo = 'default_user.jpg'

        db.session.add(user)
        try:
            db.session.commit()
            flash('Ваша заявка на регистрацию успешно отправлена. Пожалуйста, ожидайте подтверждения администратора.', 'success')
        except sqlalchemy.exc.IntegrityError:
            db.session.rollback()
            flash('Произошла ошибка при регистрации. Пожалуйста, проверьте введенные данные.', 'error')
    elif form.errors:
        flash('Произошла ошибка при регистрации. Пожалуйста, проверьте введенные данные.', 'error')

    return render_template('register_organaizer.html', title='Подача заявки', form=form)


@app.route('/register_visitor', methods=['POST'])
def register_visitor():
    form = RegistrationFormVisitor()
    if form.validate_on_submit():
        email = form.email.data.lower()
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({'success': False, 'errors': {'email': ['Почта уже используется.']}})

        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(full_name=form.full_name.data, email=email, password=hashed_password, type='visitor')
        db.session.add(user)
        db.session.commit()
        # Код для авторизации пользователя...

        return jsonify({'success': True, 'redirect': url_for('home')})
    
    errors = {field: errors for field, errors in form.errors.items()}
    return jsonify({'success': False, 'errors': errors})

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return jsonify(success=True, next_url=url_for('home'))

    form = LoginForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            email_lowercase = form.email.data.lower()
            user = User.query.filter_by(email=email_lowercase).first()
            if user and bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user)
                next_page = request.args.get('next') or url_for('home')
                return jsonify(success=True, next_url=next_page)
            return jsonify(success=False, error='Неверный логин или пароль')
        
        errors = form.errors
        return jsonify(success=False, error='Ошибка валидации', form_errors=errors), 400

    # Если это GET запрос, отображаем шаблон только если запрос не AJAX
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        show_login_modal = session.pop('show_login_modal', False)
        next_url = session.get('next', url_for('home'))
        return render_template('login.html', form=form, show_login_modal=show_login_modal, next=next_url)
    
    # Если это AJAX GET запрос, возвращаем статус, указывающий на необходимость авторизации
    return jsonify(success=False, next_url=url_for('login')), 401

 

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route('/check_nickname', methods=['POST'])
def check_nickname():
    data = request.get_json()
    nickname = data['nickname'].lower()
    user = User.query.filter(func.lower(User.nickname) == nickname).first()
    return jsonify({'is_taken': user is not None})

@app.route('/check_email', methods=['POST'])
def check_email():
    data = request.get_json()
    email = data['email'].lower()  # Приведение email к нижнему регистру
    user = User.query.filter_by(email=email).first()
    return jsonify({'is_taken': user is not None})

@app.route('/profile/<int:user_id>')
@login_required
def profile(user_id):
    user = User.query.get_or_404(user_id)
    if current_user.id != user.id:
        return redirect(url_for('home'))  # Перенаправление на главную страницу
    return render_template('profile.html', user=user)
