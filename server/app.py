from flask import request, make_response, session
from flask_restful import Resource

# Local imports
from config import app, db, api

from models import Household, User, Bank, Transactions, Categories, Goals, MonthlyExpenses, ExpenseItem


if __name__ == '__main__':
    app.run(port=5555, debug=True)