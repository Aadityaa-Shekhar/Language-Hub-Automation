from flask import Flask, render_template, request
import smtplib
import os
import json
from datetime import datetime
from notion_client import Client
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import schedule
import time
import threading

app = Flask(__name__, template_folder='templates')

# Replace with your SMTP server details
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
SMTP_USERNAME = 'tiya.shekhar@gmail.com'
SMTP_PASSWORD = 'hehe sgxk xdwt kfti'
EMAIL_SOURCE = 'tiya.shekhar@gmail.com'

# Replace with your Notion integration token
NOTION_TOKEN = 'secret_QUPkzKMWYCcjWkTlf1b4TmVzJ3Oj2nntuS85Wh9yrg0'

# Replace with your database IDs from Notion
GOALS_DB_ID = '16fe615f37624183abba96c8a4b12d76'
VOCAB_DB_ID = '952ece35fb8b414186ed2b625ab30a26'
GRAMMAR_DB_ID = 'cede56e997594b7d8ca77503d25140d3'
DAILY_LOG_DB_ID = '245984f7c95b4c33b2b8e5834f74b89d'
TIME_DIST_DB_ID = '16005549ef2e495fa876e5c9812fa9dc'

def fetch_data_from_notion():
    client = Client(auth=NOTION_TOKEN)

    def get_database_items(database_id):
        results = client.databases.query(database_id=database_id)
        return results.get("results", [])

    goals_data = []
    for page in get_database_items(GOALS_DB_ID):
        properties = page.get("properties", {})
        name = properties.get("Name", {}).get("title", [{}])[0].get("text", {}).get("content", "Unnamed Goal")
        progress = properties.get("Progress", {}).get("number", 0)
        goals_data.append(f"- {name}: {progress}%")

    vocab_data = []
    for page in get_database_items(VOCAB_DB_ID):
        properties = page.get("properties", {})
        word = properties.get("Word", {}).get("rich_text", [{}])[0].get("text", {}).get("content", "Unknown Word")
        definition = properties.get("Definition", {}).get("rich_text", [{}])[0].get("text", {}).get("content", "No Definition")
        vocab_data.append(f"- {word}: {definition}")

    grammar_data = []
    for page in get_database_items(GRAMMAR_DB_ID):
        properties = page.get("properties", {})
        topic = properties.get("Topic", {}).get("title", [{}])[0].get("text", {}).get("content", "Unnamed Topic")
        examples = properties.get("Examples", {}).get("rich_text", [{}])[0].get("text", {}).get("content", "No Examples")
        grammar_data.append(f"- {topic}: {examples}")

    daily_log_data = []
    for page in get_database_items(DAILY_LOG_DB_ID):
        properties = page.get("properties", {})
        date = properties.get("Date", {}).get("date", {}).get("start", "Unknown Date")
        activities = properties.get("Activities", {}).get("rich_text", [{}])[0].get("text", {}).get("content", "No Activities")
        daily_log_data.append(f"- {date}: {activities}")

    time_dist_data = []
    for page in get_database_items(TIME_DIST_DB_ID):
        properties = page.get("properties", {})
        date = properties.get("Date", {}).get("date", {}).get("start", "Unknown Date")
        hours_spent = properties.get("Hours Spent", {}).get("number", 0)
        time_dist_data.append(f"- {date}: {hours_spent} hours")

    return {
        'goals': goals_data,
        'vocabulary': vocab_data,
        'grammar': grammar_data,
        'daily_log': daily_log_data,
        'time_distribution': time_dist_data
    }

def send_email_report(recipient_email, report):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_SOURCE
    msg['To'] = recipient_email
    msg['Subject'] = f"Your Notion Language Hub Report - {datetime.now().strftime('%Y-%m-%d')}"

    body = '\n\n'.join([
        'Goals:',
        '\n'.join(report['goals']),
        '',
        'Vocabulary:',
        '\n'.join(report['vocabulary']),
        '',
        'Grammar:',
        '\n'.join(report['grammar']),
        '',
        'Daily Log:',
        '\n'.join(report['daily_log']),
        '',
        'Time Distribution:',
        '\n'.join(report['time_distribution'])
    ])

    msg.attach(MIMEText(body, 'plain'))

    retries = 0
    max_retries = 5
    while retries < max_retries:
        try:
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(EMAIL_SOURCE, recipient_email, msg.as_string())
            server.close()
            print(f"Email sent successfully to {recipient_email}")
            return True
        except Exception as e:
            print(f"Failed to send email to {recipient_email}. Error: {e}")
            retries += 1
            time.sleep(5)  # Wait before retrying
    print(f"Failed to send email to {recipient_email} after {max_retries} retries.")
    return False

def check_and_send_monthly_email():
    now = datetime.now()
    if now.day == 1:  # Check if it's the 1st day of the month
        report_data = fetch_data_from_notion()
        send_email_report(recipient_email, report_data)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    global NOTION_TOKEN, GOALS_DB_ID, VOCAB_DB_ID, GRAMMAR_DB_ID, DAILY_LOG_DB_ID, TIME_DIST_DB_ID, recipient_email

    NOTION_TOKEN = request.form['notion_token']
    GOALS_DB_ID = request.form['goals_db_id']
    VOCAB_DB_ID = request.form['vocab_db_id']
    GRAMMAR_DB_ID = request.form['grammar_db_id']
    DAILY_LOG_DB_ID = request.form['daily_log_db_id']
    TIME_DIST_DB_ID = request.form['time_dist_db_id']
    recipient_email = request.form['recipient_email']

# Fetch data and send the initial email immediately
    report_data = fetch_data_from_notion()
    send_email_report(recipient_email, report_data)

    # Schedule the check to run every day
    schedule.every().day.at("09:00").do(check_and_send_monthly_email)

    # Run the scheduler in a separate thread
    def run_scheduler():
        while True:
            schedule.run_pending()
            time.sleep(1)

    import threading
    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.daemon = True
    scheduler_thread.start()

    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.daemon = True
    scheduler_thread.start()

    return 'Submitted successfully! You will receive your report via email monthly.'

if __name__ == '__main__':
    app.run(debug=True)
