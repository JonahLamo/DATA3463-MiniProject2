
import re
import requests
import time
import pandas as pd
from bs4 import BeautifulSoup

def GDP():
    url = "https://www.worldometers.info/gdp/gdp-by-country/"

    headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) GDP for Olympic Medal Correlation/1.0 (jlamo625@mtroyal.ca)',
            'Accept': 'text/html,application/xhtml+xml',
            'From': 'jlamo625@mtroyal.ca'
        }

    response = requests.get(url, timeout=10, headers=headers)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')

    table = soup.find("table")

    gdp_coutnries = []

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

                gdp = value * multipliers[multiply]
                gdp = int(gdp)
            data = [country, gdp]

        gdp_coutnries.append(data)
        time.sleep(5)   

    df = pd.DataFrame(gdp_coutnries, columns=["Country", "GDP"])

    return df


def Population ():

    url = 'https://www.worldometers.info/world-population/population-by-country/'

    headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) GDP for Olympic Medal Correlation/1.0 (jlamo625@mtroyal.ca)',
            'Accept': 'text/html,application/xhtml+xml',
            'From': 'jlamo625@mtroyal.ca'
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
            pop = cols[2].text
            pop = pop.replace(',', '').strip()
            pop = int(pop)

            data = [country, pop]

        pops.append(data)
        time.sleep(5) 

    df = pd.DataFrame(pops, columns=['Country', "Pop"])

    return df


def Countries():
    pop = Population()
    print("did pop")
    gdp = GDP()
    print("did gdp")

    df = pd.merge(pop, gdp, on = 'Country', how = 'inner')
    print('merged')
    df = df.assign(gdpPerCapita = lambda x: round(x['GDP']/ x['Pop'],2))
    country_short = pd.read_csv('country_shortForm.csv')

    df_right = pd.merge(df, country_short, on = 'Country', how = 'right')
    #df_inner = pd.merge(df, country_short, on = 'Country', how = 'inner')
    df_right.to_csv('countries.csv')
    #df_inner.to_csv('inner.csv')

if __name__ == '__main__':
    Countries()
