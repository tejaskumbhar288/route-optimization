from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
import requests
import jwt
import datetime
from flask import flash

app = Flask(__name__)
app.secret_key = '#'

# MySQL Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '#'
app.config['MYSQL_DB'] = 'flask_app'

mysql = MySQL(app)

# Routes
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')

        # Validate email
        if not email.endswith('@gmail.com'):
            flash('Email must be a Gmail address.', 'error')
            return render_template('signup.html')

        # Validate phone number
        if len(phone) != 10 or not phone.isdigit():
            flash('Phone number must be exactly 10 digits.', 'error')
            return render_template('signup.html')

        try:
            # Hash the password
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

            # Insert into database
            cursor = mysql.connection.cursor()
            cursor.execute(
                "INSERT INTO users (name, email, phone, password) VALUES (%s, %s, %s, %s)",
                (name, email, phone, hashed_password),
            )
            mysql.connection.commit()
            cursor.close()

            flash('Signup successful!', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            print(f"Error: {e}")
            flash('An error occurred while signing up. Please try again.', 'error')

    return render_template('signup.html')



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        try:
            # Check user credentials
            cursor = mysql.connection.cursor()
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()
            cursor.close()

            if user and check_password_hash(user[4], password):  # Assuming password is in the 5th column
                # Generate JWT token
                token = jwt.encode(
                    {
                        'user_id': user[0],  # Assuming user id is in the 1st column
                        'exp': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1),
                    },
                    app.secret_key,
                    algorithm='HS256',
                )

                # Store the token in session
                session['authToken'] = token

                flash('Login successful!', 'success')

                return redirect(url_for('routes_page'))  # Redirect to routes page after successful login
            else:
                flash('Invalid email or password.', 'danger')
        except Exception as e:
            print(f"Error: {e}")
            flash('An error occurred during login. Please try again.', 'danger')

    return render_template('login.html')


@app.route('/routes')
def routes_page():
    if 'authToken' not in session:
        flash('You must log in first!', 'danger')
        return redirect(url_for('login'))
    
    return render_template('routes.html')


if __name__ == "__main__":
    app.run(debug=True)
