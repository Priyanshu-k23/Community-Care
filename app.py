import os
from flask import Flask
from models.models import db, User, Delivery
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_socketio import SocketIO, emit, join_room
from datetime import datetime
import tempfile
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

login_manager = LoginManager()
bcrypt = Bcrypt()
socketio = SocketIO(cors_allowed_origins="*")

# Socket.io events
@socketio.on('join_delivery')
def on_join(data):
    room = data['room']
    join_room(room)
    print(f"User joined room for delivery {room}")

@socketio.on('location_update')
def handle_location_update(data):
    delivery_id = data.get('delivery_id')
    lat = data.get('lat')
    lng = data.get('lng')
    
    # Save the latest coordinates to the database
    with db.app.app_context():
        delivery = Delivery.query.get(delivery_id)
        if delivery:
            delivery.current_lat = lat
            delivery.current_lng = lng
            delivery.last_location_update = datetime.utcnow()
            db.session.commit()
    
    # Broadcast to anyone tracking this delivery
    emit('new_location', {'lat': lat, 'lng': lng}, room=delivery_id)


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'sharecare_secret_key_2026')
    
    # Use postgres if provided, else fallback to sqlite
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///sharecare.db')
    # Fix for old postgres:// uri format if they use it later
    if app.config['SQLALCHEMY_DATABASE_URI'].startswith("postgres://"):
        app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'].replace("postgres://", "postgresql://", 1)
        
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Configure uploads folder (use /tmp on Vercel)
    if os.environ.get('VERCEL') == '1' or os.environ.get('VERCEL'):
        app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()
    else:
        app.config['UPLOAD_FOLDER'] = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'uploads')
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    bcrypt.init_app(app)
    socketio.init_app(app)
    db.app = app # Attach for socketio to use outside request context
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
        
    with app.app_context():
        from routes.auth import auth_bp
        from routes.admin import admin_bp
        from routes.donor import donor_bp
        from routes.ngo import ngo_bp
        from routes.volunteer import volunteer_bp
        from routes.main import main_bp
        
        app.register_blueprint(auth_bp)
        app.register_blueprint(admin_bp, url_prefix='/admin')
        app.register_blueprint(donor_bp, url_prefix='/donor')
        app.register_blueprint(ngo_bp, url_prefix='/ngo')
        app.register_blueprint(volunteer_bp, url_prefix='/volunteer')
        app.register_blueprint(main_bp)

        db.create_all()
        
        # Initialize default admin
        if not User.query.filter_by(role='admin').first():
            admin_user = User(
                role='admin',
                email='kunalsamanta513@gmail.com',
                password_hash=bcrypt.generate_password_hash('12345678').decode('utf-8'),
                is_approved=True
            )
            db.session.add(admin_user)
            db.session.commit()
            print("Default admin created.")
            
    return app

app = create_app()

if __name__ == '__main__':
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)
