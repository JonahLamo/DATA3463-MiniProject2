import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.lines import Line2D
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Patch
import seaborn as sns
from pathlib import Path

# Configuration
DB_PATH = r"DATA3463\DATA3463-MiniProject2\olympics.db"
FIG_DIR = Path(r"DATA3463\DATA3463-MiniProject2\figures")
FIG_DIR.mkdir(exist_ok=True)

# Olympic medal palette
GOLD = "#D4AF37"
SILVER = "#A8A9AD"
BRONZE = "#CD7F32"
MUTED = "#BFC5CE"
DARK = "#2C3E50"
ACCENT = "#1A5276"
BG = "#FAFBFC"
GRID_CLR = "#E0E4E8"

MEDAL_PALETTE = {"Gold": GOLD, "Silver": SILVER, "Bronze": BRONZE}
MEDAL_ORDER = ["Gold", "Silver", "Bronze"]

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


# Figure 1
def fig_top_countries(df):
    medal_cts = (
        df.groupby(["Country", "medal"]).size()
        .unstack(fill_value=0).reindex(columns=MEDAL_ORDER, fill_value=0)
    )
    medal_cts["total"] = medal_cts.sum(axis=1)
    top = medal_cts.nlargest(15, "total").sort_values("total").drop(columns="total")

    fig, ax = plt.subplots(figsize=(8, 6.5))
    left = np.zeros(len(top))
    for medal in MEDAL_ORDER:
        ax.barh(top.index, top[medal], left=left, color=MEDAL_PALETTE[medal],
                label=medal, edgecolor="white", linewidth=0.4, height=0.65)
        left += top[medal].values

    ax.set_xlabel("Total Medals (2010 - 2026)")
    ax.set_title("Top 15 Countries by Medal Count", fontsize=14, fontweight="bold", pad=12)
    ax.legend(loc="lower right")
    ax.xaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    save(fig, "01_top_countries_medals")


# Figure 2
def fig_gdp_vs_medals(df, countries):
    medal_cts = df.groupby("country").size().reset_index(name="medals")
    cm = medal_cts.merge(countries, left_on="country", right_on="country_code", how="left")
    cm = cm.dropna(subset=["GDP", "medals"])
    cm["log_gdp"] = np.log10(cm["GDP"])

    fig, ax = plt.subplots(figsize=(9, 6.5))
    ax.scatter(cm["log_gdp"], cm["medals"], s=cm["gdpPerCapita"] / 600,
               c=GOLD, edgecolors=DARK, linewidth=0.5, alpha=0.75, zorder=3)

    top5 = cm.nlargest(5, "medals")["country"].values
    for _, row in cm.iterrows():
        if row["country"] in top5:
            ax.annotate(row["Country"], (row["log_gdp"], row["medals"]),
                        fontsize=7.5, fontweight="bold", xytext=(5, 4),
                        textcoords="offset points", color=DARK)

    z = np.polyfit(cm["log_gdp"], cm["medals"], 1)
    xs = np.linspace(cm["log_gdp"].min() - 0.1, cm["log_gdp"].max() + 0.1, 100)
    ax.plot(xs, np.polyval(z, xs), color=BRONZE, linewidth=1.5, ls="--", alpha=0.7, zorder=2)

    r = cm["log_gdp"].corr(cm["medals"])
    ax.text(0.03, 0.95, f"r = {r:.2f}", transform=ax.transAxes,
            fontsize=10, va="top", color=DARK, fontstyle="italic")

    ax.set_xlabel(r"$\log_{10}(\text{GDP in USD})$")
    ax.set_ylabel("Total Medals (2010 - 2026)")
    ax.set_title("National GDP vs Olympic Medal Count", fontsize=14, fontweight="bold", pad=12)

    for val, label in [(30000, "30k"), (60000, "60k"), (90000, "90k")]:
        ax.scatter([], [], s=val / 600, c=GOLD, edgecolors=DARK, linewidth=0.5, label=f"GDP/cap ${label}")
    ax.legend(loc="lower right", fontsize=8, title="Bubble = GDP per capita", title_fontsize=8)
    save(fig, "02_gdp_vs_medals")


# Figure 3
def fig_medals_per_capita(df, countries):
    medal_cts = df.groupby("country").size().reset_index(name="medals")
    cm = medal_cts.merge(countries, left_on="country", right_on="country_code", how="left")
    cm = cm.dropna(subset=["Pop"])
    cm["medals_per_M"] = cm["medals"] / (cm["Pop"] / 1e6)
    cm = cm[cm["medals"] >= 3]
    top = cm.nlargest(12, "medals_per_M").sort_values("medals_per_M")

    fig, ax = plt.subplots(figsize=(8, 5.5))
    bars = ax.barh(top["Country"], top["medals_per_M"], color=GOLD, edgecolor="white", height=0.6)
    for bar, (_, row) in zip(bars, top.iterrows()):
        ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height() / 2,
                f"{int(row['medals'])} medals", va="center", fontsize=8, color=MUTED)

    ax.set_xlabel("Medals per Million Population")
    ax.set_title("Medal Efficiency: Medals per Capita", fontsize=14, fontweight="bold", pad=12)
    ax.invert_yaxis()
    save(fig, "03_medals_per_capita")


