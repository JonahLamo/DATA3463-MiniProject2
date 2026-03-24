import sqlite3

query = '''
SELECT c.Country, COUNT(r.medal) as medalNum
FROM countries c
JOIN results r ON c.country_code = r.country
WHERE r.sport LIKE '%Ski%'
   OR r.sport LIKE '%Biath%'
   OR r.sport LIKE '%Nord%'
GROUP BY c.Country
ORDER BY medalNum DESC
'''

db_path = r"DATA3463-MiniProject2\olympics.db"

try:
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        cursor.execute(query)
        
        rows = cursor.fetchall()
        for row in rows:
            print(row)
            
except sqlite3.OperationalError as e:
    print(f"Error: {e}. Check if the file path is correct!")
