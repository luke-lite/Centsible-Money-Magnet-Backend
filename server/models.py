from sqlalchemy.orm import validates
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy_serializer import SerializerMixin
from sqlalchemy.ext.hybrid import hybrid_property


from config import db, bcrypt

class User(db.Model, SerializerMixin):
    # using illicit table names for now
    __tablename__ = 'users_table'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable = False, unique = True)
    _password_hash = db.Column(db.String, nullable=False)
    admin = db.Column(db.Boolean)

    # foreign keys
    # household_id = db.Column(db.Integer, db.ForeignKey("household_table.id"))



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
    # using illicit table names for now
    __tablename__ = 'bank_table'

    id = db.Column(db.Integer, primary_key=True)
    public_token = db.Column(db.String,nullable=False, unique = True)
    bank_name = db.Column(db.String, nullable=False)
    account_type = db.Column(db.String, nullable=False)

    # foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey("users_table.id"))


class Transactions(db.Model, SerializerMixin):
    # using illicit table names for now
    __tablename__ = 'transactions_table'

    id = db.Column(db.Integer, primary_key=True)
    transaction_description = db.Column(db.String,nullable=False)

    # foreign keys
    bank_id = db.Column(db.Integer, db.ForeignKey("bank_table.id"))
    category_id = db.Column(db.Integer, db.ForeignKey("category_table.id"))

class Categories(db.Model, SerializerMixin):
    # using illicit table names for now
    __tablename__ = 'category_table'

    id = db.Column(db.Integer, primary_key=True)
    category_name = db.Column(db.String, nullable=False)
    category_description = db.Column(db.String, nullable=False)
    category_type = db.Column(db.Boolean, nullable=False)

