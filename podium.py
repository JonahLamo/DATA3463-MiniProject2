import requests
import time
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import sqlite3

def Podium():
    # Identify ourselves politely to the server (good scraping practice)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Podium Data for Medal Correlation/1.0 (ssain0771@mtroyal.ca)',
        'Accept': 'text/html,application/xhtml+xml',
        'From': 'ssain0771@mtroyal.ca'
    }

    base_url = "https://www.olympedia.org"
    # Olympedia edition IDs for the Winter Olympics: 2010, 2014, 2018, 2022, 2026
    medals_pages = [
        "/editions/57/medal",
        "/editions/58/medal",
        "/editions/60/medal",
        "/editions/62/medal",
        "/editions/72/medal"
    ]

    all_data = []  # Will hold one dict per athlete/podium entry found

    for page in medals_pages:
        url = base_url + page
        try:
            response = requests.get(url, timeout=15, headers=headers)
            response.raise_for_status()  # Raise an error if the request failed (4xx/5xx)

            # Parse the HTML into a searchable tree
            soup = BeautifulSoup(response.text, 'html.parser')
            table_element = soup.find('table', class_='table')  # Find the medal results table

            if table_element:
                rows = table_element.find_all('tr')  # Get every row in the table

                for row in rows:
                    # Find all header and data cells
                    cells = row.find_all(['th', 'td'])

                    medal_cells = cells[1:]  # Skip the first column (Event name)
                    # A valid medal row has exactly 6 cells: Gold name, Gold country, Silver name, Silver country, Bronze name, Bronze country
                    if len(medal_cells) == 6:
                        # Step through columns 0, 2, 4 (the three athlete name columns)
                        for i in range(0, 6, 2):
                            name_cell = medal_cells[i]

                            # Each name cell may contain one or more athlete links (e.g. relay teams)
                            links = name_cell.find_all('a', href=True)
                            if links:
                                for link in links:
                                    athlete_name = link.get_text(strip=True)
                                    # Build the full URL from the relative href
                                    athlete_url = urljoin(base_url, link['href'])

                                    # Ignore empty cells or placeholder dashes
                                    if athlete_name and athlete_name != '—':
                                        all_data.append({
                                            'athleteName': athlete_name,
                                            'athleteURL': athlete_url
                                        })

                print(f"Successfully scraped {url}")
            else:
                print(f"No table found at {url}")

        except requests.exceptions.RequestException as e:
            print(f"Error fetching {url}: {e}")

        # Polite delay between requests to avoid hammering the server
        time.sleep(15)

    # Build a DataFrame and remove duplicate athletes (keep the last occurrence by URL)
    df = pd.DataFrame(all_data).drop_duplicates(keep='last', subset=['athleteURL'])

    # Save the podium athletes table to the SQLite database
    db_path = r"DATA3463-MiniProject2\olympics.db"
    conn = sqlite3.connect(db_path)
    df.to_sql('podium', conn, if_exists='replace', index=False)  # Overwrite table if it already exists
    conn.close()
    print(f"Saved {len(df)} athletes to {db_path}")

if __name__ == '__main__':
    Podium()