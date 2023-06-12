from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from sqlalchemy import Enum, exc
from flask_login import UserMixin

db = SQLAlchemy()
bcrypt = Bcrypt()

class Fact(db.Model):
    fact_id = db.Column(db.Integer, primary_key=True)
    source_id = db.Column(db.Integer, db.ForeignKey('source.id'))
    fact = db.Column(db.Text)

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(50))
    admin = db.Column(db.Boolean)
    email_subscription = db.Column(db.Boolean, default=False)

    def __init__(self, username, password, email, admin):
        self.username = username
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        self.email = email
        self.admin = admin

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

favorites = db.Table(
    'favorites',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('source_id', db.Integer, db.ForeignKey('source.id'))
)

class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    source = db.Column(db.String(80))
    body = db.Column(db.Text)
    username = db.Column(db.String(30), db.ForeignKey('user.username'))
    status = db.Column(Enum('approved', 'rejected', 'pending', name='status_type'))
    created_at = db.Column(db.TIMESTAMP)
    quote_or_fact = db.Column(Enum('quote', 'fact', name='q_or_f'))
    source_type = db.Column(Enum('book', 'game', 'movie', 'tv', name='source_type'))


class Source(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    source_name = db.Column(db.String(80))
    san_name = db.Column(db.String(80))
    source_type = db.Column(Enum('book', 'game', 'movie', 'tv', name='source_type'))
    users = db.relationship('User', secondary=favorites, backref=db.backref('favorites', lazy='dynamic'))

class Quote(db.Model):
    quote_id = db.Column(db.Integer, primary_key=True)
    source_id = db.Column(db.Integer, db.ForeignKey('source.id'))
    quote = db.Column(db.Text)

def connect_db(app):
    db.app = (app)

    with app.app_context():
        try:
            db.reflect()
        except exc.InternalError:
            pass


   
