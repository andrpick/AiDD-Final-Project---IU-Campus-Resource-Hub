"""
Reviews controller (Flask blueprint).
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from src.services.review_service import create_review, update_review, delete_review, get_resource_reviews
from src.services.resource_service import get_resource

reviews_bp = Blueprint('reviews', __name__, url_prefix='/reviews')

@reviews_bp.route('/resource/<int:resource_id>')
def resource_reviews(resource_id):
    """List reviews for a resource."""
    page = request.args.get('page', 1, type=int)
    page_size = min(100, max(1, request.args.get('page_size', 25, type=int)))
    offset = (page - 1) * page_size
    
    result = get_resource_reviews(resource_id, limit=page_size, offset=offset)
    
    if result['success']:
        data = result['data']
        reviews = data['reviews']
        stats = data['stats']
        total = data['total']
        total_pages = (total + page_size - 1) // page_size
        
        # Get resource info
        resource_result = get_resource(resource_id)
        resource = resource_result['data'] if resource_result['success'] else None
        
        return render_template('reviews/resource_reviews.html',
                             reviews=reviews,
                             stats=stats,
                             resource=resource,
                             page=page,
                             total_pages=total_pages,
                             total=total)
    else:
        flash('Error loading reviews.', 'error')
        return redirect(url_for('search.index'))

@reviews_bp.route('/create', methods=['POST'])
@login_required
def create():
    """Submit a review."""
    resource_id = request.form.get('resource_id', type=int)
    rating = request.form.get('rating', type=int)
    comment = request.form.get('comment', '').strip() or None
    booking_id = request.form.get('booking_id', type=int) or None
    
    if not resource_id or not rating:
        flash('Missing required fields.', 'error')
        return redirect(request.referrer or url_for('search.index'))
    
    result = create_review(resource_id, current_user.user_id, rating, comment, booking_id)
    
    if result['success']:
        flash('Review submitted successfully.', 'success')
    else:
        flash(result['error'], 'error')
    
    return redirect(url_for('reviews.resource_reviews', resource_id=resource_id))

@reviews_bp.route('/<int:review_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(review_id):
    """Edit a review."""
    # Implementation placeholder - would fetch review and allow editing
    flash('Review editing not yet implemented.', 'info')
    return redirect(url_for('reviews.resource_reviews', resource_id=request.args.get('resource_id', 1, type=int)))

@reviews_bp.route('/<int:review_id>/delete', methods=['POST'])
@login_required
def delete(review_id):
    """Delete a review."""
    resource_id = request.form.get('resource_id', type=int)
    
    result = delete_review(review_id, current_user.user_id, current_user.is_admin())
    
    if result['success']:
        flash('Review deleted.', 'info')
    else:
        flash(result['error'], 'error')
    
    if resource_id:
        return redirect(url_for('reviews.resource_reviews', resource_id=resource_id))
    return redirect(url_for('search.index'))

