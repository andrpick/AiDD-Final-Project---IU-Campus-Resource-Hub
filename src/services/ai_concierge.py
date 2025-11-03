"""
AI Resource Concierge service.
Provides natural language interface for resource discovery using Google Gemini AI.
"""
import os
import json
from src.services.search_service import search_resources
from src.services.review_service import get_resource_reviews
from src.services.resource_service import get_resource, list_resources
from src.services.booking_service import check_conflicts
from src.data_access.database import get_db_connection
from datetime import datetime, timedelta
from dateutil.tz import gettz, tzutc

# Try to import Google Gemini AI
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None

# Note: Context loading functionality was removed as it was unused.
# The AI assistant now uses get_resource_context() which queries the database directly.

def parse_query(query):
    """Parse natural language query to extract search parameters."""
    query_lower = query.lower()
    
    # Extract category keywords
    category_map = {
        'study room': 'study_room',
        'study space': 'study_room',
        'lab equipment': 'lab_equipment',
        'laboratory equipment': 'lab_equipment',
        'av equipment': 'av_equipment',
        'audio visual': 'av_equipment',
        'event space': 'event_space',
        'meeting space': 'event_space',
        'tutoring': 'tutoring',
        'tutor': 'tutoring'
    }
    
    category = None
    for keyword, cat in category_map.items():
        if keyword in query_lower:
            category = cat
            break
    
    # Extract capacity
    import re
    capacity_min = None
    capacity_max = None
    
    # Look for number patterns
    capacity_patterns = [
        r'(\d+)\s*people',
        r'for\s*(\d+)',
        r'capacity\s*of\s*(\d+)',
        r'(\d+)\s*person'
    ]
    
    for pattern in capacity_patterns:
        match = re.search(pattern, query_lower)
        if match:
            capacity = int(match.group(1))
            capacity_min = capacity
            capacity_max = capacity
            break
    
    # Extract location keywords
    location = None
    location_keywords = ['library', 'building', 'room', 'hall', 'center']
    for keyword in location_keywords:
        if keyword in query_lower:
            # Try to extract location phrase
            words = query_lower.split()
            idx = words.index(keyword) if keyword in words else -1
            if idx >= 0 and idx < len(words) - 1:
                location = ' '.join(words[max(0, idx-1):idx+2])
            break
    
    # General keyword (remove common words)
    stopwords = {'find', 'me', 'a', 'an', 'the', 'for', 'with', 'that', 'has', 'have', 'what', 'is', 'are', 'show'}
    keywords = [w for w in query_lower.split() if w not in stopwords and len(w) > 2]
    keyword = ' '.join(keywords[:5]) if keywords else None
    
    return {
        'keyword': keyword,
        'category': category,
        'location': location,
        'capacity_min': capacity_min,
        'capacity_max': capacity_max
    }

def get_database_statistics():
    """
    Get read-only statistics from the database for answering user questions.
    Returns statistics about resources, bookings, categories, etc.
    """
    stats = {}
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Total resources
            cursor.execute("SELECT COUNT(*) FROM resources WHERE status = 'published'")
            stats['total_resources'] = cursor.fetchone()[0]
            
            # Resources by category
            cursor.execute("""
                SELECT category, COUNT(*) as count 
                FROM resources 
                WHERE status = 'published' 
                GROUP BY category
            """)
            stats['resources_by_category'] = {row['category']: row['count'] for row in cursor.fetchall()}
            
            # Total bookings
            cursor.execute("SELECT COUNT(*) FROM bookings")
            stats['total_bookings'] = cursor.fetchone()[0]
            
            # Total users
            cursor.execute("SELECT COUNT(*) FROM users")
            stats['total_users'] = cursor.fetchone()[0]
            
            # Featured resources count
            cursor.execute("SELECT COUNT(*) FROM resources WHERE featured = 1 AND status = 'published'")
            stats['featured_resources'] = cursor.fetchone()[0]
            
    except Exception as e:
        print(f"Error getting database statistics: {e}")
        stats = {}
    
    return stats

