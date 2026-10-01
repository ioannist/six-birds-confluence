"""Independent Boolean-matrix audit of every labeled ARS on 1..4 states.

Run with PYTHONPATH=src python3 review/run_math_audit.py.
This uses Warshall closure, independently of the library's BFS reachability.
"""

import json
from pathlib import Path

from rewriteflat.finite_ars import FiniteARS


def audit():
    counts = []
    for n in range(1, 5):
        row = {"states": n, "systems": 1 << (n * n), "terminating": 0, "confluent_terminating": 0}
        for mask in range(1 << (n * n)):
            edge = [[bool(mask & (1 << (i * n + j))) for j in range(n)] for i in range(n)]
            positive = [r[:] for r in edge]
            for k in range(n):
                for i in range(n):
                    for j in range(n):
                        positive[i][j] |= positive[i][k] and positive[k][j]
            terminating = not any(positive[i][i] for i in range(n))
            reach = [[positive[i][j] or i == j for j in range(n)] for i in range(n)]
            join = [[any(reach[i][k] and reach[j][k] for k in range(n)) for j in range(n)] for i in range(n)]
            local = all(not (edge[a][b] and edge[a][c]) or join[b][c]
                        for a in range(n) for b in range(n) for c in range(n))
            confluent = all(not (reach[a][b] and reach[a][c]) or join[b][c]
                            for a in range(n) for b in range(n) for c in range(n))
            normal = [not any(edge[i]) for i in range(n)]
            unique = all(sum(reach[a][b] and normal[b] for b in range(n)) <= 1 for a in range(n))
            labels = [str(i) for i in range(n)]
            ars = FiniteARS(labels, [(labels[i], labels[j]) for i in range(n) for j in range(n) if edge[i][j]])
            assert ars.is_terminating() == terminating, (n, mask, "termination")
            assert ars.is_locally_confluent() == local, (n, mask, "local confluence")
            assert ars.is_confluent() == confluent, (n, mask, "confluence")
            assert ars.has_unique_reachable_normal_forms() == unique, (n, mask, "normal forms")
            if terminating:
                row["terminating"] += 1
                row["confluent_terminating"] += confluent
                assert local == confluent == unique, (n, mask, "terminating equivalence")
        counts.append(row)
    result = {"kind": "independent_warshall_mathematical_audit", "per_n": counts,
              "total_systems": sum(r["systems"] for r in counts),
              "total_terminating_systems": sum(r["terminating"] for r in counts),
              "algorithm_discrepancies": 0, "terminating_equivalence_discrepancies": 0}
    Path("review/finite_ars_verification.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    audit()
