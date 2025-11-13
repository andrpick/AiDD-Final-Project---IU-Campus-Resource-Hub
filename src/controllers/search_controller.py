"""
Search controller (Flask blueprint).
"""
from flask import Blueprint, render_template, request
from src.services.search_service import search_resources
from src.data_access.database import get_db_connection

search_bp = Blueprint('search', __name__, url_prefix='/search')

@search_bp.route('/')
def index():
    """Search resources with filters."""
    keyword = request.args.get('keyword', '').strip() or None
    category = request.args.get('category', '').strip() or None
    location = request.args.get('location', '').strip() or None
    capacity_min = request.args.get('capacity_min', type=int)
    capacity_max = request.args.get('capacity_max', type=int)
    available_from = request.args.get('available_from', '').strip() or None
    available_to = request.args.get('available_to', '').strip() or None
    # New availability filter parameters
    available_date = request.args.get('available_date', '').strip() or None
    available_start_time = request.args.get('available_start_time', '').strip() or None
    available_end_time = request.args.get('available_end_time', '').strip() or None
    # Restricted filter
    restricted_filter = request.args.get('restricted', '').strip() or None
    restricted = None
    if restricted_filter:
        if restricted_filter.lower() == 'true' or restricted_filter == '1':
            restricted = True
        elif restricted_filter.lower() == 'false' or restricted_filter == '0':
            restricted = False
    sort_by = request.args.get('sort_by', 'created_at')
    sort_order = request.args.get('sort_order', 'desc')
    page = request.args.get('page', 1, type=int)
    page_size = min(100, max(1, request.args.get('page_size', 25, type=int)))
    
    # Get unique locations for dropdown
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT location FROM resources WHERE status = 'published' ORDER BY location")
        locations_list = [row['location'] for row in cursor.fetchall()]
    
    result = search_resources(
        keyword=keyword,
        category=category,
        location=location,
        capacity_min=capacity_min,
        capacity_max=capacity_max,
        available_from=available_from,
        available_to=available_to,
        available_date=available_date,
        available_start_time=available_start_time,
        available_end_time=available_end_time,
        restricted=restricted,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size
    )
    
    if result['success']:
        data = result['data']
        return render_template('search/index.html',
                             resources=data['resources'],
                             page=data['page'],
                             total_pages=data['total_pages'],
                             total=data['total'],
                             keyword=keyword,
                             category=category,
                             location=location,
                             capacity_min=capacity_min,
                             capacity_max=capacity_max,
                             available_date=available_date,
                             available_start_time=available_start_time,
                             available_end_time=available_end_time,
                             restricted=restricted_filter,
                             sort_by=sort_by,
                             sort_order=sort_order,
                             locations_list=locations_list)
    else:
        return render_template('search/index.html',
                             resources=[],
                             page=1,
                             total_pages=0,
                             total=0,
                             keyword=keyword,
                             category=category,
                             location=location,
                             capacity_min=capacity_min,
                             capacity_max=capacity_max,
                             available_date=available_date,
                             available_start_time=available_start_time,
                             available_end_time=available_end_time,
                             restricted=restricted_filter,
                             sort_by=sort_by,
                             sort_order=sort_order,
                             locations_list=locations_list)

