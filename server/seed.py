# Standard library imports
from random import randint, choice as rc

# Remote library imports
from faker import Faker

from config import db, app

from models import User

if __name__ == '__main__':
    with app.app_context():
        print("Starting seed...")

        for _ in range(15):
            u = User(
                name=fake.name(),
                password_hash="123abc",
            )
            db.session.add(u)
            db.session.commit()
