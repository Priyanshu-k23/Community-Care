from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(20), nullable=False) # 'admin', 'donor', 'ngo', 'volunteer'
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_approved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Gamification
    points = db.Column(db.Integer, default=0)
    badges = db.Column(db.String(255), default="") # Comma-separated badges

    # Relationships
    donor_profile = db.relationship('Donor', backref='user', uselist=False, cascade="all, delete-orphan")
    ngo_profile = db.relationship('NGO', backref='user', uselist=False, cascade="all, delete-orphan")
    volunteer_profile = db.relationship('Volunteer', backref='user', uselist=False, cascade="all, delete-orphan")

class Donor(db.Model):
    __tablename__ = 'donors'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    address = db.Column(db.Text, nullable=False)
    gov_id_path = db.Column(db.String(255), nullable=True) # Path to uploaded file
    
    donations = db.relationship('Donation', backref='donor', lazy=True)

class NGO(db.Model):
    __tablename__ = 'ngos'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    registration_number = db.Column(db.String(100), nullable=False)
    contact_person = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    address = db.Column(db.Text, nullable=False)
    certificate_path = db.Column(db.String(255), nullable=True) # Path to uploaded file

    claimed_donations = db.relationship('Donation', backref='claimed_by_ngo', lazy=True)

class Volunteer(db.Model):
    __tablename__ = 'volunteers'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    address = db.Column(db.Text, nullable=False)
    vehicle_type = db.Column(db.String(50), nullable=True)
    id_proof_path = db.Column(db.String(255), nullable=True) # Path to uploaded file

    deliveries = db.relationship('Delivery', backref='volunteer', lazy=True)

class Donation(db.Model):
    __tablename__ = 'donations'
    id = db.Column(db.Integer, primary_key=True)
    donor_id = db.Column(db.Integer, db.ForeignKey('donors.id'), nullable=False)
    item_type = db.Column(db.String(50), nullable=False) # 'Food', 'Medicine', 'Sanitary', 'Other'
    
    # Food specific
    is_veg = db.Column(db.Boolean, nullable=True)
    quantity_desc = db.Column(db.String(100), nullable=False)
    feeds_people = db.Column(db.Integer, nullable=True)
    expiry_time = db.Column(db.DateTime, nullable=True)
    
    pickup_address = db.Column(db.Text, nullable=False)
    pickup_datetime = db.Column(db.DateTime, nullable=False)
    notes = db.Column(db.Text, nullable=True)
    
    status = db.Column(db.String(20), default='Available') # Available, Claimed, Picked Up, On The Way, Delivered
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Claim logic
    ngo_id = db.Column(db.Integer, db.ForeignKey('ngos.id'), nullable=True)
    claimed_at = db.Column(db.DateTime, nullable=True)
    
    delivery = db.relationship('Delivery', backref='donation', uselist=False)

class Delivery(db.Model):
    __tablename__ = 'deliveries'
    id = db.Column(db.Integer, primary_key=True)
    donation_id = db.Column(db.Integer, db.ForeignKey('donations.id'), nullable=False)
    volunteer_id = db.Column(db.Integer, db.ForeignKey('volunteers.id'), nullable=True)
    
    status = db.Column(db.String(20), default='Pending') # Pending, Picked Up, On The Way, Delivered
    accepted_at = db.Column(db.DateTime, nullable=True)
    picked_up_at = db.Column(db.DateTime, nullable=True)
    delivered_at = db.Column(db.DateTime, nullable=True)
    
    # Realtime tracking lat/lng
    current_lat = db.Column(db.Float, nullable=True)
    current_lng = db.Column(db.Float, nullable=True)
    last_location_update = db.Column(db.DateTime, nullable=True)
