"""
Rung-2 Phase B′ — StarPhase → normalize → ingest → score runner.

Turnkey harness for the reframed bake-off (see RUNG2_CYP2D6_SV_PLAN.md §B′):
take a StarPhase diplotype-call file produced from public GIAB long-read
data, canonicalize each CYP2D6 call to PharmVar-standard form, phenotype it
through the deterministic ingestion seam, and score it against the repaired
SV truth set — SV-split and by-population.

This module does NOT run StarPhase (that needs the long-read BAMs + the tool,
an external-compute step). It scores StarPhase *output*. When no output file
is supplied it can still run a self-check against the bundled truth set using
the truth diplotypes as a stand-in, to prove the wiring end-to-end.

StarPhase output format
-----------------------
StarPhase (`pbstarphase diplotype --output-calls calls.json`) emits JSON
keyed by gene, with a diplotype string per gene. Real shape (per the tool's
docs and Deserranno 2025 §2.3) is roughly:

    {
      "CYP2D6": {"diplotype": "*5/*68+*4", ...},
      "CYP2C19": {"diplotype": "*1/*2", ...},
      ...
    }

Per-sample files are mapped to truth `sample_id` either by an explicit
``--sample-map`` (filename → sample_id) or by embedding the sample_id in the
filename (e.g. ``HG01190.starphase.json``). The parser is tolerant of a few
shape variants (``diplotype`` / ``call`` / bare string).

References
----------
- Holt et al. 2024 (bioRxiv 2024.12.10.627527) — StarPhase.
- Deserranno et al. 2025 (Front Pharmacol 16:1653999) — StarPhase on the
  five public GIAB samples (HG001, HG01190, NA19785, HG002, HG005); the
  recipe this runner targets.
- Turner et al. 2023 (CPT 114:1220; PMID 37669183) — SV nomenclature the
  normalizer enforces.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional


def parse_starphase_calls(path: str, gene: str = "CYP2D6") -> Optional[str]:
    """Extract one gene's diplotype string from a StarPhase calls JSON file.

    Tolerant of three shapes for the per-gene value:
      {"CYP2D6": {"diplotype": "*5/*4"}}   -> "*5/*4"
      {"CYP2D6": {"call": "*5/*4"}}        -> "*5/*4"
      {"CYP2D6": "*5/*4"}                  -> "*5/*4"

    Returns None if the file is missing, unparseable, or the gene is absent.
    """
    p = Path(path)
    if not p.is_file():
        return None
    try:
        payload = json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    if not isinstance(payload, dict):
        return None

    # Real StarPhase schema (verified, pbstarphase 1.4.2):
    #   {"gene_details": {"CYP2D6": {
    #       "simple_diplotypes": [{"diplotype": "*2/*4"}],
    #       "diplotypes":        [{"diplotype": "*2.001/*4.015"}], ...}}}
    # Prefer simple_diplotypes (core star alleles) over the suballele form;
    # the normalizer collapses suballeles anyway, but simple is canonical.
    gene_details = payload.get("gene_details")
    if isinstance(gene_details, dict):
        gd = gene_details.get(gene)
        if isinstance(gd, dict):
            for key in ("simple_diplotypes", "diplotypes"):
                seq = gd.get(key)
                if isinstance(seq, list) and seq and isinstance(seq[0], dict):
                    d = seq[0].get("diplotype")
                    if isinstance(d, str) and d:
                        return d

    # Fallback shapes (older/simplified): top-level gene key.
    entry = payload.get(gene)
    if entry is None:
        return None
    if isinstance(entry, str):
        return entry
    if isinstance(entry, dict):
        for key in ("diplotype", "call", "genotype"):
            val = entry.get(key)
            if isinstance(val, str) and val:
                return val
    return None


def discover_starphase_files(
    calls_dir: str,
    sample_ids: List[str],
    sample_map: Optional[Dict[str, str]] = None,
) -> Dict[str, str]:
    """Map truth sample_ids -> StarPhase JSON file paths in `calls_dir`.

    Resolution order per sample_id:
      1. explicit `sample_map` (sample_id -> filename), if provided;
      2. otherwise any *.json file whose name contains the sample_id
         (e.g. "HG01190.starphase.json" matches "HG01190").

    Only returns entries for which a file actually exists. Missing samples
    are simply absent from the result (the scorer treats them as no-call).
    """
    base = Path(calls_dir)
    resolved: Dict[str, str] = {}
    if not base.is_dir():
        return resolved

    json_files = list(base.glob("*.json"))
    for sid in sample_ids:
        if sample_map and sid in sample_map:
            candidate = base / sample_map[sid]
            if candidate.is_file():
                resolved[sid] = str(candidate)
            continue
        for f in json_files:
            if sid in f.name:
                resolved[sid] = str(f)
                break
    return resolved


def score_starphase(
    calls_dir: Optional[str] = None,
    sample_map: Optional[Dict[str, str]] = None,
    self_check: bool = False,
) -> Dict:
    """Score StarPhase CYP2D6 calls against the SV truth set.

    Parameters
    ----------
    calls_dir
        Directory of StarPhase `*.json` call files (one per sample). If None
        or no files resolve, the runner reports zero scored samples unless
        `self_check` is set.
    sample_map
        Optional {sample_id: filename} override for file resolution.
    self_check
        When True and a sample has no StarPhase file, use the truth diplotype
        itself as the "call" — exercises the full normalize→ingest→score
        path end-to-end (must score 1.0) to prove the wiring before real data
        lands. Off by default; never use for a real benchmark number.

    Returns a dict with overall / SV-only / non-SV phenotype concordance, a
    by-population SV breakdown, and per-sample rows (truth vs StarPhase →
    ingested phenotype). Diplotype concordance is reported too, comparing the
    normalized StarPhase diplotype to the normalized truth diplotype.
    """
    from anukriti_pgx_core.phenotype.cyp2d6_sv_ingest import ingest_sv_diplotype
    from anukriti_pgx_core.phenotype.cyp2d6_sv_nomenclature import normalize_diplotype
    from .concordance import normalize_phenotype
    from .getrm_truth import get_truth_for_gene, get_truth_for_gene_by_sv

    all_truth = get_truth_for_gene("CYP2D6")
    sv_ids = {e["sample_id"] for e in get_truth_for_gene_by_sv("CYP2D6", True)}
    sample_ids = [e["sample_id"] for e in all_truth]

    files = discover_starphase_files(calls_dir, sample_ids, sample_map) if calls_dir else {}

    rows: List[Dict] = []
    for e in all_truth:
        sid = e["sample_id"]
        raw_call = parse_starphase_calls(files[sid], "CYP2D6") if sid in files else None
        used_self_check = False
        if raw_call is None and self_check:
            raw_call = e["diplotype"]
            used_self_check = True

        if raw_call is None:
            rows.append({
                "sample_id": sid, "population": e["population"],
                "sv": sid in sv_ids, "truth_diplotype": e["diplotype"],
                "truth_phenotype": e["phenotype"], "starphase_diplotype": None,
                "ingested_phenotype": None, "phenotype_match": None,
                "diplotype_match": None, "status": "no_call",
            })
            continue

        normalized = normalize_diplotype(raw_call)
        call = ingest_sv_diplotype(raw_call, "StarPhase")
        pheno_match = (
            call.phenotype != "indeterminate"
            and normalize_phenotype(call.phenotype) == normalize_phenotype(e["phenotype"])
        )
        dip_match = normalized == normalize_diplotype(e["diplotype"])
        rows.append({
            "sample_id": sid, "population": e["population"], "sv": sid in sv_ids,
            "truth_diplotype": e["diplotype"], "truth_phenotype": e["phenotype"],
            "starphase_diplotype": normalized,
            "ingested_phenotype": call.phenotype,
            "phenotype_match": pheno_match, "diplotype_match": dip_match,
            "status": "self_check" if used_self_check else "scored",
        })

    return _summarize(rows)


def _concordance(rows: List[Dict]) -> Dict:
    """Phenotype + diplotype concordance over the *scored* rows (skip no_call)."""
    scored = [r for r in rows if r["status"] != "no_call"]
    if not scored:
        return {"n": 0, "n_scored": 0, "phenotype_concordance": 0.0,
                "diplotype_concordance": 0.0}
    pheno_ok = sum(1 for r in scored if r["phenotype_match"])
    dip_ok = sum(1 for r in scored if r["diplotype_match"])
    return {
        "n": len(rows),
        "n_scored": len(scored),
        "phenotype_concordance": round(pheno_ok / len(scored), 3),
        "diplotype_concordance": round(dip_ok / len(scored), 3),
    }


def _summarize(rows: List[Dict]) -> Dict:
    """Aggregate per-sample rows into overall / SV / non-SV / by-population."""
    sv_rows = [r for r in rows if r["sv"]]
    nonsv_rows = [r for r in rows if not r["sv"]]
    by_pop: Dict[str, Dict] = {}
    for pop in sorted({r["population"] for r in sv_rows}):
        by_pop[pop] = _concordance([r for r in sv_rows if r["population"] == pop])
    return {
        "tool": "StarPhase",
        "overall": _concordance(rows),
        "sv_only": _concordance(sv_rows),
        "non_sv": _concordance(nonsv_rows),
        "sv_by_population": by_pop,
        "rows": rows,
    }


def format_report(result: Optional[Dict] = None, **kwargs) -> str:
    """Human-readable StarPhase bake-off table."""
    r = result or score_starphase(**kwargs)
    lines = [
        "CYP2D6 StarPhase bake-off (Rung-2 Phase B′)",
        "=" * 60,
        f"{'split':<14}{'scored':>8}{'diplotype':>12}{'phenotype':>12}",
    ]
    for k in ("overall", "non_sv", "sv_only"):
        s = r[k]
        lines.append(
            f"{k:<14}{s['n_scored']:>8}"
            f"{s['diplotype_concordance']:>12.3f}{s['phenotype_concordance']:>12.3f}"
        )
    lines.append("")
    lines.append("SV-only by population (diplotype / phenotype):")
    if r["sv_by_population"]:
        for pop, s in r["sv_by_population"].items():
            lines.append(
                f"  {pop:<5} n={s['n_scored']}  "
                f"{s['diplotype_concordance']:.3f} / {s['phenotype_concordance']:.3f}"
            )
    else:
        lines.append("  (no SV samples scored)")
    lines.append("")
    n_scored = r["overall"]["n_scored"]
    if n_scored == 0:
        lines.append("No StarPhase calls scored. Supply --calls-dir with per-sample")
        lines.append("StarPhase JSON, or pass --self-check to verify the wiring.")
    self_checked = [x for x in r["rows"] if x["status"] == "self_check"]
    if self_checked:
        lines.append(f"NOTE: {len(self_checked)} row(s) used SELF-CHECK (truth as")
        lines.append("stand-in) — not a real benchmark number; wiring proof only.")
    return "\n".join(lines)


def _main(argv: Optional[List[str]] = None) -> int:
    import argparse

    ap = argparse.ArgumentParser(
        description="Score StarPhase CYP2D6 calls vs the SV truth set (Rung-2 B′)."
    )
    ap.add_argument("--calls-dir", default=None,
                    help="Directory of per-sample StarPhase *.json call files.")
    ap.add_argument("--self-check", action="store_true",
                    help="Use truth diplotypes as stand-in calls to verify wiring.")
    args = ap.parse_args(argv)
    print(format_report(calls_dir=args.calls_dir, self_check=args.self_check))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
