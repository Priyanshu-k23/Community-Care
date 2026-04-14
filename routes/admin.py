from flask import Blueprint, render_template, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from models.models import db, User, Donor, NGO, Volunteer, Donation, Delivery

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/')
@admin_required
def dashboard():
    # Statistics
    stats = {
        'total_donors': Donor.query.count(),
        'total_ngos': NGO.query.count(),
        'total_volunteers': Volunteer.query.count(),
        'total_donations': Donation.query.count(),
        'total_deliveries': Delivery.query.count(),
        'total_people_helped': db.session.query(db.func.sum(Donation.feeds_people)).scalar() or 0
    }
    
    # Pending approvals
    pending_users = User.query.filter_by(is_approved=False).filter(User.role != 'admin').all()
    
    return render_template('admin/dashboard.html', stats=stats, pending_users=pending_users)

@admin_bp.route('/verify/<int:user_id>/<action>')
@admin_required
def verify_user(user_id, action):
    user = User.query.get_or_404(user_id)
    
    if action == 'approve':
        user.is_approved = True
        db.session.commit()
        flash(f'User {user.email} approved successfully.', 'success')
    elif action == 'reject':
        db.session.delete(user)
        db.session.commit()
        flash(f'User {user.email} rejected and deleted.', 'warning')
        
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/users')
@admin_required
def manage_users():
    donors = Donor.query.all()
    ngos = NGO.query.all()
    volunteers = Volunteer.query.all()
    return render_template('admin/users.html', donors=donors, ngos=ngos, volunteers=volunteers)

@admin_bp.route('/donations')
@admin_required
def manage_donations():
    donations = Donation.query.order_by(Donation.created_at.desc()).all()
    return render_template('admin/donations.html', donations=donations)
