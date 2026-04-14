import os
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from models.models import db, User, Donor, NGO, Volunteer
from flask_bcrypt import Bcrypt
from werkzeug.utils import secure_filename

auth_bp = Blueprint('auth', __name__)
bcrypt = Bcrypt()

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')
        
        user = User.query.filter_by(email=email).first()
        
        if user and bcrypt.check_password_hash(user.password_hash, password):
            if role != 'admin' and user.role != role:
                flash(f'Account exists, but not for the {role} role.', 'danger')
                return render_template('auth/login.html')
                
            if user.role != 'admin' and not user.is_approved:
                flash('Your account is pending verification by the administrator.', 'warning')
                return render_template('auth/login.html')
                
            login_user(user)
            flash('Logged in successfully.', 'success')
            
            # Redirect based on role
            if user.role == 'admin':
                return redirect(url_for('admin.dashboard'))
            elif user.role == 'donor':
                return redirect(url_for('donor.dashboard'))
            elif user.role == 'ngo':
                return redirect(url_for('ngo.dashboard'))
            elif user.role == 'volunteer':
                return redirect(url_for('volunteer.dashboard'))
                
        else:
            flash('Invalid email or password.', 'danger')
            
    return render_template('auth/login.html')

@auth_bp.route('/register')
def register():
    role = request.args.get('role', 'donor')
    if role not in ['donor', 'ngo', 'volunteer']:
        role = 'donor'
    return render_template('auth/register.html', role=role)

@auth_bp.route('/register/<role>', methods=['POST'])
def register_post(role):
    if role not in ['donor', 'ngo', 'volunteer']:
        flash('Invalid role specified', 'danger')
        return redirect(url_for('auth.register'))
        
    email = request.form.get('email')
    password = request.form.get('password')
    
    if User.query.filter_by(email=email).first():
        flash('Email address already registered', 'danger')
        return redirect(url_for('auth.register', role=role))
        
    # File upload handling
    file = request.files.get('document')
    filename = None
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Create unique filename
        filename = f"{email}_{filename}"
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
    elif role in ['donor', 'ngo', 'volunteer']:
        flash('Valid document upload is required (PDF, JPG, PNG)', 'danger')
        return redirect(url_for('auth.register', role=role))
        
    new_user = User(
        email=email,
        password_hash=bcrypt.generate_password_hash(password).decode('utf-8'),
        role=role,
        is_approved=False
    )
    db.session.add(new_user)
    db.session.flush() # To get user ID
    
    # Store specific profile details
    if role == 'donor':
        profile = Donor(
            user_id=new_user.id,
            full_name=request.form.get('full_name'),
            phone=request.form.get('phone'),
            address=request.form.get('address'),
            gov_id_path=filename
        )
    elif role == 'ngo':
        profile = NGO(
            user_id=new_user.id,
            name=request.form.get('name'),
            registration_number=request.form.get('registration_number'),
            contact_person=request.form.get('contact_person'),
            phone=request.form.get('phone'),
            address=request.form.get('address'),
            certificate_path=filename
        )
    elif role == 'volunteer':
        profile = Volunteer(
            user_id=new_user.id,
            full_name=request.form.get('full_name'),
            phone=request.form.get('phone'),
            address=request.form.get('address'),
            vehicle_type=request.form.get('vehicle_type', 'None'),
            id_proof_path=filename
        )
        
    db.session.add(profile)
    db.session.commit()
    
    flash('Registration successful! Please wait for admin approval before logging in.', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('main.index'))
