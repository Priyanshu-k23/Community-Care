from flask import Blueprint, render_template, redirect, url_for, flash, abort, request
from flask_login import login_required, current_user
from models.models import db, Delivery, Donation
from datetime import datetime

volunteer_bp = Blueprint('volunteer', __name__)

def volunteer_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'volunteer':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

@volunteer_bp.route('/')
@volunteer_required
def dashboard():
    # Tasks available to pick up (Created when NGO claimed a donation)
    available_tasks = Delivery.query.filter_by(status='Pending').join(Donation).order_by(Donation.pickup_datetime.asc()).all()
    
    # Tasks accepted by this volunteer
    my_tasks = Delivery.query.filter_by(volunteer_id=current_user.volunteer_profile.id).order_by(db.desc(Delivery.accepted_at)).all()
    
    return render_template('volunteer/dashboard.html', 
                          available=available_tasks, 
                          my_tasks=my_tasks)

@volunteer_bp.route('/accept/<int:delivery_id>', methods=['POST'])
@volunteer_required
def accept_task(delivery_id):
    delivery = Delivery.query.with_for_update().get_or_404(delivery_id)
    
    if delivery.status != 'Pending':
        flash('Sorry, this task has already been accepted by another volunteer.', 'warning')
        return redirect(url_for('volunteer.dashboard'))
        
    delivery.status = 'Accepted'
    delivery.volunteer_id = current_user.volunteer_profile.id
    delivery.accepted_at = datetime.utcnow()
    
    db.session.commit()
    flash('Delivery task accepted successfully!', 'success')
    return redirect(url_for('volunteer.dashboard'))

@volunteer_bp.route('/update_status/<int:delivery_id>', methods=['POST'])
@volunteer_required
def update_status(delivery_id):
    delivery = Delivery.query.get_or_404(delivery_id)
    
    # Authorization check
    if delivery.volunteer_id != current_user.volunteer_profile.id:
        abort(403)
        
    new_status = request.form.get('status')
    valid_statuses = ['Picked Up', 'On The Way', 'Delivered']
    
    if new_status in valid_statuses:
        delivery.status = new_status
        delivery.donation.status = new_status
        
        if new_status == 'Picked Up':
            delivery.picked_up_at = datetime.utcnow()
        elif new_status == 'Delivered':
            delivery.delivered_at = datetime.utcnow()
            # Gamification: Award points!
            delivery.volunteer.user.points += 50
            delivery.donation.donor.user.points += 50
            
            # Badge logic based on points
            for user in [delivery.volunteer.user, delivery.donation.donor.user]:
                current_badges = user.badges.split(',') if user.badges else []
                if user.points >= 50 and 'Helping Hand' not in current_badges:
                    current_badges.append('Helping Hand')
                if user.points >= 200 and 'Community Hero' not in current_badges:
                    current_badges.append('Community Hero')
                if user.points >= 500 and 'Life Saver' not in current_badges:
                    current_badges.append('Life Saver')
                user.badges = ','.join(current_badges).strip(',')
                
        db.session.commit()
        flash(f'Delivery status updated to {new_status}', 'success')
    else:
        flash('Invalid status update', 'danger')
        
    return redirect(url_for('volunteer.dashboard'))
