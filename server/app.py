from flask import request, session
from flask_restful import Resource

# Local imports
from config import app, db, api

from models import Household, User, Bank, Transactions, Categories, Goals, MonthlyExpenses, ExpenseItem


class Login(Resource):
    def post(self):
        data = request.get_json()
        name = data['name']
        password = data['password']
        if user := User.query.filter(User.name == name).first():
            if user.authenticate(password):
                session['user_id'] = user.id
                return user.to_dict(), 200
        return {'error': 'Unauthorized'}, 401


api.add_resource(Login, '/login')

# check session
class CheckSession(Resource):
    def get(self):
        if user := User.query.filter(User.id == session.get('user_id')).first():
            return user.to_dict()
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
