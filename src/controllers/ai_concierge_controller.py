"""
AI Concierge controller (Flask blueprint).
"""
from flask import Blueprint, request, jsonify
from src.services.ai_concierge import query_concierge

ai_concierge_bp = Blueprint('ai_concierge', __name__, url_prefix='/ai')

# Note: Legacy /ai/concierge route was removed.
# Crimson (the AI assistant) is now available as a floating chatbot widget on every page via /ai/chat endpoint.

@ai_concierge_bp.route('/chat', methods=['POST'])
def chat():
    """Chat API endpoint for chatbot widget."""
    data = request.get_json()
    user_message = data.get('message', '').strip()
    conversation_history = data.get('history', [])
    
    if not user_message:
        return jsonify({'success': False, 'error': 'Message is required'}), 400
    
    # Convert history format if needed
    if conversation_history:
        # Format: [{'role': 'user', 'content': '...'}, {'role': 'assistant', 'content': '...'}]
        history_for_api = []
        for msg in conversation_history:
            if isinstance(msg, dict) and 'role' in msg:
                history_for_api.append(f"{msg['role'].title()}: {msg['content']}")
    else:
        history_for_api = None
    
    # Get AI response
    result = query_concierge(user_message, conversation_history=history_for_api)
    
    if result['success']:
        return jsonify({
            'success': True,
            'response': result['data']['response'],
            'resources': result['data'].get('resources', [])
        })
    else:
        return jsonify({
            'success': False,
            'error': result.get('error', 'An error occurred'),
            'response': result.get('response', 'I encountered an error. Please try again.')
        }), 500

