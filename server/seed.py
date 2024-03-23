# Standard library imports
from random import randint, choice as rc

# Remote library imports
from faker import Faker

from config import db, app

from models import User, Household

import two_factor

import qrcode

if __name__ == '__main__':
    with app.app_context():
        # fake = Faker()

        # print("Starting seed...")

        # for _ in range(15):
        #     u = User(
        #         name=fake.name(),
        #         password_hash="123abc",
        #     )
        #     db.session.add(u)
        #     db.session.commit()

    #two factor test
        User.query.delete()
        Household.query.delete()

        newHousehold = Household(name = "Test Family", key = "secretkey")

        db.session.add(newHousehold)
        db.session.commit()

        print(newHousehold)

        uri = two_factor.createNewURI(user_name = "JoeTest")

        newUser = User(user_name = "JoeTest", 
                       admin = False, 
                       first_name = "John", 
                       last_name = "Doe", 
                       email = "johndoe@gmail.com", 
                       date_of_birth = "1/1/1980", 
                       OTPkey = uri[0],
                       household_id = newHousehold.id)
    
        newUser.password_hash = "JohnDoeSecretPassword"

        qrcode.make(uri[1]).save("test_totp.png")

        db.session.add(newUser)
        db.session.commit()
        
        


