"""
Rounds comparison: MaxHS vs. iterative Kissat
for the AGP SAT/MaxSAT pipeline, varying candidate generation rounds.
Usage:
    python3 run_benchmark_v3.py preprocess
    python3 run_benchmark_v3.py solve
    python3 run_benchmark_v3.py all
"""

import subprocess
import time
import csv
import sys
import json
from pathlib import Path
from datetime import datetime

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------

MAXHS_BIN = "maxhs"
KISSAT_BIN = "kissat"
MAIN_PY = "main.py"
PYTHON_BIN = sys.executable

DATA_DIR = Path("data")
CACHE_DIR = Path("cache_rounds")
PREPROCESS_CSV = Path("preprocessing_rounds.csv")
RESULTS_CSV = Path("results_rounds.csv")
LOG_FILE = Path("benchmark_rounds.log")

INSTANCE_FAMILIES = {
    "comb": {
        "sizes": [3, 4, 5, 6],
        "seeds": [None],
        "rounds": [0, 1, 2],
    },
    "random": {
        "sizes": [10, 20, 30, 40],
        "seeds": [1, 2, 3, 4, 5],
        "rounds": [0, 1, 2],          # round 2 explodes for random_30/40
    },
}

K_MAX = 20                  # upper bound; iterative search stops at SAT

# Timeouts (seconds)
PREPROCESS_TIMEOUT = 7200
MAXHS_TIMEOUT = 600
KISSAT_TIMEOUT = 600

TOTAL_BUDGET_SECONDS = 8 * 3600

PREPROCESS_FIELDS = [
    "family", "size", "seed", "rounds", "instance",
    "n_candidates", "n_vars_maxsat", "n_hard", "n_soft",
    "wcnf_write_time", "total_preprocess_time",
    "error",
]

RESULTS_FIELDS = [
    "family", "size", "seed", "rounds", "instance",
    "maxhs_status", "maxhs_opt", "maxhs_time",
    "kissat_optimal_k", "kissat_total_time",
    "kissat_unsat_time", "kissat_sat_time",
    "kissat_num_calls", "kissat_per_k",
    "error",
]


# ----------------------------------------------------------------------
# Logging
# ----------------------------------------------------------------------

def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")


# ----------------------------------------------------------------------
# Subprocess helper
# ----------------------------------------------------------------------

def run_cmd(cmd, timeout, cwd=None):
    start = time.perf_counter()
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, cwd=cwd
        )
        elapsed = time.perf_counter() - start
        return result.stdout, result.stderr, result.returncode, elapsed, False
    except subprocess.TimeoutExpired as e:
        elapsed = time.perf_counter() - start
        stdout = e.stdout.decode() if isinstance(e.stdout, bytes) else (e.stdout or "")
        stderr = e.stderr.decode() if isinstance(e.stderr, bytes) else (e.stderr or "")
        return stdout, stderr, -1, elapsed, True


def parse_vars_hard_soft(stdout):
    for line in stdout.splitlines():
        if "vars" in line and "hard" in line and "soft" in line:
            parts = line.split("(")[-1].split(")")[0]
            nums = [int(s) for s in parts.replace(",", "").split() if s.isdigit()]
            if len(nums) >= 3:
                return nums[0], nums[1], nums[2]
    return None, None, None


# ----------------------------------------------------------------------
# Instance list — tag includes round number
# ----------------------------------------------------------------------

def build_instance_list():
    instances = []
    for family, cfg in INSTANCE_FAMILIES.items():
        for rounds in cfg["rounds"]:
            for size in cfg["sizes"]:
                for seed in cfg["seeds"]:
                    if seed is None:
                        csv_path = DATA_DIR / f"{family}_{size}.csv"
                        tag = f"{family}_{size}_r{rounds}"
                    else:
                        csv_path = DATA_DIR / f"{family}_{size}_seed{seed}.csv"
                        tag = f"{family}_{size}_seed{seed}_r{rounds}"
                    instances.append((family, size, seed, rounds, csv_path, tag))
    return instances