def get_largest_resource_by_capacity():
    """
    Get the resource(s) with the highest capacity.
    Returns read-only resource information.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get the maximum capacity
            cursor.execute("""
                SELECT MAX(capacity) as max_capacity
                FROM resources
                WHERE status = 'published' AND capacity IS NOT NULL
            """)
            max_row = cursor.fetchone()
            if not max_row or max_row['max_capacity'] is None:
                return []
            
            max_capacity = max_row['max_capacity']
            
            # Get all resources with this maximum capacity
            cursor.execute("""
                SELECT resource_id, title, description, category, location, capacity, status
                FROM resources
                WHERE status = 'published' AND capacity = ?
                ORDER BY title
            """, (max_capacity,))
            
            rows = cursor.fetchall()
            resources = []
            for row in rows:
                resources.append({
                    'resource_id': row['resource_id'],
                    'title': row['title'],
                    'description': row['description'],
                    'category': row['category'],
                    'location': row['location'],
                    'capacity': row['capacity']
                })
            
            return resources
    except Exception as e:
        print(f"Error querying largest resource: {e}")
        return []

def get_resource_by_name_or_id(query):
    """
    Safely query the database for a specific resource by name or ID.
    Returns read-only resource information.
    """
    # Check if query is numeric (could be resource_id)
    resource_id = None
    if query.isdigit():
        resource_id = int(query)
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            if resource_id:
                cursor.execute("""
                    SELECT resource_id, title, description, category, location, capacity, status
                    FROM resources
                    WHERE resource_id = ? AND status = 'published'
                """, (resource_id,))
            else:
                # Search by title (case-insensitive)
                cursor.execute("""
                    SELECT resource_id, title, description, category, location, capacity, status
                    FROM resources
                    WHERE status = 'published' AND LOWER(title) LIKE LOWER(?)
                    LIMIT 5
                """, (f'%{query}%',))
            
            rows = cursor.fetchall()
            resources = []
            for row in rows:
                resources.append({
                    'resource_id': row['resource_id'],
                    'title': row['title'],
                    'description': row['description'],
                    'category': row['category'],
                    'location': row['location'],
                    'capacity': row['capacity']
                })
            
            return resources
    except Exception as e:
        print(f"Error querying resource: {e}")
        return []

def get_resources_by_category(category):
    """
    Get all resources in a specific category.
    Returns read-only resource information.
    """
    try:
        # Map user-friendly category names to database values
        category_map = {
            'study room': 'study_room',
            'study rooms': 'study_room',
            'study space': 'study_room',
            'lab equipment': 'lab_equipment',
            'laboratory equipment': 'lab_equipment',
            'av equipment': 'av_equipment',
            'audio visual': 'av_equipment',
            'event space': 'event_space',
            'event spaces': 'event_space',
            'meeting space': 'event_space',
            'tutoring': 'tutoring',
            'tutor': 'tutoring',
            'other': 'other'
        }
        
        db_category = category_map.get(category.lower(), category.lower().replace(' ', '_'))
        
        result = list_resources(status='published', category=db_category, limit=50, offset=0)
        if result['success']:
            resources = result['data']['resources']
            # Enrich with reviews
            for resource in resources:
                reviews_result = get_resource_reviews(resource['resource_id'], limit=1)
                if reviews_result['success'] and reviews_result['data']['stats']['avg_rating']:
                    resource['rating'] = reviews_result['data']['stats']['avg_rating']
            return resources
        return []
    except Exception as e:
        print(f"Error querying resources by category: {e}")
        return []

def get_resources_by_location(location_keyword):
    """
    Get all resources at a specific location or containing location keyword.
    Returns read-only resource information.
    """
    try:
        # Search for resources by location keyword
        search_result = search_resources(
            location=location_keyword,
            page=1,
            page_size=50
        )
        
        if search_result['success']:
            resources = search_result['data']['resources']
            # Enrich with reviews
            for resource in resources:
                reviews_result = get_resource_reviews(resource['resource_id'], limit=1)
                if reviews_result['success'] and reviews_result['data']['stats']['avg_rating']:
                    resource['rating'] = reviews_result['data']['stats']['avg_rating']
            return resources
        return []
    except Exception as e:
        print(f"Error querying resources by location: {e}")
        return []

def get_top_rated_resources(limit=10, category=None):
    """
    Get top-rated resources, optionally filtered by category.
    Returns read-only resource information sorted by rating.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Build query to get resources with their average ratings
            if category:
                # Map category name
                category_map = {
                    'study room': 'study_room',
                    'study rooms': 'study_room',
                    'lab equipment': 'lab_equipment',
                    'av equipment': 'av_equipment',
                    'event space': 'event_space',
                    'tutoring': 'tutoring'
                }
                db_category = category_map.get(category.lower(), category.lower().replace(' ', '_'))
                category_filter = "AND r.category = ?"
                params = [db_category, limit]
            else:
                category_filter = ""
                params = [limit]
            
            query = f"""
                SELECT r.*, AVG(rev.rating) as avg_rating, COUNT(rev.review_id) as review_count
                FROM resources r
                LEFT JOIN reviews rev ON r.resource_id = rev.resource_id
                WHERE r.status = 'published'
                {category_filter}
                GROUP BY r.resource_id
                HAVING avg_rating IS NOT NULL AND avg_rating > 0
                ORDER BY avg_rating DESC, review_count DESC
                LIMIT ?
            """
            
            cursor.execute(query, params if category else [limit])
            rows = cursor.fetchall()
            
            resources = []
            for row in rows:
                resource = dict(row)
                # Parse JSON fields
                if resource.get('images'):
                    try:
                        resource['images'] = json.loads(resource['images'])
                    except:
                        resource['images'] = []
                
                # Convert rating to float
                if resource.get('avg_rating'):
                    resource['rating'] = float(resource['avg_rating'])
                
                resources.append(resource)
            
            return resources
    except Exception as e:
        print(f"Error querying top-rated resources: {e}")
        return []

