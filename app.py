import os

from flask import Flask, request, render_template, redirect, flash, session, redirect
from flask_debugtoolbar import DebugToolbarExtension
from flask_sqlalchemy import SQLAlchemy
from forms import LoginForm, SignUpForm
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user
from flask_bcrypt import Bcrypt
from models import db, connect_db
from random import sample
from flask_mail import Message
from datetime import timedelta
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask (__name__)

app. config ['SQLALCHEMY _DATABASE_URI' = 'postgresql: ///
app. config ['SQLALCHEMY _TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', "it's a secret")
app. config ['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

app.config['MAIL_SERVER'] = 'placeholder'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'placeholder'
app.config['MAIL_PASSWORD'] = 'placeholder'

mail = Mail(app)

scheduler = BackgroundScheduler()
scheduler.add_job(send_weekly_emails, 'interval', weeks=1)
scheduler.start()

debug = DebugToolbarExtension (app)
login_manager = LoginManager(app)
connect_db(app)

class User(UserMixin, db.Model):
     id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=True, nullable=False)
    password_hash = db.Column(db.String(30), nullable=False)
    admin = db.Column(db.Boolean, default=False)

def __init__(self, username, password, admin=False):
        self.username = username
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        self.admin = admin

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

def send_weekly_email(user):
    favorites = user.favorites.all()
    quotes = sample(favorites, min(len(favorites), 5))
    facts = sample(favorites, min(len(favorites), 5))

    # Compose email message
    subject = 'Your Weekly Quotes and Facts'
    body = render_template('weekly_email.html', quotes=quotes, facts=facts)
    recipients = [user.email]

    # Send email
    msg = Message(subject=subject, recipients=recipients)
    msg.html = body
    mail.send(msg)

def send_weekly_emails():
    subscribed_users = User.query.filter_by(email_subscription=True).all()

    for user in subscribed_users:
        send_weekly_email(user)

    # Schedule the next weekly email sending
    next_week = datetime.now() + timedelta(weeks=1)
    scheduler.add_job(send_weekly_emails, 'date', run_date=next_week)

@app.context_processor
def inject_current_user():
    return dict(current_user=current_user)


@login_manager.user_loader
def load_user(username):
    return users.get(username)

# Home page
@app.route('/')
def home():
    if current_user.is_authenticated:
        favorites = current_user.favorites.all()
        quotes = sample(favorites, min(len(favorites), 5))
        facts = sample(favorites, min(len(favorites), 5))
    else:
        quotes = Quote.query.order_by(func.random()).limit(5).all()
        facts = Fact.query.order_by(func.random()).limit(5).all()
    
    return render_template('home.html', quotes=quotes, facts=facts)

#login
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect('/')
        else:
            flash('Invalid username or password.')
    return render_template('login.html', form=form)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignUpForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        email = form.email.data

        # Check if the username is already taken
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists. Please choose a different username.')
            return redirect('/signup')

        # Create a new user
        new_user = User(username=username, password=password, email=email)
        db.session.add(new_user)
        db.session.commit()

        flash('Account created successfully! You can now log in.')
        return redirect('/login')

    return render_template('signup.html', form=form)

#admin page
@app.route('/admin')
@login_required
def admin():
    if not user.admin:
        flash('Access Denied. Admins Only.')
        return redirect('/')
    pending_submissions = Submission.query.filter_by(status='pending').all()

    return render_template('admin.html', submissions=pending_submissions)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')

@app.errorhandler(403)
def forbidden_error(error):
    return render_template('403.html'), 403

# sources of quotes and facts
@app.route('/sources', methods=['GET', 'POST'])
def sources():
    source_type_filter = request.form.get('source_type')
    query = Source.query

    if source_type_filter:
        query = query.filter_by(source_type=source_type_filter)

    sorted_sources = query.order_by(Source.source_name).all()

    return render_template('sources.html', sources=sorted_sources, source_type_filter=source_type_filter)


@app.route('/favorites')
@login_required
def favorites():
    user = current_user
    return render_template('favorites.html', user=user)

@app.route('/submit', methods=['GET', 'POST'])
@login_required
def submit():
    form = SubmissionForm()
    form.username.data = current_user.username  # Set the current user's username

    # Hide the 'username' and 'status' fields from the user
    form.username.render_kw = {'style': 'display:none;'}
    form.status.render_kw = {'style': 'display:none;'}
    form.status.data = 'pending'  # Set the default value for 'status'

    if form.validate_on_submit():
        source = form.source.data
        body = form.body.data
        quote_or_fact = form.quote_or_fact.data

        new_submission = Submission(source=source, body=body, username=current_user.username, status='pending', quote_or_fact=quote_or_fact)
        db.session.add(new_submission)
        db.session.commit()

        flash('Submission added successfully!')
        return redirect('/')

@app.route('/process_submission/<int:submission_id>', methods=['POST'])
@login_required
def process_submission(submission_id):
    if not current_user.admin:
        flash('Admins Only.')
        return redirect('/')  

    submission = Submission.query.get_or_404(submission_id)

    if submission.status != 'pending':
        flash('Submission has already been processed.')
        return redirect('/admin')

    if request.form.get('approve'):
        # Create a new quote or fact based on the submission
        if submission.quote_or_fact == 'quote':
            new_quote = Quote(source=submission.source, quote=submission.body)
            db.session.add(new_quote)
            db.session.commit()
        elif submission.quote_or_fact == 'fact':
            new_fact = Fact(source=submission.source, fact=submission.body)
            db.session.add(new_fact)
            db.session.commit()

        submission.status = 'approved'
        db.session.commit()

        flash('Submission approved and added to the database.')
    elif request.form.get('deny'):
        submission.status = 'rejected'
        db.session.commit()

        flash('Submission rejected.')

    return redirect('/admin')

    return render_template('submit.html', form=form)

@app.route('/subscribe', methods=['POST'])
@login_required
def subscribe():
    current_user.email_subscription = True
    db.session.commit()
    flash('Successfully subscribed to weekly email.')
    return redirect(url_for('home'))

@app.route('/unsubscribe', methods=['POST'])
@login_required
def unsubscribe():
    current_user.email_subscription = False
    db.session.commit()
    flash('Successfully unsubscribed from weekly email.')
    return redirect(url_for('home'))



if __name__ == '__main__':
    app.run(debug=True)