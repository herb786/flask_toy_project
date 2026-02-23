import re
from app.models import Lead, db

def process_chat(user_message):
    # 1. Simple regex to find an email or phone number
    email_pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
    phone_pattern = r'\+?\d{10,12}'
    
    found_email = re.search(email_pattern, user_message)
    found_phone = re.search(phone_pattern, user_message)

    # 2. If contact info is found, save it as a Lead
    if found_email or found_phone:
        contact = found_email.group() if found_email else found_phone.group()
        new_lead = Lead(contact_info=contact)
        db.session.add(new_lead)
        db.session.commit()
        return f"Thanks! I've saved {contact}. A farm representative will reach out soon. How else can I help?"

    # 3. Default farm bot responses
    if "price" in user_message.lower():
        return "Our seasonal vegetable crates start at $25. Would you like to leave your email for a quote?"
    
    return "Welcome to TerraFarm! I can help with pricing or harvest schedules. Just leave your email if you'd like us to call you."	
