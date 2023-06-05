from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
import enum 

def connect_db(app):
    db = SQLAlchemy(app)
    bcrypt = Bcrypt(app)
    db.app = (app)
    db.init_app(app)


q_or_f_enum = db.Enum('quote', 'fact', name='q_or_f')
status_type_enum = db.Enum('approved', 'rejected', 'pending', name='status_type')
source_type_enum = db.Enum('book', 'game', 'movie', 'tv', name='source_type')

class Fact(db.Model):
    fact_id = db.Column(db.Integer, primary_key=True)
    source_id = db.Column(db.Integer, db.ForeignKey('source.id'))
    fact = db.Column(db.Text)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=True, nullable=False)
    admin = db.Column(db.Boolean)
    password_hash = db.Column(db.String(30), nullable=False)
    favorites = db.Column(db.Integer, db.ForeignKey('source.id'))
    email = db.Column(db.String(50))
    email_subscription = db.Column(db.Boolean, default=False)

    def __init__(self, username, password):
        self.username = username
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

class Submition(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    source = db.Column(db.String(50))
    body = db.Column(db.Text)
    username = db.Column(db.String(30), db.ForeignKey('user.username'))
    status = db.Column(status_type_enum)
    created_at = db.Column(db.TIMESTAMP)
    quote_or_fact = db.Column(q_or_f_enum)
    source_type = db.Column(source_type_enum)

class Source(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    source_name = db.Column(db.String(50))
    san_name = db.Column(db.String(50))
    source_type = db.Column(source_type_enum)
    users = db.relationship('User', secondary=favorites, backref=db.backref('favorites', lazy='dynamic'))

class Quote(db.Model):
    quote_id = db.Column(db.Integer, primary_key=True)
    source_id = db.Column(db.Integer, db.ForeignKey('source.id'))
    quote = db.Column(db.Text)

# Define the relationships
Fact.source = db.relationship('Source', backref='facts', lazy=True)
User.favorites_source = db.relationship('Source', backref='favorited_by', lazy=True)
Submition.user = db.relationship('User', backref='submitions', lazy=True)
Quote.source = db.relationship('Source', backref='quotes', lazy=True)
