import requests
import time
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urljoin

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Medal_Correlation/1.0 (ssain0771@mtroyal.ca)',
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

tables = []

for page in medals_pages:
    url = base_url + page
    try:
        response = requests.get(url, timeout=10, headers=headers)
        response.raise_for_status()

        # Parse Content
        soup = BeautifulSoup(response.text, 'html.parser')
        table_element = soup.find('table', class_='table')

        if table_element:
            # Create empty list
            table_data = []
            current_sport = "Unknown" # Placeholder

            # Find all rows
            rows = table_element.find_all('tr')

            for row in rows:
                # Find all header and data cells
                cells = row.find_all(['th', 'td'])

                # Check if 
                if len(cells) == 1:
                    current_sport = cells[0].get_text(strip=True)
                    continue 
                
                # Extract text from each cell
                row_text = [current_sport]
                for cell in cells:
                    text = cell.get_text(strip=True) # clean whitespace
                    link = cell.find('a', href=True)

                    if link:
                        # Get the urls for each athlete
                        full_url = urljoin(base_url, link['href'])
                        row_text.append(f"{text} ({full_url})")
                    else:
                        row_text.append(text)

                # append cells to table
                if len(row_text) >= 7:
                    table_data.append(row_text)

            # Create DataFrame
            columns = ['Sport', 'Event', 'Gold', 'NOC_G', 'Silver', 'NOC_S', 'Bronze', 'NOC_B']
            df = pd.DataFrame(table_data, columns=columns)
            tables.append(df)
        else:
            print(f"No table found at {url}")

    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")

    # Implement 20 second delay, only 10 second is necessary, but this is safer.
    time.sleep(20)

set = 0
for table in tables:
    set =+ 1
    table['set'] = set

combined_df = pd.concat(tables, ignore_index=True)
combined_df.to_csv(r"miniProject2\out\podium.csv", index=False)