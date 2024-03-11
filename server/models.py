from sqlalchemy.orm import validates
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy_serializer import SerializerMixin
from sqlalchemy.ext.hybrid import hybrid_property


from config import db, bcrypt

class Household(db.Model, SerializerMixin):
    # using specific table names for now
    __tablename__ = 'household_table'

    id = db.Column(db.Integer, primary_key=True)


class User(db.Model, SerializerMixin):
    # using specific table names for now
    __tablename__ = 'users_table'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable = False, unique = True)
    _password_hash = db.Column(db.String, nullable=False)
    admin = db.Column(db.Boolean)

    # foreign keys
    household_id = db.Column(db.Integer, db.ForeignKey("household_table.id"))



    @hybrid_property
    def password_hash(self):
        return self._password_hash

    @password_hash.setter
    def password_hash(self, password):
        # utf-8 encoding and decoding is required in python 3
        password_hash = bcrypt.generate_password_hash(
            password.encode('utf-8'))
        self._password_hash = password_hash.decode('utf-8')

    def authenticate(self, password):
        return bcrypt.check_password_hash(
            self._password_hash, password.encode('utf-8'))
    
class Bank(db.Model, SerializerMixin):
    # using specific table names for now
    __tablename__ = 'bank_table'

    id = db.Column(db.Integer, primary_key=True)
    public_token = db.Column(db.String,nullable=False, unique = True)
    bank_name = db.Column(db.String, nullable=False)
    account_type = db.Column(db.String, nullable=False)

    # foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey("users_table.id"))


class Transactions(db.Model, SerializerMixin):
    # using specific table names for now
    __tablename__ = 'transactions_table'

    id = db.Column(db.Integer, primary_key=True)
    transaction_description = db.Column(db.String,nullable=False)

    # foreign keys
    bank_id = db.Column(db.Integer, db.ForeignKey("bank_table.id"))
    category_id = db.Column(db.Integer, db.ForeignKey("category_table.id"))

class Categories(db.Model, SerializerMixin):
    # using specific table names for now
    __tablename__ = 'category_table'

    id = db.Column(db.Integer, primary_key=True)
    category_name = db.Column(db.String, nullable=False)
    category_description = db.Column(db.String, nullable=False)
    category_type = db.Column(db.Boolean, nullable=False)

class Goals(db.Model, SerializerMixin):
    # using specific table names for now
    __tablename__ = 'goals_table'

    id = db.Column(db.Integer, primary_key=True)
    household_budget = db.Column(db.Boolean, nullable=False)
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.String, nullable=False)
    target_amount = db.Column(db.String, nullable=False)
    current_amount = db.Column(db.String, nullable=False)
    deadline = db.Column(db.String, nullable=False)

    #foreign keys
    user_id = db.Column(db.String, db.Foreignkey("user_table.id"))
    household_id = db.Column(db.String, db.Foreignkey("household_table.id"))

class MonthlyExpenses(db.Model, SerializerMixin):
    # using specific table names for now
    __tablename__ = 'monthly_expenses_table'

    # both foreign and primary?
    id = db.Column(db.Integer, db.Foreignkey("expense_item_table.monthly_expenses_id"), primary_key=True)
    is_household_budget = db.Column(db.Boolean, nullable=False)
    user_expected_income = db.Column(db.String, nullable=False)
    actual_income = db.Column(db.String, nullable=False)
    user_expected_monthly_expenses_total = db.Column(db.String, nullable=False)
    is_fluctuating_income = db.Column(db.Boolean, nullable=False)

    #foreign keys
    user_id = db.Column(db.String, db.Foreignkey("user_table.id"))
    household_id = db.Column(db.String, db.Foreignkey("household_table.id"))