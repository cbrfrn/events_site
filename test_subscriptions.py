from app.app import app
from app.database import db
from app.models import User

with app.app_context():
    # Получение посетителей
    visitor1 = User.query.filter_by(id=5).first()
    visitor2 = User.query.filter_by(id=6).first()

    # Получение всех организаторов
    all_organizers = User.query.filter_by(type='organaizer').all()

    # Посетитель 1 подписывается на всех организаторов
    for organizer in all_organizers:
        organizer.subscribed_visitors.append(visitor1)

    # Посетитель 2 подписывается только на первых двух организаторов
    all_organizers[0].subscribed_visitors.append(visitor2)
    all_organizers[1].subscribed_visitors.append(visitor2)

    # Сохранение изменений в базе данных
    db.session.commit()

    # Проверка подписок
    print(f"Организаторы, на которых подписан {visitor1.full_name}:")
    for org in visitor1.subscribed_organizers:
        print(org.full_name)

    print(f"Организаторы, на которых подписан {visitor2.full_name}:")
    for org in visitor2.subscribed_organizers:
        print(org.full_name)