import os
import sqlite3

queries = [
    '''
    SELECT c.Country, COUNT(r.medal) as medalNum
    FROM countries c
    JOIN results r ON c.country_code = r.country
    WHERE r.sport LIKE '%Ski%'
        OR r.sport LIKE '%Biath%'
        OR r.sport LIKE '%Nord%'
    GROUP BY c.Country
    ORDER BY medalNum DESC
    ''',
    '''
    SELECT c.Country, COUNT(r.medal) as medalNum
    FROM countries c
    JOIN results r ON c.country_code = r.country
    WHERE r.sport LIKE '%Skat%'
    GROUP BY c.Country
    ORDER BY medalNum DESC
    ''',
    '''
    SELECT c.Country, COUNT(r.medal) as medalNum
    FROM countries c
    JOIN results r ON c.country_code = r.country
    WHERE r.sport LIKE '%Snowb%'
    GROUP BY c.Country
    ORDER BY medalNum DESC
    ''',
    '''
    SELECT AVG(a.height), AVG(a.weight), AVG(r.year - CAST(strftime('%Y', a.dob) AS INTEGER))
    FROM results r
    JOIN athletes a ON a.athlete_url = r.athlete_url
    JOIN countries c ON c.country_code = r.country
    WHERE r.sport LIKE '%Ski%'
        OR r.sport LIKE '%Biath%'
        OR r.sport LIKE '%Nord%'
    GROUP BY c.Country
    ORDER BY COUNT(r.medal) DESC
    ''',
    '''
    SELECT AVG(a.height), AVG(a.weight), AVG(r.year - CAST(strftime('%Y', a.dob) AS INTEGER))
    FROM results r
    JOIN athletes a ON a.athlete_url = r.athlete_url
    JOIN countries c ON c.country_code = r.country
    WHERE r.sport LIKE '%Skat%'
    GROUP BY c.Country
    ORDER BY COUNT(r.medal) DESC
    ''',
    '''
    SELECT AVG(a.height), AVG(a.weight), AVG(r.year - CAST(strftime('%Y', a.dob) AS INTEGER))
    FROM results r
    JOIN athletes a ON a.athlete_url = r.athlete_url
    JOIN countries c ON c.country_code = r.country
    WHERE r.sport LIKE '%Snowb%'
    GROUP BY c.Country
    ORDER BY COUNT(r.medal) DESC
    '''
    ]

db_path = r"DATA3463-MiniProject2\olympics.db"

if not os.path.exists(db_path):
    print(f"Error: Database not found at {db_path}")
else:
    db_uri = f'file:{db_path}?mode=ro'
    
    try:
        with sqlite3.connect(db_uri, uri=True) as conn:
            cursor = conn.cursor()
            
            for i, query in enumerate(queries):
                print(f"Running Query {i+1}")
                cursor.execute(query)
                rows = cursor.fetchall()
                for row in rows:
                    print(row)
                print("\n")
                
    except sqlite3.OperationalError as e:
        print(f"Error: {e}. Check if the file path is correct!")
