"""
Unit tests for QueryBuilder utility.
Tests dynamic SQL query construction with various filters, joins, and clauses.
"""
import pytest
from src.utils.query_builder import QueryBuilder


class TestQueryBuilderInitialization:
    """Tests for QueryBuilder initialization."""
    
    def test_init_default_select(self):
        """Test initialization with default SELECT clause."""
        qb = QueryBuilder('resources')
        
        assert qb.base_table == 'resources'
        assert qb.base_select == 'SELECT * FROM resources'
        assert qb.conditions == []
        assert qb.params == []
        assert qb.joins == []
        assert qb.group_by is None
        assert qb.order_by is None
        assert qb.limit is None
        assert qb.offset is None
    
    def test_init_custom_select(self):
        """Test initialization with custom SELECT clause."""
        qb = QueryBuilder('resources', 'SELECT r.*, u.name FROM resources r')
        
        assert qb.base_table == 'resources'
        assert qb.base_select == 'SELECT r.*, u.name FROM resources r'
    
    def test_init_with_table_alias(self):
        """Test initialization with table alias."""
        qb = QueryBuilder('resources r')
        
        assert qb.base_table == 'resources r'
        assert qb.base_select == 'SELECT * FROM resources r'


class TestQueryBuilderConditions:
    """Tests for adding WHERE conditions."""
    
    def test_add_condition_single(self):
        """Test adding a single condition."""
        qb = QueryBuilder('resources')
        qb.add_condition('status = ?', 'published')
        
        assert len(qb.conditions) == 1
        assert qb.conditions[0] == 'status = ?'
        assert qb.params == ['published']
    
    def test_add_condition_multiple(self):
        """Test adding multiple conditions."""
        qb = QueryBuilder('resources')
        qb.add_condition('status = ?', 'published')
        qb.add_condition('category = ?', 'study_room')
        
        assert len(qb.conditions) == 2
        assert qb.params == ['published', 'study_room']
    
    def test_add_condition_with_multiple_params(self):
        """Test adding condition with multiple parameters."""
        qb = QueryBuilder('resources')
        qb.add_condition('(start_date <= ? AND end_date >= ?)', '2024-01-01', '2024-12-31')
        
        assert len(qb.conditions) == 1
        assert qb.params == ['2024-01-01', '2024-12-31']
    
    def test_add_condition_empty_string(self):
        """Test that empty condition string is skipped."""
        qb = QueryBuilder('resources')
        qb.add_condition('', 'value')
        
        assert len(qb.conditions) == 0
        assert len(qb.params) == 0
    
    def test_add_condition_method_chaining(self):
        """Test that add_condition returns self for chaining."""
        qb = QueryBuilder('resources')
        result = qb.add_condition('status = ?', 'published')
        
        assert result is qb


class TestQueryBuilderJoins:
    """Tests for adding JOIN clauses."""
    
    def test_add_join_single(self):
        """Test adding a single JOIN."""
        qb = QueryBuilder('resources')
        qb.add_join('LEFT JOIN users u ON u.user_id = resources.owner_id')
        
        assert len(qb.joins) == 1
        assert 'LEFT JOIN users' in qb.joins[0]
    
    def test_add_join_multiple(self):
        """Test adding multiple JOINs."""
        qb = QueryBuilder('resources')
        qb.add_join('LEFT JOIN users u ON u.user_id = resources.owner_id')
        qb.add_join('LEFT JOIN reviews r ON r.resource_id = resources.resource_id')
        
        assert len(qb.joins) == 2
    
    def test_add_join_empty_string(self):
        """Test that empty JOIN string is skipped."""
        qb = QueryBuilder('resources')
        qb.add_join('')
        
        assert len(qb.joins) == 0
    
    def test_add_join_method_chaining(self):
        """Test that add_join returns self for chaining."""
        qb = QueryBuilder('resources')
        result = qb.add_join('LEFT JOIN users u ON u.user_id = resources.owner_id')
        
        assert result is qb


