"""One-time Phase 8 live API verification against a running uvicorn server."""
import sys

import httpx

BASE = "http://127.0.0.1:8010"
client = httpx.Client(base_url=BASE, timeout=30.0)
failures = []


def check(name, condition, extra=""):
    label = "PASS" if condition else "FAIL"
    print(f"{label} {name}{(' ' + extra) if extra else ''}")
    if not condition:
        failures.append(name)


def make_experiment(name, controls, trials=1):
    created = client.post(
        "/api/v1/research/experiments",
        json={
            "name": name,
            "experiment_type": "DEFENSE_AMPLIFICATION",
            "attack_type": "ddos",
            "attack_intensity": "low",
            "security_controls": controls,
            "duration_seconds": 30,
            "number_of_trials": trials,
        },
    )
    assert created.status_code == 201, created.text
    uuid = created.json()["experiment_uuid"]
    executed = client.post(f"/api/v1/research/experiments/{uuid}/execute")
    assert executed.status_code == 200, executed.text
    runs = client.get(f"/api/v1/research/experiments/{uuid}/runs").json()["items"]
    return uuid, [r["id"] for r in runs]


def main():
    r = client.get("/health")
    check("health endpoint", r.status_code == 200)

    _, baseline_runs = make_experiment("phase8_live_base", [], trials=2)
    _, defense_runs = make_experiment("phase8_live_fw", ["firewall"], trials=2)

    amplified = client.post(
        "/api/v1/research/defense-energy-amplification",
        json={
            "control_name": "firewall",
            "baseline_run_ids": baseline_runs,
            "defense_run_ids": defense_runs,
        },
    )
    check("phase7 amplification computes", amplified.status_code == 201)

    body = {
        "source": "amplification",
        "metric": "additional_defense_energy",
        "hypothesis_test": "wilcoxon_signed_rank",
        "group_by": ["control_name"],
    }
    first = client.post("/api/v1/research/analytics", json=body)
    check("analytics 201", first.status_code == 201, first.text[:120] if first.status_code != 201 else "")
    if first.status_code != 201:
        return
    d1 = first.json()

    second = client.post("/api/v1/research/analytics", json=body)
    d2 = second.json()
    check(
        "deterministic repeat",
        d1["analysis_id"] == d2["analysis_id"]
        and d1["statistics"] == d2["statistics"]
        and d1["hypothesis_test"]["p_value"] == d2["hypothesis_test"]["p_value"]
        and d1["groups"] == d2["groups"],
        d1["analysis_id"],
    )

    fetched = client.get(f"/api/v1/research/analytics/{d1['analysis_id']}")
    check(
        "GET analytics by id",
        fetched.status_code == 200
        and fetched.json()["analysis_id"] == d1["analysis_id"],
    )

    missing = client.get("/api/v1/research/analytics/anl_missing00000")
    check("GET unknown 404", missing.status_code == 404)

    listed = client.get("/api/v1/research/analytics", params={"source": "amplification"})
    check(
        "GET analytics list",
        listed.status_code == 200 and listed.json()["total"] >= 1,
        f"total={listed.json().get('total')}",
    )

    invalid = client.post(
        "/api/v1/research/analytics",
        json={"source": "amplification", "metric": "bogus_metric"},
    )
    check("invalid metric 400", invalid.status_code == 400)

    empty = client.post(
        "/api/v1/research/analytics",
        json={
            "source": "amplification",
            "metric": "additional_defense_energy",
            "filters": {"experiment_id": 999999},
        },
    )
    check("insufficient data 400", empty.status_code == 400)

    level_test = client.post(
        "/api/v1/research/analytics",
        json={
            "source": "amplification",
            "metric": "energy_attack_only",
            "hypothesis_test": "paired_t",
        },
    )
    check("level metric test rejected 400", level_test.status_code == 400)

    wilcoxon = d1["hypothesis_test"]
    check(
        "wilcoxon result numeric",
        wilcoxon is not None
        and wilcoxon["status"] == "ok"
        and wilcoxon["p_value"] is not None
        and 0.0 <= wilcoxon["p_value"] <= 1.0,
        f"p={wilcoxon and wilcoxon['p_value']}",
    )
    check(
        "analysis metadata",
        d1["analysis_version"] == "research_analytics_v1"
        and d1["std_dev_convention"] == "population_standard_deviation_n"
        and d1["measurement_mode"] == "ESTIMATED"
        and any("ESTIMATED" in item for item in d1["limitations"]),
    )
    check(
        "grouped output",
        len(d1["groups"]) == 1 and d1["groups"][0]["group"]["control_name"] == "firewall",
    )

    print(f"TOTAL {len(failures)} failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
