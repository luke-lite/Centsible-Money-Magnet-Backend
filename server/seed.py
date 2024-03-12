from config import db, app

if __name__ == '__main__':
    with app.app_context():
        print("Starting seed...")