class TestQueryBuilderFilters:
    """Tests for filter helper methods."""
    
    def test_add_like_filter(self):
        """Test adding LIKE filter."""
        qb = QueryBuilder('resources')
        qb.add_like_filter('title', 'study')
        
        assert len(qb.conditions) == 1
        assert 'LIKE' in qb.conditions[0]
        assert '%study%' in qb.params
    
    def test_add_like_filter_case_sensitive(self):
        """Test adding case-sensitive LIKE filter."""
        qb = QueryBuilder('resources')
        qb.add_like_filter('title', 'Study', case_sensitive=True)
        
        assert 'LOWER' not in qb.conditions[0]
        assert '%Study%' in qb.params
    
    def test_add_like_filter_case_insensitive(self):
        """Test adding case-insensitive LIKE filter."""
        qb = QueryBuilder('resources')
        qb.add_like_filter('title', 'study', case_sensitive=False)
        
        assert 'LOWER' in qb.conditions[0]
    
    def test_add_like_filter_none_value(self):
        """Test that None value skips LIKE filter."""
        qb = QueryBuilder('resources')
        qb.add_like_filter('title', None)
        
        assert len(qb.conditions) == 0
    
    def test_add_equals_filter(self):
        """Test adding equality filter."""
        qb = QueryBuilder('resources')
        qb.add_equals_filter('status', 'published')
        
        assert len(qb.conditions) == 1
        assert qb.conditions[0] == 'status = ?'
        assert qb.params == ['published']
    
    def test_add_equals_filter_none_value(self):
        """Test that None value skips equality filter."""
        qb = QueryBuilder('resources')
        qb.add_equals_filter('status', None)
        
        assert len(qb.conditions) == 0
    
    def test_add_equals_filter_zero_value(self):
        """Test that zero value is included."""
        qb = QueryBuilder('resources')
        qb.add_equals_filter('capacity', 0)
        
        assert len(qb.conditions) == 1
        assert qb.params == [0]
    
    def test_add_in_filter(self):
        """Test adding IN filter."""
        qb = QueryBuilder('resources')
        qb.add_in_filter('category', ['study_room', 'lab_equipment', 'av_equipment'])
        
        assert len(qb.conditions) == 1
        assert 'IN (?,?,?)' in qb.conditions[0]
        assert qb.params == ['study_room', 'lab_equipment', 'av_equipment']
    
    def test_add_in_filter_empty_list(self):
        """Test that empty list skips IN filter."""
        qb = QueryBuilder('resources')
        qb.add_in_filter('category', [])
        
        assert len(qb.conditions) == 0
    
    def test_add_in_filter_none_value(self):
        """Test that None value skips IN filter."""
        qb = QueryBuilder('resources')
        qb.add_in_filter('category', None)
        
        assert len(qb.conditions) == 0
    
    def test_add_range_filter_min_only(self):
        """Test adding range filter with minimum only."""
        qb = QueryBuilder('resources')
        qb.add_range_filter('capacity', min_value=5)
        
        assert len(qb.conditions) == 1
        assert 'capacity >= ?' in qb.conditions[0]
        assert qb.params == [5]
    
    def test_add_range_filter_max_only(self):
        """Test adding range filter with maximum only."""
        qb = QueryBuilder('resources')
        qb.add_range_filter('capacity', max_value=10)
        
        assert len(qb.conditions) == 1
        assert 'capacity <= ?' in qb.conditions[0]
        assert qb.params == [10]
    
    def test_add_range_filter_both(self):
        """Test adding range filter with both min and max."""
        qb = QueryBuilder('resources')
        qb.add_range_filter('capacity', min_value=5, max_value=10)
        
        assert len(qb.conditions) == 2
        assert qb.params == [5, 10]
    
    def test_add_range_filter_none_values(self):
        """Test that None values skip range filter."""
        qb = QueryBuilder('resources')
        qb.add_range_filter('capacity', min_value=None, max_value=None)
        
        assert len(qb.conditions) == 0


class TestQueryBuilderGroupBy:
    """Tests for GROUP BY clause."""
    
    def test_set_group_by(self):
        """Test setting GROUP BY clause."""
        qb = QueryBuilder('resources')
        qb.set_group_by('category')
        
        assert qb.group_by == 'category'
    
    def test_set_group_by_multiple_columns(self):
        """Test setting GROUP BY with multiple columns."""
        qb = QueryBuilder('resources')
        qb.set_group_by('category, location')
        
        assert qb.group_by == 'category, location'
    
    def test_set_group_by_method_chaining(self):
        """Test that set_group_by returns self for chaining."""
        qb = QueryBuilder('resources')
        result = qb.set_group_by('category')
        
        assert result is qb


