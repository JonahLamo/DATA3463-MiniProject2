import re
import requests
import time
import pandas as pd
from bs4 import BeautifulSoup
import sqlite3

def GDP():
    url = "https://www.worldometers.info/gdp/gdp-by-country/"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) GDP for Olympic Medal Correlation/1.0 (ssain0771@mtroyal.ca)',
        'Accept': 'text/html,application/xhtml+xml',
        'From': 'ssain0771@mtroyal.ca'
    }

    response = requests.get(url, timeout=10, headers=headers)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')

    table = soup.find("table")
    gdp_countries = []

    for row in table.find_all('tr')[1:]:
        cols = row.find_all('td')

        if len(cols) > 2:
            country = cols[1].text.strip()
            gdp = cols[2].text.strip()

            gdp_match = re.search(r'\$?([\d.]+)\s*(million|billion|trillion)', gdp)

            if gdp_match:
                value = float(gdp_match.group(1))
                multiply = gdp_match.group(2)

                multipliers = {
                    "million": 1e6,
                    "billion": 1e9,
                    "trillion": 1e12
                }

                gdp_value = int(value * multipliers[multiply])
                gdp_countries.append([country, gdp_value])

    return pd.DataFrame(gdp_countries, columns=["Country", "GDP"])


def Population():
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

    for row in table.find_all('tr')[1:]:
        cols = row.find_all('td')

        if len(cols) > 2:
            country = cols[1].text.strip()
            pop = int(cols[2].text.replace(',', '').strip())
            pops.append([country, pop])

    return pd.DataFrame(pops, columns=['Country', 'Pop'])


def Countries():
    pop = Population()
    print("Scraped population")

    time.sleep(20)

    gdp = GDP()
    print("Scraped GDP")

    df = pd.merge(pop, gdp, on='Country', how='inner')
    df['gdpPerCapita'] = round(df['GDP'] / df['Pop'], 2)

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

    short_df = pd.DataFrame(list(country_short.items()), columns=['Country', 'country_code'])
    df = pd.merge(df, short_df, on='Country', how='right')

    db_path = r"DATA3463-MiniProject2\olympics.db"
    conn = sqlite3.connect(db_path)
    df.to_sql('countries', conn, if_exists='replace', index=False)
    conn.close()
    print(f"Saved {len(df)} countries to {db_path}")

if __name__ == '__main__':
    Countries()