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

                        row_text.append(text)

                        if link:
                            # Get the urls for each athlete
                            full_url = urljoin(base_url, link['href'])
                            row_text.append(full_url)
                        else:
                            row_text.append(pd.NA) # All players have links, but teams/countries do not, this allows those to be removed later easily usign dropna

                    # append cells to table
                    if len(row_text) == 15:
                        table_data.append(row_text)

                # Create DataFrame
                columns = [
                    'Sport',
                    'Event', 'Event_url',
                    'Gold', 'Gold_url',
                    'NOC_G', 'NOC_G_url',
                    'Silver', 'Silver_url',
                    'NOC_S', 'NOC_S_url',
                    'Bronze', 'Bronze_url',
                    'NOC_B', 'NOC_B_url'
                ]
                df = pd.DataFrame(table_data, columns=columns)
                tables.append(df)
                print(f"Successfully scraped {url}")
            else:
                print(f"No table found at {url}")

        except requests.exceptions.RequestException as e:
            print(f"Error fetching {url}: {e}")

        # Implement 20 second delay, only 10 second is necessary, but this is safer.
        time.sleep(20)

    year = 2010
    for i in range(len(tables)):
        df = tables[i]
        df.drop(index=df.index[0], axis=0, inplace=True)
        df = df.replace('—', pd.NA).dropna()
        df['year'] = year
        tables[i] = df
        year += 4

    combined_df = pd.concat(tables, ignore_index=True)
    combined_df = combined_df.drop(['Event_url', 'NOC_G_url', 'NOC_S_url', 'NOC_B_url'], axis=1)

    combined_df.to_csv(r"DATA3463-MiniProject2\out\podium.csv", index=False)

if __name__ == '__main__':
    Podium()