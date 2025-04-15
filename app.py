# app.py
from flask import Flask, render_template, request, redirect, url_for, flash, session
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
from datetime import datetime
import os
from dotenv import load_dotenv
import timeago
from datetime import datetime
from bson import ObjectId




# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key')

# Configure MongoDB Atlas connection
MONGO_URI = os.getenv('MONGODB_URI')
if not MONGO_URI:
    raise ValueError("Missing MONGODB_URI in environment variables")

app.config["MONGO_URI"] = MONGO_URI

# mongo = PyMongo(app)

# Database collections
client = MongoClient("mongodb+srv://root:root@cluster0.2chuo.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client['internship_db']
users = db['users']
internships = db['internships']
applications = db['applications']

# Authentication check decorator
def login_required(f):
    def wrapper(*args, **kwargs):
        if 'user' not in session:
            flash('Please login to access this page', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper


@app.template_filter('timeago')
def timeago_filter(date):
    return timeago.format(date, datetime.now())
 

# Routes
@app.route('/')
def home():
    featured_internships = list(internships.find().sort('posted_date', -1).limit(5))
    return render_template('index.html', internships=featured_internships)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Check if user already exists
        if users.find_one({'email': request.form['email']}):
            flash('Email already registered', 'danger')
            return redirect(url_for('register'))
        
        # Create new user
        new_user = {
            'name': request.form['name'],
            'email': request.form['email'],
            'password': generate_password_hash(request.form['password']),
            'role': request.form['role'],  # 'student' or 'employer'
            'created_at': datetime.now()
        }
        
        # Additional fields for students
        if request.form['role'] == 'student':
            new_user.update({
                'university': request.form.get('university', ''),
                'major': request.form.get('major', ''),
                'grad_year': request.form.get('grad_year', '')
            })
        # Additional fields for employers
        elif request.form['role'] == 'employer':
            new_user.update({
                'company': request.form.get('company', ''),
                'industry': request.form.get('industry', ''),
                'website': request.form.get('website', '')
            })
            
        users.insert_one(new_user)
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
        
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = users.find_one({'email': email})
        
        if user and check_password_hash(user['password'], password):
            # Create session
            session['user'] = {
                'id': str(user['_id']),
                'name': user['name'],
                'email': user['email'],
                'role': user['role']
            }
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('You have been logged out', 'info')
    return redirect(url_for('home'))

from datetime import datetime

@app.route('/dashboard')
@login_required
def dashboard():
    user_id = session['user']['id']
    user_role = session['user']['role']
    
    if user_role == 'student':
        # Get student's applied internships
        my_applications = list(applications.find({'student_id': user_id}))
        internship_ids = [ObjectId(app['internship_id']) for app in my_applications]
        
        applied_internships = []
        if internship_ids:
            applied_internships = list(internships.find({'_id': {'$in': internship_ids}}))
            
        # Match applications with internships for status
        for internship in applied_internships:
            for application in my_applications:
                if str(internship['_id']) == application['internship_id']:
                    internship['application_status'] = application['status']
                    break
                    
        recommended_internships = list(internships.find().limit(3))
        return render_template('student_dashboard.html', 
                              applied_internships=applied_internships, 
                              recommended_internships=recommended_internships, 
                              now=datetime.now())
    
    elif user_role == 'employer':
        # Get employer's posted internships
        my_internships = list(internships.find({'employer_id': user_id}))
        
        # Get applications for each internship
        for internship in my_internships:
            internship['applications_count'] = applications.count_documents({'internship_id': str(internship['_id'])})
            
        return render_template('employer_dashboard.html', internships=my_internships, now=datetime.now())

@app.route('/internships')
def browse_internships():
    query = {}
    search = request.args.get('search', '')
    category = request.args.get('category', '')
    
    if search:
        query['$or'] = [
            {'title': {'$regex': search, '$options': 'i'}},
            {'company': {'$regex': search, '$options': 'i'}},
            {'description': {'$regex': search, '$options': 'i'}}
        ]
    
    if category and category != 'all':
        query['category'] = category
    
    all_internships = list(internships.find(query).sort('posted_date', -1))
    categories = internships.distinct('category')
    
    return render_template('browse_internships.html', 
                          internships=all_internships, 
                          categories=categories,
                          search=search,
                          selected_category=category)

@app.route('/internships/<id>')
def view_internship(id):
    internship = internships.find_one({'_id': ObjectId(id)})
    if not internship:
        flash('Internship not found', 'danger')
        return redirect(url_for('browse_internships'))
    
    employer = users.find_one({'_id': ObjectId(internship['employer_id'])})
    
    # Check if user has already applied
    already_applied = False
    if 'user' in session:
        already_applied = applications.find_one({
            'internship_id': id,
            'student_id': session['user']['id']
        }) is not None
    
    return render_template('internship_details.html', 
                          internship=internship, 
                          employer=employer,
                          already_applied=already_applied)

from datetime import datetime
from flask import render_template, request, redirect, url_for, flash, session
from functools import wraps

# Assuming you have a decorator for login_required
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            flash('You need to log in first', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/post-internship', methods=['GET', 'POST'])
@login_required
def post_internship():
    # Check if the user is an employer before allowing them to post internships
    if session['user']['role'] != 'employer':
        flash('Only employers can post internships', 'danger')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        # Validate the incoming data (you can add more validation if necessary)
        try:
            new_internship = {
                'title': request.form['title'],
                'company': request.form['company'],
                'location': request.form['location'],
                'description': request.form['description'],
                'requirements': request.form['requirements'],
                'category': request.form['category'],
                'duration': request.form['duration'],
                'is_paid': 'is_paid' in request.form,
                'salary': request.form.get('salary', ''),  # Default to empty string if no salary provided
                'employer_id': session['user']['id'],
                'posted_date': datetime.now(),
                'deadline': datetime.strptime(request.form['deadline'], '%Y-%m-%d')
            }
            
            # Insert the internship into the MongoDB collection (assuming it's named 'internships')
            internships.insert_one(new_internship)
            
            flash('Internship posted successfully!', 'success')
            return redirect(url_for('dashboard'))
        
        except Exception as e:
            flash(f'Error posting internship: {str(e)}', 'danger')
            return render_template('post_internship.html', user=session['user'])
    
    # Render the post internship page, passing the user information to the template
    return render_template('post_internship.html', user=session['user'])


@app.route('/apply/<internship_id>', methods=['GET', 'POST'])
@login_required
def apply_internship(internship_id):
    if session['user']['role'] != 'student':
        flash('Only students can apply for internships', 'danger')
        return redirect(url_for('view_internship', id=internship_id))
    
    internship = internships.find_one({'_id': ObjectId(internship_id)})
    if not internship:
        flash('Internship not found', 'danger')
        return redirect(url_for('browse_internships'))
    
    # Check if already applied
    existing_application = applications.find_one({
        'internship_id': internship_id,
        'student_id': session['user']['id']
    })
    
    if existing_application:
        flash('You have already applied for this internship', 'info')
        return redirect(url_for('view_internship', id=internship_id))
    
    if request.method == 'POST':
        new_application = {
            'internship_id': internship_id,
            'student_id': session['user']['id'],
            'cover_letter': request.form['cover_letter'],
            'resume_link': request.form['resume_link'],  # In a real app, handle file uploads
            'status': 'pending',
            'applied_date': datetime.now()
        }
        
        applications.insert_one(new_application)
        flash('Application submitted successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('apply_internship.html', internship=internship)

@app.route('/applications/<internship_id>')
@login_required
def view_applications(internship_id):
    if session['user']['role'] != 'employer':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    internship = internships.find_one({'_id': ObjectId(internship_id)})
    
    # Verify ownership
    if internship['employer_id'] != session['user']['id']:
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get all applications for this internship
    all_applications = list(applications.find({'internship_id': internship_id}))
    
    # Get student information for each application
    for application in all_applications:
        student = users.find_one({'_id': ObjectId(application['student_id'])})
        application['student'] = student
    
    return render_template('view_applications.html', 
                          applications=all_applications, 
                          internship=internship)

@app.route('/update-application-status/<application_id>', methods=['POST'])
@login_required
def update_application_status(application_id):
    if session['user']['role'] != 'employer':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    # Ensure ObjectId conversion
    try:
        application_id = ObjectId(application_id)
    except Exception as e:
        flash('Invalid application ID', 'danger')
        return redirect(url_for('dashboard'))
    
    application = applications.find_one({'_id': application_id})
    if not application:
        flash('Application not found', 'danger')
        return redirect(url_for('dashboard'))
    
    internship = internships.find_one({'_id': ObjectId(application['internship_id'])})
    
    # Verify ownership
    if internship['employer_id'] != session['user']['id']:
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    new_status = request.form['status']
    
    # Update the application status
    applications.update_one(
        {'_id': application_id},
        {'$set': {'status': new_status}}
    )
    
    flash('Application status updated', 'success')
    return redirect(url_for('view_applications', internship_id=application['internship_id']))

@app.route('/profile')
@login_required
def profile():
    user_id = session['user']['id']
    user = users.find_one({'_id': ObjectId(user_id)})
    
    return render_template('profile.html', user=user)

@app.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    user_id = session['user']['id']
    user = users.find_one({'_id': ObjectId(user_id)})

    if request.method == 'POST':
        # Basic information
        updates = {
            'name': request.form['name'],
            'email': request.form['email']
        }

        # Role-specific information
        if user['role'] == 'student':
            updates.update({
                'university': request.form['university'],
                'major': request.form['major'],
                'grad_year': request.form['grad_year'],
                'skills': request.form.get('skills', ''),
                'bio': request.form.get('bio', '')
            })
        elif user['role'] == 'employer':
            updates.update({
                'company': request.form['company'],
                'industry': request.form['industry'],
                'website': request.form['website'],
                'company_bio': request.form.get('company_bio', '')
            })

        # Update the user document
        users.update_one({'_id': ObjectId(user_id)}, {'$set': updates})
        flash('Profile updated successfully', 'success')
        return redirect(url_for('profile'))

    return render_template('edit_profile.html', user=user)


if __name__ == '__main__':
    app.run(debug=True)