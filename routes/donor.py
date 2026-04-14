from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from models.models import db, Donation
from datetime import datetime

donor_bp = Blueprint('donor', __name__)

def donor_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'donor':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

@donor_bp.route('/')
@donor_required
def dashboard():
    donations = Donation.query.filter_by(donor_id=current_user.donor_profile.id).order_by(Donation.created_at.desc()).all()
    stats = {
        'total_donated': len(donations),
        'people_helped': sum(d.feeds_people for d in donations if d.feeds_people is not None)
    }
    return render_template('donor/dashboard.html', donations=donations, stats=stats)

@donor_bp.route('/donate', methods=['GET', 'POST'])
@donor_required
def create_donation():
    if request.method == 'POST':
        item_type = request.form.get('item_type')
        quantity_desc = request.form.get('quantity_desc')
        pickup_address = request.form.get('pickup_address')
        pickup_datetime = request.form.get('pickup_datetime')
        notes = request.form.get('notes')
        
        is_veg = None
        feeds_people = None
        expiry_time = None
        
        if item_type == 'Food':
            is_veg = request.form.get('is_veg') == 'True'
            feeds_people = request.form.get('feeds_people', type=int)
            expiry_str = request.form.get('expiry_time')
            if expiry_str:
                expiry_time = datetime.strptime(expiry_str, '%Y-%m-%dT%H:%M')
                
        # Parse pickup datetime        
        pickup_dt = datetime.strptime(pickup_datetime, '%Y-%m-%dT%H:%M')
        
        new_donation = Donation(
            donor_id=current_user.donor_profile.id,
            item_type=item_type,
            quantity_desc=quantity_desc,
            is_veg=is_veg,
            feeds_people=feeds_people,
            expiry_time=expiry_time,
            pickup_address=pickup_address,
            pickup_datetime=pickup_dt,
            notes=notes,
            status='Available'
        )
        
        db.session.add(new_donation)
        db.session.commit()
        
        flash('Donation listing created successfully! NGOs have been notified.', 'success')
        return redirect(url_for('donor.dashboard'))
        
    return render_template('donor/donate.html')

@donor_bp.route('/history')
@donor_required
def history():
    return redirect(url_for('donor.dashboard'))