# Figure 4
def fig_medal_timeseries(df):
    code_to_name = dict(zip(df["country"], df["Country"]))
    by_cy = df.groupby(["year", "country", "medal"]).size().reset_index(name="n")
    totals = by_cy.groupby(["year", "country"])["n"].sum().reset_index(name="total")
    golds = by_cy[by_cy["medal"] == "Gold"].rename(columns={"n": "gold"}).drop(columns="medal")
    merged = totals.merge(golds, on=["year", "country"], how="left").fillna(0)
    top_countries = merged.groupby("country")["total"].sum().nlargest(TOP_N).index

    fig, axes = plt.subplots(2, 4, figsize=(14, 6), sharex=True, sharey=True)
    for i, c in enumerate(top_countries):
        ax = axes.flatten()[i]
        sub = merged[merged["country"] == c].sort_values("year")
        ax.fill_between(sub["year"], sub["total"], color=MUTED, alpha=0.35)
        ax.plot(sub["year"], sub["total"], color=DARK, linewidth=1.8, marker="o", markersize=5, zorder=3)
        ax.plot(sub["year"], sub["gold"], color=GOLD, linewidth=1.4, marker="D", markersize=4, zorder=4)
        ax.fill_between(sub["year"], sub["gold"], color=GOLD, alpha=0.18)
        ax.set_title(code_to_name.get(c, c), fontsize=10, fontweight="bold")
        ax.set_xticks([2010, 2014, 2018, 2022, 2026])
        ax.set_xticklabels(["'10", "'14", "'18", "'22", "'26"], fontsize=8)
        if i % 4 == 0:
            ax.set_ylabel("Medals")

    handles = [
        Line2D([0], [0], color=DARK, lw=1.8, marker="o", markersize=5, label="Total medals"),
        Line2D([0], [0], color=GOLD, lw=1.4, marker="D", markersize=4, label="Gold medals"),
    ]
    fig.legend(handles=handles, loc="lower center", ncol=2, fontsize=9, bbox_to_anchor=(0.5, -0.02))
    fig.suptitle("Medal Trajectories by Country (2010 - 2026)",
                 fontsize=14, fontweight="bold", x=0.0, ha="left", y=1.01)
    fig.tight_layout()
    save(fig, "04_medal_timeseries")


# Figure 5
def fig_gdp_percap_timeseries(df, countries):
    medal_by_cy = df.groupby(["year", "country"]).size().reset_index(name="medals")
    top = medal_by_cy.groupby("country")["medals"].sum().nlargest(TOP_N).index
    sub = medal_by_cy[medal_by_cy["country"].isin(top)]
    sub = sub.merge(countries[["country_code", "gdpPerCapita"]], left_on="country", right_on="country_code")

    fig, ax = plt.subplots(figsize=(10, 6))
    x = np.arange(len(top))
    width = 0.35
    gdps = [countries[countries["country_code"] == c]["gdpPerCapita"].values[0] for c in top]
    totals = [medal_by_cy[medal_by_cy["country"] == c]["medals"].sum() for c in top]
    top_names = [countries[countries["country_code"] == c]["Country"].values[0] for c in top]

    ax2 = ax.twinx()
    ax.bar(x - width / 2, gdps, width, color=GOLD, alpha=0.7, label="GDP per Capita ($)", edgecolor="white")
    ax2.bar(x + width / 2, totals, width, color=ACCENT, alpha=0.7, label="Total Medals", edgecolor="white")
    ax.set_xticks(x)
    ax.set_xticklabels(top_names, fontsize=9, fontweight="bold", rotation=25, ha="right")
    ax.set_ylabel("GDP per Capita ($)", color=GOLD)
    ax2.set_ylabel("Total Medals", color=ACCENT)
    ax.set_title("GDP per Capita vs Medal Count (Top 8 Countries)",
                 fontsize=14, fontweight="bold", pad=12)
    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, loc="upper right", fontsize=9)
    ax.spines["top"].set_visible(False)
    ax2.spines["top"].set_visible(False)
    save(fig, "05_gdp_percap_vs_medals")


# Figure 6
def fig_height_by_sport(df):
    sub = df.dropna(subset=["height"]).copy()
    valid = sub.groupby("sport")["height"].count()
    valid = valid[valid >= 10].index
    sub = sub[sub["sport"].isin(valid)]
    order = sub.groupby("sport")["height"].median().sort_values(ascending=False).index

    fig, ax = plt.subplots(figsize=(12, 6))
    sns.boxplot(data=sub, x="sport", y="height", order=order,
                boxprops=dict(facecolor=SILVER, alpha=0.5),
                medianprops=dict(color=GOLD, linewidth=2),
                whiskerprops=dict(color=DARK, linewidth=0.8),
                capprops=dict(color=DARK, linewidth=0.8),
                flierprops=dict(marker=".", color=MUTED, markersize=4),
                ax=ax, linewidth=0.7)
    sns.stripplot(data=sub, x="sport", y="height", order=order,
                  color=BRONZE, alpha=0.25, size=3, jitter=0.25, ax=ax, zorder=1)
    ax.set_ylabel("Height (cm)")
    ax.set_xlabel("")
    ax.set_title("Medalist Height Distribution by Sport", fontsize=14, fontweight="bold", pad=12)
    ax.tick_params(axis="x", rotation=40)
    fig.tight_layout()
    save(fig, "06_height_by_sport")


