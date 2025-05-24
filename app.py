from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
import sqlite3
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

DB = 'wiperwala.db'


def get_db_connection():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def get_user():
    user_id = session.get('user_id')
    if not user_id:
        return None
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    return user


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        if not username or not password:
            flash("Please enter both username and password.")
            return redirect(url_for('register'))
        conn = get_db_connection()
        exists = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        if exists:
            flash("Username already taken.")
            conn.close()
            return redirect(url_for('register'))
        conn.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)', (username, password, 'user'))
        conn.commit()
        conn.close()
        flash("Registration successful. Please login.")
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password)).fetchone()
        conn.close()
        if user:
            session['user_id'] = user['id']
            flash(f"Welcome back, {username}!")
            return redirect(url_for('home'))  # Redirect to home after login
        else:
            flash("Invalid username or password.")
            return redirect(url_for('login'))
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.")
    return redirect(url_for('home'))


@app.route('/profile')
def profile():
    user = get_user()
    if not user:
        flash("Please login first.")
        return redirect(url_for('login'))
    conn = get_db_connection()
    bookings = conn.execute('SELECT * FROM bookings WHERE user_id = ?', (user['id'],)).fetchall()
    conn.close()
    return render_template('profile.html', user=user, bookings=bookings)


@app.route('/booking', methods=['GET', 'POST'])
def booking():
    user = get_user()
    if not user:
        flash("Please login first.")
        return redirect(url_for('login'))

    today = datetime.utcnow()
    min_date = today.strftime('%Y-%m-%d')
    max_date = (today + timedelta(days=15)).strftime('%Y-%m-%d')

    if request.method == 'POST':
        flat_type = request.form.get('flat_type')
        date = request.form.get('date')

        try:
            booking_date = datetime.strptime(date, '%Y-%m-%d').date()
            if booking_date < today.date() or booking_date > (today + timedelta(days=15)).date():
                flash("Booking date must be from today up to 15 days ahead.")
                return redirect(url_for('booking'))
        except Exception:
            flash("Invalid date format.")
            return redirect(url_for('booking'))

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO bookings (user_id, flat_type, date, status) VALUES (?, ?, ?, ?)',
                       (user['id'], flat_type, date, 'Pending'))
        booking_id = cursor.lastrowid
        conn.commit()
        conn.close()

        flash("Booking created successfully! Redirecting to payment.")
        return redirect(url_for('wiperpay', booking_id=booking_id))

    return render_template('booking.html', min_date=min_date, max_date=max_date, user=user)


@app.route('/wiperpay/<int:booking_id>', methods=['GET', 'POST'])
def wiperpay(booking_id):
    user = get_user()
    if not user:
        flash("Please login first.")
        return redirect(url_for('login'))

    conn = get_db_connection()
    booking = conn.execute('SELECT * FROM bookings WHERE id = ? AND user_id = ?', (booking_id, user['id'])).fetchone()

    if not booking:
        conn.close()
        flash("Booking not found.")
        return redirect(url_for('profile'))

    if booking['status'] == 'Paid':
        conn.close()
        flash("This booking is already paid.")
        return redirect(url_for('profile'))

    if request.method == 'POST':
        upi_id = request.form.get('upi_id')
        if not upi_id:
            flash("Please enter a valid UPI ID.")
            return redirect(url_for('wiperpay', booking_id=booking_id))

        conn.execute('UPDATE bookings SET status = ? WHERE id = ?', ('Paid', booking_id))
        conn.commit()
        conn.close()
        flash("Payment successful via UPI!")
        return redirect(url_for('payment_success', booking_id=booking_id))

    conn.close()
    return render_template('wiperpay.html', booking=booking)


@app.route('/payment_success/<int:booking_id>')
def payment_success(booking_id):
    return render_template('payment_success.html', booking_id=booking_id)


@app.route('/invoice/<int:booking_id>')
def invoice(booking_id):
    user = get_user()
    if not user:
        flash("Please login first.")
        return redirect(url_for('login'))

    conn = get_db_connection()
    booking = conn.execute('SELECT * FROM bookings WHERE id = ? AND user_id = ?', (booking_id, user['id'])).fetchone()
    conn.close()

    if not booking:
        flash("Booking not found.")
        return redirect(url_for('profile'))

    upi_id = "wiperwala@upi"  # Replace with actual UPI ID or get from user

    return render_template('invoice.html', booking=booking, user=user, upi_id=upi_id)


@app.route('/api/user/<int:user_id>')
def get_user_api(user_id):
    conn = get_db_connection()
    user = conn.execute('SELECT id, username, email, name FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    if not user:
        return jsonify({"error": "User not found"}), 404

    user_dict = dict(user)
    return jsonify(user_dict)


@app.route('/api/chatbot', methods=['POST'])
def chatbot_api():
    user_message = request.json.get('message', '').lower()

    if 'price' in user_message:
        reply = "Our prices start from ₹2999 for 1 BHK, ₹3699 for 2 BHK, and ₹4999 for 3 BHK."
    elif 'contact' in user_message or 'support' in user_message:
        reply = "You can contact us at support@wiperwala.com or call +91-9876543210."
    elif 'hello' in user_message or 'hi' in user_message:
        reply = "Hello! How can I help you today?"
    else:
        reply = f"Thanks for your message: '{user_message}'. Our support team will contact you soon."

    return jsonify({'reply': reply})


@app.route('/chatbot')
def chatbot_page():
    user = get_user()
    if not user:
        flash("Please login to use the chatbot.")
        return redirect(url_for('login'))
    return render_template('chatbot.html', user=user)


@app.route('/delete_account', methods=['POST'])
def delete_account():
    user = get_user()
    if not user:
        flash("You need to log in to delete your account.")
        return redirect(url_for('login'))

    conn = get_db_connection()
    # Delete user's bookings first (foreign key constraint)
    conn.execute("DELETE FROM bookings WHERE user_id = ?", (user['id'],))
    # Delete user account
    conn.execute("DELETE FROM users WHERE id = ?", (user['id'],))
    conn.commit()
    conn.close()

    session.clear()  # Log user out
    flash("Your account has been deleted.")
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)
