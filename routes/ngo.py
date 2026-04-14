from flask import Blueprint, render_template, redirect, url_for, flash, abort, request
from flask_login import login_required, current_user
from models.models import db, Donation, Delivery
from datetime import datetime

ngo_bp = Blueprint('ngo', __name__)

def ngo_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'ngo':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

@ngo_bp.route('/')
@ngo_required
def dashboard():
    # Available donations not claimed by anyone yet
    available_donations = Donation.query.filter_by(status='Available').order_by(Donation.created_at.desc()).all()
    
    # Donations claimed by this NGO
    claimed_donations = Donation.query.filter_by(ngo_id=current_user.ngo_profile.id).order_by(Donation.claimed_at.desc()).all()
    
    stats = {
        'total_claimed': len(claimed_donations),
        'people_fed': sum(d.feeds_people for d in claimed_donations if d.feeds_people is not None)
    }
    
    return render_template('ngo/dashboard.html', 
                          available=available_donations, 
                          claimed=claimed_donations,
                          stats=stats)

@ngo_bp.route('/claim/<int:donation_id>', methods=['POST'])
@ngo_required
def claim_donation(donation_id):
    # Retrieve donation and lock for update (prevent race conditions)
    # Using SQLAlchemy with_for_update() requires a transaction
    donation = Donation.query.with_for_update().get_or_404(donation_id)
    
    if donation.status != 'Available':
        flash('Sorry, this donation has already been claimed.', 'warning')
        return redirect(url_for('ngo.dashboard'))
        
    donation.status = 'Claimed'
    donation.ngo_id = current_user.ngo_profile.id
    donation.claimed_at = datetime.utcnow()
    
    # Create the delivery request for volunteers immediately upon claim
    delivery = Delivery(
        donation_id=donation.id,
        status='Pending'
    )
    db.session.add(delivery)
    db.session.commit()
    
    flash('Donation claimed successfully! Volunteers have been notified for delivery.', 'success')
    return redirect(url_for('ngo.dashboard'))
