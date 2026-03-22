import re
import requests
import time
import pandas as pd
from bs4 import BeautifulSoup
import sqlite3

def GDP():
    """Scrapes GDP by country from Worldometers and returns a DataFrame with columns [Country, GDP]."""
    url = "https://www.worldometers.info/gdp/gdp-by-country/"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) GDP for Olympic Medal Correlation/1.0 (ssain0771@mtroyal.ca)',
        'Accept': 'text/html,application/xhtml+xml',
        'From': 'ssain0771@mtroyal.ca'
    }

    response = requests.get(url, timeout=10, headers=headers)
    response.raise_for_status()  # Raise an error if the request failed (4xx/5xx)
    soup = BeautifulSoup(response.text, 'html.parser')

    table = soup.find("table")  # The page has one main table
    gdp_countries = []

    for row in table.find_all('tr')[1:]:  # Skip the header row
        cols = row.find_all('td')

        if len(cols) > 2:
            country = cols[1].text.strip()   # Column 1: country name
            gdp = cols[2].text.strip()        # Column 2: GDP as a formatted string (e.g. "$1.5 trillion")

            # Extract the numeric value and the scale word (million/billion/trillion)
            gdp_match = re.search(r'\$?([\d.]+)\s*(million|billion|trillion)', gdp)

            if gdp_match:
                value = float(gdp_match.group(1))   # The numeric part (e.g. 1.5)
                multiply = gdp_match.group(2)         # The scale word

                # Map each scale word to its numeric multiplier
                multipliers = {
                    "million": 1e6,
                    "billion": 1e9,
                    "trillion": 1e12
                }

                # Convert to a plain integer (e.g. 1.5 trillion to 1_500_000_000_000)
                gdp_value = int(value * multipliers[multiply])
                gdp_countries.append([country, gdp_value])

    return pd.DataFrame(gdp_countries, columns=["Country", "GDP"])


def Population():
    """Scrapes population by country from Worldometers and returns a DataFrame with columns [Country, Pop]."""
    url = 'https://www.worldometers.info/world-population/population-by-country/'

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) GDP for Olympic Medal Correlation/1.0 (ssain0771@mtroyal.ca)',
        'Accept': 'text/html,application/xhtml+xml',
        'From': 'ssain0771@mtroyal.ca'
    }

    response = requests.get(url, timeout=10, headers=headers)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')

    table = soup.find("table")
    pops = []

    for row in table.find_all('tr')[1:]:  # Skip the header row
        cols = row.find_all('td')

        if len(cols) > 2:
            country = cols[1].text.strip()                        # Column 1: country name
            pop = int(cols[2].text.replace(',', '').strip())      # Column 2: population (strip commas before converting)
            pops.append([country, pop])

    return pd.DataFrame(pops, columns=['Country', 'Pop'])


def Countries():
    """Combines population and GDP data, calculates GDP per capita, maps country codes,
    and saves the result to the 'countries' table in the SQLite database."""

    pop = Population()
    print("Scraped population")

    time.sleep(20)  # Polite delay between requests

    gdp = GDP()
    print("Scraped GDP")

    # Inner join so we only keep countries present in both datasets
    df = pd.merge(pop, gdp, on='Country', how='inner')
    # Derive GDP per capita as a rounded float
    df['gdpPerCapita'] = round(df['GDP'] / df['Pop'], 2)

    # Mapping from Worldometers country names to 3-letter Olympic NOC codes
    # Only includes countries that actually appear in the Winter Olympics medal tables
    country_short = {
        "Norway": "NOR",
        "United States": "USA",
        "Germany": "GER",
        "Canada": "CAN",
        "Austria": "AUT",
        "Sweden": "SWE",
        "Switzerland": "SUI",
        "Netherlands": "NED",
        "Russia": "RUS",
        "Italy": "ITA",
        "France": "FRA",
        "Finland": "FIN",
        "South Korea": "KOR",
        "China": "CHN",
        "Japan": "JPN",
        "United Kingdom": "GBR",
        "Czech Republic (Czechia)": "CZE",
        "Australia": "AUS",
        "Belarus": "BLR",
        "Poland": "POL",
        "Slovenia": "SLO",
        "Croatia": "CRO",
        "Slovakia": "SVK",
        "Estonia": "EST",
        "Ukraine": "UKR",
        "Hungary": "HUN",
        "Liechtenstein": "LIE",
        "Belgium": "BEL",
        "New Zealand": "NZL",
        "Kazakhstan": "KAZ",
        "Spain": "ESP",
        "Latvia": "LAT",
        "Bulgaria": "BUL",
        "Uzbekistan": "UZB",
        "Brazil": "BRA",
        "Luxembourg": "LUX",
        "Denmark": "DEN",
        "Georgia": "GEO",
        "Romania": "ROU"
    }

    # Convert the mapping dict to a DataFrame so we can join on it
    short_df = pd.DataFrame(list(country_short.items()), columns=['Country', 'country_code'])
    # Right join: keep only countries in our NOC list (drops countries without Olympic codes)
    df = pd.merge(df, short_df, on='Country', how='right')

    # Save the countries table to the SQLite database
    db_path = r"DATA3463-MiniProject2\olympics.db"
    conn = sqlite3.connect(db_path)
    df.to_sql('countries', conn, if_exists='replace', index=False)  # Overwrite if table already exists
    conn.close()
    print(f"Saved {len(df)} countries to {db_path}")

if __name__ == '__main__':
    Countries()