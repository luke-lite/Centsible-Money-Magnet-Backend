from flask import request, session
from flask_restful import Resource
import two_factor
from datetime import datetime
import random


# Local imports
from config import app, db, api

from models import Household, User, Bank, Transactions, Categories, Goals, MonthlyExpenses, ExpenseItem, Backup_Codes, LoginAttempts

class CreateSuperUser(Resource):
    def post(self):
        try: 
            data = request.get_json()
            newHousehold = Household(name = data.get("household_name"), key = data.get("key"))
            db.session.add(newHousehold)
            db.session.commit()
            uri = two_factor.createNewURI(user_name = data.get("user_name"))
            newUser = User(user_name = data.get("user_name"), 
                           admin = True,
                           first_name = data.get("first_name"),
                           last_name = data.get("last_name"),
                           email = data.get("email"),
                           date_of_birth = data.get("date_of_birth"),
                           OTPkey = uri[0],
                           household_id = newHousehold.id
                           )
            newUser.password_hash = data.get("password_hash")

            db.session.add(newUser)
            db.session.commit()

            #backup code logic
            backup_codes = []
            for _ in range(4):
                new_backup_code =  Backup_Codes(user_id = newUser.id, backup_code = random.randint(1, 1000000000))
                backup_codes.append(new_backup_code)
                db.session.add(new_backup_code)
            db.session.commit()

            return [uri[1], newUser.to_dict(), [b.to_dict() for b in backup_codes]], 200
        except Exception as e:
            print(e)
            return {'error': 'Account not Created'}, 402
        
api.add_resource(CreateSuperUser, '/create_super_user')

# test curl command
# curl --header "Content-Type: application/json" \--request POST \--data '{"household_name":"test","key":"test","user_name":"xyz11","password_hash":"xyz","first_name":"test","last_name":"test","email":"test@gmail","date_of_birth":"3/3/2023"}' \http://127.0.0.1:5555/create_super_user

class CreateUser(Resource):
    def post(self):
        try: 
            data = request.get_json()
            householdName = data.get("household_name")
            householdKey = data.get("key")
            household = Household.query.filter(Household.name == householdName, Household.key == householdKey).first()

            uri = two_factor.createNewURI(user_name = data.get("user_name"))
            newUser = User(user_name = data.get("user_name"), 
                           admin = False,
                           first_name = data.get("first_name"),
                           last_name = data.get("last_name"),
                           email = data.get("email"),
                           date_of_birth = data.get("date_of_birth"),
                           OTPkey = uri[0],
                           household_id = household.id
                           )
            newUser.password_hash = data.get("password_hash")
            db.session.add(newUser)
            db.session.commit()

            #backup code logic
            backup_codes = []
            for _ in range(4):
                new_backup_code =  Backup_Codes(user_id = newUser.id, backup_code = random.randint(1, 1000000000))
                backup_codes.append(new_backup_code)
                db.session.add(new_backup_code)
            db.session.commit()

            return [uri[1], newUser.to_dict(), [b.to_dict() for b in backup_codes]], 200
        except Exception as e:
            print(e)
            return {'error': 'Account not Created'}, 402
        
api.add_resource(CreateUser, '/create_user')

# test curl command
# curl --header "Content-Type: application/json" \--request POST \--data '{"household_name":"test","key":"test","user_name":"xyz111122","password_hash":"xyz","first_name":"test","last_name":"test","email":"test@gmail","date_of_birth":"3/3/2023"}' \http://127.0.0.1:5555/create_user

class Login(Resource):
    def post(self):

        #logic for login attempts (max 5 attempts per every 3 hours)
        time_of_attempt = datetime.now()
        attempts = LoginAttempts.query.filter(LoginAttempts.ip_address == request.remote_addr, 
                                              LoginAttempts.attempt_date == time_of_attempt.date(),
                                              LoginAttempts.attempt_time >= (time_of_attempt.time().hour - 3),
                                              LoginAttempts.success == False
                                              ).all()
        if len(attempts) >= 4:
            return {'error': 'Too Many Attempts'}, 401

        data = request.get_json()
        name = data['user_name']
        password = data['password']
        otpCode = data['otpCode']
        if user := User.query.filter(User.user_name == name).first():
            if user.authenticate(password) and two_factor.authenticateUser(OTPkey = user.OTPkey, OTPcode = otpCode):
                session['user_id'] = user.id
                newLogin = LoginAttempts(ip_address = request.remote_addr, success = True)
                db.session.add(newLogin)
                db.session.commit()
                return user.to_dict(), 200
        newLogin = LoginAttempts(ip_address = request.remote_addr, success = False)
        db.session.add(newLogin)
        db.session.commit()
        return {'error': 'Unauthorized'}, 401


api.add_resource(Login, '/login')

# check session
class CheckSession(Resource):
    def get(self):
        if user := User.query.filter(User.id == session.get('user_id')).first():
            print(user)
            return user.to_dict(rules = ["-uri"])
        else:
            return {'message': '401: Not Authorized'}, 401


api.add_resource(CheckSession, '/check_session')

# logout
class Logout(Resource):
    def delete(self):
        session['user_id'] = None
        return {'message': '204: No Content'}


api.add_resource(Logout, '/logout')

class TwoFactorRecovery(Resource):
    def post(self):

        #logic for login attempts (max 5 attempts per every 3 hours)
        time_of_attempt = datetime.now()
        attempts = LoginAttempts.query.filter(LoginAttempts.ip_address == request.remote_addr, 
                                              LoginAttempts.attempt_date == time_of_attempt.date(),
                                              LoginAttempts.attempt_time >= (time_of_attempt.time().hour - 3),
                                              LoginAttempts.success == False
                                              ).all()
        if len(attempts) >= 4:
            return {'error': 'Too Many Attempts'}, 401

        data = request.get_json()
        name = data['user_name']
        password = data['password']
        backup_code = data['backup_code']
        backup_code_record = Backup_Codes.query.filter(Backup_Codes.backup_code == backup_code, Backup_Codes.used == False).first()
        if user := User.query.filter(User.user_name == name).first():
            if user.authenticate(password) and backup_code_record:
                #marks backup code as used
                backup_code_record.used = True

                #creates new 2-factor imformation
                uri = two_factor.createNewURI(user_name = data.get("user_name"))
                user.OTPkey = uri[0]

                #add login attempt
                newLogin = LoginAttempts(ip_address = request.remote_addr, success = True)
                db.session.add(newLogin)
                db.session.commit()

                #queries all backup remaining backup codes to return to the user
                backup_code_records = Backup_Codes.query.filter(Backup_Codes.user_id == user.id, Backup_Codes.used == False).all()

                return [uri[1], user.to_dict(), [b.to_dict() for b in backup_code_records]], 200
        newLogin = LoginAttempts(ip_address = request.remote_addr, success = False)
        db.session.add(newLogin)
        db.session.commit()
        return {'error': 'Unauthorized'}, 401


api.add_resource(TwoFactorRecovery, '/two_factor_recovery')


if __name__ == '__main__':
    app.run(port=5555, debug=True)