# Figure 7
def fig_gold_ratio_heatmap(df):
    medal_cts = (
        df.groupby(["Country", "medal"]).size()
        .unstack(fill_value=0).reindex(columns=MEDAL_ORDER, fill_value=0)
    )
    medal_cts["total"] = medal_cts.sum(axis=1)
    top = medal_cts[medal_cts["total"] >= 10].nlargest(15, "total")
    props = top[MEDAL_ORDER].div(top["total"], axis=0).sort_values("Gold", ascending=True)

    fig, axes = plt.subplots(1, 3, figsize=(7, 7), sharey=True, gridspec_kw={"wspace": 0.05})
    medal_colors = {"Gold": GOLD, "Silver": SILVER, "Bronze": BRONZE}
    for ax, medal in zip(axes, MEDAL_ORDER):
        cmap = sns.light_palette(medal_colors[medal], as_cmap=True)
        sns.heatmap(props[[medal]], annot=True, fmt=".0%", cmap=cmap,
                    linewidths=0.8, linecolor="white", cbar=False,
                    ax=ax, vmin=0.10, vmax=0.55,
                    annot_kws={"fontsize": 11, "fontweight": "bold"})
        ax.set_xlabel("")
        ax.set_ylabel("")
        ax.tick_params(axis="y", rotation=0)
        ax.xaxis.set_ticks_position("top")

    fig.suptitle("Medal Composition by Country",
                 fontsize=14, fontweight="bold", x=0.0, ha="left", y=0.98)
    save(fig, "07_gold_ratio_heatmap")


# Figure 8
def fig_population_vs_medals(df, countries):
    medal_cts = df.groupby("country").size().reset_index(name="medals")
    cm = medal_cts.merge(countries, left_on="country", right_on="country_code", how="left")
    cm = cm.dropna(subset=["Pop"])
    cm["log_pop"] = np.log10(cm["Pop"])

    fig, ax = plt.subplots(figsize=(9, 6.5))
    ax.scatter(cm["log_pop"], cm["medals"], s=70, c=BRONZE, edgecolors=DARK,
               linewidth=0.5, alpha=0.8, zorder=3)

    top5 = cm.nlargest(5, "medals")["country"].values
    for _, row in cm.iterrows():
        if row["country"] in top5:
            ax.annotate(row["Country"], (row["log_pop"], row["medals"]),
                        fontsize=7.5, fontweight="bold", color=DARK,
                        xytext=(5, 4), textcoords="offset points")

    z = np.polyfit(cm["log_pop"], cm["medals"], 1)
    xs = np.linspace(cm["log_pop"].min() - 0.1, cm["log_pop"].max() + 0.1, 100)
    ax.plot(xs, np.polyval(z, xs), color=GOLD, linewidth=1.5, ls="--", alpha=0.7, zorder=2)

    r = cm["log_pop"].corr(cm["medals"])
    ax.text(0.03, 0.95, f"r = {r:.2f}  (log pop vs medals)", transform=ax.transAxes,
            fontsize=10, va="top", color=DARK, fontstyle="italic")
    ax.set_xlabel(r"$\log_{10}(\text{Population})$")
    ax.set_ylabel("Total Medals (2010 - 2026)")
    ax.set_title("Population vs Medal Count", fontsize=14, fontweight="bold", pad=12)
    save(fig, "08_population_vs_medals")


# Figure 9
def fig_stacked_area(df):
    code_to_name = dict(zip(df["country"], df["Country"]))
    by_cy = df.groupby(["year", "country"]).size().reset_index(name="medals")
    top = by_cy.groupby("country")["medals"].sum().nlargest(TOP_N).index
    pivot = by_cy.pivot_table(index="year", columns="country", values="medals", fill_value=0)
    other = pivot[[c for c in pivot.columns if c not in top]].sum(axis=1)
    plot_df = pivot[top].copy()
    plot_df["Other"] = other
    plot_df = plot_df.rename(columns=code_to_name)

    palette = sns.color_palette("YlOrBr_r", n_colors=TOP_N)
    colors = list(palette) + [MUTED]

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.stackplot(plot_df.index, *[plot_df[c] for c in plot_df.columns],
                 labels=plot_df.columns, colors=colors, alpha=0.85, edgecolor="white", linewidth=0.5)
    ax.set_xlabel("Olympic Year")
    ax.set_ylabel("Total Medals Awarded")
    ax.set_title("Medal Distribution Over Time", fontsize=14, fontweight="bold", pad=12)
    ax.set_xticks([2010, 2014, 2018, 2022, 2026])
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles[::-1], labels[::-1], loc="upper left", fontsize=8, ncol=1)
    save(fig, "09_stacked_area_medals")


