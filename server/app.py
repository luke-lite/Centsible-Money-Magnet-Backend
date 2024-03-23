import os
import time
from datetime import date, timedelta

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

# plaid request section
import requests
# https://pypi.org/project/python-dotenv/
from dotenv import load_dotenv


import plaid
from plaid.api import plaid_api
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.transactions_sync_request import TransactionsSyncRequest
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.link_token_create_request_statements import LinkTokenCreateRequestStatements
from plaid.model.products import Products
from plaid.model.country_code import CountryCode

load_dotenv()


def empty_to_none(field):
    value = os.getenv(field)
    return None if value is None or len(value) == 0 else value


# plaid redirect uri is our website link
PLAID_REDIRECT_URI = empty_to_none('PLAID_REDIRECT_URI')

# error: certificate verify failed: unable to get local issuer certificate 
# solution: /Applications/Python*/Install\ Certificates.command

# env_vars = dotenv_values(".env")
secret_token = os.getenv('PLAID_SECRET')
access_id = os.getenv('PLAID_CLIENT_ID')
configuration = plaid.Configuration(
    host=plaid.Environment.Sandbox,
    api_key={
        'clientId': access_id,
        'secret': secret_token,
    }
)

api_client = plaid.ApiClient(configuration)
client = plaid_api.PlaidApi(api_client)

# PLAID_COUNTRY_CODES is a comma-separated list of countries for which users
# will be able to select institutions from.
PLAID_COUNTRY_CODES = os.getenv('PLAID_COUNTRY_CODES', 'US').split(',')

PLAID_PRODUCTS = os.getenv('PLAID_PRODUCTS', 'transactions').split(',')

products = [Products(product) for product in PLAID_PRODUCTS]
link_token = None
access_token = None
item_id = None


class PlaidCreateLinkToken(Resource):
    def post(self):  # sourcery skip: extract-method
        global link_token
        global secret_token
        global access_id
        print(secret_token, access_id)
        # print(client)
        try:
            request = LinkTokenCreateRequest(
                products=products,
                client_name="Sams Test",
                country_codes=list(
                    map(lambda x: CountryCode(x), PLAID_COUNTRY_CODES)),
                language='en',
                user=LinkTokenCreateRequestUser(
                    client_user_id=str(time.time())
                )
            )
            # print(request)

            # if PLAID_REDIRECT_URI != None:
            #     request['redirect_uri'] = PLAID_REDIRECT_URI
            # print(products)
            if Products('statements') in products:
                statements = LinkTokenCreateRequestStatements(
                    end_date=date.today(),
                    start_date=date.today()-timedelta(days=30)
                )
                request['statements'] = statements
            # # create link token
            response = client.link_token_create(request)
            link_token = response['link_token']
            print(link_token)
            return {'link_token': response['link_token']}
        except plaid.ApiException as e:
            print({'inside exception': e})
            return {'error': 'error'}, 500


api.add_resource(PlaidCreateLinkToken, '/getlinktoken')


class ExchangePublicToken(Resource):
    def post(self):
        global access_token
        global item_id
        public_token = request.get_json()['public_token']
        request = ItemPublicTokenExchangeRequest(
            public_token=public_token
        )
        response = client.item_public_token_exchange(request)
        # These values should be saved to a persistent database and
        # associated with the currently signed-in user
        access_token = response['access_token']
        item_id = response['item_id']
        return {'public_token_exchange': 'complete'}

api.add_resource(ExchangePublicToken, '/getpublictoken')



class PlaidDataRequest(Resource):
    def post(self):
        pt_token = request.get_json()['pt_token']
        try:
            exchange_request = ItemPublicTokenExchangeRequest(
                public_token=pt_token
            )
            exchange_response = client.item_public_token_exchange(
                exchange_request)
            access_token = exchange_response['access_token']
            request = TransactionsSyncRequest(
                access_token=access_token,
            )
            response = client.transactions_sync(request)
            transactions = response['added']
            # the transactions in the response are paginated, so make multiple calls while incrementing the cursor to
            # retrieve all transactions
            while (response['has_more']):
                request = TransactionsSyncRequest(
                    access_token=access_token,
                    cursor=response['next_cursor']
                )
                response = client.transactions_sync(request)
                transactions += response['added']
            return transactions, 200
        except plaid.ApiException as e:
            return {'message': e.message}, 500


class PlaidData(Resource):
    def post(self):
        data = request.get_json()
        public_token = data.get('public_token')
        endpoint_url = "plaid request"
        headers = {
            'Public-Token': public_token,
            'Secret-Token': secret_token,
            'Access-ID': access_id,
            'Content-Type': 'application/json'
        }
        try:
            response = requests.post(endpoint_url, headers=headers, json={})
            if not response.ok:
                return {'error': 'Failed to fetch external data'}, response.status_code
            external_data = response.json()
            public_access_token = external_data.get('public_access_token')
            try:
                endpoint_url = "plaid request"
                headers = {
                    'Public-Access-Token': public_access_token,
                    'Secret-Token': secret_token,
                    'Access-ID': access_id,
                    'Content-Type': 'application/json'
                }
                response = requests.post(
                    endpoint_url, headers=headers, json={})

            except Exception as e:
                return {'error': str(e)}, 500

                # return external_data, 200
        except Exception as e:
            return {'error': str(e)}, 500

# end of plaid request section

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
