import json
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
import datetime

# Initializing our Flask app and configuring it
app = Flask(__name__, template_folder='./templates')
app._static_folder = './static'
app.secret_key = 'your_secret_key'  # Idk if we should change this?

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///plannerpad.db'  # Using a local SQLite database
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# User database model to store user credentials and their relationships
class User(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)  # Requiring it to be a unique username
    password = db.Column(db.String(120), nullable=False)  # Using a hashed password

    # Creating a relationship to categories and calendars
    categories = db.relationship('Category', backref='user', lazy=True)
    calendars = db.relationship('Calendar', backref='user', lazy=True)

# Calendar database model to represent each week's planner
class Calendar(db.Model):
    calendar_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)  # Link to specific User
    date = db.Column(db.Date, nullable=False)  # Start date of the week, Monday in our case 

    # Relationship to categories within the calendar
    categories = db.relationship('Category', backref='calendar', lazy=True)

# Category database model to organize tasks
class Category(db.Model):
    category_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)  # Link to a specfic User
    calendar_id = db.Column(db.Integer, db.ForeignKey('calendar.calendar_id'), nullable=False)  # Link to Calendar
    category_name = db.Column(db.String(100), nullable=False)  # Name of the category

    # Relationship to tasks within the category
    tasks = db.relationship('Task', backref='category', lazy=True)

# Schedule database model to assign tasks to specific days and time slots
class Schedule(db.Model):
    schedule_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)  # Link to User
    task_id = db.Column(db.Integer, db.ForeignKey('task.task_id'), nullable=False)  # Link to Task
    day_of_week = db.Column(db.String(50), nullable=False)  # Day of the week
    time_slot = db.Column(db.String(50), nullable=False)  # Time slot of the day

# Task model to represent individual tasks
class Task(db.Model):
    task_id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.category_id'), nullable=True)  # Link to Category
    calendar_id = db.Column(db.Integer, db.ForeignKey('calendar.calendar_id'), nullable=False)  # Link to Calendar
    task_name = db.Column(db.String(255), nullable=False)  # Name of the task
    assigned_day = db.Column(db.String(50), nullable=True)  # Day the task is assigned to
    time_slot = db.Column(db.String(50), nullable=True)  # Time slot the task is assigned to
    slot_number = db.Column(db.Integer, nullable=True)  # Position in the list

    def __init__(self, task_name, category_id=None, assigned_day=None, time_slot=None, slot_number=None, calendar_id=None):
        self.task_name = task_name
        self.category_id = category_id
        self.assigned_day = assigned_day
        self.time_slot = time_slot
        self.slot_number = slot_number
        self.calendar_id = calendar_id

# Create tables if they don't exist
with app.app_context():
    db.create_all()

# Index route to display the main planner page
@app.route('/index', defaults={'calendar_date': None})
@app.route('/index/<calendar_date>')
def index(calendar_date):
    user_id = session.get('user_id')
    if not user_id:
        flash('Please login to be able to use your planner!', 'danger')
        return redirect(url_for('login'))

    # Determine the calendar to load based on the date
    if calendar_date is None:
        current_date = datetime.date.today()
    else:
        current_date = datetime.datetime.strptime(calendar_date, '%Y-%m-%d').date()

    # Calculate the week start date (Monday of the current week)
    week_start_date = current_date - datetime.timedelta(days=current_date.weekday())

    # Ensure the calendar for the week exists
    calendar = Calendar.query.filter_by(user_id=user_id, date=week_start_date).first()
    if not calendar:
        # Create a new calendar for the week if it doesn't exist
        calendar = Calendar(user_id=user_id, date=week_start_date)
        db.session.add(calendar)
        db.session.commit()

    # Storing calendar details in the session
    session['calendar_id'] = calendar.calendar_id
    session['calendar_date'] = week_start_date.strftime('%Y-%m-%d')

    # Fetch categories for the current user and calendar
    categories = Category.query.filter_by(user_id=user_id, calendar_id=calendar.calendar_id).all()

    # If there are no categories, this where create default ones (Good find Corey <3)
    if not categories:
        categories = [Category(user_id=user_id, calendar_id=calendar.calendar_id, category_name=f"Category {i}") for i in range(1, 8)]
        db.session.add_all(categories)
        db.session.commit()

    # Fetch all tasks linked to the current calendar
    tasks = Task.query.filter_by(calendar_id=calendar.calendar_id).all()

    # Fetch all schedules for the current calendar
    schedules = Schedule.query.join(Task).filter(
        Schedule.user_id == user_id,
        Task.calendar_id == calendar.calendar_id
    ).all()

    # Define days of the week and time slots, we can change these if we decided to
    days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    time_slots = ['7 AM', '8 AM', '9 AM', '10 AM', '11 AM', '12 PM', '1 PM', '2 PM', '3 PM', '4 PM', '5 PM', '6 PM', '7 PM', '8 PM', '9 PM']

    # Preparing the dictionaries for easy lookup within our database
    tasks_by_category = {}
    for task in tasks:
        if task.category_id:
            tasks_by_category.setdefault(task.category_id, {})[task.slot_number] = task

    tasks_by_day = {day: {} for day in days_of_week}
    for task in tasks:
        if task.assigned_day and task.slot_number:
            tasks_by_day[task.assigned_day][task.slot_number] = task.task_name

    time_schedule = {day: {} for day in days_of_week}
    for schedule in schedules:
        time_schedule[schedule.day_of_week][schedule.time_slot] = Task.query.get(schedule.task_id).task_name

    return render_template('index.html', categories=categories, tasks_by_category=tasks_by_category,
                           tasks_by_day=tasks_by_day, time_schedule=time_schedule,
                           days_of_week=days_of_week, time_slots=time_slots, username=session.get('username'),
                           calendar_date=week_start_date, week_start_date=week_start_date)

