from flask import Blueprint, render_template, request, Response, url_for, flash, jsonify
from .models import db, Lead, Solution
import os
import csv
from .chatbot.logic import process_chat

main = Blueprint('main', __name__)

# Simple security check
def check_auth(username, password):
    return username == 'admin' and password == os.environ.get('ADMIN_PWD', 'farm-pass-2026')

def authenticate():
    return Response('Could not verify your login!', 401, {'WWW-Authenticate': 'Basic realm="Login Required"'})

@main.route('/admin')
def admin_dashboard():
    auth = request.authorization
    if not auth or not check_auth(auth.username, auth.password):
        return authenticate()
    
    # Query all leads from SQLite, newest first
    all_leads = Lead.query.order_by(Lead.timestamp.desc()).all()
    return render_template('admin.html', leads=all_leads)


@main.route('/admin/add-solution', methods=['POST'])
def add_solution():
    # Simple Auth check again (or use a decorator)
    auth = request.authorization
    if not auth or not check_auth(auth.username, auth.password):
        return authenticate()

    name = request.form.get('name')
    desc = request.form.get('description')
    price = request.form.get('price')

    new_item = Solution(name=name, description=desc, price_estimate=price)
    db.session.add(new_item)
    db.session.commit()
    
    return redirect(url_for('main.admin_dashboard'))


@main.route('/')
def index():
    return render_template('index.html')

# Ensure the data directory exists for our CSV
DATA_FILE = 'leads.csv'

@main.route('/chat_old', methods=['POST'])
def chat_old():
    user_text = request.json.get("message", "").lower()
    
    if any(word in user_text for word in ["quote", "price", "contact", "call"]):
        response = "I'd love to get you a custom quote! Could you please provide your **Email** or **Phone number**?"
    elif "soil" in user_text:
        response = "Our Soil Analytics sensors measure NPK levels in real-time. Interested in a demo?"
    else:
        response = "That's a great question. You can also reach our farm office at (555) 0123."
    
    # Lead Capture Logic: Simple regex or keyword check for email/phone
    if "@" in user_text or (len(user_text) > 7 and any(char.isdigit() for char in user_text)):
        save_lead(user_text)
        response = "Got it! One of our specialists will reach out to you shortly."

    return jsonify({"response": response})

def save_lead(contact_info):
    file_exists = os.path.isfile(DATA_FILE)
    with open(DATA_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['Timestamp', 'Contact Info'])
        writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M"), contact_info])

@main.route('/solution_chat', methods=['POST'])
def solution_chat():
    user_text = request.json.get("message", "").lower()
    
    # Check database for solutions
    # Example: User asks "What do you have for irrigation?"
    solutions = Solution.query.all()
    response = "I couldn't find a specific match. Would you like a custom quote?"

    for item in solutions:
        if item.name.lower() in user_text:
            response = f"Our {item.name} costs roughly {item.price_estimate}. {item.description}"
            break

    # If the user provides an email, save it as a Lead
    if "@" in user_text:
        new_lead = Lead(contact_info=user_text)
        db.session.add(new_lead)
        db.session.commit()
        response = "Thanks! I've saved your contact info. Our farm manager will reach out."

    return jsonify({"response": response})

@main.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_message = data.get("message", "")

    if not user_message:
        return jsonify({"response": "I didn't quite catch that. Could you repeat it?"}), 400

    # Execute the NLP logic (Intent, Entity, and Sentiment analysis)
    bot_response = process_chat(user_message)

    return jsonify({"response": bot_response})