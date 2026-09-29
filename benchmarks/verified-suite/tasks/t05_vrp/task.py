"""T05 - Ruteo de vehículos con capacidad y distancia máxima. Puntuación continua frente a una heurística de referencia."""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent))
from suite_lib import Report, fail_report, read_json, rng, write_json  # noqa: E402

ID = "t05_vrp"
TITLE = "Ruteo de vehículos (optimización, puntuación continua)"
LEVELS = (1, 2, 3)
DELIVERABLES = ["routes.json"]
NEEDS = "Ejecutar código Python ayuda mucho; un chat sin código obtiene rutas de mala calidad."
SIZES = {1: 30, 2: 80, 3: 200}
CAPACITY = {1: 100, 2: 150, 3: 200}
MAX_DIST = {1: 2400, 2: 2800, 3: 3200}

TASK = """# Requirements — Vehicle Routing Planner

## Introduction

A distribution company must deliver goods from a single depot to {n} customers. Vehicles are identical, and there are as many vehicles as needed. Each vehicle
performs one **route**: it leaves the depot, visits some customers in a chosen order, and returns to the depot. You must plan the routes so that the **total distance driven is as small as possible**.

All distances are **Manhattan distances between integer coordinates**: `dist((x1,y1),(x2,y2)) = |x1-x2| + |y1-y2|`. There is no randomness and no external service: everything you need is in `instance.json`.

`instance.json` contains:
```json
{{"depot": [500, 500], "capacity": {cap}, "max_route_distance": {maxd},
  "customers": [{{"id": 1, "x": 120, "y": 870, "demand": 14}}, ...]}}
```

## Requirements

### Requirement 1 — Feasible routes

**User Story:** As a dispatcher, I want every customer served exactly once by a route that respects vehicle limits, so the plan can actually be driven.

#### Acceptance Criteria
1. THE plan SHALL contain every customer id exactly once across all routes, and no id that is not in the instance.
2. FOR every route THE sum of the demands of its customers SHALL NOT exceed `capacity`.
3. FOR every route THE distance `depot → c1 → … → ck → depot` SHALL NOT exceed `max_route_distance`.
4. EVERY route SHALL contain at least one customer.

### Requirement 2 — Low total distance

**User Story:** As a dispatcher, I want the shortest total distance you can find, so fuel and driver time are minimised.

#### Acceptance Criteria
1. THE score of a feasible plan SHALL be `min(1, reference_distance / your_distance)`, where `reference_distance` is the total distance of a fixed, strong (but not optimal) heuristic solution that you cannot see. Matching it gives 1.0; a plan that is 25 % longer scores 0.8.
2. WHEN the plan is not feasible (Requirement 1) THEN its score SHALL be 0.
3. THE evaluation is deterministic and depends only on the submitted routes — running time is not measured, but the plan must be computed by you before you finish.

### Requirement 3 — Output contract

#### Acceptance Criteria
1. THE deliverable SHALL be the file `routes.json` containing exactly: `{{"routes": [[3, 17, 5], [1, 9], ...]}}` — a list of routes, each a list of customer ids in visiting order.
2. THE ids SHALL be integers exactly as given in `instance.json`.

### Requirement 4 — Environment, dependencies, safety
1. Use Python 3.10+ and only the standard library if you write code. No network access is needed or allowed.
2. Do not modify `instance.json`.

## Deliverables and provided files
Deliver `answer/routes.json`. Provided (read-only): `instance.json`.
"""