# Signup route for a new user to create a new account
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

# Route to update categories and tasks
@app.route('/update_categories_and_tasks', methods=['POST'])
def update_categories_and_tasks():
    user_id = session.get('user_id')
    calendar_date = session.get('calendar_date')

    if not user_id:
        flash('Please login to perform this action', 'danger')
        return redirect(url_for('login'))

    # Fetch the calendar for the current week
    calendar = Calendar.query.filter_by(user_id=user_id, date=calendar_date).first()
    if not calendar:
        flash('Error: Calendar not found.', 'danger')
        return redirect(url_for('index'))

    # Fetch categories for the current user and calendar
    categories = Category.query.filter_by(user_id=user_id, calendar_id=calendar.calendar_id).all()

    # Update categories based on form input
    for i in range(1, 8):  # Only allow up to 7 categories
        category_name = request.form.get(f'category{i}')

        if category_name:
            if i <= len(categories):
                # Update existing category
                categories[i - 1].category_name = category_name
            else:
                # Add new category if under the limit
                if len(categories) < 7:
                    new_category = Category(user_id=user_id, calendar_id=calendar.calendar_id, category_name=category_name)
                    db.session.add(new_category)

    # Update or add tasks for each category
    for category in categories:
        for j in range(1, 9):  # Assume up to 8 tasks per category
            task_name = request.form.get(f'action{j}_category{categories.index(category) + 1}')
            existing_task = Task.query.filter_by(
                category_id=category.category_id,
                calendar_id=calendar.calendar_id,
                slot_number=j
            ).first()

            if task_name:
                if existing_task:
                    # Update existing task
                    existing_task.task_name = task_name
                else:
                    # Add new task with slot_number
                    new_task = Task(
                        task_name=task_name,
                        category_id=category.category_id,
                        calendar_id=calendar.calendar_id,
                        slot_number=j
                    )
                    db.session.add(new_task)
            else:
                # If task is empty and exists, delete it
                if existing_task:
                    db.session.delete(existing_task)

    try:
        db.session.commit()
        flash('Categories and tasks updated successfully!', 'success')
    except Exception as e:
        print("Error saving categories and tasks:", e)
        db.session.rollback()
        flash('An error occurred while saving categories and tasks. Please try again.', 'danger')

    return redirect(url_for('index', calendar_date=calendar_date))

# Route to assign tasks to specific days of the week
@app.route('/assign_task_to_day', methods=['POST'])
def assign_task_to_day():
    user_id = session.get('user_id')
    calendar_date = session.get('calendar_date')  # Get the current calendar date from the session

    if not user_id:
        flash('You need to be logged in to perform this action', 'danger')
        return redirect(url_for('login'))

    # Fetch the calendar for the current date
    calendar = Calendar.query.filter_by(user_id=user_id, date=calendar_date).first()
    if not calendar:
        flash('Error: Calendar not found.', 'danger')
        return redirect(url_for('index'))

    days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

    for day in days_of_week:
        for i in range(1, 8):
            task_name = request.form.get(f'{day.lower()}_task{i}')

            existing_task = Task.query.filter_by(
                assigned_day=day,
                slot_number=i,
                calendar_id=calendar.calendar_id
            ).first()

            if task_name:
                if existing_task:
                    if existing_task.task_name != task_name:
                        existing_task.task_name = task_name
                else:
                    # Create a new task and assign to the day and slot
                    new_task = Task(
                        task_name=task_name,
                        calendar_id=calendar.calendar_id,
                        assigned_day=day,
                        slot_number=i
                    )
                    db.session.add(new_task)
            else:
                if existing_task:
                    db.session.delete(existing_task)

    try:
        db.session.commit()
        flash('Tasks assigned to days successfully!', 'success')
    except Exception as e:
        # Handle errors during the commit
        print("Error saving tasks:", e)
        db.session.rollback()
        flash('An error occurred while saving tasks. Please try again.', 'danger')

    return redirect(url_for('index', calendar_date=calendar_date))