def check_resource_availability(resource_id, date_str=None):
    """
    Check if a resource is available, optionally for a specific date.
    Returns availability information and upcoming bookings.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get resource info
            cursor.execute("""
                SELECT resource_id, title, location, capacity
                FROM resources
                WHERE resource_id = ? AND status = 'published'
            """, (resource_id,))
            row = cursor.fetchone()
            if not row:
                return None
            
            resource_info = dict(row)
            
            # Get upcoming bookings (approved and pending)
            now = datetime.now(tzutc())
            
            if date_str:
                # Parse date string (could be "today", "tomorrow", or a date)
                est_tz = gettz('America/New_York')
                today_est = datetime.now(est_tz).date()
                
                if date_str.lower() in ['today', 'now']:
                    target_date = today_est
                elif date_str.lower() == 'tomorrow':
                    target_date = today_est + timedelta(days=1)
                else:
                    try:
                        from dateutil import parser
                        target_date = parser.parse(date_str).date()
                    except:
                        target_date = today_est
                
                # Get bookings for that date
                date_start = datetime.combine(target_date, datetime.min.time()).replace(tzinfo=est_tz).astimezone(tzutc())
                date_end = datetime.combine(target_date, datetime.max.time()).replace(tzinfo=est_tz).astimezone(tzutc())
                
                cursor.execute("""
                    SELECT start_datetime, end_datetime, status
                    FROM bookings
                    WHERE resource_id = ?
                    AND status IN ('pending', 'approved')
                    AND start_datetime >= ? AND start_datetime <= ?
                    ORDER BY start_datetime
                """, (resource_id, date_start.isoformat(), date_end.isoformat()))
            else:
                # Get all upcoming bookings
                cursor.execute("""
                    SELECT start_datetime, end_datetime, status
                    FROM bookings
                    WHERE resource_id = ?
                    AND status IN ('pending', 'approved')
                    AND start_datetime >= ?
                    ORDER BY start_datetime
                    LIMIT 10
                """, (resource_id, now.isoformat()))
            
            bookings = [dict(row) for row in cursor.fetchall()]
            
            return {
                'resource': resource_info,
                'bookings': bookings,
                'is_available_today': len([b for b in bookings if b['status'] == 'approved']) == 0 if date_str else None
            }
    except Exception as e:
        print(f"Error checking resource availability: {e}")
        return None

def get_recently_added_resources(limit=10):
    """
    Get recently added resources.
    Returns read-only resource information sorted by creation date.
    """
    try:
        result = list_resources(status='published', limit=limit, offset=0)
        if result['success']:
            resources = result['data']['resources']
            # Enrich with reviews
            for resource in resources:
                reviews_result = get_resource_reviews(resource['resource_id'], limit=1)
                if reviews_result['success'] and reviews_result['data']['stats']['avg_rating']:
                    resource['rating'] = reviews_result['data']['stats']['avg_rating']
            return resources
        return []
    except Exception as e:
        print(f"Error querying recently added resources: {e}")
        return []

def compare_resources(resource_id_1, resource_id_2):
    """
    Compare two resources side by side.
    Returns comparison information.
    """
    try:
        resource1 = get_resource(resource_id_1)
        resource2 = get_resource(resource_id_2)
        
        if not resource1['success'] or not resource2['success']:
            return None
        
        res1 = resource1['data']
        res2 = resource2['data']
        
        # Get reviews for both
        reviews1 = get_resource_reviews(resource_id_1, limit=1)
        reviews2 = get_resource_reviews(resource_id_2, limit=1)
        
        if reviews1['success'] and reviews1['data']['stats']['avg_rating']:
            res1['rating'] = reviews1['data']['stats']['avg_rating']
        if reviews2['success'] and reviews2['data']['stats']['avg_rating']:
            res2['rating'] = reviews2['data']['stats']['avg_rating']
        
        return {
            'resource1': res1,
            'resource2': res2
        }
    except Exception as e:
        print(f"Error comparing resources: {e}")
        return None

def get_resource_context():
    """Get context about available resources for the AI."""
    # Get sample of resources to understand what's available
    result = list_resources(status='published', limit=50, offset=0)
    if not result['success']:
        return "Resources are currently unavailable."
    
    resources = result['data']['resources']
    total_count = result['data'].get('total', len(resources))
    
    # Get categories and locations with counts
    categories = {}
    locations = []
    resource_examples = []  # Sample resources with details
    
    for resource in resources:
        cat = resource['category'].replace('_', ' ').title()
        if cat not in categories:
            categories[cat] = 0
        categories[cat] += 1
        
        if resource['location'] not in locations:
            locations.append(resource['location'])
        
        # Collect examples (up to 5 different categories)
        if len(resource_examples) < 5:
            category_exists = any(ex['category'] == cat for ex in resource_examples)
            if not category_exists:
                resource_examples.append({
                    'title': resource['title'],
                    'category': cat,
                    'location': resource['location'],
                    'capacity': resource['capacity'] if resource['capacity'] is not None else 'N/A'
                })
    
    # Build category string with counts
    category_list = [f"{cat} ({count} available)" for cat, count in categories.items()]
    category_text = ', '.join(category_list) if category_list else "No categories available"
    
    # Build example resources text
    examples_text = ""
    if resource_examples:
        examples_text = "\n\nExample resources in the system:\n"
        for ex in resource_examples:
            capacity_text = f", capacity: {ex['capacity']}" if ex['capacity'] != 'N/A' else ""
            examples_text += f"- {ex['title']} ({ex['category']}) at {ex['location']}{capacity_text}\n"
    
    # Get database statistics for answering questions
    stats = get_database_statistics()
    stats_text = ""
    if stats:
        stats_text = f"\nDatabase Statistics:\n"
        stats_text += f"- Total published resources: {stats.get('total_resources', 0)}\n"
        stats_text += f"- Total bookings: {stats.get('total_bookings', 0)}\n"
        stats_text += f"- Featured resources: {stats.get('featured_resources', 0)}\n"
        if stats.get('resources_by_category'):
            stats_text += f"- Resources by category:\n"
            for cat, count in stats['resources_by_category'].items():
                stats_text += f"  * {cat.replace('_', ' ').title()}: {count}\n"
    
    context = f"""You are an AI assistant EXCLUSIVELY for the Indiana University Campus Resource Hub. 

STRICT TOPIC RESTRICTIONS:
- You MUST ONLY discuss topics related to the Indiana University Campus Resource Hub
- You CAN help with: finding resources, booking resources, resource information, platform features, resource statistics, resource details
- You CANNOT discuss: general topics, other universities, unrelated subjects, personal advice, topics outside the resource hub
- If asked about topics outside the resource hub, politely decline and redirect to resource hub topics
- You are NOT a general-purpose AI assistant - you are specialized ONLY for this resource hub

There are {total_count} published resources available in the system.
Available resource categories: {category_text}
Sample locations: {', '.join(locations[:15])}
{examples_text}
{stats_text}

You can help users with:
- Finding resources by category, location, or capacity
- Searching the database for specific resources
- Answering questions like "how many resources are there?" or "tell me about [resource name]"
- Providing detailed information about specific resources
- Explaining how to book resources
- Providing information about available resources and statistics
- Guiding users through the booking process

DATABASE ACCESS:
You have READ-ONLY access to the database through helper functions that will provide:
- Statistics (total resources, bookings, categories)
- Resource details by name or ID
- Resource searches and filters
You CANNOT modify the database - you can only READ information to answer user questions.

IMPORTANT: 
- When users ask about resources (even general questions), use the database query functions to provide accurate, up-to-date information
- Always reference actual resources from the database when responding
- If asked "how many resources are there?", use the statistics function
- If asked "tell me about [resource name]", use the resource lookup function
- Stay strictly within the topic of the resource hub

