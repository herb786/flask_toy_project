import re
import spacy
from app.models import Lead, FrequentAQ, db
from spacytextblob.spacytextblob import SpacyTextBlob
from flask import session
import json
import random
import os
import torch

current_file_path = os.path.abspath(__file__)
current_file_directory = os.path.dirname(current_file_path)
faq_file_path = os.path.join(current_file_directory, 'agrotech_faq.json')
trained_file_path = os.path.join(current_file_directory, 'agrotech_model')

# Load the model we just trained
nlp_trained = spacy.load(trained_file_path)

# Load the FAQ JSON to retrieve the actual answers
with open(faq_file_path, "r") as f:
    faq_data = json.load(f)["faqs"]
    
# Load the lightweight NLP model
try:
    nlp = spacy.load("en_core_web_sm")
except:
    # Fallback if model isn't linked correctly
    import en_core_web_sm
    nlp = en_core_web_sm.load()
    
# Pre-process FAQ questions into spaCy docs to save time
processed_faqs = [
    {"doc": nlp(item["question"]), "answer": item["answer"], "question": item["question"]} 
    for item in faq_data
]

# Load the Transformer model
# Note: This will be significantly slower to load than the 'md' model
nlpt = spacy.load("en_core_web_trf")

# Pre-calculate transformer outputs for your 100 FAQs
# We store the 'tensor' (the numerical meaning) of each question
processed_faqs_trf = []
for item in faq_data:
    doc = nlpt(item["question"])
    embeddings = torch.tensor(doc._.trf_data.last_hidden_layer_state.data).float()
    vector = embeddings.mean(dim=0)
    processed_faqs_trf.append({
        "vector": vector,
        "answer": item["answer"],
        "question": item["question"]
    })

nlp.add_pipe('spacytextblob') # Adds sentiment capabilities to the pipeline

def process_model2(user_message):
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

def process_model3(user_message):
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

def process_model4(user_message):
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

def process_model5(user_message):
    # Process text through our natural model
    doc = nlp_trained(user_message)
    
    # Get the category with the highest confidence score
    category = max(doc.cats, key=doc.cats.get)
    confidence = doc.cats[category]

    print(f'Confidence: {confidence:.2%}')  
    print(f'Category: {category}')  
    if confidence < 0.6:
        return "I'm not quite sure about that. Could you rephrase your question about our agrotech services?"

    # Find a relevant answer from our JSON based on the category
    # (In a real app, you'd use semantic similarity here, but this is the first 'natural' step)
    relevant_answers = [item["answer"] for item in faq_data if item["category"] == category]
    
    return random.choice(relevant_answers)

def process_model6(user_message):
    user_doc = nlp(user_message)
    
    best_match = None
    highest_score = 0

    # Compare user input to every FAQ question
    for faq in processed_faqs:
        score = user_doc.similarity(faq["doc"])
        if score > highest_score:
            highest_score = score
            best_match = faq

    print(f'Score: {highest_score:.2%}')  
    print(f'Best match: {best_match}')
    # Set a threshold (0.7 - 0.8 is usually the sweet spot)
    if highest_score < 0.75:
        return "I'm not 100% sure about that. Are you asking about our soil sensors or drone services?"

    return best_match["answer"]

def process_model7(user_message):
    
    best_match = None
    highest_score = 0
    
    # 1. Retrieve history from session (defaults to empty list)
    history = session.get("history", [])

    # 2. Add current message to history
    history.append({"role": "user", "content": user_message})

    # 3. Contextual Logic: Check if the user is using pronouns like "it" or "they"
    # If they are, we prepend the previous topic to the current input
    if any(token.lemma_ == "-PRON-" for token in nlp(user_message)) and len(history) > 1:
        previous_topic = history[-2]["content"]
        contextual_input = f"{previous_topic} {user_message}"
    else:
        contextual_input = user_message

    # ... [Insert your Similarity Logic here using contextual_input] ...
    user_doc = nlp(contextual_input)
    # Compare user input to every FAQ question
    for faq in processed_faqs:
        score = user_doc.similarity(faq["doc"])
        if score > highest_score:
            highest_score = score
            best_match = faq

    print(f'Score: {highest_score:.2%}')  
    print(f'Best match: {best_match}')

    # Set a threshold (0.7 - 0.8 is usually the sweet spot)
    if highest_score < 0.75:
        return "I'm not 100% sure about that. Are you asking about our soil sensors or drone services?"

    bot_response = best_match["answer"]

    # 4. Save bot response and update session
    history.append({"role": "bot", "content": bot_response})
    session["history"] = history[-5:]  # Keep only last 5 exchanges to save space
    
    return bot_response

def process_model8(user_input):
    user_doc = nlpt(user_input)
    user_doc = nlpt(user_input)
    user_embeddings = torch.tensor(user_doc._.trf_data.last_hidden_layer_state.data).float()
    user_vector = user_embeddings.mean(dim=0)

    best_match = None
    highest_score = 0

    # We use Cosine Similarity to compare the user's "thought" to the FAQ "thoughts"
    for faq in processed_faqs_trf:
        cos = torch.nn.CosineSimilarity(dim=0)
        score = cos(user_vector, faq["vector"]).item()

        if score > highest_score:
            highest_score = score
            best_match = faq

    print(f'Score: {highest_score:.2%}')  
    print(f'Best match: {best_match["question"]}')
    
    # Transformers are very precise; a score > 0.85 is usually an excellent match
    if highest_score < 0.80:
        return "I'm detecting a complex request. Could you specify if you need help with irrigation or drone hardware?"

    return best_match["answer"]