# Figure 10
def fig_correlation_dashboard(df, countries):
    medal_cts = df.groupby("country").size().reset_index(name="medals")
    cm = medal_cts.merge(countries, left_on="country", right_on="country_code", how="left").dropna()
    cm["log_gdp"] = np.log10(cm["GDP"])
    cm["log_pop"] = np.log10(cm["Pop"])
    cm["medals_per_M"] = cm["medals"] / (cm["Pop"] / 1e6)

    panels = [
        ("log_gdp",       "medals",       r"$\log_{10}(\text{GDP})$",        "Medals",              GOLD),
        ("gdpPerCapita",  "medals",       "GDP per Capita ($)",              "Medals",              SILVER),
        ("log_pop",       "medals",       r"$\log_{10}(\text{Population})$", "Medals",              BRONZE),
        ("gdpPerCapita",  "medals_per_M", "GDP per Capita ($)",              "Medals / Million Pop", ACCENT),
    ]

    fig, axes = plt.subplots(2, 2, figsize=(11, 9))
    for ax, (xvar, yvar, xlabel, ylabel, color) in zip(axes.flatten(), panels):
        ax.scatter(cm[xvar], cm[yvar], s=50, c=color, edgecolors=DARK, linewidth=0.4, alpha=0.75)
        z = np.polyfit(cm[xvar], cm[yvar], 1)
        xs = np.linspace(cm[xvar].min(), cm[xvar].max(), 100)
        ax.plot(xs, np.polyval(z, xs), color=color, linewidth=1.5, ls="--", alpha=0.6)
        r = cm[xvar].corr(cm[yvar])
        ax.set_xlabel(xlabel, fontsize=9)
        ax.set_ylabel(ylabel, fontsize=9)
        ax.set_title(f"r = {r:.2f}", fontsize=11, fontweight="bold")

    fig.suptitle("Correlation Summary: What Predicts Medal Success?",
                 fontsize=14, fontweight="bold", x=0.0, ha="left", y=1.01)
    fig.tight_layout()
    save(fig, "10_correlation_dashboard")


# Figure 11
def fig_r2_heatmap(df, countries):
    MIN_COUNTRIES = 8
    factors = {
        r"$\log_{10}(\text{GDP})$": ("log_gdp", "medals"),
        r"$\log_{10}(\text{Pop})$": ("log_pop", "medals"),
        "GDP per Capita": ("gdpPerCapita", "medals"),
        "GDP per Capita vs Medals per Million": ("gdpPerCapita", "medals_per_M"),
    }

    records = []
    for sport in sorted(df["sport"].unique()):
        sub = df[df["sport"] == sport]
        by_c = (sub.groupby(["country"]).size().reset_index(name="medals")
                .merge(countries, left_on="country", right_on="country_code", how="inner")
                .dropna(subset=["GDP", "Pop", "gdpPerCapita"]))
        if len(by_c) < MIN_COUNTRIES:
            continue
        by_c["log_gdp"] = np.log10(by_c["GDP"])
        by_c["log_pop"] = np.log10(by_c["Pop"])
        by_c["medals_per_M"] = by_c["medals"] / (by_c["Pop"] / 1e6)
        row = {"sport": sport, "n_countries": len(by_c)}
        for label, (xcol, ycol) in factors.items():
            r = by_c[xcol].corr(by_c[ycol])
            row[label] = r ** 2
        records.append(row)

    r2_df = pd.DataFrame(records).set_index("sport")
    n_countries = r2_df.pop("n_countries")
    factor_cols = list(factors.keys())
    r2_df["avg"] = r2_df[factor_cols].mean(axis=1)
    r2_df = r2_df.sort_values("avg", ascending=True).drop(columns="avg")
    cmap = LinearSegmentedColormap.from_list("medal", ["#FFFFFF", GOLD], N=256)

    fig, ax = plt.subplots(figsize=(9, 7))
    sns.heatmap(r2_df[factor_cols], annot=True, fmt=".2f", cmap=cmap,
                linewidths=1, linecolor="white", vmin=0, vmax=0.85,
                cbar_kws={"label": "R\u00B2", "shrink": 0.65}, ax=ax,
                annot_kws={"fontsize": 11, "fontweight": "bold"})
    ylabels = [f"{s}  (n={int(n_countries[s])})" for s in r2_df.index]
    ax.set_yticklabels(ylabels, rotation=0, fontsize=10)
    ax.set_xticklabels(ax.get_xticklabels(), fontsize=10)
    ax.set_title("What Predicts Medal Success? R\u00B2 by Sport",
                 fontsize=14, fontweight="bold", pad=14)
    ax.set_ylabel("")
    ax.set_xlabel("")
    fig.text(0.5, -0.01,
             "Each cell shows R\u00B2 between a country-level factor and medal count in that sport.",
             ha="center", fontsize=8, color=MUTED, style="italic")
    fig.tight_layout()
    save(fig, "11_r2_heatmap_by_sport")
    return r2_df, n_countries, factor_cols