class TestQueryBuilderOrderBy:
    """Tests for ORDER BY clause."""
    
    def test_set_order_by_asc(self):
        """Test setting ORDER BY ASC."""
        qb = QueryBuilder('resources')
        qb.set_order_by('title', 'ASC')
        
        assert qb.order_by == 'title ASC'
    
    def test_set_order_by_desc(self):
        """Test setting ORDER BY DESC."""
        qb = QueryBuilder('resources')
        qb.set_order_by('title', 'DESC')
        
        assert qb.order_by == 'title DESC'
    
    def test_set_order_by_default(self):
        """Test that default order is ASC."""
        qb = QueryBuilder('resources')
        qb.set_order_by('title')
        
        assert qb.order_by == 'title ASC'
    
    def test_set_order_by_invalid_direction(self):
        """Test that invalid direction defaults to ASC."""
        qb = QueryBuilder('resources')
        qb.set_order_by('title', 'INVALID')
        
        assert qb.order_by == 'title ASC'
    
    def test_set_order_by_method_chaining(self):
        """Test that set_order_by returns self for chaining."""
        qb = QueryBuilder('resources')
        result = qb.set_order_by('title')
        
        assert result is qb


class TestQueryBuilderPagination:
    """Tests for pagination."""
    
    def test_set_pagination_limit_only(self):
        """Test setting pagination with limit only."""
        qb = QueryBuilder('resources')
        qb.set_pagination(10)
        
        assert qb.limit == 10
        assert qb.offset == 0
    
    def test_set_pagination_with_offset(self):
        """Test setting pagination with limit and offset."""
        qb = QueryBuilder('resources')
        qb.set_pagination(10, 20)
        
        assert qb.limit == 10
        assert qb.offset == 20
    
    def test_set_pagination_method_chaining(self):
        """Test that set_pagination returns self for chaining."""
        qb = QueryBuilder('resources')
        result = qb.set_pagination(10)
        
        assert result is qb


class TestQueryBuilderBuild:
    """Tests for building final queries."""
    
    def test_build_simple_query(self):
        """Test building a simple query."""
        qb = QueryBuilder('resources')
        query, params = qb.build()
        
        assert query == 'SELECT * FROM resources'
        assert params == []
    
    def test_build_query_with_conditions(self):
        """Test building query with WHERE conditions."""
        qb = QueryBuilder('resources')
        qb.add_condition('status = ?', 'published')
        qb.add_condition('category = ?', 'study_room')
        
        query, params = qb.build()
        
        assert 'WHERE' in query
        assert 'status = ?' in query
        assert 'category = ?' in query
        assert 'AND' in query
        assert params == ['published', 'study_room']
    
    def test_build_query_with_joins(self):
        """Test building query with JOINs."""
        qb = QueryBuilder('resources')
        qb.add_join('LEFT JOIN users u ON u.user_id = resources.owner_id')
        
        query, params = qb.build()
        
        assert 'LEFT JOIN users' in query
        assert params == []
    
    def test_build_query_with_group_by(self):
        """Test building query with GROUP BY."""
        qb = QueryBuilder('resources')
        qb.set_group_by('category')
        
        query, params = qb.build()
        
        assert 'GROUP BY category' in query
    
    def test_build_query_with_order_by(self):
        """Test building query with ORDER BY."""
        qb = QueryBuilder('resources')
        qb.set_order_by('title', 'DESC')
        
        query, params = qb.build()
        
        assert 'ORDER BY title DESC' in query
    
    def test_build_query_with_limit(self):
        """Test building query with LIMIT."""
        qb = QueryBuilder('resources')
        qb.set_pagination(10)
        
        query, params = qb.build()
        
        assert 'LIMIT ?' in query
        assert params == [10]
    
    def test_build_query_with_limit_and_offset(self):
        """Test building query with LIMIT and OFFSET."""
        qb = QueryBuilder('resources')
        qb.set_pagination(10, 20)
        
        query, params = qb.build()
        
        assert 'LIMIT ?' in query
        assert 'OFFSET ?' in query
        assert params == [10, 20]
    
    def test_build_query_with_offset_zero(self):
        """Test that offset of 0 doesn't add OFFSET clause."""
        qb = QueryBuilder('resources')
        qb.set_pagination(10, 0)
        
        query, params = qb.build()
        
        assert 'LIMIT ?' in query
        assert 'OFFSET' not in query
        assert params == [10]
    
    def test_build_complex_query(self):
        """Test building a complex query with all features."""
        qb = QueryBuilder('resources')
        qb.add_join('LEFT JOIN users u ON u.user_id = resources.owner_id')
        qb.add_condition('status = ?', 'published')
        qb.add_like_filter('title', 'study')
        qb.set_group_by('category')
        qb.set_order_by('title', 'DESC')
        qb.set_pagination(10, 20)
        
        query, params = qb.build()
        
        assert 'SELECT * FROM resources' in query
        assert 'LEFT JOIN users' in query
        assert 'WHERE' in query
        assert 'GROUP BY category' in query
        assert 'ORDER BY title DESC' in query
        assert 'LIMIT ?' in query
        assert 'OFFSET ?' in query
        assert len(params) == 4  # 'published', '%study%', 10, 20


