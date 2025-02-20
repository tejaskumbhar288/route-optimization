from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
import os
from dotenv import load_dotenv
from datetime import datetime
from functools import wraps
from flask_pymongo import PyMongo
from bson.objectid import ObjectId

# Load environment variables
load_dotenv()

# Configuration classes
class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'your_secret_key')
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb+srv://username:password@cluster0.mongodb.net/flask_app?retryWrites=true&w=majority')
    GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY', '')
    SESSION_PERMANENT = False
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    PERMANENT_SESSION_LIFETIME = 3600  # 1-hour session timeout

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

app = Flask(__name__)
app.config.from_object(ProductionConfig)

# Initialize MongoDB
mongo = PyMongo(app)

@app.route('/')
def home():
    return render_template('index.html', google_maps_api_key=app.config['GOOGLE_MAPS_API_KEY'])

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/history')
@login_required
def history():
    try:
        # Query routes collection for user's history
        history = list(mongo.db.routes.find(
            {'user_id': session['user_id']},
            {'start_location': 1, 'end_location': 1, 'timestamp': 1, 'distance': 1, 'duration': 1, '_id': 0}
        ).sort('timestamp', -1).limit(50))
        
        return render_template('history.html', history=history)
    
    except Exception as e:
        # Log the error and show a flash message
        app.logger.error(f"History fetch error: {str(e)}")
        flash("An error occurred while fetching history.", "error")
        return redirect(url_for('routes'))

@app.route('/routes')
@login_required
def routes():
    return render_template('routes.html', google_maps_api_key=app.config['GOOGLE_MAPS_API_KEY'])

@app.route("/save_route", methods=["POST"])
@login_required
def save_route():
    data = request.json
    start = data.get("start")
    end = data.get("end")
    distance = data.get("distance")
    duration = data.get("duration")

    app.logger.debug(f"Received data: start={start}, end={end}, distance={distance}, duration={duration}")  

    # Ensure user is logged in
    user_id = session.get('user_id')
    if not user_id:
        app.logger.error("User ID is missing from session")
        return jsonify({"error": "Unauthorized"}), 401

    # Ensure all required data is provided
    if not all([start, end, distance, duration]):
        return jsonify({"error": "Missing required data"}), 400

    try:
        route_data = {
            'user_id': user_id,
            'start_location': start,
            'end_location': end,
            'distance': distance,
            'duration': duration,
            'timestamp': datetime.now()
        }
        
        result = mongo.db.routes.insert_one(route_data)
        
        if result.inserted_id:
            return jsonify({"message": "Route saved successfully!"}), 201
        else:
            return jsonify({"error": "Failed to save route"}), 500
            
    except Exception as e:
        app.logger.error(f"Unexpected error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/get_traffic_data", methods=["GET"])
def get_traffic_data():
    # Simulate traffic data retrieval, for example from an API or database
    traffic_data = {
        "location": "Downtown",
        "congestion": "Heavy",
        "travel_time": "30 minutes"
    }
    return jsonify(traffic_data)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')

        if not all([name, email, phone, password]) or len(password) < 8:
            flash('All fields are required and password must be at least 8 characters.', 'error')
            return redirect(url_for('signup'))

        try:
            # Check if email already exists
            existing_user = mongo.db.users.find_one({'email': email})
            if existing_user:
                flash('Email already registered.', 'error')
                return redirect(url_for('signup'))

            # Create new user document
            user_data = {
                'name': name,
                'email': email,
                'phone': phone,
                'password': generate_password_hash(password),
                'created_at': datetime.now()
            }
            
            result = mongo.db.users.insert_one(user_data)
            
            if result.inserted_id:
                flash('Signup successful! Please log in.', 'success')
                return redirect(url_for('login'))
            else:
                flash('Failed to create account.', 'error')
                return redirect(url_for('signup'))
                
        except Exception as e:
            app.logger.error(f"Signup error: {str(e)}")
            flash('An error occurred during signup.', 'error')
            return redirect(url_for('signup'))

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    if not email or not password:
        flash("Email and password are required.", "error")
        return redirect(url_for("login"))

    try:
        # Find user by email
        user = mongo.db.users.find_one({'email': email})

        if user and check_password_hash(user["password"], password):
            # Convert ObjectId to string for session storage
            session['user_id'] = str(user["_id"])
            session['user_name'] = user["name"]
            return redirect(url_for('routes'))

        flash("Invalid email or password", "error")
        return redirect(url_for("login"))
    except Exception as e:
        app.logger.error(f"Login error: {str(e)}")
        flash("Internal server error", "error")
        return redirect(url_for("login"))

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out successfully.", "success")
    return redirect(url_for('login'))





if __name__ == "__main__":
    app.run(debug=True)