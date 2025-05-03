from questsite import create_app
from questsite.models import db

app = create_app()

with app.app_context():
    db.create_all()
    print("База данных и таблицы успешно созданы.")
