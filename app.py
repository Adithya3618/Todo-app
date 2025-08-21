from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Todo
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db.init_app(app)

# Create tables at startup (Flask 2.3+ removed before_first_request)
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return render_template('register.html')
        
        # Create new user
        hashed_password = generate_password_hash(password)
        new_user = User(name=name, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['user_name'] = user.name
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'success')
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Please log in to access dashboard', 'error')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    todos = Todo.query.filter_by(user_id=user_id).all()
    return render_template('dashboard.html', todos=todos)

@app.route('/add_todo', methods=['POST'])
def add_todo():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    task = request.form['task']
    if task:
        new_todo = Todo(task=task, user_id=session['user_id'])
        db.session.add(new_todo)
        db.session.commit()
        flash('Todo added successfully!', 'success')
    
    return redirect(url_for('dashboard'))

@app.route('/delete_todo/<int:todo_id>')
def delete_todo(todo_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    todo = Todo.query.get_or_404(todo_id)
    
    # Ensure user can only delete their own todos
    if todo.user_id == session['user_id']:
        db.session.delete(todo)
        db.session.commit()
        flash('Todo deleted successfully!', 'success')
    else:
        flash('Unauthorized action', 'error')
    
    return redirect(url_for('dashboard'))

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()
        
        if user:
            # In a real app, you'd send an email with a reset link
            # For this demo, we'll redirect to reset password with user ID
            session['reset_user_id'] = user.id
            flash('User found! You can now reset your password.', 'success')
            return redirect(url_for('reset_password'))
        else:
            flash('Email not found', 'error')
    
    return render_template('forgot_password.html')

@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if 'reset_user_id' not in session:
        flash('Invalid reset session', 'error')
        return redirect(url_for('forgot_password'))
    
    if request.method == 'POST':
        new_password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if new_password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('reset_password.html')
        
        user = User.query.get(session['reset_user_id'])
        user.password = generate_password_hash(new_password)
        db.session.commit()
        
        session.pop('reset_user_id', None)
        flash('Password reset successfully! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('reset_password.html')

if __name__ == '__main__':
    app.run(debug=True)