# ----------------------------------------------------------------------
# CSV helpers
# ----------------------------------------------------------------------

def load_done(csv_path, key_field="instance"):
    done = set()
    if csv_path.exists():
        with open(csv_path, "r", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                done.add(row[key_field])
    return done


def init_csv(csv_path, fields):
    if not csv_path.exists():
        with open(csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()


def append_row(csv_path, fields, row):
    with open(csv_path, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writerow(row)


# ----------------------------------------------------------------------
# Cache paths
# ----------------------------------------------------------------------

def cache_paths(tag):
    return {
        "wcnf": CACHE_DIR / f"{tag}.wcnf",
        "meta": CACHE_DIR / f"{tag}.meta.json",
        "cnf_dir": CACHE_DIR / f"{tag}_cnfs",
    }


# ----------------------------------------------------------------------
# STAGE 1: Preprocessing
# ----------------------------------------------------------------------

def preprocess_instance(family, size, seed, rounds, csv_path, tag):
    paths = cache_paths(tag)
    paths["cnf_dir"].mkdir(parents=True, exist_ok=True)

    row = {f: "" for f in PREPROCESS_FIELDS}
    row.update(
        family=family, size=size,
        seed=seed if seed is not None else "",
        rounds=rounds, instance=tag,
    )

    t_start = time.perf_counter()

    # WCNF generation
    cmd = [
        PYTHON_BIN, MAIN_PY, str(csv_path),
        "--maxsat", "--rounds", str(rounds),
        "-o", str(paths["wcnf"]),
    ]
    stdout, stderr, rc, elapsed, timed_out = run_cmd(cmd, PREPROCESS_TIMEOUT)
    if timed_out:
        raise RuntimeError(f"WCNF generation timed out after {elapsed:.0f}s")
    if rc != 0:
        raise RuntimeError(f"WCNF generation failed rc={rc}: {stderr[:500]}")

    n_vars, n_hard, n_soft = parse_vars_hard_soft(stdout)
    row["n_candidates"] = n_vars
    row["n_vars_maxsat"] = n_vars
    row["n_hard"] = n_hard
    row["n_soft"] = n_soft
    row["wcnf_write_time"] = f"{elapsed:.4f}"

    # k_cap from Chvátal bound on polygon vertices
    # poly_n = size * 4 - 2 for comb (approx)
    try:
        with open(csv_path) as f:
            poly_n = sum(1 for _ in f)
        k_cap = min(poly_n // 3, K_MAX)
    except Exception:
        k_cap = K_MAX
    k_cap = max(k_cap, 1)

    meta = {
        "tag": tag,
        "rounds": rounds,
        "n_candidates": n_vars,
        "k_cap": k_cap,
        "cnf_paths": {},
    }

    # In-process CNF generation for all k
    try:
        import sys as _sys
        if "" not in _sys.path:
            _sys.path.insert(0, "")

        from main import load_polygon
        from src.candidates import build_candidates
        from src.visibility import compute_visibility
        from src.encoding import coverage_clauses, sequential_counter, write_dimacs

        poly = load_polygon(str(csv_path))
        pts = build_candidates(poly, poly, max_rounds=rounds)
        V = compute_visibility(pts, poly)
        n = len(pts)
        cov = coverage_clauses(V)

        for k in range(1, k_cap + 1):
            cnf_path = paths["cnf_dir"] / f"k{k}.cnf"
            cnt, num_vars_k = sequential_counter(n, k, first_aux=n + 1)
            write_dimacs(
                cov + cnt, num_vars_k, str(cnf_path),
                comments=[f"AGP SAT-Encoding: {csv_path}", f"candidates: {n}", f"k={k}", f"rounds={rounds}"],
            )
            meta["cnf_paths"][str(k)] = str(cnf_path)

    except ImportError as e:
        log(f"{tag}: in-process encoding unavailable ({e}), falling back to subprocess per k")
        for k in range(1, k_cap + 1):
            cnf_path = paths["cnf_dir"] / f"k{k}.cnf"
            cmd = [
                PYTHON_BIN, MAIN_PY, str(csv_path),
                "-k", str(k),
                "--rounds", str(rounds),
                "-o", str(cnf_path),
            ]
            stdout, stderr, rc, elapsed, timed_out = run_cmd(cmd, 120)
            if timed_out or rc != 0:
                log(f"{tag}: CNF for k={k} failed, stopping k-cache here")
                meta["k_cap"] = k - 1
                break
            meta["cnf_paths"][str(k)] = str(cnf_path)

    with open(paths["meta"], "w") as f:
        json.dump(meta, f, indent=2)

    total_preprocess = time.perf_counter() - t_start
    row["total_preprocess_time"] = f"{total_preprocess:.4f}"
    return row


def stage_preprocess():
    CACHE_DIR.mkdir(exist_ok=True)
    init_csv(PREPROCESS_CSV, PREPROCESS_FIELDS)
    done = load_done(PREPROCESS_CSV)

    instances = build_instance_list()
    log(f"=== PREPROCESS stage: {len(instances)} instances, {len(done)} already cached ===")

    run_start = time.perf_counter()
    for family, size, seed, rounds, csv_path, tag in instances:
        if tag in done:
            log(f"SKIP preprocess {tag} (cached)")
            continue
        if time.perf_counter() - run_start > TOTAL_BUDGET_SECONDS:
            log("Time budget exceeded, stopping.")
            break
        if not csv_path.exists():
            log(f"SKIP {tag}: {csv_path} not found")
            continue

        log(f"--- Preprocessing {tag} ---")
        row = {f: "" for f in PREPROCESS_FIELDS}
        row.update(family=family, size=size, seed=seed if seed is not None else "",
                   rounds=rounds, instance=tag)
        try:
            row = preprocess_instance(family, size, seed, rounds, csv_path, tag)
            log(f"{tag}: done in {row['total_preprocess_time']}s ({row['n_candidates']} candidates)")
        except Exception as e:
            log(f"{tag}: PREPROCESS ERROR {e}")
            row["error"] = str(e)

        append_row(PREPROCESS_CSV, PREPROCESS_FIELDS, row)

    log("=== PREPROCESS stage finished ===")


# ----------------------------------------------------------------------
# STAGE 2: Solve
# ----------------------------------------------------------------------

def run_maxhs(wcnf_path):
    cmd = [MAXHS_BIN, "-printSoln-old-format", str(wcnf_path)]
    stdout, stderr, rc, elapsed, timed_out = run_cmd(cmd, MAXHS_TIMEOUT)
    if timed_out:
        return "TIMEOUT", None, elapsed

    status = "UNKNOWN"
    opt_value = None
    for line in stdout.splitlines():
        if line.startswith("s "):
            status = line[2:].strip()
        elif line.startswith("o "):
            try:
                opt_value = int(line[2:].strip())
            except ValueError:
                pass
    return status, opt_value, elapsed


def run_kissat(cnf_path):
    cmd = [KISSAT_BIN, str(cnf_path)]
    stdout, stderr, rc, elapsed, timed_out = run_cmd(cmd, KISSAT_TIMEOUT)
    if timed_out:
        return "TIMEOUT", elapsed

    status = "UNKNOWN"
    for line in stdout.splitlines():
        if line.startswith("s "):
            status = line[2:].strip()
            break
    return status, elapsed


def iterative_kissat_from_cache(meta):
    per_k = []
    unsat_time = 0.0
    sat_time = 0.0
    optimal_k = None

    for k in range(1, meta["k_cap"] + 1):
        if str(k) not in meta["cnf_paths"]:
            break
        cnf_path = Path(meta["cnf_paths"][str(k)])
        status, elapsed = run_kissat(cnf_path)
        per_k.append((k, status, elapsed))

        if status == "SATISFIABLE":
            sat_time += elapsed
            optimal_k = k
            break
        elif status == "UNSATISFIABLE":
            unsat_time += elapsed
        else:
            break

    total_time = sum(e for _, _, e in per_k)
    per_k_str = ";".join(f"k{k}:{s}:{e:.4f}" for k, s, e in per_k)

    return {
        "optimal_k": optimal_k,
        "total_time": total_time,
        "unsat_time": unsat_time,
        "sat_time": sat_time,
        "num_calls": len(per_k),
        "per_k": per_k_str,
    }


def stage_solve():
    init_csv(RESULTS_CSV, RESULTS_FIELDS)
    done = load_done(RESULTS_CSV)

    instances = build_instance_list()
    log(f"=== SOLVE stage: {len(instances)} instances, {len(done)} already done ===")

    run_start = time.perf_counter()
    for family, size, seed, rounds, csv_path, tag in instances:
        if tag in done:
            log(f"SKIP solve {tag} (already done)")
            continue
        if time.perf_counter() - run_start > TOTAL_BUDGET_SECONDS:
            log("Time budget exceeded, stopping.")
            break

        paths = cache_paths(tag)
        if not paths["wcnf"].exists() or not paths["meta"].exists():
            log(f"SKIP solve {tag}: not cached — run preprocess first")
            continue

        log(f"--- Solving {tag} ---")
        row = {f: "" for f in RESULTS_FIELDS}
        row.update(family=family, size=size, seed=seed if seed is not None else "",
                   rounds=rounds, instance=tag)

        try:
            maxhs_status, maxhs_opt, maxhs_time = run_maxhs(paths["wcnf"])
            row["maxhs_status"] = maxhs_status
            row["maxhs_opt"] = maxhs_opt
            row["maxhs_time"] = f"{maxhs_time:.4f}"
            log(f"{tag}: MaxHS -> {maxhs_status} (o={maxhs_opt}) in {maxhs_time:.4f}s")

            with open(paths["meta"]) as f:
                meta = json.load(f)

            kresult = iterative_kissat_from_cache(meta)
            row["kissat_optimal_k"] = kresult["optimal_k"]
            row["kissat_total_time"] = f"{kresult['total_time']:.4f}"
            row["kissat_unsat_time"] = f"{kresult['unsat_time']:.4f}"
            row["kissat_sat_time"] = f"{kresult['sat_time']:.4f}"
            row["kissat_num_calls"] = kresult["num_calls"]
            row["kissat_per_k"] = kresult["per_k"]
            log(
                f"{tag}: Kissat -> k_opt={kresult['optimal_k']} "
                f"total={kresult['total_time']:.4f}s (calls={kresult['num_calls']})"
            )

            if maxhs_opt is not None and kresult["optimal_k"] is not None:
                if maxhs_opt != kresult["optimal_k"]:
                    log(f"{tag}: WARNING mismatch! MaxHS o={maxhs_opt} vs Kissat k_opt={kresult['optimal_k']}")
                    row["error"] = f"k mismatch: maxhs={maxhs_opt} kissat={kresult['optimal_k']}"

        except Exception as e:
            log(f"{tag}: SOLVE ERROR {e}")
            row["error"] = str(e)

        append_row(RESULTS_CSV, RESULTS_FIELDS, row)

    log("=== SOLVE stage finished ===")


# ----------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------

def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ("preprocess", "solve", "all"):
        print(__doc__)
        sys.exit(1)

    mode = sys.argv[1]
    log(f"=== Benchmark run started (mode={mode}) ===")

    if mode in ("preprocess", "all"):
        stage_preprocess()
    if mode in ("solve", "all"):
        stage_solve()

    log("=== Benchmark run complete ===")


if __name__ == "__main__":
    main()