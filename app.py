import json
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash

# Initializing the Flask app and configure it
app = Flask(__name__, template_folder='./templates')
app._static_folder = './static'
app.secret_key = 'your_secret_key'

# Database configuration deal
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///plannerpad.db'  # Database URI, we can change
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# User model to store user credentials and create the relationship with categories
class User(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

    # One-to-many relationship 1: Users can have multiple categories
    categories = db.relationship('Category', backref='user', lazy=True)

# Category model to store category names for each user
class Category(db.Model):
    category_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    category_name = db.Column(db.String(100), nullable=False)

    # One-to-many relationship 2: A category can have multiple tasks
    tasks = db.relationship('Task', backref='category', lazy=True)

# Task model to store tasks, which can be linked to a category, day, and time slot
class Task(db.Model):
    task_id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.category_id'), nullable=True)
    task_name = db.Column(db.String(255), nullable=False)
    assigned_day = db.Column(db.String(50), nullable=True)
    time_slot = db.Column(db.String(50), nullable=True)
    slot_number = db.Column(db.Integer, nullable=True)  # Slot number for the task (This slot number thing once I messed with it was key for everything to save.)
                                                        # I dont really fully understand it yet, but using it helped.
    # Task initialization
    def __init__(self, task_name, category_id=None, assigned_day=None, time_slot=None, slot_number=None):
        self.task_name = task_name
        self.category_id = category_id
        self.assigned_day = assigned_day
        self.time_slot = time_slot
        self.slot_number = slot_number

# Schedule model to store task assignments for specific days and time slots
class Schedule(db.Model):
    schedule_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('task.task_id'), nullable=False)
    day_of_week = db.Column(db.String(50), nullable=False)
    time_slot = db.Column(db.String(50), nullable=False)

# Create tables for a user if they don't exist
with app.app_context():
    db.create_all()

# Index route to display the main (index) page of the planner
@app.route('/index')
def index():
    user_id = session.get('user_id')
    if not user_id:
        flash('Please login to be able to use your planner!', 'danger')
        return redirect(url_for('login'))

    # Fetch categories from the DB for the current user
    categories = Category.query.filter_by(user_id=user_id).all()

    # If there are no categories, create placeholder names (this was tough bc the placeholders were unable to change at first, now they change)
    if not categories:
        categories = [f"Category {i}" for i in range(1, 8)]

    # Fetch any tasks linked to categories
    tasks = Task.query.filter(Task.category_id.in_([category.category_id for category in categories if hasattr(category, 'category_id')])).all() if categories else []

    # Fetch all schedules
    schedules = Schedule.query.all()

    days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    time_slots = ['7 AM', '8 AM', '9 AM', '10 AM', '11 AM', '12 PM', '1 PM', '2 PM', '3 PM', '4 PM', '5 PM', '6 PM', '7 PM', '8 PM', '9 PM']

    # Prepare the dictionaries for an easy lookup of tasks by category, day, and time
    tasks_by_category = {}
    for task in tasks:
        tasks_by_category.setdefault(task.category_id, []).append(task)

    tasks_by_day = {day: [] for day in days_of_week}
    for task in tasks:
        if task.assigned_day:
            tasks_by_day[task.assigned_day].append(task.task_name)

    time_schedule = {day: {} for day in days_of_week}
    for schedule in schedules:
        time_schedule[schedule.day_of_week][schedule.time_slot] = Task.query.get(schedule.task_id).task_name

    return render_template('index.html', categories=categories, tasks_by_category=tasks_by_category,
                           tasks_by_day=tasks_by_day, time_schedule=time_schedule,
                           days_of_week=days_of_week, time_slots=time_slots, username=session.get('username'))

# Signup route to create a new user account
@app.route('/', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Checking if the username already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists. Please choose a different one.', 'danger')
            return redirect(url_for('signup'))
        
        # Creating a new user with a hashed password
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=username, password=hashed_password)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Your account was created successfully!', 'success')
        return redirect(url_for('login'))
    
    return render_template('signup.html')

