# TerraFarm Chatbot & Admin Dashboard

A Flask-based lead generation system featuring an automated chatbot and a protected admin dashboard for lead management.

## 🚀 Local Development Setup

Follow these steps to run the project locally without Docker.

### 1. Clone & Navigate
```bash
git clone <your-repo-url>
cd farm_flask

### 2. Create Virtual Environment
python3.11 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

### 3. Install Requirements
pip install -r requirements.txt

### 3.a. Install 
python -m textblob.download_corpora

### 4. Update ENV file
Copy .env.example to a new file named .env.
Update the values in .env to match your local setup.

### 5. Run
export FLASK_APP=wsgi.py
export FLASK_DEBUG=1
flask run

### 6. Migration
flask db init      # Only run this once ever
flask db migrate -m "Initial migration with current tables"  # Generates the script
flask db upgrade   # Actually applies the change to the .db file

The app will be available at http://127.0.0.1:5000.