# Route to schedule tasks to specific time slots
@app.route('/schedule_task_time_slot', methods=['POST'])
def schedule_task_time_slot():
    user_id = session.get('user_id')
    calendar_date = session.get('calendar_date')  # Get the current calendar date from the first session

    if not user_id:
        flash('You need to be logged in to assign time slots', 'danger')
        return redirect(url_for('login'))

    # Fetching the calendar for the current date
    calendar = Calendar.query.filter_by(user_id=user_id, date=calendar_date).first()
    if not calendar:
        flash('Error: Calendar not found.', 'danger')
        return redirect(url_for('index'))

    days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    time_slots = ['7 AM', '8 AM', '9 AM', '10 AM', '11 AM', '12 PM', '1 PM', '2 PM', '3 PM', '4 PM', '5 PM', '6 PM', '7 PM', '8 PM', '9 PM']

    for day in days_of_week:
        for time_slot in time_slots:
            input_name = f'schedule_{time_slot.replace(" ", "").lower()}_{day.lower()}'
            task_name = request.form.get(input_name)

            # Find the existing schedule for the given day and time slot for the user
            existing_schedule = Schedule.query.join(Task).filter(
                Schedule.user_id == user_id,
                Schedule.day_of_week == day,
                Schedule.time_slot == time_slot,
                Task.calendar_id == calendar.calendar_id
            ).first()

            if task_name:
                if existing_schedule:
                    #This allows the user to edit the existing task name if changed
                    existing_task = Task.query.get(existing_schedule.task_id)
                    if existing_task and existing_task.task_name != task_name:
                        existing_task.task_name = task_name
                else:
                    # Create a new task and schedule entry
                    new_task = Task(
                        task_name=task_name,
                        assigned_day=day,
                        calendar_id=calendar.calendar_id
                    )
                    db.session.add(new_task)
                    db.session.flush()  # Get the ID of the new task without committing

                    new_schedule = Schedule(
                        user_id=user_id,
                        task_id=new_task.task_id,
                        day_of_week=day,
                        time_slot=time_slot
                    )
                    db.session.add(new_schedule)
            else:
                # If no task name is provided, we delete existing schedule and task
                if existing_schedule:
                    existing_task = Task.query.get(existing_schedule.task_id)
                    db.session.delete(existing_schedule)
                    if existing_task:
                        db.session.delete(existing_task)

    try:
        db.session.commit()
        flash('Schedule updated successfully!', 'success')
    except Exception as e:
        print("Error saving schedule:", e)
        db.session.rollback()
        flash('There was an error updating the schedule. Please try again.', 'danger')

    return redirect(url_for('index', calendar_date=calendar_date))

# Route for the user to navigate to the previous week's calendar, everything should be saved from when they used it
@app.route('/previous_calendar/<calendar_date>')
def previous_calendar(calendar_date):
    user_id = session.get('user_id')
    if not user_id:
        flash('Please login to be able to use your planner!', 'danger')
        return redirect(url_for('login'))

    current_date = datetime.datetime.strptime(calendar_date, '%Y-%m-%d').date()
    # Go back by one week
    previous_week_date = current_date - datetime.timedelta(weeks=1)
    return redirect(url_for('index', calendar_date=previous_week_date.strftime('%Y-%m-%d')))

# Route for a user to navigate to the next week's calendar
@app.route('/next_calendar/<calendar_date>')
def next_calendar(calendar_date):
    user_id = session.get('user_id')
    if not user_id:
        flash('Please login to be able to use your planner!', 'danger')
        return redirect(url_for('login'))

    current_date = datetime.datetime.strptime(calendar_date, '%Y-%m-%d').date()
    # Go forward by one week, should be the next Monday
    next_week_date = current_date + datetime.timedelta(weeks=1)
    return redirect(url_for('index', calendar_date=next_week_date.strftime('%Y-%m-%d')))

if __name__ == '__main__':
    app.run(debug=True)
