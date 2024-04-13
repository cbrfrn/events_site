from . import app, db, bcrypt
from flask import render_template, flash, redirect, url_for, jsonify, request, get_flashed_messages, session
import sqlalchemy
import uuid
from sqlalchemy import func, collate
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from werkzeug.utils import secure_filename
from urllib.parse import urlparse
from .forms import RegistrationFormVisitor, RegistrationFormOrganaizer, LoginForm, SettingsForm, EditOrganaizerForm, OrgSettingsForm, EventForm
from .models import User, Event, subscriptions
import os
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash



@app.context_processor
def context_processor():
    return dict(
        login_form=LoginForm(),
        register_form=RegistrationFormVisitor()
    )

@app.route('/')
def home():
    return render_template('index.html', title='Главная страница')


@app.route('/all_of_us')
def all_of_us():
    return render_template('all_of_us.html', title='Все организаторы')

@app.route('/about')
def about():
    return render_template('about.html', title='О проекте')

@app.route('/<nickname>')
def organaizer(nickname):
    organaizer = User.query.filter_by(nickname=nickname, type='organaizer').first()
    form = EditOrganaizerForm(obj=organaizer)
    if organaizer is None or not organaizer.is_confirmed:
        return redirect(url_for('home'))  # или render_template('404.html'), если у вас есть такой шаблон

    # Получение событий организатора с сортировкой по дате и времени
    events = Event.query.filter_by(organaizer_id=organaizer.id).order_by(Event.start_date, Event.start_time).all()

    return render_template('organaizer.html', title='Страница организатора', nickname=nickname, user=organaizer, edit_organaizer_form=form, events=events)

@app.route('/apply', methods=['GET', 'POST'])
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
            original_filename = secure_filename(file.filename)
            file_ext = os.path.splitext(original_filename)[1]  # Получаем расширение файла
            unique_filename = f"{uuid.uuid4()}{file_ext}"  # Создаем уникальное имя файла
            file.save(os.path.join(app.root_path, 'static', 'uploads', unique_filename))
            # Используем replace для корректного формирования пути
            user.profile_photo = os.path.join('uploads', unique_filename).replace('\\', '/')
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
            return jsonify({'success': False, 'errors': {'email': ['Почта уже используется']}})

        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(full_name=form.full_name.data, email=email, password=hashed_password, type='visitor')
        db.session.add(user)
        db.session.commit()
        # Код для авторизации пользователя...
        login_user(user)

        return jsonify({'success': True, 'redirect': url_for('home')})
    
    errors = {field: errors for field, errors in form.errors.items()}
    return jsonify({'success': False, 'errors': errors})