Be friendly, helpful, and concise. Always use database queries when users ask about resources, statistics, or specific resource information."""
    
    return context

def query_concierge(user_query, conversation_history=None):
    """
    Process natural language query using Google Gemini AI and return response.
    All results are validated against actual database content.
    """
    # Get Gemini API key
    api_key = os.environ.get('GOOGLE_GEMINI_API_KEY')
    
    # Debug logging (remove in production)
    if not GEMINI_AVAILABLE:
        print(f"[DEBUG] Gemini not available - GEMINI_AVAILABLE: {GEMINI_AVAILABLE}")
    if not api_key:
        print(f"[DEBUG] API key not found in environment - GOOGLE_GEMINI_API_KEY: {api_key}")
    
    # Check if Gemini is available and API key is provided
    if not GEMINI_AVAILABLE or not api_key:
        # Fallback to basic search-based response
        return query_concierge_fallback(user_query)
    
    try:
        # Configure Gemini
        genai.configure(api_key=api_key)
        
        # Get resource context
        system_context = get_resource_context()
        
        # Determine what type of query this is
        # Check if user is asking for statistics or specific resource information
        query_lower = user_query.lower()
        
        # Detect statistics questions
        stats_questions = ['how many', 'total', 'count', 'statistics', 'stats', 'number of']
        is_stats_query = any(keyword in query_lower for keyword in stats_questions)
        
        # Detect largest/biggest resource questions
        largest_keywords = ['largest', 'biggest', 'maximum capacity', 'max capacity', 'highest capacity', 'most capacity']
        is_largest_query = any(keyword in query_lower for keyword in largest_keywords)
        
        # Detect specific resource lookup
        resource_lookup_keywords = ['tell me about', 'about', 'details about', 'information about', 'what is', 'describe']
        is_resource_lookup = any(keyword in query_lower for keyword in resource_lookup_keywords)
        
        # Detect category-specific queries
        category_keywords = ['study rooms', 'lab equipment', 'av equipment', 'event spaces', 'tutoring', 'all study rooms', 'all event spaces']
        is_category_query = any(keyword in query_lower for keyword in category_keywords)
        # Extract category from query
        category_in_query = None
        if is_category_query:
            category_map = {
                'study room': 'study_room',
                'study rooms': 'study_room',
                'study space': 'study_room',
                'lab equipment': 'lab_equipment',
                'laboratory equipment': 'lab_equipment',
                'av equipment': 'av_equipment',
                'audio visual': 'av_equipment',
                'event space': 'event_space',
                'event spaces': 'event_space',
                'meeting space': 'event_space',
                'tutoring': 'tutoring',
                'tutor': 'tutoring'
            }
            for key, value in category_map.items():
                if key in query_lower:
                    category_in_query = key
                    break
        
        # Detect location-based queries
        location_keywords = ['at', 'near', 'in', 'located at', 'resources at', 'resources in', 'resources near']
        is_location_query = any(keyword in query_lower for keyword in location_keywords)
        # Try to extract location from query
        location_in_query = None
        if is_location_query:
            # Look for location keywords and extract what comes after
            for keyword in ['at ', 'near ', 'in ', 'located at ', 'resources at ', 'resources in ', 'resources near ']:
                if keyword in query_lower:
                    parts = query_lower.split(keyword, 1)
                    if len(parts) > 1:
                        potential_location = parts[-1].split()[0:3]  # Take up to 3 words after keyword
                        location_in_query = ' '.join(potential_location).rstrip('?.!')
                        break
        
        # Detect top-rated/best resources queries
        top_rated_keywords = ['best', 'top rated', 'highest rated', 'most rated', 'top', 'best rated', 'highly rated']
        is_top_rated_query = any(keyword in query_lower for keyword in top_rated_keywords)
        
        # Detect availability queries
        availability_keywords = ['available', 'availability', 'is available', 'when available', 'free', 'booked', 'when can i book']
        is_availability_query = any(keyword in query_lower for keyword in availability_keywords)
        # Extract date from availability query (today, tomorrow, specific date)
        availability_date = None
        if is_availability_query:
            if 'today' in query_lower or 'now' in query_lower:
                availability_date = 'today'
            elif 'tomorrow' in query_lower:
                availability_date = 'tomorrow'
            else:
                # Try to extract a date pattern
                import re
                date_pattern = r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{2}-\d{2}'
                match = re.search(date_pattern, query_lower)
                if match:
                    availability_date = match.group()
        
        # Detect recently added queries
        recent_keywords = ['new', 'recent', 'recently added', 'latest', 'newest', 'just added']
        is_recent_query = any(keyword in query_lower for keyword in recent_keywords)
        
        # Detect comparison queries
        comparison_keywords = ['compare', 'difference', 'vs', 'versus', 'versus', 'better', 'which is better']
        is_comparison_query = any(keyword in query_lower for keyword in comparison_keywords)
        
        # Detect if user wants to search for resources (explicit search queries)
        search_keywords = ['find', 'search', 'looking for', 'need', 'want', 'show me', 'book', 'reserve', 
                          'resource', 'what resources', 'list resources', 'show resources']
        should_search = any(keyword in query_lower for keyword in search_keywords)
        
        # Initialize resources array - will only be populated with relevant resources
        resources = []
        
        # Get statistics if requested (no resources returned for stats-only queries)
        stats_context = ""
        if is_stats_query:
            stats = get_database_statistics()
            if stats:
                stats_context = "\n\nDatabase Statistics:\n"
                stats_context += f"- Total published resources: {stats.get('total_resources', 0)}\n"
                stats_context += f"- Total bookings: {stats.get('total_bookings', 0)}\n"
                stats_context += f"- Featured resources: {stats.get('featured_resources', 0)}\n"
                if stats.get('resources_by_category'):
                    stats_context += f"- Resources by category:\n"
                    for cat, count in stats['resources_by_category'].items():
                        stats_context += f"  * {cat.replace('_', ' ').title()}: {count}\n"
        
        # Get largest resource if requested (add to resources array)
        largest_resource_context = ""
        if is_largest_query:
            largest_resources = get_largest_resource_by_capacity()
            if largest_resources:
                # Add to resources array so they're returned in the response
                resources = largest_resources
                # Enrich with reviews
                for resource in resources:
                    reviews_result = get_resource_reviews(resource['resource_id'], limit=1)
                    if reviews_result['success'] and reviews_result['data']['stats']['avg_rating']:
                        resource['rating'] = reviews_result['data']['stats']['avg_rating']
                
                largest_resource_context = "\n\nLargest Resource(s) by Capacity (from database query):\n"
                for res in largest_resources:
                    largest_resource_context += f"- {res['title']} (ID: {res['resource_id']})\n"
                    largest_resource_context += f"  Category: {res['category'].replace('_', ' ').title()}\n"
                    largest_resource_context += f"  Location: {res['location']}\n"
                    largest_resource_context += f"  Capacity: {res['capacity']}\n"
                    if res['description']:
                        desc = res['description'][:200] + "..." if len(res['description']) > 200 else res['description']
                        largest_resource_context += f"  Description: {desc}\n"
                    largest_resource_context += "\n"
        
        # Try to extract resource name from query for lookup (for queries like "tell me about Merchants Bank Field")
        resource_info_context = ""
        if is_resource_lookup:
            # Extract potential resource name (everything after lookup keywords)
            resource_name = None
            lookup_patterns = [
                ('tell me about', 'tell me about'),
                ('details about', 'details about'),
                ('information about', 'information about'),
                ('what is', 'what is'),
                ('describe', 'describe'),
                ('about', 'about')
            ]
            
            for pattern, keyword in lookup_patterns:
                if keyword in query_lower:
                    parts = user_query.split(keyword, 1)
                    if len(parts) > 1:
                        resource_name = parts[-1].strip()
                        # Remove trailing question marks and punctuation
                        resource_name = resource_name.rstrip('?.!').strip()
                        if resource_name:  # Make sure we have something
                            break
            
            # If no resource name extracted, try to find resource-like terms in the query
            if not resource_name or len(resource_name.split()) > 5:
                # Try to extract potential resource name (look for capitalized words or resource-like terms)
                words = user_query.split()
                # Look for capitalized words that might be resource names
                potential_names = []
                for i, word in enumerate(words):
                    if word and word[0].isupper() and i > 0:  # Not first word and capitalized
                        potential_names.append(word)
                        # Also check next few words if they're part of the name
                        for j in range(i+1, min(i+4, len(words))):
                            if words[j] and words[j][0].isupper():
                                potential_names.append(words[j])
                            else:
                                break
                        if potential_names:
                            resource_name = ' '.join(potential_names)
                            break
                
                # If still nothing, try using the entire query (may match resource title)
                if not resource_name and len(user_query.split()) < 10:
                    resource_name = user_query
            
            if resource_name and len(resource_name) > 2:
                found_resources = get_resource_by_name_or_id(resource_name)
                if found_resources:
                    # Add found resources to resources array so they're returned in the response
                    # Also search for related resources by keyword to provide context
                    if not resources:  # Only if not already populated (e.g., from largest query)
                        resources = found_resources
                    else:
                        # Merge with existing resources, avoiding duplicates
                        existing_ids = {r['resource_id'] for r in resources}
                        for res in found_resources:
                            if res['resource_id'] not in existing_ids:
                                resources.append(res)
                    
                    # Enrich with reviews
                    for resource in resources:
                        if 'rating' not in resource:
                            reviews_result = get_resource_reviews(resource['resource_id'], limit=1)
                            if reviews_result['success'] and reviews_result['data']['stats']['avg_rating']:
                                resource['rating'] = reviews_result['data']['stats']['avg_rating']
                    
                    # Also search for related resources using the resource name as keyword
                    search_result = search_resources(
                        keyword=resource_name,
                        page=1,
                        page_size=5  # Limit to 5 related resources
                    )
                    if search_result['success']:
                        related_resources = search_result['data']['resources']
                        existing_ids = {r['resource_id'] for r in resources}
                        for rel_res in related_resources:
                            if rel_res['resource_id'] not in existing_ids:
                                reviews_result = get_resource_reviews(rel_res['resource_id'], limit=1)
                                if reviews_result['success'] and reviews_result['data']['stats']['avg_rating']:
                                    rel_res['rating'] = reviews_result['data']['stats']['avg_rating']
                                resources.append(rel_res)
                    
                    resource_info_context = "\n\nResource Details from Database:\n"
                    for res in found_resources[:3]:  # Limit to top 3 matches for context
                        capacity_text = f", Capacity: {res['capacity']}" if res['capacity'] is not None else ""
                        resource_info_context += f"- {res['title']} (ID: {res['resource_id']})\n"
                        resource_info_context += f"  Category: {res['category'].replace('_', ' ').title()}\n"
                        resource_info_context += f"  Location: {res['location']}{capacity_text}\n"
                        if res['description']:
                            desc = res['description'][:200] + "..." if len(res['description']) > 200 else res['description']
                            resource_info_context += f"  Description: {desc}\n"
                        resource_info_context += "\n"
        
        # Handle category-specific queries (e.g., "show me all study rooms")
        category_context = ""
        if is_category_query and category_in_query and not resources:
            category_resources = get_resources_by_category(category_in_query)
            if category_resources:
                resources = category_resources
                category_context = f"\n\nResources in {category_in_query.title()} category (from database query):\n"
                for res in category_resources[:10]:  # Limit to top 10 for context
                    capacity_text = f", Capacity: {res['capacity']}" if res['capacity'] is not None else ""
                    rating_text = f", Rating: {res.get('rating', 'N/A')}" if res.get('rating') else ""
                    category_context += f"- {res['title']} at {res['location']}{capacity_text}{rating_text}\n"
        
        # Handle location-based queries (e.g., "what resources are at Memorial Stadium")
        location_context = ""
        if is_location_query and location_in_query and not resources:
            location_resources = get_resources_by_location(location_in_query)
            if location_resources:
                resources = location_resources
                location_context = f"\n\nResources at/near {location_in_query.title()} (from database query):\n"
                for res in location_resources[:10]:  # Limit to top 10 for context
                    capacity_text = f", Capacity: {res['capacity']}" if res['capacity'] is not None else ""
                    rating_text = f", Rating: {res.get('rating', 'N/A')}" if res.get('rating') else ""
                    location_context += f"- {res['title']} ({res['category'].replace('_', ' ').title()}){capacity_text}{rating_text}\n"
        
        # Handle top-rated queries (e.g., "show me the best rated resources")
        top_rated_context = ""
        if is_top_rated_query and not resources:
            # Try to extract category from query if specified
            top_rated_category = None
            if is_category_query and category_in_query:
                top_rated_category = category_in_query
            
            top_rated_resources = get_top_rated_resources(limit=10, category=top_rated_category)
            if top_rated_resources:
                resources = top_rated_resources
                category_text = f" in {top_rated_category.title()}" if top_rated_category else ""
                top_rated_context = f"\n\nTop-Rated Resources{category_text} (from database query):\n"
                for res in top_rated_resources:
                    capacity_text = f", Capacity: {res['capacity']}" if res['capacity'] is not None else ""
                    top_rated_context += f"- {res['title']} at {res['location']} - Rating: {res.get('rating', 'N/A')}{capacity_text}\n"
        
        # Handle recently added queries (e.g., "show me new resources")
        recent_context = ""
        if is_recent_query and not resources:
            recent_resources = get_recently_added_resources(limit=10)
            if recent_resources:
                resources = recent_resources
                recent_context = "\n\nRecently Added Resources (from database query):\n"
                for res in recent_resources[:10]:
                    capacity_text = f", Capacity: {res['capacity']}" if res['capacity'] is not None else ""
                    rating_text = f", Rating: {res.get('rating', 'N/A')}" if res.get('rating') else ""
                    recent_context += f"- {res['title']} at {res['location']}{capacity_text}{rating_text}\n"
        
        # Handle availability queries (e.g., "is Merchants Bank Field available today?")
        availability_context = ""
        if is_availability_query and not resources:
            # Try to extract resource name from query
            # Look for resource lookup patterns or resource names
            resource_name_for_availability = None
            if is_resource_lookup and resource_name:
                resource_name_for_availability = resource_name
            else:
                # Try to find resource name in query (capitalized words or common resource patterns)
                words = user_query.split()
                potential_names = []
                for i, word in enumerate(words):
                    if word and word[0].isupper() and i > 0:
                        potential_names.append(word)
                        # Check next few words
                        for j in range(i+1, min(i+4, len(words))):
                            if words[j] and words[j][0].isupper():
                                potential_names.append(words[j])
                            else:
                                break
                        if potential_names:
                            resource_name_for_availability = ' '.join(potential_names)
                            break
            
            if resource_name_for_availability:
                found_resources = get_resource_by_name_or_id(resource_name_for_availability)
                if found_resources:
                    # Check availability for the first matching resource
                    main_resource = found_resources[0]
                    availability_info = check_resource_availability(main_resource['resource_id'], availability_date)
                    
                    if availability_info:
                        resources = [main_resource]  # Add to resources array
                        
                        # Build availability context
                        if availability_date:
                            availability_context = f"\n\nAvailability for {main_resource['title']} on {availability_date}:\n"
                        else:
                            availability_context = f"\n\nAvailability for {main_resource['title']}:\n"
                        
                        if availability_info['bookings']:
                            availability_context += f"Upcoming bookings:\n"
                            for booking in availability_info['bookings'][:5]:
                                availability_context += f"- {booking['start_datetime']} to {booking['end_datetime']} ({booking['status']})\n"
                        else:
                            availability_context += "No upcoming bookings found - resource is available!\n"
        
        # Handle comparison queries (e.g., "compare Merchants Bank Field and Kelley Balance Room")
        comparison_context = ""
        if is_comparison_query and not resources:
            # Try to extract two resource names from query
            # Look for "vs", "versus", "compare" keywords
            comparison_keywords_in_query = [' vs ', ' versus ', ' compare ']
            resource_names = []
            
            for keyword in comparison_keywords_in_query:
                if keyword in query_lower:
                    parts = user_query.split(keyword, 1)
                    if len(parts) == 2:
                        # Try to extract resource names from both parts
                        for part in parts:
                            # Extract capitalized words as potential resource name
                            words = part.split()
                            potential_name = []
                            for word in words:
                                if word and word[0].isupper():
                                    potential_name.append(word)
                                elif potential_name:
                                    break
                            if potential_name:
                                resource_names.append(' '.join(potential_name).rstrip('?.!'))
                    break
            
            # If not found via keywords, try to find two resource-like patterns
            if len(resource_names) < 2:
                # Look for capitalized sequences
                words = user_query.split()
                potential_resources = []
                current_resource = []
                for word in words:
                    if word and word[0].isupper():
                        current_resource.append(word)
                    elif current_resource:
                        potential_resources.append(' '.join(current_resource).rstrip('?.!'))
                        current_resource = []
                if current_resource:
                    potential_resources.append(' '.join(current_resource).rstrip('?.!'))
                
                if len(potential_resources) >= 2:
                    resource_names = potential_resources[:2]
            
            if len(resource_names) >= 2:
                # Get both resources
                res1_list = get_resource_by_name_or_id(resource_names[0])
                res2_list = get_resource_by_name_or_id(resource_names[1])
                
                if res1_list and res2_list:
                    res1 = res1_list[0]
                    res2 = res2_list[0]
                    
                    comparison = compare_resources(res1['resource_id'], res2['resource_id'])
                    if comparison:
                        resources = [res1, res2]  # Add both to resources array
                        comp = comparison
                        
                        comparison_context = f"\n\nComparison: {res1['title']} vs {res2['title']}:\n\n"
                        comparison_context += f"{res1['title']}:\n"
                        comparison_context += f"- Category: {res1['category'].replace('_', ' ').title()}\n"
                        comparison_context += f"- Location: {res1['location']}\n"
                        comparison_context += f"- Capacity: {res1['capacity'] if res1['capacity'] else 'N/A'}\n"
                        if res1.get('rating'):
                            comparison_context += f"- Rating: {res1['rating']}\n"
                        
                        comparison_context += f"\n{res2['title']}:\n"
                        comparison_context += f"- Category: {res2['category'].replace('_', ' ').title()}\n"
                        comparison_context += f"- Location: {res2['location']}\n"
                        comparison_context += f"- Capacity: {res2['capacity'] if res2['capacity'] else 'N/A'}\n"
                        if res2.get('rating'):
                            comparison_context += f"- Rating: {res2['rating']}\n"
        
        # Only search for resources if user explicitly asks to search/find resources
        # Don't search if we already have resources from other queries
        if should_search and not resources:
            # Parse and search
            search_params = parse_query(user_query)
            search_result = search_resources(
                keyword=search_params.get('keyword'),
                category=search_params.get('category'),
                location=search_params.get('location'),
                capacity_min=search_params.get('capacity_min'),
                capacity_max=search_params.get('capacity_max'),
                page=1,
                page_size=10
            )
            
            if search_result['success']:
                resources = search_result['data']['resources']
                # Enrich with reviews
                for resource in resources:
                    reviews_result = get_resource_reviews(resource['resource_id'], limit=1)
                    if reviews_result['success'] and reviews_result['data']['stats']['avg_rating']:
                        resource['rating'] = reviews_result['data']['stats']['avg_rating']
        
        # Build resources context for AI
        # Include all resources that were found (up to the search limit, which is 10)
        resources_context = ""
        if resources:
            resources_context = "\n\nFound Resources from Search:\n"
            # Show all resources found (up to the search limit), not just 5
            for i, resource in enumerate(resources, 1):
                rating_text = f" (Rating: {resource.get('rating', 'N/A')})" if resource.get('rating') else ""
                capacity_text = f"Capacity: {resource['capacity']}" if resource['capacity'] is not None else "Capacity: N/A (no capacity constraint)"
                resources_context += f"{i}. {resource['title']} - Location: {resource['location']} - {capacity_text}{rating_text} - Resource ID: {resource['resource_id']}\n"
        
        # Build conversation history string
        history_text = ""
        if conversation_history:
            history_text = "\n\nPrevious conversation:\n"
            for msg in conversation_history:
                history_text += f"{msg}\n"
        
        # Create comprehensive prompt with strict guardrails
        prompt = f"""{system_context}
{history_text}