# Figure 12
def fig_r2_bars(r2_df, factor_cols):
    bar_df = r2_df[factor_cols].sort_values(factor_cols[0], ascending=False)
    x = np.arange(len(bar_df))
    width = 0.2
    colors = [GOLD, SILVER, BRONZE, ACCENT]

    fig, ax = plt.subplots(figsize=(10, 6))
    for i, (col, clr) in enumerate(zip(factor_cols, colors)):
        offset = (i - 1.5) * width
        ax.bar(x + offset, bar_df[col], width, label=col, color=clr,
               edgecolor="white", linewidth=0.5, alpha=0.85)
    ax.set_xticks(x)
    ax.set_xticklabels(bar_df.index, rotation=40, ha="right", fontsize=9)
    ax.set_ylabel("R\u00B2")
    ax.set_title("Factor Explanatory Power by Sport", fontsize=14, fontweight="bold", pad=12)
    ax.legend(fontsize=8, loc="upper right", ncol=2)
    ax.set_ylim(0, 0.9)
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.1f"))
    for y in [0.1, 0.2, 0.3]:
        ax.axhline(y, color=GRID_CLR, linewidth=0.6, zorder=0)
    fig.tight_layout()
    save(fig, "12_r2_bars_by_sport")


# Figure 13: Weight Distribution by Sport
def fig_weight_by_sport(df):
    sub = df.dropna(subset=["weight"]).copy()
    valid = sub.groupby("sport")["weight"].count()
    valid = valid[valid >= 10].index
    sub = sub[sub["sport"].isin(valid)]
    order = sub.groupby("sport")["weight"].median().sort_values(ascending=False).index

    fig, ax = plt.subplots(figsize=(12, 6))
    sns.boxplot(data=sub, x="sport", y="weight", order=order,
                boxprops=dict(facecolor=SILVER, alpha=0.5),
                medianprops=dict(color=GOLD, linewidth=2),
                whiskerprops=dict(color=DARK, linewidth=0.8),
                capprops=dict(color=DARK, linewidth=0.8),
                flierprops=dict(marker=".", color=MUTED, markersize=4),
                ax=ax, linewidth=0.7)
    sns.stripplot(data=sub, x="sport", y="weight", order=order,
                  color=BRONZE, alpha=0.25, size=3, jitter=0.25, ax=ax, zorder=1)
    ax.set_ylabel("Weight (kg)")
    ax.set_xlabel("")
    ax.set_title("Medalist Weight Distribution by Sport", fontsize=14, fontweight="bold", pad=12)
    ax.tick_params(axis="x", rotation=40)
    fig.tight_layout()
    save(fig, "13_weight_by_sport")


# Figure 14: Age Distribution by Sport
def fig_age_by_sport(df):
    sub = df.dropna(subset=["age"]).copy()
    valid = sub.groupby("sport")["age"].count()
    valid = valid[valid >= 10].index
    sub = sub[sub["sport"].isin(valid)]
    order = sub.groupby("sport")["age"].median().sort_values(ascending=False).index

    fig, ax = plt.subplots(figsize=(12, 6))
    sns.boxplot(data=sub, x="sport", y="age", order=order,
                boxprops=dict(facecolor=SILVER, alpha=0.5),
                medianprops=dict(color=GOLD, linewidth=2),
                whiskerprops=dict(color=DARK, linewidth=0.8),
                capprops=dict(color=DARK, linewidth=0.8),
                flierprops=dict(marker=".", color=MUTED, markersize=4),
                ax=ax, linewidth=0.7)
    sns.stripplot(data=sub, x="sport", y="age", order=order,
                  color=BRONZE, alpha=0.25, size=3, jitter=0.25, ax=ax, zorder=1)
    ax.set_ylabel("Age at Time of Medal")
    ax.set_xlabel("")
    ax.set_title("Medalist Age Distribution by Sport", fontsize=14, fontweight="bold", pad=12)
    ax.tick_params(axis="x", rotation=40)
    fig.tight_layout()
    save(fig, "14_age_by_sport")


