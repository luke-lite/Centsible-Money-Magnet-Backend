from sqlalchemy.orm import validates
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy_serializer import SerializerMixin
from sqlalchemy.ext.hybrid import hybrid_property


from config import db, bcrypt


class Household(db.Model, SerializerMixin):
    # using specific table names for now
    __tablename__ = 'household_table'

    id = db.Column(db.Integer, primary_key=True)

    # relationships
    goals = db.relationship(
        'Goals', back_populates='household', cascade='all, delete-orphan')
    monthly_expenses = db.relationship(
        'MonthlyExpenses', back_populates='household', cascade='all, delete-orphan')

    # serialize rule
    serialize_rules = ['-goals.household', '-monthly_expenses.household']

    def __repr__(self):
        return f'<Household {self.id}>'


class User(db.Model, SerializerMixin):
    # using specific table names for now
    __tablename__ = 'users_table'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False, unique=True)
    _password_hash = db.Column(db.String, nullable=False)
    admin = db.Column(db.Boolean)

    # foreign keys
    household_id = db.Column(db.Integer, db.ForeignKey("household_table.id"))

    # relationships
    banks = db.relationship('Bank', back_populates='user',
                            cascade='all, delete-orphan')
    goals = db.relationship('Goals', back_populates='user',
                            cascade='all, delete-orphan')
    monthly_expenses = db.relationship('MonthlyExpenses', back_populates='user',
                            cascade='all, delete-orphan')


    # serialize rule
    serialize_rules = ['-banks.user', '-goals.user', '-monthly_expenses.user']

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
    
    def __repr__(self):
        return f'<User {self.id}>'

    def __repr__(self):
        return f'<User {self.id}>'


class Bank(db.Model, SerializerMixin):
    # using specific table names for now
    __tablename__ = 'bank_table'

    id = db.Column(db.Integer, primary_key=True)
    public_token = db.Column(db.String, nullable=False, unique=True)
    bank_name = db.Column(db.String, nullable=False)
    account_type = db.Column(db.String, nullable=False)

    # foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey("users_table.id"))

    # relationships
    user = db.relationship('User', back_populates='banks')
    transactions = db.relationship('Transactions', back_populates='bank')

    # serialize rule
    serialize_rules = ['-user.banks', '-transactions.bank']

    def __repr__(self):
        return f'<Bank {self.id}>'


class Transactions(db.Model, SerializerMixin):
    # using specific table names for now
    __tablename__ = 'transactions_table'

    id = db.Column(db.Integer, primary_key=True)
    transaction_description = db.Column(db.String, nullable=False)

    # foreign keys
    bank_id = db.Column(db.Integer, db.ForeignKey("bank_table.id"))
    category_id = db.Column(db.Integer, db.ForeignKey("category_table.id"))

    # relationships
    bank = db.relationship('Bank', back_populates='transactions')
    category = db.relationship('Categories', back_populates='transaction')


    # serialize rule
    serialize_rules = ['-bank.transactions', '-category.transaction']

    def __repr__(self):
        return f'<Transactions {self.id}>'


class Categories(db.Model, SerializerMixin):
    # using specific table names for now
    __tablename__ = 'category_table'

    id = db.Column(db.Integer, primary_key=True)
    category_name = db.Column(db.String, nullable=False)
    category_description = db.Column(db.String, nullable=False)
    category_type = db.Column(db.Boolean, nullable=False)

    # relationships
    transaction = db.relationship(
        'Transactions', back_populates='category', cascade='all, delete-orphan')
    expense_items = db.relationship(
        'ExpenseItem', back_populates='category', cascade='all, delete-orphan')

    # serialize rule
    serialize_rules = ['-transaction.category', '-expense_items.category']

    def __repr__(self):
        return f'<Categories {self.id}>'


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

    # foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey("users_table.id"))
    household_id = db.Column(db.Integer, db.ForeignKey("household_table.id"))

    # relationships
    user = db.relationship('User', back_populates='goals')
    household = db.relationship('Household', back_populates='goals')

    # serialize rule
    serialize_rules = ['-user.goals', '-household.goals']

    def __repr__(self):
        return f'<Goals {self.id}>'

      
class MonthlyExpenses(db.Model, SerializerMixin):
    # using specific table names for now
    __tablename__ = 'monthly_expenses_table'

    id = db.Column(db.Integer, primary_key=True)
    is_household_budget = db.Column(db.Boolean, nullable=False)
    user_expected_income = db.Column(db.String, nullable=False)
    actual_income = db.Column(db.String, nullable=False)
    user_expected_monthly_expenses_total = db.Column(db.String, nullable=False)
    is_fluctuating_income = db.Column(db.Boolean, nullable=False)

    # foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey("users_table.id"))
    household_id = db.Column(db.Integer, db.ForeignKey("household_table.id"))

    # relationships
    user = db.relationship('User', back_populates='monthly_expenses')
    household = db.relationship('Household', back_populates='monthly_expenses')
    expense_items = db.relationship('ExpenseItem', back_populates='monthly_expenses',
                                    cascade='all, delete-orphan')

    # serialize rule
    serialize_rules = ['-user.monthly_expenses',
                       '-household.monthly_expenses',
                       '-expense_items.monthly_expenses']

    def __repr__(self):
        return f'<Monthly Expenses {self.id}>'


class ExpenseItem(db.Model, SerializerMixin):
    # using specific table names for now
    __tablename__ = 'expense_item_table'

    id = db.Column(db.Integer, primary_key=True)
    item_name = db.Column(db.String, nullable=False)
    item_desc = db.Column(db.String)
    planned_amount = db.Column(db.Integer, nullable=False)

    # foreign keys
    monthly_expenses_id = db.Column(
        db.Integer, db.ForeignKey("monthly_expenses_table.id"))
    category_id = db.Column(db.Integer, db.ForeignKey("category_table.id"))

    # relationships
    monthly_expenses = db.relationship(
        'MonthlyExpenses', back_populates='expense_items')
    category = db.relationship('Categories', back_populates='expense_items')

    # serialize rule
    serialize_rules = ['-monthly_expenses.expense_items',
                       '-category.expense_items']

    def __repr__(self):
        return f'<Expense Item {self.id}>'
