# TerraFarm Chatbot & Admin Dashboard

A Flask-based lead generation system featuring an automated chatbot and a protected admin dashboard for lead management.

## 🚀 Local Development Setup

Follow these steps to run the project locally without Docker.

### 1. Clone & Navigate
```bash
git clone <your-repo-url>
cd farm_flask

### 2. Create Virtual Environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

### 3. Install Requirements
pip install -r requirements.txt

### 4. Run
export FLASK_APP=wsgi.py
export FLASK_DEBUG=1
flask run

The app will be available at http://127.0.0.1:5000.
