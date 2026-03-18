import requests
import time
import pandas as pd
from bs4 import BeautifulSoup
import re

def AthletesResults():
    # Load the urls from podium.csv
    try:
        podium_df = pd.read_csv(r"DATA3463-MiniProject2\out\podium.csv")
    except FileNotFoundError:
        print("podium.csv not found. Run podium.py first.")
        return

    # adding all the years the athlete got a podium finish
    melted = podium_df.melt(id_vars=['year'], value_vars=['Gold_url', 'Silver_url', 'Bronze_url'], value_name='url').dropna()
    year_map = melted.groupby('url')['year'].apply(lambda x: ", ".join(map(str, sorted(set(x))))).to_dict()
    # Get unique athlete urls only (combining Gold, Silver, Bronze URL columns)
    # We filter out NAs because teams/countries don't have athlete pages
    all_urls = list(year_map.keys())

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Athlete Data for Medal Correlation/1.0 (ssain0771@mtroyal.ca)',
        'Accept': 'text/html,application/xhtml+xml',
        'From': 'ssain0771@mtroyal.ca'
    }

    athlete_data = []

    for url in all_urls:
        print(f"Scraping: {url}")
        try:
            response = requests.get(url, timeout=20, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Initialize fields as NA
            dob, birth_city, height, weight, affiliation = pd.NA, pd.NA, pd.NA, pd.NA, pd.NA
            
            # Find the biographical table
            bio_table = soup.find('table', class_='biodata')
            if bio_table:
                for row in bio_table.find_all('tr'):
                    th = row.find('th')
                    td = row.find('td')
                    if not th or not td: continue

                    header = th.get_text(strip=True)
                    value = td.get_text(' ', strip=True)
                    
                    if header == 'Born':
                        # Date = "11 March 2026"
                        dob_match = re.search(r'(\d+\s+\w+\s+\d{4})', value)
                        if dob_match:
                            dob = dob_match.group(1)
                        
                        if 'in ' in value:
                            city_info = value.split('in ')[-1]
                            birth_city = re.sub(r'\s*\([^)]*\)$', '', city_info).strip()
                            
                    elif header == 'Measurements':
                        # Pattern for "173 cm / 66 kg"
                        m_match = re.search(r'(\d+)\s*cm\s*/\s*(\d+)\s*kg', value)
                        if m_match:
                            height = m_match.group(1)
                            weight = m_match.group(2)
                    
                    elif header == "Affiliations":
                        affiliations = value
                            
            athlete_data.append({
                'athlete_url': url,
                'medal_years': year_map.get(url),
                'dob': dob,
                'birth_city': birth_city,
                'height_cm': height,
                'weight_kg': weight,
                "affiliations": affiliations
            })

        except Exception as e:
            print(f"Error scraping {url}: {e}")
        
        # Implement 20 second delay, only 10 second is necessary, but this is safer.
        time.sleep(20) 

    # Create DataFrame and Save
    athletes_df = pd.DataFrame(athlete_data)
    athletes_df['dob'] = pd.to_datetime(athletes_df['dob'], format='%d %B %Y', errors='coerce')
    athletes_df.to_csv(r"DATA3463-MiniProject2\out\athletes.csv", index=False)
    print("Finished Scraping. Athletes CSV created.")

if __name__ == '__main__':
    AthletesResults()