# Figure 15: Body Profiles – Dot Plot (Height + Weight side by side)
def fig_height_weight_profile(df):
    """Paired dot plot showing mean height and mean weight per sport,
    sorted by height. Clean and readable with no overlap."""
    sub = df.dropna(subset=["height", "weight"]).copy()
    valid = sub.groupby("sport")["height"].count()
    valid = valid[valid >= 15].index
    sub = sub[sub["sport"].isin(valid)]

    stats = sub.groupby("sport").agg(
        h_mean=("height", "mean"), w_mean=("weight", "mean")
    ).reset_index()
    order = stats.sort_values("h_mean")["sport"].values
    y_pos = np.arange(len(order))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 6), sharey=True,
                                     gridspec_kw={"wspace": 0.15})

    # Height dots
    h_vals = stats.set_index("sport").loc[order, "h_mean"]
    ax1.scatter(h_vals, y_pos, s=80, c=GOLD, edgecolors=DARK, linewidth=0.5, zorder=3)
    for i, (sport, val) in enumerate(zip(order, h_vals)):
        ax1.plot([ax1.get_xlim()[0] if i > 0 else 155, val], [i, i],
                 color=MUTED, linewidth=0.8, zorder=1)
    ax1.set_xlim(155, 185)
    # Re-draw connector lines with correct xlim
    ax1.cla()
    ax1.scatter(h_vals, y_pos, s=80, c=GOLD, edgecolors=DARK, linewidth=0.5, zorder=3)
    for i, val in enumerate(h_vals):
        ax1.plot([155, val], [i, i], color=MUTED, linewidth=0.8, zorder=1)
    ax1.set_xlim(155, 185)
    ax1.set_yticks(y_pos)
    ax1.set_yticklabels(order, fontsize=9)
    ax1.set_xlabel("Mean Height (cm)")
    ax1.set_title("Height", fontsize=11, fontweight="bold")

    # Weight dots
    w_vals = stats.set_index("sport").loc[order, "w_mean"]
    ax2.scatter(w_vals, y_pos, s=80, c=BRONZE, edgecolors=DARK, linewidth=0.5, zorder=3)
    for i, val in enumerate(w_vals):
        ax2.plot([50, val], [i, i], color=MUTED, linewidth=0.8, zorder=1)
    ax2.set_xlim(50, 90)
    ax2.set_xlabel("Mean Weight (kg)")
    ax2.set_title("Weight", fontsize=11, fontweight="bold")

    fig.suptitle("Medalist Body Profiles by Sport",
                 fontsize=14, fontweight="bold", x=0.0, ha="left", y=1.01)
    fig.tight_layout()
    save(fig, "15_height_weight_profile")


# Figure 16: Top Medal-Producing Cities by Sport
def fig_top_cities(df):
    sub = df.dropna(subset=["city"]).copy()
    sub["city_short"] = sub["city"].str.split(",").str[0].str.strip()
    city_sport = (sub.groupby(["sport", "city_short"])
                  .size().reset_index(name="medals")
                  .sort_values("medals", ascending=False))
    top = city_sport.head(15).sort_values("medals")
    top["label"] = top["city_short"] + "  (" + top["sport"] + ")"

    sports = top["sport"].unique()
    palette = dict(zip(sports, sns.color_palette("YlOrBr", n_colors=len(sports))))

    fig, ax = plt.subplots(figsize=(9, 6.5))
    bars = ax.barh(top["label"], top["medals"], height=0.6, edgecolor="white")
    for bar, (_, row) in zip(bars, top.iterrows()):
        bar.set_color(palette[row["sport"]])
    ax.set_xlabel("Number of Medals Won by Athletes from This City")
    ax.set_title("Top Medal-Producing Cities by Sport", fontsize=14, fontweight="bold", pad=12)
    ax.invert_yaxis()
    fig.tight_layout()
    save(fig, "16_top_cities_by_sport")


# Figure 17: Overall Physique Trends
def fig_physique_trends(df):
    sub = df.dropna(subset=["height", "weight", "age"]).copy()
    valid = sub.groupby("sport")["height"].count()
    valid = valid[valid >= 30].index
    sub = sub[sub["sport"].isin(valid)]

    metrics = [("height", "Mean Height (cm)", GOLD),
               ("weight", "Mean Weight (kg)", SILVER),
               ("age",    "Mean Age at Medal", BRONZE)]

    fig, axes = plt.subplots(1, 3, figsize=(16, 5.5), sharey=False)
    for ax, (col, ylabel, color) in zip(axes, metrics):
        trend = sub.groupby(["year", "sport"])[col].mean().reset_index()
        for sport in sorted(trend["sport"].unique()):
            s = trend[trend["sport"] == sport].sort_values("year")
            ax.plot(s["year"], s[col], color=MUTED, linewidth=0.8, alpha=0.5)
        overall = sub.groupby("year")[col].mean()
        ax.plot(overall.index, overall.values, color=color, linewidth=2.5,
                marker="o", markersize=6, zorder=5, label="All sports")
        ax.set_ylabel(ylabel)
        ax.set_xticks([2010, 2014, 2018, 2022, 2026])
        ax.set_xticklabels(["2010", "2014", "2018", "2022", "2026"])
        ax.set_title(ylabel, fontsize=11, fontweight="bold")
        ax.legend(fontsize=8, loc="best")

    fig.suptitle("How Medalist Physiques Have Changed Over Time",
                 fontsize=14, fontweight="bold", x=0.0, ha="left", y=1.02)
    fig.tight_layout()
    save(fig, "17_physique_trends")


