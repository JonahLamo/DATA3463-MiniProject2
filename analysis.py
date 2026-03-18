import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def analyze():
    db_path = r"DATA3463-MiniProject2\olympics.db"
    conn = sqlite3.connect(db_path)

    athletes = pd.read_sql('SELECT * FROM athletes', conn)
    results = pd.read_sql('SELECT * FROM results', conn)
    countries = pd.read_sql('SELECT * FROM countries', conn)
    conn.close()

    # Merge athletes with their results
    df = pd.merge(results, athletes, on='athlete_url', how='left')

    # Merge country data via the country code in results
    df = pd.merge(df, countries, left_on='country', right_on='country_code', how='left')

    # Convert types
    df['height'] = pd.to_numeric(df['height'], errors='coerce')
    df['weight'] = pd.to_numeric(df['weight'], errors='coerce')

    sns.set_theme(style='whitegrid')

    # Height distribution by sport
    fig, ax = plt.subplots(figsize=(12, 6))
    sport_counts = df.groupby('sport')['height'].count()
    valid_sports = sport_counts[sport_counts >= 5].index
    sns.boxplot(data=df[df['sport'].isin(valid_sports)], x='sport', y='height', ax=ax)
    ax.set_title('Medalist Height by Sport')
    ax.set_xlabel('')
    ax.tick_params(axis='x', rotation=45)
    plt.tight_layout()
    plt.savefig(r"DATA3463-MiniProject2\out\height_by_sport.png")
    plt.show()

    # GDP per capita vs medal count by country
    medal_counts = df.groupby('country').size().reset_index(name='medal_count')
    country_medals = pd.merge(medal_counts, countries, left_on='country', right_on='country_code', how='left')

    fig, ax = plt.subplots(figsize=(10, 6))
    sns.scatterplot(data=country_medals, x='gdpPerCapita', y='medal_count', ax=ax)
    for _, row in country_medals.iterrows():
        if pd.notna(row['country_code']):
            ax.annotate(row['country_code'], (row['gdpPerCapita'], row['medal_count']), fontsize=8)
    ax.set_title('GDP per Capita vs Medal Count')
    ax.set_xlabel('GDP per Capita ($)')
    ax.set_ylabel('Total Medals')
    plt.tight_layout()
    plt.savefig(r"DATA3463-MiniProject2\out\gdp_vs_medals.png")
    plt.show()

    # Population vs medal count
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.scatterplot(data=country_medals, x='Pop', y='medal_count', ax=ax)
    for _, row in country_medals.iterrows():
        if pd.notna(row['country_code']):
            ax.annotate(row['country_code'], (row['Pop'], row['medal_count']), fontsize=8)
    ax.set_title('Population vs Medal Count')
    ax.set_xlabel('Population')
    ax.set_ylabel('Total Medals')
    plt.tight_layout()
    plt.savefig(r"DATA3463-MiniProject2\out\pop_vs_medals.png")
    plt.show()

    # Medal count by country (top 15)
    top_countries = medal_counts.nlargest(15, 'medal_count')
    fig, ax = plt.subplots(figsize=(12, 6))
    sns.barplot(data=top_countries, x='country', y='medal_count', ax=ax)
    ax.set_title('Top 15 Countries by Medal Count')
    ax.set_xlabel('')
    ax.set_ylabel('Total Medals')
    ax.tick_params(axis='x', rotation=45)
    plt.tight_layout()
    plt.savefig(r"DATA3463-MiniProject2\out\top_countries.png")
    plt.show()

    print("Done. Charts saved to out folder.")

if __name__ == '__main__':
    analyze()