# Login route to authenticate users
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            # Store user info in session upon successful login
            session['user_id'] = user.user_id
            session['username'] = user.username
            flash('Logged in successfully!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'danger')
    return render_template('login.html')

# Logout route to clear the session
@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

# Update categories and tasks route
@app.route('/update_categories_and_tasks', methods=['POST'])
def update_categories_and_tasks():
    user_id = session.get('user_id')
    if not user_id:
        flash('You need to be logged in to perform this action', 'danger')
        return redirect(url_for('login'))

    # Fetch categories for the current user
    categories = Category.query.filter_by(user_id=user_id).all()
    tasks_by_category = {category.category_id: Task.query.filter_by(category_id=category.category_id).all() for category in categories}

    # Update or add categories (always 7 categories)
    for i in range(1, 8):
        category_name = request.form.get(f'category{i}')

        # Update existing category
        if category_name and i <= len(categories):
            categories[i - 1].category_name = category_name

        # Add new category if less than 7. The max for the categories is key because otherwise it just displays any in the DB for that user.
        if len(categories) < 7:
            new_category = Category(user_id=user_id, category_name=category_name)
            db.session.add(new_category)

    # Update or add tasks for each category
    for category in categories:
        for j in range(1, 9):  # Max 8 tasks per category but like in the HTML this could change as it is not uniform it seems
            task_name = request.form.get(f'action{j}_category{categories.index(category) + 1}')
            if task_name:
                if j <= len(tasks_by_category[category.category_id]):
                    # Update an existing task
                    tasks_by_category[category.category_id][j - 1].task_name = task_name
                else:
                    # Add a new task
                    new_task = Task(task_name=task_name, category_id=category.category_id)
                    db.session.add(new_task)

    db.session.commit()
    flash('Categories and tasks updated successfully!', 'success')
    return redirect(url_for('index'))

# Assign tasks to specific days of the week
@app.route('/assign_task_to_day', methods=['POST'])
def assign_task_to_day():
    user_id = session.get('user_id')
    if not user_id:
        flash('You need to be logged in to perform this action', 'danger')
        return redirect(url_for('login'))

    days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

    for day in days_of_week:
        for i in range(1, 8):
            task_name = request.form.get(f'{day.lower()}_task{i}')

            if task_name:
                # Try to find an existing task by name first
                existing_task = Task.query.filter_by(task_name=task_name).first()
                if existing_task:
                    # Update the task's day and slot if needed
                    existing_task.assigned_day = day
                    existing_task.slot_number = i
                else:
                    # Assign the task to the first available category. This was a fix for it breaking when a task was entered before being in a category.
                    # It would probably be beneficial to explore other fixese here. But I was just trying anything to get it to save tbh.
                    category = Category.query.filter_by(user_id=user_id).first()
                    if category:
                        new_task = Task(
                            task_name=task_name,
                            category_id=category.category_id,
                            assigned_day=day,
                            slot_number=i
                        )
                        db.session.add(new_task)
                    else:
                        flash('You need to create a category before assigning tasks to a day.', 'warning')
                        return redirect(url_for('index'))

    try:
        db.session.commit()
        flash('Tasks assigned to days successfully!', 'success')
    except Exception as e:
        # Handle errors during the commit
        print("Error saving tasks:", e)
        db.session.rollback()
        flash('An error occurred while saving tasks. Please try again.', 'danger')

    return redirect(url_for('index'))

# Schedule task to specific time slots
@app.route('/schedule_task_time_slot', methods=['POST'])
def schedule_task_time_slot():
    user_id = session.get('user_id')
    if not user_id:
        flash('You need to be logged in to assign time slots', 'danger')
        return redirect(url_for('login'))

    days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    time_slots = ['7 AM', '8 AM', '9 AM', '10 AM', '11 AM', '12 PM', '1 PM', '2 PM', '3 PM', '4 PM', '5 PM', '6 PM', '7 PM', '8 PM', '9 PM']

    for day in days_of_week:
        for time_slot in time_slots:
            task_name = request.form.get(f'schedule_{time_slot.replace(" ", "").lower()}_{day.lower()}')

            if task_name:
                # Find existing schedule for the given day and time slot
                existing_schedule = Schedule.query.filter_by(user_id=user_id, day_of_week=day, time_slot=time_slot).first()

                if existing_schedule:
                    # Update existing task name
                    existing_task = Task.query.get(existing_schedule.task_id)
                    if existing_task:
                        existing_task.task_name = task_name
                else:
                    # Create a new task and schedule entry
                    new_task = Task(task_name=task_name, assigned_day=day)
                    db.session.add(new_task)
                    db.session.flush()  # Get the ID of the new task without committing

                    new_schedule = Schedule(user_id=user_id, task_id=new_task.task_id, day_of_week=day, time_slot=time_slot)
                    db.session.add(new_schedule)

    try:
        db.session.commit()
        flash('Schedule updated successfully!', 'success')
    except Exception as e:
        print("Error saving schedule:", e)
        db.session.rollback()
        flash('There was an error updating the schedule. Please try again.', 'danger')

    return redirect(url_for('index'))



if __name__ == '__main__':
    app.run(debug=True)
