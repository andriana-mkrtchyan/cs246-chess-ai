import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import glob

sns.set_theme(style="whitegrid", palette="deep")
plt.rcParams["figure.figsize"] = (9, 5)


def save_fig(name: str):
    """Save current figure as PNG in charts/ and close."""

    os.makedirs("charts", exist_ok=True)
    plt.tight_layout()
    plt.savefig(os.path.join("charts", f"{name}.png"), dpi=220)
    plt.close()


def load_tests() -> pd.DataFrame:
    """Load all CSVs from tests/ and normalize columns."""
    files = glob.glob("tests/*.csv")
    if not files:
        raise FileNotFoundError("No CSV files found in tests/ folder.")

    dfs = []

    for path in files:
        try:
            raw = pd.read_csv(path, on_bad_lines="skip")
        except Exception as e:
            print(f"Skipping {path} due to read error: {e}")
            continue

        # normalize column names: lower + remove spaces
        raw.columns = [c.strip().lower().replace(" ", "") for c in raw.columns]

        # ensure optional columns exist
        if "drawreason" not in raw.columns:
            raw["drawreason"] = np.nan
        if "startfen" not in raw.columns:
            raw["startfen"] = np.nan

        # basic required columns check
        required = {"game", "whitealgo", "blackalgo", "result", "moves"}
        if not required.issubset(set(raw.columns)):
            print(f"Skipping {path}: missing required columns {required - set(raw.columns)}")
            continue

        # scenario from filename
        fname = os.path.basename(path)
        scenario = "random" if fname.startswith("rdb_") else "fixed"
        raw["scenario"] = scenario
        raw["file"] = fname

        dfs.append(raw)

    if not dfs:
        raise RuntimeError("No valid CSVs after filtering.")

    df = pd.concat(dfs, ignore_index=True)

    # keep only rows with valid algo names (alphabetic; drop garbage lines)
    df = df.dropna(subset=["whitealgo", "blackalgo"])
    mask_valid = df["whitealgo"].astype(str).str.isalpha() & df["blackalgo"].astype(str).str.isalpha()
    df = df[mask_valid].copy()

    # numeric conversion
    df["result"] = pd.to_numeric(df["result"], errors="coerce")
    df["moves"] = pd.to_numeric(df["moves"], errors="coerce")
    df = df.dropna(subset=["result", "moves"])

    # derive winner / loser / outcome / winner color
    df["winneralgo"] = np.where(
        df["result"] == 1,
        df["whitealgo"],
        np.where(df["result"] == -1, df["blackalgo"], np.nan),
    )
    df["loseralgo"] = np.where(
        df["result"] == 1,
        df["blackalgo"],
        np.where(df["result"] == -1, df["whitealgo"], np.nan),
    )
    df["winnercolor"] = None
    df.loc[df["result"] == 1, "winnercolor"] = "White"
    df.loc[df["result"] == -1, "winnercolor"] = "Black"
    df["outcome"] = df["result"].map({1: "Win", 0: "Draw", -1: "Loss"})

    return df


def add_stacked_labels(ax):
    """Add percentage labels inside stacked bars."""
    for p in ax.patches:
        height = p.get_height()
        if height <= 0:
            continue
        x = p.get_x() + p.get_width() / 2
        y = p.get_y() + height / 2
        ax.text(x, y, f"{height:.1f}%", ha="center", va="center", fontsize=9, color="white")


