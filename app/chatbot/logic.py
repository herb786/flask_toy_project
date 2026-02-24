import re
import spacy
from app.models import Lead, FrequentAQ, db
from spacytextblob.spacytextblob import SpacyTextBlob

# Load the lightweight NLP model
try:
    nlp = spacy.load("en_core_web_sm")
except:
    # Fallback if model isn't linked correctly
    import en_core_web_sm
    nlp = en_core_web_sm.load()

nlp.add_pipe('spacytextblob') # Adds sentiment capabilities to the pipeline

def process_chat_sentiment(user_message):
    doc = nlp(user_message.lower())
    sentiment = doc._.blob.polarity  # Returns a value from -1.0 to 1.0
    
    # Identify Intent/Entities
    contact_info = next((token.text for token in doc if token.like_email), None)
    
    # Logic based on Sentiment
    response_prefix = ""
    priority = "Normal"

    if sentiment > 0.5:
        response_prefix = "We love the enthusiasm! 🌿 "
        priority = "Hot"
    elif sentiment < -0.2:
        response_prefix = "I'm so sorry to hear you're having trouble. "
        priority = "Urgent"

    if contact_info:
        # We save the priority to the database so you see it in the Admin Panel
        new_lead = Lead(contact_info=contact_info, status=priority)
        db.session.add(new_lead)
        db.session.commit()
        return f"{response_prefix}I've saved your contact. Someone will reach out to help personally."

    # 2. Intent Recognition (Using Keywords + Lemma check)
    # Lemmatization turns "buying", "bought", "buys" all into "buy"
    keywords = [token.lemma_ for token in doc]

    if any(word in keywords for word in ["buy", "price", "cost", "sell"]):
        return "We have fresh seasonal crates! Our current harvest includes kale and carrots. Want a price list?"
    
    if any(word in keywords for word in ["where", "location", "address", "find"]):
        return "TerraFarm is located in the North Valley. We're open for tours every Saturday!"

    return f"{response_prefix}How else can TerraFarm help you today?"
    #return "I'm the TerraFarm assistant. I can help with locations, pricing, or taking your contact info!"


def process_chat_info(user_message):
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


def process_chat(user_message):
    doc = nlp(user_message)
    sentiment = doc._.blob.polarity
    
    # 1. High Priority: Extract Leads immediately
    contact_info = next((token.text for token in doc if token.like_email), None)
    if contact_info:
        status = "Hot" if sentiment > 0.4 else "New"
        new_lead = Lead(contact_info=contact_info, status=status)
        db.session.add(new_lead)
        db.session.commit()
        return f"Got it! I've saved {contact_info}. One of our farmers will contact you."

    # 2. Check NLP Intents (Hardcoded logic for core features)
    keywords = [token.lemma_.lower() for token in doc]
    if "price" in keywords or "buy" in keywords:
        return "Our seasonal crates are currently $30. Would you like to leave your email for a custom quote?"

    # 3. Fallback: Query the 'FrequentAQ' table for specific FAQ matches
    # This lets you update answers in the database without redeploying code
    for word in keywords:
        match = FrequentAQ.query.filter(FrequentAQ.keyword.ilike(f"%{word}%")).first()
        if match:
            return match.answer

    # 4. Final Safety Net
    return "I'm not quite sure about that. Try asking about our 'location', 'prices', or leave your 'email'!"