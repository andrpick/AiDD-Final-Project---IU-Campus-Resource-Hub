"""
Messages controller (Flask blueprint).
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from src.services.messaging_service import (send_message, get_thread_messages, list_threads, 
                                           delete_message, search_users_for_messaging, get_existing_thread_id,
                                           mark_thread_read, mark_thread_unread)
from src.models.user import User

messages_bp = Blueprint('messages', __name__, url_prefix='/messages')

@messages_bp.route('/')
@login_required
def index():
    """List message threads."""
    result = list_threads(current_user.user_id)
    
    if result['success']:
        threads = result['data']['threads']
        return render_template('messages/index.html', threads=threads)
    else:
        return render_template('messages/index.html', threads=[])

@messages_bp.route('/thread/<int:thread_id>')
@login_required
def thread(thread_id):
    """View thread messages."""
    result = get_thread_messages(thread_id, current_user.user_id)
    
    if not result['success']:
        flash('Thread not found.', 'error')
        return redirect(url_for('messages.index'))
    
    messages = result['data']['messages']
    
    # Get other user info and resource info
    other_user_id = None
    resource_id = None
    if messages:
        first_message = messages[0]
        if first_message['sender_id'] == current_user.user_id:
            other_user_id = first_message['receiver_id']
        else:
            other_user_id = first_message['sender_id']
        resource_id = first_message.get('resource_id')
    else:
        # If no messages yet, try to get user/resource from query params (for new threads)
        receiver_id = request.args.get('receiver_id', type=int)
        if receiver_id:
            other_user_id = receiver_id
        resource_id = request.args.get('resource_id', type=int) or None
    
    other_user = User.get(other_user_id) if other_user_id else None
    
    # Get resource info if resource_id exists
    resource = None
    if resource_id:
        from src.services.resource_service import get_resource
        resource_result = get_resource(resource_id)
        if resource_result['success']:
            resource = resource_result['data']
    
    return render_template('messages/thread.html', 
                         messages=messages, 
                         other_user=other_user, 
                         thread_id=thread_id,
                         resource=resource)

@messages_bp.route('/send', methods=['POST'])
@login_required
def send():
    """Send a message."""
    receiver_id = request.form.get('receiver_id', type=int)
    content = request.form.get('content', '').strip()
    thread_id = request.form.get('thread_id', type=int)
    resource_id = request.form.get('resource_id', type=int) or None
    
    if not receiver_id or not content:
        flash('Missing required fields.', 'error')
        return redirect(request.referrer or url_for('messages.index'))
    
    result = send_message(current_user.user_id, receiver_id, content, resource_id=resource_id)
    
    if result['success']:
        flash('Message sent.', 'success')
        if thread_id:
            return redirect(url_for('messages.thread', thread_id=thread_id))
        else:
            return redirect(url_for('messages.thread', thread_id=result['data']['thread_id']))
    else:
        flash(result['error'], 'error')
        return redirect(request.referrer or url_for('messages.index'))

@messages_bp.route('/new')
@login_required
def new():
    """Start a new message conversation, optionally about a specific resource."""
    search_query = request.args.get('search', '').strip()
    receiver_id = request.args.get('receiver_id', type=int)
    resource_id = request.args.get('resource_id', type=int) or None
    
    users = []
    if search_query or not receiver_id:
        result = search_users_for_messaging(current_user.user_id, search=search_query if search_query else None)
        if result['success']:
            users = result['data']['users']
    
    receiver = None
    existing_thread_id = None
    resource = None
    
    if receiver_id:
        receiver = User.get(receiver_id)
        if receiver:
            existing_thread_id = get_existing_thread_id(current_user.user_id, receiver_id, resource_id=resource_id)
    
    # Get resource info if resource_id exists
    if resource_id:
        from src.services.resource_service import get_resource
        resource_result = get_resource(resource_id)
        if resource_result['success']:
            resource = resource_result['data']
    
    return render_template('messages/new.html', 
                         users=users, 
                         receiver=receiver, 
                         existing_thread_id=existing_thread_id, 
                         search_query=search_query,
                         resource=resource,
                         resource_id=resource_id)

@messages_bp.route('/new/<int:receiver_id>')
@login_required
def new_to_user(receiver_id):
    """Start a new message to a specific user."""
    return redirect(url_for('messages.new', receiver_id=receiver_id))

@messages_bp.route('/<int:message_id>/delete', methods=['POST'])
@login_required
def delete(message_id):
    """Delete a message."""
    result = delete_message(message_id, current_user.user_id)
    
    if result['success']:
        flash('Message deleted.', 'info')
    else:
        flash(result['error'], 'error')
    
    return redirect(request.referrer or url_for('messages.index'))

@messages_bp.route('/thread/<int:thread_id>/read', methods=['POST'])
@login_required
def mark_thread_read_route(thread_id):
    """Mark a thread as read."""
    result = mark_thread_read(thread_id, current_user.user_id)
    
    if result['success']:
        flash('Thread marked as read.', 'success')
    else:
        flash(result.get('error', 'Error marking thread as read.'), 'error')
    
    # Redirect to index page (where the thread list is)
    return redirect(request.referrer or url_for('messages.index'))

@messages_bp.route('/thread/<int:thread_id>/unread', methods=['POST'])
@login_required
def mark_thread_unread_route(thread_id):
    """Mark a thread as unread."""
    result = mark_thread_unread(thread_id, current_user.user_id)
    
    if result['success']:
        flash('Thread marked as unread.', 'success')
    else:
        flash(result.get('error', 'Error marking thread as unread.'), 'error')
    
    # Redirect to index page (where the thread list is)
    return redirect(request.referrer or url_for('messages.index'))