# Figure 18: Per-Sport Physique Trends (small multiples)
def fig_physique_trends_by_sport(df):
    """Small-multiple grid: one row per sport, three columns (height,
    weight, age), with y-axes zoomed to show actual variation."""
    sub = df.dropna(subset=["height", "weight", "age"]).copy()
    valid = sub.groupby("sport")["height"].count()
    valid = valid[valid >= 30].index
    sub = sub[sub["sport"].isin(valid)]
    sports = sorted(sub["sport"].unique())
    n_sports = len(sports)

    metrics = [("height", "Height (cm)", GOLD),
               ("weight", "Weight (kg)", SILVER),
               ("age", "Age", BRONZE)]

    fig, axes = plt.subplots(n_sports, 3, figsize=(13, n_sports * 1.8), sharex=True)

    for row_i, sport in enumerate(sports):
        s = sub[sub["sport"] == sport]
        for col_i, (col, label, color) in enumerate(metrics):
            ax = axes[row_i, col_i]
            trend = s.groupby("year")[col].mean()

            ax.plot(trend.index, trend.values, color=color, linewidth=2.2,
                    marker="o", markersize=5, zorder=3)
            ax.fill_between(trend.index, trend.values, color=color, alpha=0.08)

            # Zoom y-axis to show variation
            ymin, ymax = trend.min(), trend.max()
            yrange = max(ymax - ymin, 2)
            ymid = (ymin + ymax) / 2
            ax.set_ylim(ymid - yrange * 1.3, ymid + yrange * 1.3)

            if row_i == 0:
                ax.set_title(label, fontsize=11, fontweight="bold")
            if col_i == 0:
                ax.set_ylabel(sport, fontsize=8, fontweight="bold")
            else:
                ax.set_ylabel("")

            ax.tick_params(axis="y", labelsize=7)
            ax.set_xticks([2010, 2014, 2018, 2022, 2026])
            if row_i == n_sports - 1:
                ax.set_xticklabels(["2010", "2014", "2018", "2022", "2026"], fontsize=8)

    fig.suptitle("Medalist Physique Trends by Sport (2010 - 2026)",
                 fontsize=14, fontweight="bold", x=0.0, ha="left", y=1.005)
    fig.subplots_adjust(left=0.15, hspace=0.45)
    save(fig, "18_physique_trends_by_sport")

# Figure 19: Sport Count
def fig_sport_count(df):
    counts = df.groupby("sport").size().reset_index(name="medals")
    counts = counts.sort_values("medals", ascending=True)

    # Map sport → color
    def get_color(sport):
        sport_lower = sport.lower()
        if "ski" or "biath" or "nord" in sport_lower:
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
        Patch(facecolor=GOLD, label="Skiing"),
        Patch(facecolor=SILVER, label="Skating"),
        Patch(facecolor=BRONZE, label="Other")
    ]

    ax.legend(handles=legend_elements, loc="lower right")

    save(fig, "19_sport_count")

def fig_medal_efficiency(df):
    by_sport = df.groupby(["sport", "country"]).size().reset_index(name="medals")
    sport_stats = by_sport.groupby("sport").agg(
        total_medals=("medals", "sum"),
        countries=("country", "nunique")
    ).reset_index()

    sport_stats["efficiency"] = sport_stats["total_medals"] / sport_stats["countries"]
    sport_stats = sport_stats.sort_values("efficiency")

    fig, ax = plt.subplots(figsize=(9, 6))
    ax.scatter(sport_stats["countries"], sport_stats["total_medals"],
               s=sport_stats["efficiency"] * 8,
               c=GOLD, edgecolors=DARK, alpha=0.75)

    for _, row in sport_stats.iterrows():
        ax.text(row["countries"] + 0.2, row["total_medals"], row["sport"], fontsize=7)

    ax.set_xlabel("Number of Competing Countries")
    ax.set_ylabel("Total Medals Awarded")
    ax.set_title("Medal Efficiency by Sport", fontsize=14, fontweight="bold")
    save(fig, "20_medal_efficiency")

def fig_gold_conversion(df):
    medal_cts = df.groupby(["Country", "medal"]).size().unstack(fill_value=0)
    medal_cts["total"] = medal_cts.sum(axis=1)
    medal_cts = medal_cts[medal_cts["total"] >= 10]

    medal_cts["gold_ratio"] = medal_cts["Gold"] / medal_cts["total"]
    top = medal_cts.sort_values("gold_ratio").tail(15)

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.barh(top.index, top["gold_ratio"], color=GOLD)

    ax.set_xlabel("Gold Medal Share")
    ax.set_title("Gold Conversion Rate by Country", fontsize=14, fontweight="bold")
    ax.xaxis.set_major_formatter(mticker.PercentFormatter(1.0))
    save(fig, "21_gold_conversion")

