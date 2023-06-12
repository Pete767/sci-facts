import os
from flask import Flask, request, render_template, redirect, flash, session, url_for, jsonify
from flask_debugtoolbar import DebugToolbarExtension
from flask_sqlalchemy import SQLAlchemy
from forms import LoginForm, SignUpForm, SubmissionForm, SearchForm
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user
from flask_bcrypt import Bcrypt
from models import db, connect_db, Quote, User, Submission, Fact, Source
from random import sample
from flask_mail import Mail, Message
from datetime import timedelta, datetime
from apscheduler.schedulers.background import BackgroundScheduler
from game_list import game_list
from movie_list import movie_list
from tv_list import tv_list
from book_list import book_list
from flask_bootstrap import Bootstrap
from sqlalchemy import func, Enum, exc
from fuzzywuzzy import fuzz

app = Flask (__name__, static_url_path='/static')

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///sci_facts'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', "it's a secret")
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

app.config['MAIL_SERVER']='sandbox.smtp.mailtrap.io'
app.config['MAIL_PORT'] = 2525
app.config['MAIL_USERNAME'] = '01135db1e4bb46'
app.config['MAIL_PASSWORD'] = '188d53688c2456'
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False

mail = Mail(app)
bootstrap = Bootstrap(app)
bcrypt = Bcrypt(app)
db.init_app(app)

debug = DebugToolbarExtension (app)
login_manager = LoginManager(app)
connect_db(app)

@app.context_processor
def inject_current_user():
    return dict(current_user=current_user)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


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

scheduler = BackgroundScheduler()
scheduler.add_job(send_weekly_emails, 'interval', weeks=1)
scheduler.start()

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

    search_form = SearchForm()
    
    return render_template('home.html', quotes=quotes, facts=facts, search_form = search_form)

#login
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    search_form = SearchForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect('/')
        else:
            flash('Invalid username or password.')
    return render_template('login.html', form=form, search_form = search_form)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignUpForm()
    search_form = SearchForm()

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
        new_user = User(username=username, password=password, email=email, admin=False)
        db.session.add(new_user)
        db.session.commit()

        flash('Account created successfully! You can now log in.')
        return redirect('/login')

    return render_template('signup.html', form=form, search_form = search_form)

#admin page
@app.route('/admin')
@login_required
def admin():
    if not current_user.admin:
        flash('Access Denied. Admins Only.')
        return redirect('/')

    pending_submissions = Submission.query.filter_by(status='pending').all()
    search_form = SearchForm()

    return render_template('admin.html', submissions=pending_submissions, search_form = search_form)

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
    form = SubmissionForm()

    if source_type_filter:
        query = query.filter_by(source_type=source_type_filter)

    sorted_sources = query.order_by(Source.source_name).all()

    search_form = SearchForm()

    return render_template('sources.html', sources=sorted_sources, source_type_filter=source_type_filter, search_form=search_form)


@app.route('/favorites')
@login_required
def favorites():
    user = current_user
    favorite_sources = user.favorites.all()
    search_form = SearchForm()

    return render_template('favorites.html', user=user, search_form = search_form, sources=favorite_sources)

@app.route('/toggle_favorite/<int:source_id>', methods=['POST'])
@login_required
def toggle_favorite(source_id):
    source = Source.query.get_or_404(source_id)

    if source in current_user.favorites:
        current_user.favorites.remove(source)
        action = 'remove'
    else:
        current_user.favorites.append(source)
        action = 'add'

    db.session.commit()

    return jsonify({'action': action})

@app.route('/submit', methods=['GET', 'POST'])
@login_required
def submit():
    form = SubmissionForm()
    form.username.data = current_user.username  

    # Hide the 'username' and 'status' fields from the user
    form.username.render_kw = {'style': 'display:none;'}
    form.status.render_kw = {'style': 'display:none;'}
    form.status.data = 'pending'  

    search_form = SearchForm()

    if form.validate_on_submit():
        source = form.source.data
        body = form.body.data
        quote_or_fact = form.quote_or_fact.data

        new_submission = Submission(source=source, body=body, username=current_user.username, status='pending', quote_or_fact=quote_or_fact)
        db.session.add(new_submission)
        db.session.commit()

        flash('Submission added successfully!')
        return redirect('/')
    return render_template('submit.html', form=form, search_form = search_form)

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
    return redirect("/")

@app.route('/unsubscribe', methods=['POST'])
@login_required
def unsubscribe():
    current_user.email_subscription = False
    db.session.commit()
    flash('Successfully unsubscribed from weekly email.')
    return redirect("/")

@app.route('/add_sources', methods=['POST'])
def add_sources():
    games = game_list  # List of games
    movies = movie_list # List of movies
    tv_shows = tv_list  # List of TV shows
    books = book_list # List of books

    sources_added = 0

    # Add games to sources database with source_type as "game"
    for game in games:
        if not source_exists(game.strip(), "game"):
            source = Source(source_name=game.strip(), source_type="game")
            db.session.add(source)
            sources_added += 1

    # Add movies to sources database with source_type as "movie"
    for movie in movies:
        if not source_exists(movie.strip(), "movie"):
            source = Source(source_name=movie.strip(), source_type="movie")
            db.session.add(source)
            sources_added += 1

    # Add TV shows to sources database with source_type as "tv"
    for tv_show in tv_shows:
        if not source_exists(tv_show.strip(), "tv"):
            source = Source(source_name=tv_show.strip(), source_type="tv")
            db.session.add(source)
            sources_added += 1

    #abb books to sources with source_type as "book"
    for book in books:
        if not source_exists(book.strip(), "book"):
            source = Source(source_name=book.strip(), source_type="book")
            db.session.add(source)
            sources_added += 1


    db.session.commit()
    return f"{sources_added} sources added successfully"

def source_exists(source_name, source_type):
    # Check if a source with the given title and source_type already exists in the database
    existing_source = Source.query.filter(func.lower(Source.source_name) == func.lower(source_name), Source.source_type == source_type).first()
    return existing_source is not None

with app.app_context():
    db.metadata.create_all(bind=db.engine, checkfirst=True)

@app.route('/sources/<int:source_id>')
def source_details(source_id):
    source = Source.query.get(source_id)
    facts = Fact.query.filter_by(source_id=source_id).all()
    quotes = Quote.query.filter_by(source_id=source_id).all()
    search_form = SearchForm()
    return render_template('source_details.html', source=source, facts=facts, quotes=quotes, search_form = search_form)

@app.route('/search', methods=['POST'])
def search():
    search_form = SearchForm(request.form)
    if search_form.validate_on_submit():
        search_query = search_form.search.data

        all_sources = Source.query.all()
        similar_sources = []
        for source in all_sources:
            similarity_score = fuzz.ratio(search_query.lower(), source.source_name.lower())
            if similarity_score > 70 or search_query.lower() in source.source_name.lower():
                similar_sources.append(source)

        # Perform search logic based on the search_query
        return render_template('search_results.html', search_query=search_query, search_form=search_form, similar_sources=similar_sources)
    return render_template('search_results.html', search_form=search_form)

@app.route('/unfavorite/<int:source_id>', methods=['POST'])
@login_required  
def unfavorite(source_id):
    source = Source.query.get_or_404(source_id)
    current_user.favorites.remove(source)
    db.session.commit()
    return redirect(url_for('sources'))

@app.route('/add_favorites', methods=['GET'])
@login_required 
def add_favorites():
    favorite_sources = current_user.favorites.all()
    return render_template('favorites.html', sources=favorite_sources)

if __name__ == '__main__':
    with app.app_context():
        
        app.run(debug=True)