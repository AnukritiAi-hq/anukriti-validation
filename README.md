# Anukriti PGx Engine — CYP2D6 Validation Artifacts

This repository holds the benchmarking script and StarPhase-derived call
outputs used to validate the Anukriti pharmacogenomics interpretation engine
(`anukriti-pgx-core` v0.6.0) on CYP2D6 — the gene whose Poor/Ultrarapid
Metabolizer calls are driven by structural variants. It contains the StarPhase
1.4.2 diplotype call JSONs for three GIAB/GeT-RM reference samples (HG002,
HG001/NA12878, HG01190), the phenotype-concordance score for the South Asian
equity cell (HG01190), MD5/SHA-256 checksums, and the scoring script
(`cyp2d6_starphase_runner.py`) that normalizes each StarPhase call, ingests it
through the deterministic engine, and scores it against the GeT-RM truth set.
These artifacts back the CYP2D6/DPYD/warfarin validation paper (in submission).

## Data deposit (Zenodo)

The full artifact set is archived with a citable DOI:

**https://doi.org/10.5281/zenodo.20727790**

> Publish the Zenodo deposit before relying on this DOI — it is reserved on a
> draft until the record is published.

## Files

| File | What it is |
|---|---|
| `cyp2d6_starphase_runner.py` | StarPhase output → normalize → ingest → score vs GeT-RM truth (SV-split + by-population) |
| `HG001.starphase.json` | StarPhase 1.4.2 CYP2D6 call for HG001/NA12878 (EUR) — byte-identical to NA12878 |
| `HG002.starphase.json` | StarPhase 1.4.2 CYP2D6 call for HG002 |
| `HG01190.starphase.json` | StarPhase 1.4.2 CYP2D6 call for HG01190 (SAS/Gujarati) |
| `hg01190_score.txt` | Phenotype-concordance score for the HG01190 SAS equity cell |
| `checksums.sha256` / `checksums.md5` | Integrity checksums for the full local artifact set |
| `GIAB_ARTIFACT_BACKUP.md` | Provenance + Azure Blob backup manifest |

StarPhase version `1.4.2-f11d33f`, database `v1.4.0-fe124d0`. Overall
phenotype concordance: **1.000 (3/3)**.

## BAM files are intentionally excluded

Raw aligned read data (`.bam` / `.bai`) is **not** included in this repository,
as those derive from external reference samples under their own data use terms.
This repo carries only the StarPhase-derived call outputs, scores, checksums,
and analysis code produced by the authors. The original read data can be
obtained from its sources:

- **HG01190** (1000 Genomes, SAS/Gujarati) — ENA run **`SRR25583344`**
  (ArrayExpress `E-MTAB-15248`), long-read FASTQ.
- **HG001 / HG002** (GIAB) — GIAB FTP
  (`https://ftp-trace.ncbi.nlm.nih.gov/ReferenceSamples/giab/`).

> The `checksums.*` files list hashes for the full local 18-file set (including
> the excluded BAMs) as a provenance record; some entries therefore reference
> files not present in this repo.

## Authors

- Abhimanyu R B (ORCID: [0009-0007-9540-521X](https://orcid.org/0009-0007-9540-521X)), Anukriti AI

## License

Apache 2.0 — see [`LICENSE`](LICENSE).
