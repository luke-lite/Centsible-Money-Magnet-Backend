from flask import request, session
from flask_restful import Resource
import two_factor

# Local imports
from config import app, db, api

from models import Household, User, Bank, Transactions, Categories, Goals, MonthlyExpenses, ExpenseItem

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
            return uri[1], newUser.to_dict()
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
            return newUser.to_dict()
        except Exception as e:
            print(e)
            return {'error': 'Account not Created'}, 402
        
api.add_resource(CreateUser, '/create_user')

# test curl command
# curl --header "Content-Type: application/json" \--request POST \--data '{"household_name":"test","key":"test","user_name":"xyz111122","password_hash":"xyz","first_name":"test","last_name":"test","email":"test@gmail","date_of_birth":"3/3/2023"}' \http://127.0.0.1:5555/create_user

class Login(Resource):
    def post(self):
        data = request.get_json()
        name = data['user_name']
        password = data['password']
        otpCode = data['otpCode']
        if user := User.query.filter(User.user_name == name).first():
            if user.authenticate(password) and two_factor.authenticateUser(OTPkey = user.OTPkey, OTPcode = otpCode):
                session['user_id'] = user.id
                return user.to_dict(rules = ["-uri"]), 200
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


if __name__ == '__main__':
    app.run(port=5555, debug=True)