def fig_medal_concentration(df):
    by_sc = df.groupby(["sport", "country"]).size().reset_index(name="medals")

    records = []
    for sport in by_sc["sport"].unique():
        sub = by_sc[by_sc["sport"] == sport]
        total = sub["medals"].sum()
        top3 = sub.nlargest(3, "medals")["medals"].sum()
        records.append((sport, top3 / total))

    conc = pd.DataFrame(records, columns=["sport", "top3_share"])
    conc = conc.sort_values("top3_share")

    fig, ax = plt.subplots(figsize=(9, 6))
    ax.barh(conc["sport"], conc["top3_share"], color=BRONZE)

    ax.set_xlabel("Share of Medals Won by Top 3 Countries")
    ax.set_title("How Competitive is Each Sport?", fontsize=14, fontweight="bold")
    ax.xaxis.set_major_formatter(mticker.PercentFormatter(1.0))
    save(fig, "22_medal_concentration")

def fig_gdp_efficiency(df, countries):
    medal_cts = df.groupby("country").size().reset_index(name="medals")
    cm = medal_cts.merge(countries, left_on="country", right_on="country_code")
    cm = cm.dropna(subset=["gdpPerCapita", "Pop"])

    cm["medals_per_M"] = cm["medals"] / (cm["Pop"] / 1e6)

    fig, ax = plt.subplots(figsize=(9, 6))
    ax.scatter(cm["gdpPerCapita"], cm["medals_per_M"],
               s=70, c=SILVER, edgecolors=DARK, alpha=0.8)

    for _, row in cm.nlargest(5, "medals_per_M").iterrows():
        ax.annotate(row["Country"],
                    (row["gdpPerCapita"], row["medals_per_M"]),
                    fontsize=8)

    ax.set_xlabel("GDP per Capita ($)")
    ax.set_ylabel("Medals per Million People")
    ax.set_title("Which Countries Overperform Their Wealth?",
                 fontsize=14, fontweight="bold")
    save(fig, "23_gdp_efficiency")

def fig_physique_advantage(df):
    sub = df.dropna(subset=["height"]).copy()

    global_means = sub.groupby("sport")["height"].mean()
    top = df.groupby("country").size().nlargest(8).index
    top_df = sub[sub["country"].isin(top)]

    top_means = top_df.groupby("sport")["height"].mean()

    diff = (top_means - global_means).dropna().sort_values()

    fig, ax = plt.subplots(figsize=(9, 6))
    ax.barh(diff.index, diff.values, color=GOLD)

    ax.axvline(0, color=DARK, linewidth=1)
    ax.set_xlabel("Height Advantage (cm)")
    ax.set_title("Do Top Countries Have Physique Advantages?",
                 fontsize=14, fontweight="bold")
    save(fig, "24_physique_advantage")

def fig_medal_growth(df):
    by_cy = df.groupby(["year", "country"]).size().reset_index(name="medals")

    growth = []
    for c in by_cy["country"].unique():
        sub = by_cy[by_cy["country"] == c].sort_values("year")
        if len(sub) >= 2:
            growth.append((c, sub["medals"].iloc[-1] - sub["medals"].iloc[0]))

    growth_df = pd.DataFrame(growth, columns=["country", "growth"])
    top = growth_df.sort_values("growth").tail(12)

    names = df[["country", "Country"]].drop_duplicates().set_index("country")

    labels = []
    for c in top["country"]:
        if c in names.index and pd.notna(names.loc[c, "Country"]):
            labels.append(str(names.loc[c, "Country"]))
        else:
            labels.append(str(c))  # fallback to country code

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.barh(labels, top["growth"], color=ACCENT)

    ax.set_xlabel("Change in Medal Count (2010 → 2026)")
    ax.set_title("Fastest Improving Countries", fontsize=14, fontweight="bold")
    save(fig, "25_medal_growth")

# Main
def main():
    apply_theme()
    df, countries = load_data()
    print(f"Loaded {len(df)} medal records, {df['country'].nunique()} countries, "
          f"{df['year'].nunique()} Games\n")

    fig_top_countries(df)
    fig_gdp_vs_medals(df, countries)
    fig_medals_per_capita(df, countries)
    fig_medal_timeseries(df)
    fig_gdp_percap_timeseries(df, countries)
    fig_height_by_sport(df)
    fig_gold_ratio_heatmap(df)
    fig_population_vs_medals(df, countries)
    fig_stacked_area(df)
    fig_correlation_dashboard(df, countries)
    r2_df, n_countries, factor_cols = fig_r2_heatmap(df, countries)
    fig_r2_bars(r2_df, factor_cols)
    fig_weight_by_sport(df)
    fig_age_by_sport(df)
    fig_height_weight_profile(df)
    fig_top_cities(df)
    fig_physique_trends(df)
    fig_physique_trends_by_sport(df)
    fig_sport_count(df)
    fig_medal_efficiency(df)
    fig_gold_conversion(df)
    fig_medal_concentration(df)
    fig_gdp_efficiency(df, countries)
    fig_physique_advantage(df)
    fig_medal_growth(df)

    print(f"\nDone - {len(list(FIG_DIR.glob('*.png')))} figures saved to {FIG_DIR}")

if __name__ == "__main__":
    main()