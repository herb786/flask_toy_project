import re
import spacy
from spacytextblob.spacytextblob import SpacyTextBlob
import json
import random
import os
import torch

current_file_path = os.path.abspath(__file__)
current_file_directory = os.path.dirname(current_file_path)
faq_file_path = os.path.join(current_file_directory, 'agrotech_faq.json')

# Load the FAQ JSON to retrieve the actual answers
with open(faq_file_path, "r") as f:
    faq_data = json.load(f)["faqs"]

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
    
user_input = 'Will the flying sensors work if it is pouring?'
user_doc = nlpt(user_input)
user_embeddings = torch.tensor(user_doc._.trf_data.last_hidden_layer_state.data).float()
user_vector = user_embeddings.mean(dim=0)

best_match = None
highest_score = 0

# We use Cosine Similarity to compare the user's "thought" to the FAQ "thoughts"
for faq in processed_faqs_trf:
    # Simple dot product/cosine similarity via torch
    cos = torch.nn.CosineSimilarity(dim=0)
    score = cos(user_vector, faq["vector"]).item()
    
    if score > highest_score:
        highest_score = score
        best_match = faq

print(f'Score: {highest_score:.2%}')  
print(f'Best match: {best_match["question"]}')

# Transformers are very precise; a score > 0.85 is usually an excellent match
if highest_score < 0.80:
    print("I'm detecting a complex request. Could you specify if you need help with irrigation or drone hardware?")
else:
    print(best_match["answer"])