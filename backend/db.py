import duckdb

def init_db(db_path: str = "havn.duckdb"):
    conn = duckdb.connect(db_path)
    
    # Create tables
    conn.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id VARCHAR,
            source VARCHAR,
            timestamp TIMESTAMP,
            type VARCHAR,
            description VARCHAR,
            metadata JSON
        );
    """)
    
    conn.execute("""
        CREATE TABLE IF NOT EXISTS metrics (
            id VARCHAR,
            source VARCHAR,
            timestamp TIMESTAMP,
            metric_name VARCHAR,
            value DOUBLE,
            unit VARCHAR
        );
    """)
    
    conn.execute("""
        CREATE TABLE IF NOT EXISTS entities (
            id VARCHAR,
            source VARCHAR,
            entity_type VARCHAR,
            name VARCHAR,
            properties JSON
        );
    """)
    
    # Create some helpful views
    conn.execute("""
        CREATE VIEW IF NOT EXISTS daily_metrics AS
        SELECT 
            source,
            metric_name,
            CAST(timestamp AS DATE) AS date,
            AVG(value) as avg_value,
            SUM(value) as sum_value,
            COUNT(value) as count_value,
            unit
        FROM metrics
        GROUP BY source, metric_name, CAST(timestamp AS DATE), unit;
    """)

    conn.execute("""
        CREATE VIEW IF NOT EXISTS daily_events AS
        SELECT
            source,
            type,
            CAST(timestamp AS DATE) AS date,
            COUNT(*) as event_count
        FROM events
        GROUP BY source, type, CAST(timestamp AS DATE);
    """)
    
    return conn

def get_connection(db_path: str = "havn.duckdb"):
    return duckdb.connect(db_path)

if __name__ == "__main__":
    init_db()
    print("Database initialized.")
