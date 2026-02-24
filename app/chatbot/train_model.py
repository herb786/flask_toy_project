import spacy
from spacy.tokens import DocBin
from spacy.training import Example
import json
import random
import os 

# 1. Load your JSON FAQ data
current_file_path = os.path.abspath(__file__)
current_file_directory = os.path.dirname(current_file_path)
faq_file_path = os.path.join(current_file_directory, 'agrotech_faq.json')

with open(faq_file_path, "r") as f:
    data = json.load(f)

# 2. Initialize a blank English model
nlp = spacy.blank("en")
textcat = nlp.add_pipe("textcat")

# 3. Add labels from your JSON categories
categories = list(set(item["category"] for item in data["faqs"]))
for cat in categories:
    textcat.add_label(cat)

# 4. Prepare training data
train_data = []
for item in data["faqs"]:
    text = item["question"]
    # Create a dictionary of boolean labels
    labels = {cat: (1.0 if cat == item["category"] else 0.0) for cat in categories}
    train_data.append((text, labels))

# 5. Training Loop
optimizer = nlp.begin_training()
for i in range(20):  # 20 iterations
    random.shuffle(train_data)
    losses = {}
    for text, annotations in train_data:
        doc = nlp.make_doc(text)
        example = Example.from_dict(doc, {"cats": annotations})
        nlp.update([example], sgd=optimizer, losses=losses)
    print(f"Iteration {i} - Loss: {losses['textcat']:.3f}")

# 6. Save the model
model_file_path = os.path.join(current_file_directory, 'agrotech_model')
nlp.to_disk(model_file_path)
print("Model saved to 'agrotech_model' directory.")