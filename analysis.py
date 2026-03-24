import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import seaborn as sns
from pathlib import Path

# Configuration
_HERE = Path(__file__).parent
DB_PATH = _HERE / "olympics.db"
FIG_DIR = _HERE / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

# Olympic medal palette
GOLD = "#D4AF37"
SILVER = "#A8A9AD"
BRONZE = "#CD7F32"
MUTED = "#BFC5CE"
DARK = "#2C3E50"
BG = "#FFFFFF"
GRID_CLR = "#E0E4E8"

TOP_N = 8

# Utility / Theme
def apply_theme():
    sns.set_theme(style="white", context="notebook", font_scale=1.05)
    plt.rcParams.update({
        "figure.facecolor": BG,
        "axes.facecolor": BG,
        "axes.edgecolor": GRID_CLR,
        "axes.labelcolor": DARK,
        "axes.grid": False,
        "axes.titlelocation": "left",
        "xtick.color": DARK,
        "ytick.color": DARK,
        "text.color": DARK,
        "font.family": "sans-serif",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "legend.frameon": False,
        "legend.fontsize": 9,
        "figure.dpi": 150,
        "savefig.dpi": 200,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.3,
    })

def save(fig, name):
    fig.savefig(FIG_DIR / f"{name}.png")
    plt.close(fig)
    print(f"Saved {name}.png")

# Data Loading
def load_data():
    conn = sqlite3.connect(DB_PATH)
    athletes = pd.read_sql("SELECT * FROM athletes", conn)
    results = pd.read_sql("SELECT * FROM results", conn)
    countries = pd.read_sql("SELECT * FROM countries", conn)
    conn.close()

    df = (
        results
        .merge(athletes, on="athlete_url", how="left")
        .merge(countries, left_on="country", right_on="country_code", how="left")
    )
    df["height"] = pd.to_numeric(df["height"], errors="coerce")
    df["weight"] = pd.to_numeric(df["weight"], errors="coerce")
    df["dob"] = pd.to_datetime(df["dob"], errors="coerce")
    df["age"] = df["year"] - df["dob"].dt.year

    return df, countries


# Figure 1: GDP per Capita vs Total Medals
def fig_gdp_percap_timeseries(df, countries):
    medal_by_cy = df.groupby(["year", "country"]).size().reset_index(name="medals")
    top = medal_by_cy.groupby("country")["medals"].sum().nlargest(TOP_N).index

    gdps = [countries[countries["country_code"] == c]["gdpPerCapita"].values[0] for c in top]
    totals = [medal_by_cy[medal_by_cy["country"] == c]["medals"].sum() for c in top]
    top_names = [countries[countries["country_code"] == c]["Country"].values[0] for c in top]

    fig, ax = plt.subplots(figsize=(10, 6))
    x = np.arange(len(top))
    width = 0.35

    ax2 = ax.twinx()
    ax.bar(x - width / 2, gdps, width, color=GOLD, alpha=0.7, label="GDP per Capita ($)", edgecolor="white")
    ax2.bar(x + width / 2, totals, width, color=SILVER, alpha=0.7, label="Total Medals", edgecolor="white")
    ax.set_xticks(x)
    ax.set_xticklabels(top_names, fontsize=9, fontweight="bold", rotation=25, ha="right")
    ax.set_ylabel("GDP per Capita ($)", color=GOLD)
    ax2.set_ylabel("Total Medals", color=SILVER)
    ax.set_title("GDP per Capita vs Total Medals (Top 8 Countries)",
                 fontsize=14, fontweight="bold", pad=12)
    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, loc="upper center",
              bbox_to_anchor=(0.5, -0.18), ncol=2, fontsize=9)
    fig.subplots_adjust(bottom=0.22)
    ax.spines["top"].set_visible(False)
    ax2.spines["top"].set_visible(False)
    save(fig, "01_gdp_percap_vs_medals")


# Figure 2: Stacked Area – Top 10 Countries Medal Share Over Time
def fig_stacked_area(df):
    CANADA_RED = "#FF1A1A"
    TOP_N2 = 10

    code_to_name = dict(zip(df["country"], df["Country"]))
    by_cy = df.groupby(["year", "country"]).size().reset_index(name="medals")
    top = by_cy.groupby("country")["medals"].sum().nlargest(TOP_N2).index
    pivot = by_cy.pivot_table(index="year", columns="country", values="medals", fill_value=0)
    plot_df = pivot[top].copy()
    plot_df = plot_df.rename(columns=code_to_name)

    top_list = list(top)
    palette = sns.color_palette("YlOrBr_r", n_colors=TOP_N2)
    colors = list(palette)
    if "CAN" in top_list:
        colors[top_list.index("CAN")] = CANADA_RED

    fig, ax = plt.subplots(figsize=(11, 6))
    ax.stackplot(plot_df.index, *[plot_df[c] for c in plot_df.columns],
                 labels=plot_df.columns, colors=colors, alpha=0.85, edgecolor="white", linewidth=0.5)
    ax.set_xlabel("Olympic Year")
    ax.set_ylabel("Total Medals Awarded")
    ax.set_title("Top 10 Countries – Medal Distribution Over Time", fontsize=14, fontweight="bold", pad=12)
    ax.set_xticks([2010, 2014, 2018, 2022, 2026])
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles[::-1], labels[::-1], loc="upper center",
              bbox_to_anchor=(0.5, -0.13), ncol=5, fontsize=8)
    fig.subplots_adjust(bottom=0.22)
    save(fig, "02_stacked_area_medals")