class TestQueryBuilderBuildCountQuery:
    """Tests for building COUNT queries."""
    
    def test_build_count_query_simple(self):
        """Test building a simple COUNT query."""
        qb = QueryBuilder('resources')
        query, params = qb.build_count_query()
        
        assert 'SELECT COUNT(DISTINCT' in query
        assert 'FROM resources' in query
        # The implementation generates resources.resources_id (table name + table name + _id)
        assert 'resources.' in query and '_id' in query
    
    def test_build_count_query_with_conditions(self):
        """Test building COUNT query with conditions."""
        qb = QueryBuilder('resources')
        qb.add_condition('status = ?', 'published')
        qb.add_condition('category = ?', 'study_room')
        
        query, params = qb.build_count_query()
        
        assert 'WHERE' in query
        assert params == ['published', 'study_room']
    
    def test_build_count_query_with_joins(self):
        """Test building COUNT query with JOINs."""
        qb = QueryBuilder('resources')
        qb.add_join('LEFT JOIN users u ON u.user_id = resources.owner_id')
        
        query, params = qb.build_count_query()
        
        assert 'LEFT JOIN users' in query
    
    def test_build_count_query_with_custom_distinct_column(self):
        """Test building COUNT query with custom distinct column."""
        qb = QueryBuilder('resources')
        qb.add_join('LEFT JOIN reviews r ON r.resource_id = resources.resource_id')
        
        query, params = qb.build_count_query(distinct_column='r.review_id')
        
        assert 'COUNT(DISTINCT r.review_id)' in query
    
    def test_build_count_query_no_group_by(self):
        """Test that COUNT query doesn't include GROUP BY."""
        qb = QueryBuilder('resources')
        qb.set_group_by('category')
        
        query, params = qb.build_count_query()
        
        assert 'GROUP BY' not in query
    
    def test_build_count_query_no_order_by(self):
        """Test that COUNT query doesn't include ORDER BY."""
        qb = QueryBuilder('resources')
        qb.set_order_by('title')
        
        query, params = qb.build_count_query()
        
        assert 'ORDER BY' not in query
    
    def test_build_count_query_no_pagination(self):
        """Test that COUNT query doesn't include LIMIT/OFFSET."""
        qb = QueryBuilder('resources')
        qb.set_pagination(10, 20)
        
        query, params = qb.build_count_query()
        
        assert 'LIMIT' not in query
        assert 'OFFSET' not in query


class TestQueryBuilderMethodChaining:
    """Tests for method chaining."""
    
    def test_fluent_api(self):
        """Test that all methods can be chained."""
        qb = QueryBuilder('resources')
        result = (qb
                 .add_join('LEFT JOIN users u ON u.user_id = resources.owner_id')
                 .add_condition('status = ?', 'published')
                 .add_like_filter('title', 'study')
                 .add_equals_filter('category', 'study_room')
                 .set_group_by('category')
                 .set_order_by('title', 'DESC')
                 .set_pagination(10, 0))
        
        assert result is qb
        
        query, params = qb.build()
        assert 'WHERE' in query
        assert 'GROUP BY' in query
        assert 'ORDER BY' in query
        assert 'LIMIT' in query
