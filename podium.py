import requests
import time
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urljoin

def Podium():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Podium Data for Medal Correlation/1.0 (ssain0771@mtroyal.ca)',
        'Accept': 'text/html,application/xhtml+xml',
        'From': 'ssain0771@mtroyal.ca'
    }

    base_url = "https://www.olympedia.org"
    medals_pages = [
        "/editions/57/medal",
        "/editions/58/medal",
        "/editions/60/medal",
        "/editions/62/medal",
        "/editions/72/medal"
    ]

    all_data = []

    for page in medals_pages:
        url = base_url + page
        try:
            response = requests.get(url, timeout=10, headers=headers)
            response.raise_for_status()

            # Parse Content
            soup = BeautifulSoup(response.text, 'html.parser')
            table_element = soup.find('table', class_='table')

            if table_element:
                rows = table_element.find_all('tr')

                for row in rows:
                    # Find all header and data cells
                    cells = row.find_all(['th', 'td'])

                    if len(cells) == 1:
                        continue

                    medal_cells = cells[1:] # skip Event column
                    if len(medal_cells) == 6:
                        for i in range(0, 6, 2):
                            name_cell = medal_cells[i]
                            noc_cell = medal_cells[i + 1]
                            country = noc_cell.get_text(strip=True)

                            links = name_cell.find_all('a', href=True)
                            if links:
                                for link in links:
                                    athlete_name = link.get_text(strip=True)
                                    athlete_url = urljoin(base_url, link['href'])

                                    if athlete_name and athlete_name != '—':
                                        all_data.append({
                                            'athleteName': athlete_name,
                                            'athleteURL': athlete_url,
                                            'country': country
                                        })

                print(f"Successfully scraped {url}")
            else:
                print(f"No table found at {url}")

        except requests.exceptions.RequestException as e:
            print(f"Error fetching {url}: {e}")

        time.sleep(20)

    df = pd.DataFrame(all_data).dropna()
    df = df.drop_duplicates(keep='last', subset=['athleteURL']) # keeps most recent information about athletes that won multiple times, ensures all urls are unique
    df.to_csv(r"DATA3463-MiniProject2\out\podium.csv", index=False)
    print(f"Saved {len(df)} athletes")

if __name__ == '__main__':
    Podium()