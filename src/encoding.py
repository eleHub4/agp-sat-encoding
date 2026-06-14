def coverage_clauses(V):
    n = len(V)
    clauses = []
    for j in range(n):
        clause = []
        for i in range(n):
            if V[i][j]:
                clause.append(i + 1)
        if not clause:
            raise ValueError(f"Witness {j} not visible from any guard")
        clauses.append(clause)
    return clauses


def sequential_counter(n, k, first_aux):
    def s(i, j):
        return first_aux + (i - 1) * k + (j - 1)

    clauses = []

    # i=1
    clauses.append([-1, s(1, 1)])
    clauses.append([1, -s(1, 1)])

    # i=2..n
    for i in range(2, n + 1):
        xi = i
        clauses.append([-xi, s(i, 1)])
        for j in range(1, k + 1):
            clauses.append([-s(i - 1, j), s(i, j)])
            if j < k:
                clauses.append([-xi, -s(i - 1, j), s(i, j + 1)])
        clauses.append([-xi, -s(i - 1, k)])

    return clauses, s(n, k)


def write_dimacs(clauses, num_vars, filepath, comments=None):
    with open(filepath, "w") as f:
        if comments:
            for line in comments:
                f.write(f"c {line}\n")
        f.write(f"p cnf {num_vars} {len(clauses)}\n")
        for clause in clauses:
            f.write(" ".join(map(str, clause)) + " 0\n")


def soft_clauses(n):
    return [[-(j + 1)] for j in range(n)]


def write_wcnf(hard_clauses, soft_clauses, num_vars, filepath, comments=None):
    with open(filepath, "w") as f:
        if comments:
            for line in comments:
                f.write(f"c {line}\n")
        for clause in hard_clauses:
            f.write("h " + " ".join(map(str, clause)) + " 0\n")
        for clause in soft_clauses:
            f.write("1 " + " ".join(map(str, clause)) + " 0\n")
