"""
SQL query builder utilities for constructing dynamic queries.
"""
from typing import List, Dict, Optional, Tuple, Any


class QueryBuilder:
    """
    Helper class for building SQL queries dynamically.
    """
    
    def __init__(self, base_table: str, base_select: Optional[str] = None):
        """
        Initialize query builder.
        
        Args:
            base_table: Base table name (e.g., 'resources')
            base_select: Custom SELECT clause (defaults to selecting all from base_table)
        """
        self.base_table = base_table
        self.base_select = base_select or f"SELECT * FROM {base_table}"
        self.conditions: List[str] = []
        self.params: List[Any] = []
        self.joins: List[str] = []
        self.group_by: Optional[str] = None
        self.order_by: Optional[str] = None
        self.limit: Optional[int] = None
        self.offset: Optional[int] = None
    
    def add_condition(self, condition: str, *params: Any) -> 'QueryBuilder':
        """
        Add a WHERE condition.
        
        Args:
            condition: SQL condition (e.g., "status = ?")
            *params: Parameters for the condition
            
        Returns:
            Self for method chaining
        """
        if condition:
            self.conditions.append(condition)
            self.params.extend(params)
        return self
    
    def add_join(self, join_clause: str) -> 'QueryBuilder':
        """
        Add a JOIN clause.
        
        Args:
            join_clause: JOIN statement (e.g., "LEFT JOIN reviews r ON r.resource_id = resources.resource_id")
            
        Returns:
            Self for method chaining
        """
        if join_clause:
            self.joins.append(join_clause)
        return self
    
    def add_like_filter(self, column: str, value: Optional[str], 
                        case_sensitive: bool = False) -> 'QueryBuilder':
        """
        Add a LIKE filter condition.
        
        Args:
            column: Column name
            value: Search value (None skips the condition)
            case_sensitive: Whether to use case-sensitive matching
            
        Returns:
            Self for method chaining
        """
        if value:
            pattern = f"%{value}%"
            if case_sensitive:
                self.add_condition(f"{column} LIKE ?", pattern)
            else:
                self.add_condition(f"LOWER({column}) LIKE LOWER(?)", pattern)
        return self
    
    def add_equals_filter(self, column: str, value: Optional[Any]) -> 'QueryBuilder':
        """
        Add an equality filter condition.
        
        Args:
            column: Column name
            value: Value to match (None skips the condition)
            
        Returns:
            Self for method chaining
        """
        if value is not None:
            self.add_condition(f"{column} = ?", value)
        return self
    
    def add_in_filter(self, column: str, values: Optional[List[Any]]) -> 'QueryBuilder':
        """
        Add an IN filter condition.
        
        Args:
            column: Column name
            values: List of values (None or empty list skips the condition)
            
        Returns:
            Self for method chaining
        """
        if values:
            placeholders = ','.join('?' * len(values))
            self.add_condition(f"{column} IN ({placeholders})", *values)
        return self
    
    def add_range_filter(self, column: str, min_value: Optional[Any] = None, 
                        max_value: Optional[Any] = None) -> 'QueryBuilder':
        """
        Add a range filter condition.
        
        Args:
            column: Column name
            min_value: Minimum value (None skips)
            max_value: Maximum value (None skips)
            
        Returns:
            Self for method chaining
        """
        if min_value is not None:
            self.add_condition(f"{column} >= ?", min_value)
        if max_value is not None:
            self.add_condition(f"{column} <= ?", max_value)
        return self
    
    def set_group_by(self, columns: str) -> 'QueryBuilder':
        """
        Set GROUP BY clause.
        
        Args:
            columns: Column(s) to group by
            
        Returns:
            Self for method chaining
        """
        self.group_by = columns
        return self
    
    def set_order_by(self, column: str, direction: str = 'ASC') -> 'QueryBuilder':
        """
        Set ORDER BY clause.
        
        Args:
            column: Column to order by
            direction: 'ASC' or 'DESC'
            
        Returns:
            Self for method chaining
        """
        direction = direction.upper()
        if direction not in ('ASC', 'DESC'):
            direction = 'ASC'
        self.order_by = f"{column} {direction}"
        return self
    
    def set_pagination(self, limit: int, offset: int = 0) -> 'QueryBuilder':
        """
        Set pagination parameters.
        
        Args:
            limit: Maximum number of rows
            offset: Number of rows to skip
            
        Returns:
            Self for method chaining
        """
        self.limit = limit
        self.offset = offset
        return self
    
    def build(self) -> Tuple[str, List[Any]]:
        """
        Build the final SQL query.
        
        Returns:
            Tuple of (query_string, parameters)
        """
        query = self.base_select
        
        # Add JOINs
        if self.joins:
            query += " " + " ".join(self.joins)
        
        # Add WHERE clause
        if self.conditions:
            query += " WHERE " + " AND ".join(self.conditions)
        
        # Add GROUP BY
        if self.group_by:
            query += f" GROUP BY {self.group_by}"
        
        # Add ORDER BY
        if self.order_by:
            query += f" ORDER BY {self.order_by}"
        
        # Add LIMIT and OFFSET
        if self.limit is not None:
            query += f" LIMIT ?"
            self.params.append(self.limit)
            if self.offset is not None and self.offset > 0:
                query += " OFFSET ?"
                self.params.append(self.offset)
        
        return query, self.params
    
    def build_count_query(self, distinct_column: Optional[str] = None) -> Tuple[str, List[Any]]:
        """
        Build a COUNT query for the same conditions.
        
        Args:
            distinct_column: Column to count distinct (e.g., 'resource_id'). 
                           If None, uses base_table with _id suffix.
        
        Returns:
            Tuple of (query_string, parameters)
        """
        # Determine column to count
        if distinct_column:
            count_col = distinct_column
        else:
            # Extract table name and add _id suffix
            table_name = self.base_table.split()[-1].split('.')[-1]
            count_col = f"{self.base_table}.{table_name}_id"
        
        # Build count query
        count_select = f"SELECT COUNT(DISTINCT {count_col}) FROM {self.base_table}"
        
        query = count_select
        
        # Add JOINs
        if self.joins:
            query += " " + " ".join(self.joins)
        
        # Add WHERE clause
        if self.conditions:
            query += " WHERE " + " AND ".join(self.conditions)
        
        return query, self.params