# Figure 3: Body Profiles – Dot Plot (Height + Weight + Age)
def fig_height_weight_profile(df):
    sub = df.dropna(subset=["height", "weight", "age"]).copy()
    valid = sub.groupby("sport")["height"].count()
    valid = valid[valid >= 15].index
    sub = sub[sub["sport"].isin(valid)]

    stats = sub.groupby("sport").agg(
        h_mean=("height", "mean"),
        w_mean=("weight", "mean"),
        a_mean=("age", "mean"),
    ).reset_index()
    order = stats.sort_values("h_mean")["sport"].values
    y_pos = np.arange(len(order))

    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(14, 6), sharey=True,
                                         gridspec_kw={"wspace": 0.15})

    # Height dots
    h_vals = stats.set_index("sport").loc[order, "h_mean"]
    ax1.scatter(h_vals, y_pos, s=80, c=GOLD, edgecolors=DARK, linewidth=0.5, zorder=3)
    for i, val in enumerate(h_vals):
        ax1.plot([155, val], [i, i], color=MUTED, linewidth=0.8, zorder=1)
    ax1.set_xlim(155, 185)
    ax1.set_yticks(y_pos)
    ax1.set_yticklabels(order, fontsize=11)
    ax1.set_xlabel("Mean Height (cm)")
    ax1.set_title("Height", fontsize=11, fontweight="bold")

    # Weight dots
    w_vals = stats.set_index("sport").loc[order, "w_mean"]
    ax2.scatter(w_vals, y_pos, s=80, c=SILVER, edgecolors=DARK, linewidth=0.5, zorder=3)
    for i, val in enumerate(w_vals):
        ax2.plot([50, val], [i, i], color=MUTED, linewidth=0.8, zorder=1)
    ax2.set_xlim(50, 90)
    ax2.set_xlabel("Mean Weight (kg)")
    ax2.set_title("Weight", fontsize=11, fontweight="bold")

    # Age dots
    a_vals = stats.set_index("sport").loc[order, "a_mean"]
    ax3.scatter(a_vals, y_pos, s=80, c=BRONZE, edgecolors=DARK, linewidth=0.5, zorder=3)
    for i, val in enumerate(a_vals):
        ax3.plot([20, val], [i, i], color=MUTED, linewidth=0.8, zorder=1)
    ax3.set_xlim(20, 35)
    ax3.set_xlabel("Mean Age (years)")
    ax3.set_title("Age", fontsize=11, fontweight="bold")

    fig.suptitle("Medalist Body Profiles by Sport",
                 fontsize=14, fontweight="bold", x=0.0, ha="left", y=1.01)
    fig.tight_layout()
    save(fig, "03_height_weight_profile")


# Figure 4: Sport Medal Count
def fig_sport_count(df):
    counts = df.groupby("sport").size().reset_index(name="medals")
    counts = counts.sort_values("medals", ascending=True)

    def get_color(sport):
        sport_lower = sport.lower()
        if any(x in sport_lower for x in ["ski", "biath", "nord"]):
            return GOLD
        elif "skat" in sport_lower:
            return SILVER
        else:
            return BRONZE

    colors = counts["sport"].apply(get_color)

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.barh(counts["sport"], counts["medals"],
            color=colors, edgecolor="white", height=0.6)

    ax.set_xlabel("Total Medals")
    ax.set_title("What Sports Give the Most Medals?",
                 fontsize=14, fontweight="bold", pad=12)

    legend_elements = [
        Patch(facecolor=GOLD, label="Skiing / Biathlon / Nordic"),
        Patch(facecolor=SILVER, label="Skating"),
        Patch(facecolor=BRONZE, label="Other")
    ]

    ax.legend(handles=legend_elements, loc="lower right")

    save(fig, "04_sport_count")


# Main
def main():
    apply_theme()
    df, countries = load_data()
    print(f"Loaded {len(df)} medal records, {df['country'].nunique()} countries, "
          f"{df['year'].nunique()} Games\n")

    fig_gdp_percap_timeseries(df, countries)
    fig_stacked_area(df)
    fig_height_weight_profile(df)
    fig_sport_count(df)

    print(f"\nDone - {len(list(FIG_DIR.glob('*.png')))} figures saved to {FIG_DIR}")

if __name__ == "__main__":
    main()