def dist(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def solve_reference(inst: dict) -> list[list[int]]:
    """Savings de Clarke-Wright + búsqueda local (2-opt intra-ruta, reubicación). Totalmente determinista."""
    depot, Q, D = tuple(inst["depot"]), inst["capacity"], inst["max_route_distance"]
    cust = {c["id"]: (c["x"], c["y"]) for c in inst["customers"]}
    dem = {c["id"]: c["demand"] for c in inst["customers"]}
    ids = sorted(cust)

    def rdist(rt):
        if not rt:
            return 0
        d, p = 0, depot
        for c in rt:
            d += dist(p, cust[c]); p = cust[c]
        return d + dist(p, depot)

    routes = {i: [i] for i in ids}
    where = {i: i for i in ids}
    d0 = {i: dist(depot, cust[i]) for i in ids}
    savings = sorted(((d0[i] + d0[j] - dist(cust[i], cust[j]), i, j) for a, i in enumerate(ids) for j in ids[a + 1:]), key=lambda t: (-t[0], t[1], t[2]))
    for s, i, j in savings:
        if s <= 0:
            break
        ri, rj = where[i], where[j]
        if ri == rj:
            continue
        A, B = routes[ri], routes[rj]
        if sum(dem[c] for c in A) + sum(dem[c] for c in B) > Q:
            continue
        if A[-1] == i and B[0] == j:
            new = A + B
        elif A[0] == i and B[-1] == j:
            new = B + A
        elif A[0] == i and B[0] == j:
            new = A[::-1] + B
        elif A[-1] == i and B[-1] == j:
            new = A + B[::-1]
        else:
            continue
        if rdist(new) > D:
            continue
        routes[ri] = new
        del routes[rj]
        for c in new:
            where[c] = ri
    rts = [routes[k] for k in sorted(routes)]

    for _ in range(60):
        improved = False
        for r_i, rt in enumerate(rts):  # 2-opt intra-ruta
            best = rdist(rt)
            for a in range(len(rt) - 1):
                for b in range(a + 1, len(rt)):
                    cand = rt[:a] + rt[a:b + 1][::-1] + rt[b + 1:]
                    dcand = rdist(cand)
                    if dcand < best:
                        rt, best, improved = cand, dcand, True
            rts[r_i] = rt
        loads = [sum(dem[c] for c in rt) for rt in rts]
        dists = [rdist(rt) for rt in rts]
        moved = False
        for ra in range(len(rts)):  # reubicación de un cliente a la mejor posición (cualquier ruta)
            if moved:
                break
            for pa in range(len(rts[ra])):
                c = rts[ra][pa]
                rem = rts[ra][:pa] + rts[ra][pa + 1:]
                gain_a = dists[ra] - rdist(rem)
                best_delta, best_move = 0, None
                for rb in range(len(rts)):
                    base = rem if rb == ra else rts[rb]
                    if rb != ra and loads[rb] + dem[c] > Q:
                        continue
                    base_d = rdist(base)
                    for pb in range(len(base) + 1):
                        cand = base[:pb] + [c] + base[pb:]
                        dcand = rdist(cand)
                        if dcand > D:
                            continue
                        if rb == ra:
                            delta = dcand - dists[ra]
                        else:
                            delta = (dcand - base_d) - gain_a
                        if delta < best_delta:
                            best_delta, best_move = delta, (rb, cand, rem)
                if best_move:
                    rb, cand, rem = best_move
                    if rb == ra:
                        rts[ra] = cand
                    else:
                        rts[rb] = cand
                        rts[ra] = rem
                    rts = [rt for rt in rts if rt]
                    improved = moved = True
                    break
        if not improved:
            break
    return [rt for rt in rts if rt]


def total_distance(inst: dict, routes) -> int:
    depot = tuple(inst["depot"])
    cust = {c["id"]: (c["x"], c["y"]) for c in inst["customers"]}
    tot = 0
    for rt in routes:
        p = depot
        for c in rt:
            tot += dist(p, cust[c]); p = cust[c]
        tot += dist(p, depot)
    return tot


def generate(tool: Path, hidden: Path, seed: int, level: int) -> None:
    r = rng(seed, ID)
    n = SIZES[level]
    customers = [{"id": i, "x": r.randint(0, 1000), "y": r.randint(0, 1000), "demand": r.randint(1, 30)} for i in range(1, n + 1)]
    inst = {"depot": [500, 500], "capacity": CAPACITY[level], "max_route_distance": MAX_DIST[level], "customers": customers}
    write_json(tool / "instance.json", inst)
    (tool / "TASK.md").write_text(TASK.format(n=n, cap=CAPACITY[level], maxd=MAX_DIST[level]), encoding="utf-8")
    ref = solve_reference(inst)
    naive = total_distance(inst, [[c["id"]] for c in customers])
    write_json(hidden / "ref.json", {"ref_distance": total_distance(inst, ref), "naive_distance": naive})


def evaluate(answer: Path, hidden: Path) -> dict:
    f = answer / "routes.json"
    if not f.exists():
        return fail_report("falta routes.json")
    inst = read_json(answer.parent / "instance.json")
    ref = read_json(hidden / "ref.json")
    try:
        routes = read_json(f)["routes"]
        assert isinstance(routes, list) and all(isinstance(rt, list) and rt and all(type(c) is int for c in rt) for rt in routes)
    except Exception as e:  # noqa: BLE001
        return fail_report(f"formato inválido de routes.json: {type(e).__name__}")
    cust = {c["id"]: c for c in inst["customers"]}
    seen = [c for rt in routes for c in rt]
    problems = []
    if sorted(seen) != sorted(cust):
        missing = sorted(set(cust) - set(seen))[:5]
        extra = sorted(set(seen) - set(cust))[:5]
        dup = sorted({c for c in seen if seen.count(c) > 1})[:5]
        problems.append(f"clientes: faltan={missing} sobran={extra} repetidos={dup}")
    else:
        over = [i for i, rt in enumerate(routes) if sum(cust[c]["demand"] for c in rt) > inst["capacity"]]
        long = [i for i, rt in enumerate(routes) if total_distance(inst, [rt]) > inst["max_route_distance"]]
        if over:
            problems.append(f"capacidad excedida en rutas {over[:5]}")
        if long:
            problems.append(f"distancia máxima excedida en rutas {long[:5]}")
    rep = Report()
    if problems:
        rep.add("factibilidad", False, 1, "; ".join(problems))
        return rep.result()
    cost = total_distance(inst, routes)
    q = min(1.0, ref["ref_distance"] / cost)
    rep.add("factibilidad", True, 1, f"{len(routes)} rutas")
    rep.add("calidad_frente_a_referencia", q, 9,
            f"distancia={cost} referencia={ref['ref_distance']} ingenua={ref['naive_distance']} diferencia={100 * (cost / ref['ref_distance'] - 1):+.1f}%")
    return rep.result()


def reference(tool: Path, hidden: Path, answer: Path) -> None:
    answer.mkdir(parents=True, exist_ok=True)
    write_json(answer / "routes.json", {"routes": solve_reference(read_json(tool / "instance.json"))})
