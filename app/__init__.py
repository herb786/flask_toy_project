# app/__init__.py
from flask import Flask
from .models import db
from .routes import main
import os

def create_app():
    app = Flask(__name__)

    basedir = os.path.abspath(os.path.dirname(__file__))
    instance_path = os.path.join(os.path.dirname(basedir), 'instance')
   
    if os.path.exists('/app'):
        # Docker Path
        instance_path = '/app/instance'
    else:
        # Local Dev Path (creates 'instance' in the current project folder)
        instance_path = os.path.join(os.getcwd(), 'instance')

    if not os.path.exists(instance_path):
        os.makedirs(instance_path)
 
    print(f'DB path: {instance_path}')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(instance_path, "farm_data.db")}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)

    with app.app_context():
        app.register_blueprint(main)
        db.create_all()

    return app