@app.route('/login', methods=['POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email_lowercase = form.email.data.lower()  # Приводим email к нижнему регистру
        user = User.query.filter_by(email=email_lowercase).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            if user.type == 'organaizer' and not user.is_confirmed:
                # Если пользователь - организатор и его аккаунт не подтвержден
                return jsonify({'success': False, 'error': 'Ваш аккаунт ожидает подтверждения.'})
            login_user(user)
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Неверная почта или пароль'})
    return jsonify({'success': False, 'error': 'Неверная почта или пароль'})



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
def profile(user_id):
    user = User.query.filter_by(id=user_id, type='visitor').first_or_404()
    form = SettingsForm(obj=user)  # Создаем экземпляр формы с данными пользователя
    return render_template('profile.html', user=user, form=form)

@app.route('/visitor_settings', methods=['POST'])
@login_required
def visitor_settings():
    form = SettingsForm()
    print("Form validation status:", form.validate_on_submit())  # Для дебага
    print("Form errors:", form.errors)

    if form.validate_on_submit():
        print("Received data:", form.full_name.data, form.email.data, form.new_password.data)  # Логирование полученных данных
        # Приводим введенную и текущую почту к нижнему регистру для сравнения
        new_email = form.email.data.lower()
        current_email = current_user.email.lower()

        # Проверяем, был ли изменен пароль или почта
        email_changed = current_email != new_email
        password_changed = form.new_password.data != ''

        # Проверяем, занята ли новая почта другим пользователем
        if email_changed:
            existing_user = User.query.filter_by(email=new_email).first()
            if existing_user:
                return jsonify({'success': False, 'errors': {'email': ['Эта почта уже используется.']}})

        # Проверяем текущий пароль, если требуется
        if (email_changed or password_changed) and not bcrypt.check_password_hash(current_user.password, form.current_password.data):
            # Неверный текущий пароль
            return jsonify({'success': False, 'errors': {'current_password': ['Неверный текущий пароль']}})

        # Обновляем данные пользователя
        current_user.full_name = form.full_name.data
        if email_changed:
            current_user.email = new_email
        if password_changed:
            # Обновляем пароль, если он был изменен
            # Генерируем хеш пароля только если новый пароль не пустой
            if form.new_password.data:
                current_user.password = bcrypt.generate_password_hash(form.new_password.data).decode('utf-8')

        db.session.commit()
        # Успешное обновление данных пользователя
        return jsonify({'success': True, 'redirect': url_for('profile', user_id=current_user.id)})

    # Обработка ошибок валидации формы
    errors = {field: errors for field, errors in form.errors.items()}
    print("Validation failed with errors:", form.errors)
    return jsonify({'success': False, 'errors': errors})


@app.route('/delete_account', methods=['POST'])
@login_required
def delete_account():
    user_id = current_user.id
    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Пользователь не найден.'}), 404


@app.route('/subscribe/<int:organaizer_id>', methods=['POST'])
@login_required
def subscribe(organaizer_id):
    organaizer = User.query.get_or_404(organaizer_id)
    if organaizer not in current_user.subscribed_organaizers:
        current_user.subscribed_organaizers.append(organaizer)
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Уже подписан'})

@app.route('/unsubscribe/<int:organaizer_id>', methods=['POST'])
@login_required
def unsubscribe(organaizer_id):
    organaizer = User.query.get_or_404(organaizer_id)
    if organaizer in current_user.subscribed_organaizers:
        current_user.subscribed_organaizers.remove(organaizer)
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Не подписан'})


@app.route('/edit_organaizer/<int:organaizer_id>', methods=['GET', 'POST'])
def edit_organaizer(organaizer_id):
    organaizer = User.query.get_or_404(organaizer_id)
    form = EditOrganaizerForm(obj=organaizer)
    if form.validate_on_submit():
        organaizer.full_name = form.full_name.data
        organaizer.short_description = form.short_description.data
        organaizer.full_description = form.full_description.data
        organaizer.address = form.address.data

        website = form.website.data
        if website and not urlparse(website).scheme:
            website = 'http://' + website
        organaizer.website = website

        # Обработка фотографии профиля
        # if form.profile_photo.data:  # Проверяем, был ли файл загружен
        #     file = form.profile_photo.data
        #     if hasattr(file, 'filename'):  # Проверяем, что file имеет атрибут filename
        #         filename = secure_filename(file.filename)
        #         if filename != '':  # Проверяем, что имя файла не пустое
        #             file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        #             file.save(file_path)
        #             # Замена обратных слэшей на прямые для совместимости с URL
        #             file_url = os.path.join('uploads', filename).replace(os.sep, '/')
        #             organaizer.profile_photo = file_url
        if form.profile_photo.data:
            file = form.profile_photo.data
            original_filename = secure_filename(file.filename)
            file_ext = os.path.splitext(original_filename)[1]
            unique_filename = f"{uuid.uuid4()}{file_ext}"
            new_file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(new_file_path)

            # Удаление старого файла, если он существует и не является файлом по умолчанию
            # old_file = organaizer.profile_photo
            # if old_file and old_file != 'default_user.jpg':
            #     old_file_path = os.path.join(app.config['UPLOAD_FOLDER'], old_file)
            #     if os.path.exists(old_file_path):
                    # os.remove(old_file_path)
            old_file = organaizer.profile_photo
            if old_file and old_file != 'default_user.jpg':
                old_file_path = os.path.join(app.root_path, 'static', organaizer.profile_photo)
                if os.path.exists(old_file_path) and old_file != 'default_user.jpg':
                    os.remove(old_file_path)

            # Обновление ссылки на файл в базе данных
            organaizer.profile_photo = os.path.join('uploads', unique_filename).replace('\\', '/')


        db.session.commit()
        return redirect(url_for('organaizer', nickname=organaizer.nickname))
    return render_template('edit_organaizer.html', title='Редактировать профиль', form=form, organaizer=organaizer)

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def org_settings():
    form = OrgSettingsForm(obj=current_user)
    if form.validate_on_submit():
        # Проверка текущего пароля с использованием bcrypt
        if not bcrypt.check_password_hash(current_user.password, form.current_password.data):
            flash('Неверный текущий пароль', 'error')
        else:
            # Обновление никнейма и почты с приведением к нижнему регистру
            current_user.nickname = form.nickname.data.lower()
            current_user.email = form.email.data.lower()

            # Обновление пароля, если новый пароль предоставлен
            if form.password.data:
                current_user.password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')

            db.session.commit()
            flash('Настройки успешно обновлены.', 'success')
            return redirect(url_for('org_settings'))
    elif form.errors:
        # Если в форме есть ошибки валидации
        flash('Пожалуйста, проверьте введенные данные.', 'error')

    return render_template('org_settings.html', form=form)


@app.route('/get_organaizers')
def get_organaizers():
    organaizers = User.query.filter_by(type='organaizer').all()
    return jsonify([
        {
            'nickname': organaizer.nickname, 
            'full_name': organaizer.full_name,
            'profile_photo': url_for('static', filename=organaizer.profile_photo) if organaizer.profile_photo else None
        }
        for organaizer in organaizers
    ])

@app.route('/create', methods=['GET', 'POST'])
@login_required
def create_event():
    if current_user.type != 'organaizer':
        return redirect(url_for('home'))
    
    form = EventForm()
    if form.validate_on_submit():
        filename = None
        if form.photo.data:
            original_filename = secure_filename(form.photo.data.filename)
            file_ext = os.path.splitext(original_filename)[1]  # Получаем расширение файла
            unique_filename = f"{uuid.uuid4()}{file_ext}"  # Создаем уникальное имя файла
            form.photo.data.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))
            filename = unique_filename
        else:
            filename = 'default_event.jpg'

        start_date = datetime.strptime(form.start_date.data, '%d.%m.%Y').date()
        end_date = None
        if form.event_type.data == 'ongoing':
            end_date = datetime.strptime(form.end_date.data, '%d.%m.%Y').date()

        # price_value = str(form.price.data) if form.price_option.data == 'number' else form.price_option.data

        event = Event(
            title=form.title.data,
            photo=filename if filename else 'default_event.jpg',
            event_type=form.event_type.data,
            start_date=start_date,
            end_date=end_date,
            start_time=form.start_time.data,
            address=form.address.data,
            organaizer_id=current_user.id,
            price=form.price.data,
            description=form.description.data
        )
        db.session.add(event)
        db.session.commit()

        # Перенаправление на страницу созданного события
        return redirect(url_for('show_event', event_id=event.id))
    
    return render_template('create_event.html', form=form)
     

