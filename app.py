import requests
import csv
import json
import random
import string
import smtplib
from io import StringIO
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from flask import Flask, request, render_template

app = Flask(__name__)

# Load users from JSON file
def load_users():
    with open('users.json', 'r') as f:
        return json.load(f)

def save_users(users):
    with open('users.json', 'w') as f:
        json.dump(users, f, indent=4)

users = load_users()

# Generate a random password of 8 characters
def generate_random_password(length=8):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for i in range(length))

# Send an email with the new password
def send_email(reg_num, new_password):
    email = f"{reg_num}@students.iitmandi.ac.in"
    subject = "Your New Password"
    body = f"Dear {reg_num},\n\nYour new password is: {new_password}\n\nPlease keep this password safe and do not share it with anyone."

    # Email configuration
    sender_email = "nandan_abhi_45@outlook.com"  # Replace with your email address
    sender_password = "lol"  # Replace with your email password

    # Create a MIME object
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = email
    msg['Subject'] = subject

    # Attach the body to the MIME object
    msg.attach(MIMEText(body, 'plain'))

    try:
        # Establish a secure session with Gmail's SMTP server
        server = smtplib.SMTP('smtp-mail.outlook.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        
        # Send the email
        server.sendmail(sender_email, email, msg.as_string())
        server.quit()
        print(f"Email sent to {email}")
    except Exception as e:
        print(f"Failed to send email: {str(e)}")

# URL to download the Google Sheet as CSV
csv_url = "https://docs.google.com/spreadsheets/d/1wnSzf650yrsK4egrG9a1XDmlkwFpKIEAbCF6bdVUNYM/export?format=csv"

def download_csv():
    response = requests.get(csv_url)
    response.raise_for_status()
    csv_data = StringIO(response.text)
    reader = csv.DictReader(csv_data)
    data = [row for row in reader]
    return data

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        reg_num = request.form['reg_num'].lower()  # Convert input registration number to lowercase
        password = request.form['password']
        
        # Convert stored registration numbers to lowercase for comparison
        normalized_users = {k.lower(): v for k, v in users.items()}
        
        # Check if the registration number is in users (case-insensitive check)
        if reg_num in normalized_users and normalized_users[reg_num] == password:
            records = download_csv()
            for record in records:
                if record["Roll Number"].lower() == reg_num:  # Compare with lowercase
                    attendance = {date: status for date, status in record.items() if date not in ["Name", "Roll Number"]}
                    total_present = sum(1 for status in attendance.values() if status == 'P')
                    total_absent = sum(1 for status in attendance.values() if status == '')
                    return render_template('attendance.html', 
                                           name=record["Name"], 
                                           roll_number=reg_num,
                                           attendance=attendance,
                                           total_present=total_present,
                                           total_absent=total_absent)
            return render_template('login.html', error="No attendance record found")
        else:
            return render_template('login.html', error="Invalid credentials")
    return render_template('login.html')

@app.route('/generate_password', methods=['GET', 'POST'])
def generate_password():
    if request.method == 'POST':
        reg_num = request.form['reg_num']
        
        # Generate a new password
        new_password = generate_random_password()
        
        # Update the users dictionary
        users[reg_num] = new_password
        
        # Save the updated users dictionary to the file
        save_users(users)
        
        # Send the new password via email
        send_email(reg_num, new_password)
        
        # Provide feedback to the user
        message = f"Password for {reg_num} has been generated and emailed successfully."
        return render_template('generate_password.html', message=message)
    
    return render_template('generate_password.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
