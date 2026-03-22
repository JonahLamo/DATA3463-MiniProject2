import requests
import time
import pandas as pd
from bs4 import BeautifulSoup
import re
import sqlite3

# Only collect results from these Winter Olympics years
YEARS = [2010, 2014, 2018, 2022, 2026]

def AthletesResults():
    """For every athlete in the podium table, scrapes their Olympedia profile page to collect:
    - Bio data (DOB, height, weight, city, affiliations) is saved to 'athletes' table
    - Individual medal results for the target years is saved to 'results' table
    """
    db_path = r"DATA3463\DATA3463-MiniProject2\olympics.db"

    # Load the list of athlete profile URLs that were collected by podium.py
    try:
        conn = sqlite3.connect(db_path)
        podium_df = pd.read_sql('SELECT * FROM podium', conn)
        conn.close()
    except Exception as e:
        print(f"Could not read podium table: {e}")
        return

    # Deduplicate URLs so we don't scrape the same athlete twice
    all_urls = podium_df['athleteURL'].dropna().unique().tolist()
    print(f"Loaded {len(all_urls)} unique URLs from podium table")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Athlete Data for Medal Correlation/1.0 (ssain0771@mtroyal.ca)',
        'Accept': 'text/html,application/xhtml+xml',
        'From': 'ssain0771@mtroyal.ca'
    }

    athlete_data = []   # One entry per athlete (bio info)
    results_data = []   # One entry per individual medal result

    for url in all_urls:
        print(f"Scraping: {url}")
        try:
            response = requests.get(url, timeout=15, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            # Bio table
            # Default all bio fields to NA in case they are missing from the page
            dob, city, height, weight, affiliations = pd.NA, pd.NA, pd.NA, pd.NA, pd.NA

            bio_table = soup.find('table', class_='biodata')
            if bio_table:
                for row in bio_table.find_all('tr'):
                    th = row.find('th')   # Row label (e.g. "Born", "Measurements")
                    td = row.find('td')   # Row value
                    if not th or not td:
                        continue

                    header = th.get_text(strip=True)
                    value = td.get_text(' ', strip=True)

                    if header == 'Born':
                        # Extract date like "15 February 1985"
                        dob_match = re.search(r'(\d+\s+\w+\s+\d{4})', value)
                        if dob_match:
                            dob = dob_match.group(1)
                        # Extract birth city (text after "in ", stripping any parenthetical notes)
                        if 'in ' in value:
                            city_info = value.split('in ')[-1]
                            city = re.sub(r'\s*\([^)]*\)$', '', city_info).strip()

                    elif header == 'Measurements':
                        # Extract height in cm and weight in kg
                        h_match = re.search(r'(\d+)\s*cm', value)
                        w_match = re.search(r'(\d+)\s*kg', value)
                        if h_match:
                            height = h_match.group(1)
                        if w_match:
                            weight = w_match.group(1)

                    elif header == 'Affiliations':
                        affiliations = value  # e.g. club or national team name

            # Store the bio record regardless of whether bio data was found
            athlete_data.append({
                'athlete_url': url,
                'dob': dob,
                'height': height,
                'weight': weight,
                'city': city,
                'affiliations': affiliations
            })

            # Results table
            # The results table groups rows: an 'active' header row gives the year/sport/country,
            # followed by indented rows for each individual event within that group.
            results_table = soup.find('table', class_='table')
            if results_table:
                # Track the current year/sport/country as we walk down the grouped rows
                current_year = None
                current_sport = None
                current_country = None

                for row in results_table.find('tbody').find_all('tr'):
                    if 'active' in row.get('class', []):
                        # Header row for an Olympics appearance — sets context for following event rows
                        cells = row.find_all('td')
                        year_match = re.search(r'(\d{4})', cells[0].get_text(strip=True))
                        current_year = int(year_match.group(1)) if year_match else None

                        # Skip this entire block if the year is not in our target list
                        if current_year not in YEARS:
                            continue

                        # Sport name may be a link or plain text
                        sport_cell = cells[1]
                        sport_link = sport_cell.find('a')
                        current_sport = sport_link.get_text(strip=True) if sport_link else cells[1].get_text(strip=True)

                        # NOC (country code) the athlete competed under that year
                        noc_cell = cells[2]
                        noc_link = noc_cell.find('a')
                        current_country = noc_link.get_text(strip=True) if noc_link else noc_cell.get_text(strip=True)

                    else:
                        # Event row — only process if the parent year is relevant
                        if current_year not in YEARS:
                            continue

                        cells = row.find_all('td')

                        # Skip team events - they have a value in the NOC/Team column
                        # (individual event rows leave this cell blank)
                        team_cell = cells[2].get_text(strip=True)
                        if team_cell:
                            continue

                        # Get event name
                        event_cell = cells[1]
                        event_link = event_cell.find('a')
                        event_name = event_link.get_text(strip=True) if event_link else event_cell.get_text(strip=True)

                        # Check for medals — look for a coloured span in any cell
                        medal = None
                        for cell in cells:
                            if cell.find('span', class_='Gold'):
                                medal = 'Gold'
                            elif cell.find('span', class_='Silver'):
                                medal = 'Silver'
                            elif cell.find('span', class_='Bronze'):
                                medal = 'Bronze'

                        # Only record rows where a medal was actually won
                        if medal:
                            results_data.append({
                                'athlete_url': url,
                                'year': current_year,
                                'sport': current_sport,
                                'event': event_name,
                                'medal': medal,
                                'country': current_country
                            })

        except Exception as e:
            print(f"Error scraping {url}: {e}")

        # Polite delay between athlete pages
        time.sleep(15)

    # Save to SQLite
    athletes_df = pd.DataFrame(athlete_data)
    # Parse DOB strings into proper datetime objects; invalid formats become NaT
    athletes_df['dob'] = pd.to_datetime(athletes_df['dob'], format='%d %B %Y', errors='coerce')

    results_df = pd.DataFrame(results_data)

    conn = sqlite3.connect(db_path)
    athletes_df.to_sql('athletes', conn, if_exists='replace', index=False)
    results_df.to_sql('results', conn, if_exists='replace', index=False)
    conn.close()
    print(f"Saved {len(athletes_df)} athletes and {len(results_df)} results to {db_path}")

if __name__ == '__main__':
    AthletesResults()