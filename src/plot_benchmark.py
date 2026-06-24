import csv
import os
import statistics
import matplotlib.pyplot as plt
from collections import defaultdict

INPUT_FILE = "results_rounds.csv"
PLOT_DIR = "plots"

TIMEOUT_LIMIT = 120.0

# Slightly stagger the timeouts
# so that r=1 and r=2 do not overlap.
TIMEOUT_Y = {
    0: 135.0,
    1: 150.0,
    2: 170.0,
}

ROUND_COLORS = {
    0: "tab:blue",
    1: "tab:orange",
    2: "tab:green",
}


def to_float(value):
    if value == "" or value is None:
        return None
    return float(value)


def median_or_none(values):
    if not values:
        return None
    return statistics.median(values)


def plot_all_rounds_one_diagram(rows, family):
    os.makedirs(PLOT_DIR, exist_ok=True)

    plt.figure(figsize=(10, 5))

    for r in [0, 1, 2]:
        maxhs = defaultdict(list)
        kissat_solved = defaultdict(list)
        timeouts = defaultdict(int)

        for row in rows:
            if row["family"] != family:
                continue

            if int(row["rounds"]) != r:
                continue

            size = int(row["size"])
            x = size if family == "random" else size * 4

            maxhs_time = to_float(row["maxhs_time"])
            kissat_time = to_float(row["kissat_total_time"])
            kissat_k = to_float(row["kissat_optimal_k"])

            if maxhs_time is not None:
                maxhs[x].append(maxhs_time)

            # Kissat curve only for solved instances
            if kissat_k is not None and kissat_time is not None:
                kissat_solved[x].append(kissat_time)

            # Mark timeouts separately
            if kissat_k is None:
                timeouts[x] += 1

        xs = sorted(set(maxhs.keys()) | set(kissat_solved.keys()) | set(timeouts.keys()))
        color = ROUND_COLORS[r]

        maxhs_x = []
        maxhs_y = []
        kissat_x = []
        kissat_y = []
        timeout_x = []
        timeout_y = []

        for x in xs:
            m_maxhs = median_or_none(maxhs[x])
            m_kissat = median_or_none(kissat_solved[x])

            if m_maxhs is not None:
                maxhs_x.append(x)
                maxhs_y.append(m_maxhs)

            if m_kissat is not None:
                kissat_x.append(x)
                kissat_y.append(m_kissat)

            if timeouts[x] > 0:
                timeout_x.append(x)
                timeout_y.append(TIMEOUT_Y[r])

        plt.plot(
            maxhs_x,
            maxhs_y,
            marker="o",
            linestyle="-",
            linewidth=2,
            color=color,
            label=f"MaxHS r={r}"
        )

        plt.plot(
            kissat_x,
            kissat_y,
            marker="s",
            linestyle="--",
            linewidth=2,
            color=color,
            label=f"Kissat r={r}"
        )

        plt.scatter(
            timeout_x,
            timeout_y,
            marker="x",
            s=160,
            linewidths=3,
            color=color,
            zorder=10,
            label=f"Timeout r={r}"
        )

    plt.axhline(
        TIMEOUT_LIMIT,
        color="black",
        linestyle=":",
        linewidth=1.6,
        alpha=0.8,
        label="Timeout-Grenze"
    )

    plt.yscale("log")
    plt.ylim(0.005, 300)

    plt.xlabel("Polygon-Größe" if family == "random" else "Kandidatenzahl")
    plt.ylabel("Median-Zeit (s)")
    plt.title(f"{family}: Einfluss der Kandidatenrunden")

    plt.grid(True, which="both", alpha=0.3)

    plt.legend(
        loc="center left",
        bbox_to_anchor=(1.02, 0.5),
        fontsize=9
    )

    plt.tight_layout(rect=[0, 0, 0.78, 1])

    out_file = os.path.join(PLOT_DIR, f"{family}_all_rounds_timeouts.pdf")
    plt.savefig(out_file, bbox_inches="tight")
    plt.show()

    print(f"Saved: {out_file}")


with open(INPUT_FILE, newline="") as f:
    reader = csv.DictReader(f)
    rows = list(reader)

plot_all_rounds_one_diagram(rows, "comb")
plot_all_rounds_one_diagram(rows, "random")