Current user query: {user_query}

{stats_context}
{largest_resource_context}
{category_context}
{location_context}
{top_rated_context}
{recent_context}
{availability_context}
{comparison_context}
{resource_info_context}
{resources_context if resources_context else "No specific resources found in database search."}

CRITICAL INSTRUCTIONS:
1. TOPIC RESTRICTION: You MUST ONLY discuss topics related to the Indiana University Campus Resource Hub. If the user asks about unrelated topics, politely decline and redirect them to resource hub topics.

2. RESPONSE GUIDELINES:
- Be conversational, friendly, and helpful
- Use the statistics and resource information provided above to answer questions accurately
- If resources are found above, mention them naturally in your response
- If asked about statistics (total resources, counts, etc.), use the statistics provided above
- If asked about a specific resource, use the resource details provided above
- Keep responses concise but informative
- Only discuss: resources, bookings, the platform, resource hub features, campus resources
- DO NOT discuss: unrelated topics, other universities, general knowledge outside the resource hub

3. CAPACITY INFORMATION:
- When displaying resource capacity, only show it if the resource has a capacity constraint (not null)
- Resources without capacity constraints are equipment or items that don't have capacity limits

4. DATA ACCURACY:
- Always use the actual data provided above from the database
- Do not make up or guess information
- Reference specific resource IDs, names, and details from the database queries

