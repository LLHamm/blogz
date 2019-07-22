from flask import Flask, request, redirect, render_template, session, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.mysql import TEXT, DATETIME
from datetime import datetime

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://blogz:Bananas@localhost:8889/blogz'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)
app.secret_key = 'f367c577eac03b32a77ee55aa3179723'
# pylint: disable=no-member


class Blog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    body = db.Column(db.TEXT())
    created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __init__(self, title, body, owner):
        self.title = title
        self.body = body

        self.owner = owner

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(120))
    blogs = db.relationship('Blog', backref='owner')

    def __init__(self, email, password):
        self.email = email
        self.password = password

@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        verify = request.form['verify']

        validate_success = True
        if email.strip() == '':
            flash('Email address required', 'error')
            validate_success = False
        if verify != password:
            flash('Passwords do not match!','error')
            validate_success = False
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already in use', 'error')
            validate_success = False
        
        if validate_success:
            new_user = User(email, password)
            db.session.add(new_user)
            db.session.commit()
            return redirect('/login')        

    return render_template('register.html', title="Join uz!") 

@app.before_request
def require_login():
    allowed_routes = ['index', 'login', 'register']
    if request.endpoint not in allowed_routes and 'email' not in session:
        return redirect('/login')

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and user.password == password:
            session['email'] = email
            return redirect('/createnew')
        else:
            flash("User name or password incorrect", "error")            

    return render_template('login.html', title = 'Log in to Blogz')

@app.route('/logout')
def logout():
    del session['email']
    return redirect('/blog')

@app.route('/blog')
def blog():
    entries = Blog.query.all()
    return render_template('blog.html', title='Blogz', entries=entries, user_logged_in = 'email' in session)

@app.route('/createnew', methods=['GET', 'POST'])
def create_new():
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        if title.strip() == '' or body.strip() == '':
            flash('We need both a title and some actual text in the post.', 'error')
        else:
            user = User.query.filter_by(email = session['email']).first()
            blog_entry = Blog(title, body, user)
            db.session.add(blog_entry)
            db.session.commit()
            id = blog_entry.id
            return redirect('/showentry?id=' + str(id))        
    
    return render_template('new_entry.html', title='Create new entry', user_logged_in = True, hide_new = True)

@app.route('/showentry')
def show_entry(): 
    id = request.args.get('id', type = int)   
    blog_entry = Blog.query.filter_by(id=id).first()
    return render_template('entry.html', title = blog_entry.title, entry = blog_entry, user_logged_in = 'email' in session)

@app.route('/')
def index():
    users = User.query.all()
    return render_template('index.html', title='Blogz Userz', users=users, user_logged_in = 'email' in session)

@app.route('/showuserentries')
def show_user_entries():
    id = request.args.get('id', type = int)
    user = User.query.filter_by(id = id).first()
    entry_list = Blog.query.filter_by(owner=user).all()
    return render_template('blog.html', title='Blogz for ' + user.email, entries=entry_list, user_logged_in = 'email' in session)


    


if __name__ == '__main__':
    app.run()