@app.route('/event/<int:event_id>')
def show_event(event_id):
    event = Event.query.get_or_404(event_id)
    return render_template('event.html', event=event)


@app.route('/edit/<int:event_id>', methods=['GET', 'POST'])
@login_required
def edit_event(event_id):
    event = Event.query.get_or_404(event_id)
    if current_user.id != event.organaizer_id:
        abort(403)

    form = EventForm()
    if request.method == 'GET':
        form.title.data = event.title
        form.start_date.data = event.start_date.strftime('%d.%m.%Y') if event.start_date else ''
        form.end_date.data = event.end_date.strftime('%d.%m.%Y') if event.end_date else ''
        form.start_time.data = event.start_time
        form.address.data = event.address
        form.description.data = event.description
        form.event_type.data = event.event_type
        # form.price_option.data = 'number' if event.price and event.price.isdigit() else event.price
        form.price.data = event.price
        # int(event.price) if event.price and event.price.isdigit() else None
        # ... (остальные поля)
    else:
        if form.validate_on_submit():
            event.title = form.title.data
            if form.photo.data:
                if event.photo and event.photo != 'default_event.jpg':
                    old_file_path = os.path.join(app.config['UPLOAD_FOLDER'], event.photo)
                    if os.path.exists(old_file_path):
                        os.remove(old_file_path)

                # Сохранение нового файла
                original_filename = secure_filename(form.photo.data.filename)
                file_ext = os.path.splitext(original_filename)[1]
                unique_filename = f"{uuid.uuid4()}{file_ext}"
                form.photo.data.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))
                event.photo = unique_filename

                # filename = secure_filename(form.photo.data.filename)
                # form.photo.data.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                # event.photo = filename

            event.event_type = form.event_type.data
            event.start_date = datetime.strptime(form.start_date.data, '%d.%m.%Y').date()
            event.end_date = datetime.strptime(form.end_date.data, '%d.%m.%Y').date() if form.event_type.data == 'ongoing' else None
            event.start_time = form.start_time.data
            event.address = form.address.data
            event.description = form.description.data
            event.price = form.price.data 
            # str(form.price.data) if form.price_option.data == 'number' else form.price_option.data

            db.session.commit()
            return redirect(url_for('show_event', event_id=event.id))

    return render_template('edit_event.html', form=form, event=event)



@app.route('/delete_event/<int:event_id>', methods=['POST'])
@login_required
def delete_event(event_id):
    event = Event.query.get_or_404(event_id)
    if current_user.id != event.organaizer_id:
        return jsonify({'success': False, 'error': 'Нет доступа'}), 403

    # Проверка наличия файла изображения и его удаление
    if event.photo and event.photo != 'default_event.jpg':
        photo_path = os.path.join(app.config['UPLOAD_FOLDER'], event.photo)
        if os.path.exists(photo_path):
            os.remove(photo_path)

    db.session.delete(event)
    db.session.commit()
    return jsonify({'success': True})