Respond naturally to the user's query, but strictly within the bounds of the campus resource hub topic:"""
        
        # Use Gemini to generate response
        # Only use flash models - try gemini-2.5-flash first (user preferred), then fallback to other flash models
        model_names = [
            'gemini-2.5-flash',           # Primary choice
            'models/gemini-2.5-flash',    # With models/ prefix
            'gemini-2.0-flash',            # Fallback flash model
            'models/gemini-2.0-flash',    # With models/ prefix
            'gemini-2.5-flash-lite',       # Lite version
            'models/gemini-2.5-flash-lite',
            'gemini-2.0-flash-lite',       # 2.0 lite version
            'models/gemini-2.0-flash-lite',
            'gemini-2.0-flash-exp',        # Experimental
            'models/gemini-2.0-flash-exp'
        ]
        response = None
        last_error = None
        
        for model_name in model_names:
            try:
                model = genai.GenerativeModel(model_name)
                # Try to generate content with this model
                response = model.generate_content(prompt)
                # If successful, break out of the loop
                break
            except Exception as e:
                last_error = e
                print(f"[DEBUG] Model {model_name} failed: {e}")
                continue
        
        if response is None:
            # If all flash models failed, raise the last error
            raise last_error if last_error else Exception("Could not generate content with any Gemini flash model")
        
        # Extract response text
        if hasattr(response, 'text'):
            ai_response = response.text
        elif hasattr(response, 'candidates') and response.candidates:
            if hasattr(response.candidates[0].content, 'parts') and response.candidates[0].content.parts:
                ai_response = response.candidates[0].content.parts[0].text
            elif hasattr(response.candidates[0], 'text'):
                ai_response = response.candidates[0].text
            else:
                ai_response = str(response.candidates[0])
        else:
            ai_response = str(response)
        
        # Only return resources if they're directly relevant to the query
        # Don't return resources for statistics-only queries or general questions
        resources_to_return = []
        if resources:
            # Only return resources if:
            # 1. User asked for a search/find (should_search is True)
            # 2. User asked about a specific resource (is_resource_lookup found resources)
            # 3. User asked about largest resource (is_largest_query found resources)
            # 4. User asked for category-specific resources (is_category_query)
            # 5. User asked for location-based resources (is_location_query)
            # 6. User asked for top-rated resources (is_top_rated_query)
            # 7. User asked for recently added resources (is_recent_query)
            # 8. User asked about availability (is_availability_query)
            # 9. User asked for comparison (is_comparison_query)
            if (should_search or is_resource_lookup or is_largest_query or 
                is_category_query or is_location_query or is_top_rated_query or 
                is_recent_query or is_availability_query or is_comparison_query):
                resources_to_return = resources
        
        return {
            'success': True,
            'data': {
                'query': user_query,
                'response': ai_response,
                'resources': resources_to_return
            }
        }
    except Exception as e:
        # Fallback on error
        print(f"Gemini API error: {e}")
        import traceback
        traceback.print_exc()
        return query_concierge_fallback(user_query)