def analyze(df: pd.DataFrame):
    # --------------------------------------------------
    # 1. Algorithm performance on random vs fixed
    # --------------------------------------------------
    print("\n[1] Algorithm performance on random vs fixed")

    # wins / losses / draws per (scenario, algo)
    wins = df.dropna(subset=["winneralgo"]).groupby(["scenario", "winneralgo"]).size().rename("Win")

    losses = df.dropna(subset=["loseralgo"]).groupby(["scenario", "loseralgo"]).size().rename("Loss")

    draw_rows = df[df["result"] == 0]
    if not draw_rows.empty:
        draw_long = pd.DataFrame(
            {
                "scenario": pd.concat([draw_rows["scenario"], draw_rows["scenario"]]),
                "algo": pd.concat([draw_rows["whitealgo"], draw_rows["blackalgo"]]),
            }
        )
        draws = draw_long.groupby(["scenario", "algo"]).size().rename("Draw")
    else:
        draws = pd.Series(dtype=float)

    scenarios = sorted(df["scenario"].unique())
    algos = sorted(pd.unique(pd.concat([df["whitealgo"], df["blackalgo"]])))

    idx = pd.MultiIndex.from_product([scenarios, algos], names=["scenario", "algo"])
    perf_counts = pd.DataFrame(index=idx, columns=["Win", "Draw", "Loss"]).fillna(0)

    for series, col in [(wins, "Win"), (draws, "Draw"), (losses, "Loss")]:
        for (sc, al), val in series.items():
            perf_counts.loc[(sc, al), col] = val

    perf_pct = perf_counts.div(perf_counts.sum(axis=1).replace(0, np.nan), axis=0) * 100

    # one stacked bar chart per scenario
    for sc in scenarios:
        sub = perf_pct.xs(sc).dropna(how="all")
        if sub.empty:
            print(f"  - Skipping scenario {sc}: no data")
            continue

        ax = sub.plot(kind="bar", stacked=True)
        ax.set_title(f"Algorithm Performance on {sc.capitalize()} Boards (%)")
        ax.set_ylabel("Percentage (%)")
        add_stacked_labels(ax)
        save_fig(f"1_algo_perf_{sc}")

    # --------------------------------------------------
    # 2. Inter-algo comparison (head-to-head matrix)
    # --------------------------------------------------
    print("\n[2] Inter-algorithm head-to-head comparison")

    df_hh = df.dropna(subset=["winneralgo", "loseralgo"])
    if df_hh.empty:
        print("  - No head-to-head data available.")
    else:
        hh = df_hh.groupby(["winneralgo", "loseralgo"]).size().unstack(fill_value=0)
        plt.figure(figsize=(8, 6))
        sns.heatmap(hh, annot=True, fmt="d", cmap="Blues")
        plt.title("Head-to-Head: Wins (Row algo beats Column algo)")
        save_fig("2_head_to_head_matrix")

    # --------------------------------------------------
    # 3. Draw behaviour comparison
    # --------------------------------------------------
    print("\n[3] Draw behaviour comparison")

    draws_df = df[df["result"] == 0].copy()
    if draws_df.empty:
        print("  - No draws to analyze.")
    else:
        draws_df["drawreason_norm"] = draws_df["drawreason"].fillna("Unknown")
        draw_stats = (
            draws_df.groupby(["scenario", "drawreason_norm"]).size().unstack(fill_value=0)
        )
        draw_stats_pct = draw_stats.div(draw_stats.sum(axis=1), axis=0) * 100

        ax = draw_stats_pct.plot(kind="bar", stacked=True)
        ax.set_title("Draw Reasons by Scenario (%)")
        ax.set_ylabel("Percentage (%)")
        add_stacked_labels(ax)
        save_fig("3_draw_behavior")

    # --------------------------------------------------
    # 4. Cross-scenario correlation (algorithm strength)
    # --------------------------------------------------
    print("\n[4] Cross-scenario correlation of win rates")

    # win rate = wins / total games where algo participates
    games_long = df.melt(
        id_vars=["scenario", "game"],
        value_vars=["whitealgo", "blackalgo"],
        value_name="algo"
    )
    games_counts = games_long.groupby(["scenario", "algo"])["game"].nunique()

    wins_counts = wins.copy()
    win_rate = (wins_counts / games_counts).unstack("scenario")

    if win_rate is None or win_rate.empty or win_rate.shape[1] < 2:
        print("  - Not enough data (both random and fixed) for correlation.")
    else:
        # ensure both columns exist
        cols = [c for c in ["random", "fixed"] if c in win_rate.columns]
        if len(cols) < 2:
            print("  - Need both random and fixed win rates for correlation.")
        else:
            wr = win_rate[cols].dropna()
            if wr.empty:
                print("  - No overlapping algorithms between scenarios.")
            else:
                corr_val = wr[cols[0]].corr(wr[cols[1]])
                # simple value card + scatter
                plt.figure()
                plt.text(
                    0.5,
                    0.5,
                    f"Correlation of Win Rates\n{cols[0].capitalize()} vs {cols[1].capitalize()}:\n\n{corr_val:.3f}",
                    ha="center",
                    va="center",
                    fontsize=14,
                )
                plt.axis("off")
                save_fig("4_cross_scenario_corr_card")

                plt.figure()
                plt.scatter(wr[cols[0]], wr[cols[1]])
                maxv = float(max(wr[cols[0]].max(), wr[cols[1]].max()))
                plt.plot([0, maxv], [0, maxv], "r--", linewidth=1)
                plt.xlabel(f"{cols[0].capitalize()} win rate")
                plt.ylabel(f"{cols[1].capitalize()} win rate")
                plt.title("Cross-Scenario Win Rate Correlation")
                save_fig("4_cross_scenario_corr_scatter")

    # --------------------------------------------------
    # 5. Average move count (per scenario)
    # --------------------------------------------------
    print("\n[5] Average move count per scenario")

    moves_avg = df.groupby("scenario")["moves"].mean()
    ax = moves_avg.plot(kind="bar")
    ax.set_title("Average Game Length per Scenario")
    ax.set_ylabel("Average Moves")
    for i, v in enumerate(moves_avg):
        ax.text(i, v + 0.3, f"{v:.1f}", ha="center", fontsize=9)
    save_fig("5_avg_moves_scenario")

    # --------------------------------------------------
    # 6. Symmetry test: per-algorithm color bias (FIXED)
    # --------------------------------------------------
    print("\n[6] Symmetry test (per-algorithm color bias on fixed boards)")

    df_fixed = df[df["scenario"] == "fixed"].copy()
    if df_fixed.empty:
        print("  - No fixed-board data, skipping symmetry test.")
    else:
        algos_fixed = sorted(
            pd.unique(pd.concat([df_fixed["whitealgo"], df_fixed["blackalgo"]]))
        )

        rows = []
        for a in algos_fixed:
            white_games = df_fixed[df_fixed["whitealgo"] == a]
            black_games = df_fixed[df_fixed["blackalgo"] == a]

            white_total = len(white_games)
            black_total = len(black_games)

            white_wins = (white_games["result"] == 1).sum()
            black_wins = (black_games["result"] == -1).sum()

            white_win_rate = 100 * white_wins / white_total if white_total > 0 else np.nan
            black_win_rate = 100 * black_wins / black_total if black_total > 0 else np.nan

            rows.append(
                {
                    "algo": a,
                    "WhiteWin%": white_win_rate,
                    "BlackWin%": black_win_rate,
                    "Delta": white_win_rate - black_win_rate,
                }
            )

        sym_df = pd.DataFrame(rows).set_index("algo")
        print(sym_df)  # optional, nice to see in console

        ax = sym_df[["WhiteWin%", "BlackWin%"]].plot(kind="bar")
        ax.set_ylabel("Win rate (%)")
        ax.set_title("Per-Algorithm Color Symmetry on Fixed Boards")

        # value labels
        for p in ax.patches:
            height = p.get_height()
            if not np.isnan(height):
                ax.text(
                    p.get_x() + p.get_width() / 2,
                    height + 0.5,
                    f"{height:.1f}%",
                    ha="center",
                    va="bottom",
                    fontsize=8,
                )

        save_fig("6_symmetry_per_algo_fixed")

    # --------------------------------------------------
    # 7. Colour advantage analysis (does first move matter?)
    # --------------------------------------------------
    print("\n[7] Colour advantage analysis")

    wins_only = df[df["winnercolor"].notna()]
    if wins_only.empty:
        print("  - No decisive games to analyze color advantage.")
    else:
        color_stats = wins_only.groupby(["scenario", "winnercolor"]).size().unstack(fill_value=0)
        color_pct = color_stats.div(color_stats.sum(axis=1), axis=0) * 100

        ax = color_pct.plot(kind="bar", stacked=True)
        ax.set_title("Winning Color Distribution by Scenario (%)")
        ax.set_ylabel("Percentage of Wins (%)")
        add_stacked_labels(ax)
        save_fig("7_color_advantage")

    # --------------------------------------------------
    # 2b. Corrected: Clustered bar chart (Fixed vs Random per Outcome)
    # --------------------------------------------------
    print("\n[2b] Correct Clustered Comparison (Fixed vs Random per Outcome)")

    # perf_pct index = (scenario, algo)
    # columns = Win, Draw, Loss

    cluster = perf_pct.reset_index()  # cols: scenario, algo, Win, Draw, Loss

    # Melt into long form: but keep outcome structure
    cluster_long = cluster.melt(
        id_vars=["scenario", "algo"],
        value_vars=["Win", "Draw", "Loss"],
        var_name="Outcome",
        value_name="Percentage"
    )

    plt.figure(figsize=(12, 6))

    ax = sns.barplot(
        data=cluster_long,
        x="Outcome",
        y="Percentage",
        hue="scenario",
        ci=None,
        palette="Set2",
        dodge=True,
    )

    # Facet per algorithm → one row per algorithm
    g = sns.catplot(
        data=cluster_long,
        x="Outcome",
        y="Percentage",
        hue="scenario",
        col="algo",
        kind="bar",
        col_wrap=3,
        height=4,
        palette="Set2",
        ci=None
    )

    # Add labels to bars
    for ax in g.axes:
        for p in ax.patches:
            height = p.get_height()
            if not np.isnan(height):
                ax.text(
                    p.get_x() + p.get_width() / 2,
                    height + 1,
                    f"{height:.1f}%",
                    ha="center",
                    va="bottom",
                    fontsize=8
                )

    g.fig.suptitle("Algorithm Performance: Fixed vs Random (Clustered by Outcome)", y=1.05)

    save_fig("2b_clustered_fixed_vs_random")
    plt.close()

    # --------------------------------------------------
    # X. Algorithm Win Distribution (Pie Chart)
    # --------------------------------------------------
    print("\n[X] Algorithm Win Distribution (Pie Chart)")

    # Count algorithm wins (as White or Black)
    wins_all = (
        df.dropna(subset=["winneralgo"])
        .groupby("winneralgo")
        .size()
        .sort_values(ascending=False)
    )

    plt.figure(figsize=(7, 7))
    plt.pie(
        wins_all,
        labels=wins_all.index,
        autopct='%1.1f%%',
        startangle=90,
        counterclock=False,
    )
    plt.title("Distribution of Wins Across All Algorithms")
    save_fig("X_algorithm_win_distribution")
    plt.close()


if __name__ == "__main__":
    df_all = load_tests()
    analyze(df_all)
    print("\nAnalysis complete! Charts saved in /charts/")
