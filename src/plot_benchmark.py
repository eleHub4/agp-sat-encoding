import csv
import os
import statistics
import matplotlib.pyplot as plt
from collections import defaultdict

INPUT_FILE = "results_rounds.csv"
PLOT_DIR = "plots"


def to_float(value):
    if value == "" or value is None:
        return None
    return float(value)


def median_plot_by_family(rows, family):
    rounds_data = {
        0: {"maxhs": defaultdict(list), "kissat": defaultdict(list)},
        1: {"maxhs": defaultdict(list), "kissat": defaultdict(list)},
        2: {"maxhs": defaultdict(list), "kissat": defaultdict(list)},
    }
    for row in rows:
        if row["family"] != family:
            continue
        r = int(row["rounds"])
        size = int(row["size"])
        x = size if family == "random" else size * 4
        maxhs_time = to_float(row["maxhs_time"])
        kissat_time = to_float(row["kissat_total_time"])
        if maxhs_time is not None:
            rounds_data[r]["maxhs"][x].append(maxhs_time)
        if kissat_time is not None:
            rounds_data[r]["kissat"][x].append(kissat_time)

    plt.figure(figsize=(9, 5))
    for r in [0, 1, 2]:
        xs = sorted(rounds_data[r]["maxhs"].keys())
        maxhs_med = [statistics.median(rounds_data[r]["maxhs"][x]) for x in xs]
        kissat_med = [statistics.median(rounds_data[r]["kissat"][x]) for x in xs]
        plt.plot(xs, maxhs_med, marker="o", label=f"MaxHS r={r}")
        plt.plot(xs, kissat_med, marker="s", linestyle="--", label=f"Kissat r={r}")

    plt.yscale("log")
    plt.xlabel("Polygongröße")
    plt.ylabel("Median-Zeit (s)")
    plt.title(f"{family}: Einfluss der Kandidatenrunden")
    plt.grid(True, which="both", alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(PLOT_DIR, f"median_{family}.pdf"), bbox_inches="tight")
    plt.close()


os.makedirs(PLOT_DIR, exist_ok=True)

with open(INPUT_FILE, newline="") as f:
    reader = csv.DictReader(f)
    rows = list(reader)

median_plot_by_family(rows, "comb")
median_plot_by_family(rows, "random")