def query_concierge_fallback(user_query):
    """Fallback search-based response when Gemini API is unavailable."""
    query_lower = user_query.lower()
    
    # Check for general help queries
    help_keywords = ['help', 'what can you do', 'how can you help', 'what do you do', 'assist', 'support']
    is_help_query = any(keyword in query_lower for keyword in help_keywords)
    
    # Check for statistics questions
    stats_questions = ['how many', 'total', 'count', 'statistics', 'stats', 'number of']
    is_stats_query = any(keyword in query_lower for keyword in stats_questions)
    
    # Check for largest/biggest resource questions
    largest_keywords = ['largest', 'biggest', 'maximum capacity', 'max capacity', 'highest capacity', 'most capacity']
    is_largest_query = any(keyword in query_lower for keyword in largest_keywords)
    
    # Check for resource lookup
    resource_lookup_keywords = ['tell me about', 'about', 'details about', 'information about', 'what is', 'describe']
    is_resource_lookup = any(keyword in query_lower for keyword in resource_lookup_keywords)
    
    # Handle statistics queries directly
    if is_stats_query:
        stats = get_database_statistics()
        if stats:
            stats_text = f"""There are currently {stats.get('total_resources', 0)} published resources in the system.
Total bookings made: {stats.get('total_bookings', 0)}
Featured resources: {stats.get('featured_resources', 0)}"""
            if stats.get('resources_by_category'):
                stats_text += "\n\nResources by category:"
                for cat, count in stats['resources_by_category'].items():
                    stats_text += f"\n- {cat.replace('_', ' ').title()}: {count}"
            
            return {
                'success': True,
                'data': {
                    'query': user_query,
                    'resources': [],
                    'response': stats_text
                }
            }
    
    # Handle largest resource queries directly
    if is_largest_query:
        largest_resources = get_largest_resource_by_capacity()
        if largest_resources:
            if len(largest_resources) == 1:
                res = largest_resources[0]
                capacity_text = f"{res['capacity']} people" if res['capacity'] is not None else "N/A"
                response = f"""The largest resource by capacity is:

Title: {res['title']}
Category: {res['category'].replace('_', ' ').title()}
Location: {res['location']}
Capacity: {capacity_text}"""
                if res['description']:
                    desc = res['description'][:300] + "..." if len(res['description']) > 300 else res['description']
                    response += f"\nDescription: {desc}"
            else:
                response = f"The largest resource(s) by capacity ({largest_resources[0]['capacity']} people):\n\n"
                for res in largest_resources:
                    response += f"- {res['title']} at {res['location']}\n"
            
            return {
                'success': True,
                'data': {
                    'query': user_query,
                    'resources': largest_resources,
                    'response': response
                }
            }
        else:
            return {
                'success': True,
                'data': {
                    'query': user_query,
                    'resources': [],
                    'response': "I couldn't find any resources with capacity information in the database."
                }
            }
    
    # Handle resource lookup queries directly
    if is_resource_lookup:
        # Extract resource name
        resource_name = None
        for keyword in ['tell me about', 'about', 'details about', 'information about', 'what is', 'describe']:
            if keyword in query_lower:
                parts = user_query.split(keyword, 1)
                if len(parts) > 1:
                    resource_name = parts[-1].strip().rstrip('?.!').strip()
                    if resource_name:
                        break
        
        if resource_name:
            found_resources = get_resource_by_name_or_id(resource_name)
            if found_resources:
                # Get the main resource
                main_resource = found_resources[0]
                
                # Also search for related resources using the resource name as keyword
                # This finds resources that might be related (e.g., if asking about "Memorial Stadium",
                # might also find other stadium-related resources)
                related_resources = []
                search_result = search_resources(
                    keyword=resource_name,
                    page=1,
                    page_size=5  # Limit to 5 related resources
                )
                if search_result['success']:
                    all_found = search_result['data']['resources']
                    # Exclude the main resource from related resources
                    main_resource_id = main_resource['resource_id']
                    related_resources = [r for r in all_found if r['resource_id'] != main_resource_id]
                
                # Combine main resource with related resources
                all_resources = [main_resource] + related_resources
                
                # Enrich with reviews
                for resource in all_resources:
                    reviews_result = get_resource_reviews(resource['resource_id'], limit=1)
                    if reviews_result['success'] and reviews_result['data']['stats']['avg_rating']:
                        resource['rating'] = reviews_result['data']['stats']['avg_rating']
                
                capacity_text = f"\nCapacity: {main_resource['capacity']}" if main_resource['capacity'] is not None else ""
                rating_text = f"\nRating: {main_resource.get('rating', 'N/A')}" if main_resource.get('rating') else ""
                
                response = f"""Resource Details:

Title: {main_resource['title']}
Category: {main_resource['category'].replace('_', ' ').title()}
Location: {main_resource['location']}{capacity_text}{rating_text}"""
                if main_resource['description']:
                    desc = main_resource['description'][:300] + "..." if len(main_resource['description']) > 300 else main_resource['description']
                    response += f"\nDescription: {desc}"
                
                if related_resources:
                    response += f"\n\nRelated resources that might interest you:"
                    for rel_res in related_resources[:3]:  # Show up to 3 related resources
                        response += f"\n- {rel_res['title']} at {rel_res['location']}"
                
                return {
                    'success': True,
                    'data': {
                        'query': user_query,
                        'resources': all_resources,  # Return main resource + related resources
                        'response': response
                    }
                }
    
    # Handle help queries with context
    if is_help_query:
        stats = get_database_statistics()
        stats_context = ""
        if stats:
            stats_text = f"""There are currently {stats.get('total_resources', 0)} published resources in the system.
Total bookings made: {stats.get('total_bookings', 0)}
Featured resources: {stats.get('featured_resources', 0)}"""
            if stats.get('resources_by_category'):
                stats_text += "\n\nResources by category:"
                for cat, count in stats['resources_by_category'].items():
                    stats_text += f"\n- {cat.replace('_', ' ').title()}: {count}"
            stats_context = stats_text
        response = f"""Hello! I'm your AI assistant EXCLUSIVELY for the Indiana University Campus Resource Hub. 

IMPORTANT: I can ONLY help with topics related to the campus resource hub. I cannot discuss unrelated topics.

I can help you with:
• Finding resources - Search for study rooms, lab equipment, AV equipment, event spaces, and tutoring services
• Booking resources - I can help you understand how to make reservations
• Resource information - Ask me "how many resources are there?" or "tell me about [resource name]"
• Answering questions - Ask me about the platform, resource categories, or locations
• Exploring options - Tell me what you need, and I'll suggest available resources

Try asking me things like:
- "How many resources are there in total?"
- "Tell me about MSIS Starter Pack"
- "Find me a study room for 4 people"
- "Show me available event spaces"
- "What resources are in the library?"
- "How do I book a resource?"

{stats_context}

How can I help you today?"""
        return {
            'success': True,
            'data': {
                'query': user_query,
                'resources': [],
                'response': response
            }
        }
    
    # Parse query for search
    search_params = parse_query(user_query)
    
    # Search resources
    search_result = search_resources(
        keyword=search_params.get('keyword'),
        category=search_params.get('category'),
        location=search_params.get('location'),
        capacity_min=search_params.get('capacity_min'),
        capacity_max=search_params.get('capacity_max'),
        page=1,
        page_size=10
    )
    
    if not search_result['success']:
        return {
            'success': False,
            'error': 'Error searching resources',
            'response': 'I encountered an error while searching. Please try again.'
        }
    
    resources = search_result['data']['resources']
    
    # Enrich with review information
    for resource in resources:
        reviews_result = get_resource_reviews(resource['resource_id'], limit=1)
        if reviews_result['success'] and reviews_result['data']['stats']['avg_rating']:
            resource['rating'] = reviews_result['data']['stats']['avg_rating']
    
    # Generate natural language response
    if not resources:
        response = "I couldn't find any resources matching your query. Try adjusting your search criteria or ask me for help! Remember, I can only help with topics related to the campus resource hub."
    elif len(resources) == 1:
        resource = resources[0]
        rating_text = f" with a {resource.get('rating', 'N/A')} rating" if resource.get('rating') else ""
        capacity_text = f" with capacity for {resource['capacity']} people" if resource['capacity'] is not None else ""
        response = f"I found {resource['title']} located at {resource['location']}{capacity_text}{rating_text}. It's a {resource['category'].replace('_', ' ')}."
    else:
        response = f"I found {len(resources)} resources matching your query. Here are the results:\n\n"
        # Show all resources found, not just limited to 5
        for i, resource in enumerate(resources, 1):
            rating_text = f" (Rating: {resource.get('rating', 'N/A')})" if resource.get('rating') else ""
            capacity_text = f" - Capacity: {resource['capacity']}" if resource['capacity'] is not None else ""
            response += f"{i}. {resource['title']} - {resource['location']}{capacity_text}{rating_text}\n"
    
    return {
        'success': True,
        'data': {
            'query': user_query,
            'resources': resources,
            'response': response,
            'search_params': search_params
        }
    }

