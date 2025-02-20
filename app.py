from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
import os
from dotenv import load_dotenv
import MySQLdb
from datetime import datetime
from functools import wraps

# Load environment variables
load_dotenv()

# Configuration classes
class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'your_secret_key')
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_USER = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')
    MYSQL_DB = os.getenv('MYSQL_DB', 'flask_app')
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

# Initialize MySQL
mysql = MySQL(app)

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
        with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as cursor:
            cursor.execute("""
                SELECT start_location, end_location, timestamp, distance, duration 
                FROM routes 
                WHERE user_id = %s 
                ORDER BY timestamp DESC 
                LIMIT 50
            """, (session['user_id'],))
            history = cursor.fetchall()
        
        # Render the history page and pass the fetched data
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
    start = data.get("start")  # Corrected key names
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
        with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as cursor:
            cursor.execute("""
                INSERT INTO routes (user_id, start_location, end_location, distance, duration, timestamp) 
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (user_id, start, end, distance, duration, datetime.now()))
            mysql.connection.commit()
        
        return jsonify({"message": "Route saved successfully!"}), 201
    except MySQLdb.Error as db_error:
        app.logger.error(f"Database error: {str(db_error)}")
        return jsonify({"error": "Database error"}), 500
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
            with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as cursor:
                cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
                if cursor.fetchone():
                    flash('Email already registered.', 'error')
                    return redirect(url_for('signup'))

                password_hash = generate_password_hash(password)
                cursor.execute("""
                    INSERT INTO users (name, email, phone, password) 
                    VALUES (%s, %s, %s, %s)
                """, (name, email, phone, password_hash))
                mysql.connection.commit()

            flash('Signup successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            # app.logger.error(f"Signup error: {str(e)}")
            # flash('An error occurred during signup.', 'error')
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
        with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as cursor:
            cursor.execute("SELECT id, password, name FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()

        if user and check_password_hash(user["password"], password):
            session['user_id'] = user["id"]
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
