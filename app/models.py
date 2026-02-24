from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Lead(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    contact_info = db.Column(db.String(150), nullable=False)
    message_history = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Solution(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price_estimate = db.Column(db.String(50))
    in_stock = db.Column(db.Boolean, default=True)

class FrequentAQ(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    keyword = db.Column(db.String(50), unique=True, nullable=False)
    answer = db.Column(db.Text, nullable=False)