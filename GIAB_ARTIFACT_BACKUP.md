# GIAB CYP2D6 Validation Artifacts — Azure Blob Backup

> **Purpose:** a permanent, reproducible record of where the CYP2D6 SV
> validation artifacts (GIAB/1000G BAM slices, StarPhase JSON calls, score
> files, and the pinned StarPhase reference DB) are archived in Azure Blob
> Storage. These are the canonical references for the **Methods / Data
> Availability** section of the CYP2D6/DPYD/warfarin validation paper.
>
> **Created:** 2026-06-17. **Backed up by:** Azure CLI (`az`) from the local
> sandbox, `--auth-mode login`.
> **Source on disk:** `anukriti/data/giab_cyp2d6/` (research/benchmark repo).

---

## 0. TL;DR

All 18 files from `anukriti/data/giab_cyp2d6/` are uploaded to a Standard_LRS
blob container and **size-verified** (byte-exact, 0 mismatches).

| Item | Value |
|---|---|
| Subscription | `Azure subscription 1` (`e64e3da3-a8ef-452e-a709-7d7437e12be9`) |
| Resource group | **`anukriti-lrs-01`** |
| Region | `centralindia` (matches `anukriti-genomics-rg`) |
| Storage account | _[private — contact authors]_ |
| SKU / kind / tier | `Standard_LRS` · `StorageV2` · `Cool` access tier |
| Container | **`giab-cyp2d6-artifacts`** |
| Security | HTTPS-only, TLS 1.2, **public blob access disabled** |
| Base URL | `[private Azure Blob Storage — contact authors]` |

> **Naming caution:** `anukriti-lrs-01` is used here as a **resource group**
> name. In [`AZURE_VM_SETUP.md`](AZURE_VM_SETUP.md) the same string appears as
> a **VM** name inside `anukriti-genomics-rg`. They are different resource
> types in (potentially) different RGs — don't conflate them.

---

## 1. What was backed up

Everything in `anukriti/data/giab_cyp2d6/` (full reproducibility bundle —
per-sample artifacts **plus** the reference data needed to re-run them).

### Per-sample validation artifacts

| Sample | Pop | File | Bytes |
|---|---|---|---|
| **HG01190** | SAS | `HG01190_CYP2D6_GRCh38.bam` (373 reads) | 443,488 |
| HG01190 | SAS | `HG01190.starphase.json` | 13,168 |
| HG01190 | SAS | `hg01190_score.txt` | 452 |
| **HG001 / NA12878** | EUR | `HG001_CYP2D6_GRCh38.bam` | 1,711,311 |
| HG001 | EUR | `HG001_CYP2D6_GRCh38.bam.bai` | 22,480 |
| HG001 | EUR | `HG001_GRCh38.bam.bai` | 10,847,096 |
| HG001 | EUR | `HG001.starphase.json` | 64,860 |
| HG001 | EUR | `NA12878.starphase.json` | 64,860 |
| **HG002** | — | `HG002_CYP2D6_GRCh38.bam` | 1,847,368 |
| HG002 | — | `HG002_CYP2D6_GRCh38.bam.bai` | 22,664 |
| HG002 | — | `HG002_GRCh38.bam.bai` | 23,424,832 |
| HG002 | — | `HG002.starphase.json` | 51,372 |

> No per-sample `HG001_score.txt` or `HG002_score.txt` exists on disk — only
> `hg01190_score.txt` was produced (the scored SAS equity row). The HG001/HG002
> StarPhase results are documented narratively in `STARPHASE_SETUP.md`.

> **`HG001.starphase.json` and `NA12878.starphase.json` are byte-identical**
> (same SHA-256/MD5, both 64,860 B) — HG001 *is* NA12878 (the long-standing
> CEU/Utah reference). They are the **same StarPhase call under two
> filenames**, kept for naming convenience (GIAB ID vs. Coriell/GeT-RM ID).

### Reference / config (pinned, for re-running)

| File | Bytes | What it is |
|---|---|---|
| `pbstarphase_db.json` | 140,686,002 | StarPhase reference DB (v1.4.0, `20250515`) |
| `pbstarphase_db.json.gz` | 12,884,439 | gzipped DB |
| `chr22.fa` | 51,834,845 | GRCh38 chr22 slice (StarPhase reference) |
| `chr22.fa.gz` | 12,255,678 | gzipped chr22 |
| `chr22.fa.fai` | 23 | faidx index |
| `include_cyp2d6.txt` | 7 | StarPhase `--include-set` (literally `CYP2D6`) |

Total: **18 files, ~217 MB**. Storage cost is negligible (~$0.005/month on
LRS Cool).

---

## 2. Permanent Blob URLs (paper Data Availability)

Base: `[private Azure Blob Storage — contact authors]`

```
.../HG01190_CYP2D6_GRCh38.bam
.../HG01190.starphase.json
.../hg01190_score.txt
.../HG001_CYP2D6_GRCh38.bam
.../HG001_CYP2D6_GRCh38.bam.bai
.../HG001_GRCh38.bam.bai
.../HG001.starphase.json
.../NA12878.starphase.json
.../HG002_CYP2D6_GRCh38.bam
.../HG002_CYP2D6_GRCh38.bam.bai
.../HG002_GRCh38.bam.bai
.../HG002.starphase.json
.../pbstarphase_db.json
.../pbstarphase_db.json.gz
.../chr22.fa
.../chr22.fa.gz
.../chr22.fa.fai
.../include_cyp2d6.txt
```

> **Access note:** these URLs are **not anonymously public** (public blob
> access is disabled). To let a reviewer resolve them you need either a
> read-only **SAS token** (see §5) or to mirror the bundle to a public DOI
> (e.g. Zenodo) for the camera-ready paper. Keeping the live Azure copy private
> is intentional — GIAB BAMs and the StarPhase DB are large binaries.

---

## 3. How the backup was created (reproduce / re-run)

Run locally where `az` is logged in (`az login`).

```bash
RG=anukriti-lrs-01
LOC=centralindia
SA=<ACCOUNT>                              # private — contact authors                       # globally unique, lowercase alnum
CONTAINER=giab-cyp2d6-artifacts
SRC=anukriti/data/giab_cyp2d6

# 3a. Resource group (skip if it exists)
az group create -n "$RG" -l "$LOC"

# 3b. Storage account — cheapest durable tier
az storage account create -n "$SA" -g "$RG" -l "$LOC" \
  --sku Standard_LRS --kind StorageV2 --access-tier Cool \
  --min-tls-version TLS1_2 --allow-blob-public-access false

# 3c. Grant yourself data-plane access (required for --auth-mode login).
#     Assign by OBJECT ID — UPN lookup can be blocked by Graph policy.
SCOPE=$(az storage account show -n "$SA" -g "$RG" --query id -o tsv)
OID=$(az ad signed-in-user show --query id -o tsv)   # if blocked, decode 'oid' from `az account get-access-token`
az role assignment create --assignee-object-id "$OID" \
  --assignee-principal-type User \
  --role "Storage Blob Data Contributor" --scope "$SCOPE"

# 3d. Container (RBAC can take ~30-90s to propagate — retry if ContainerNotFound)
az storage container create --name "$CONTAINER" \
  --account-name "$SA" --auth-mode login

# 3e. Upload everything
az storage blob upload-batch \
  --account-name "$SA" --auth-mode login \
  --destination "$CONTAINER" --source "$SRC" --overwrite true
```

### Gotchas encountered (2026-06-17)

- **`az` is Azure-only** — the `use_aws` path does not run Azure CLI; use the
  shell `az` binary directly.
- **Role assignment by UPN failed** (`Cannot find user ... in graph database`).
  Fix: assign by `--assignee-object-id` (resolved via `az ad signed-in-user
  show`, or by decoding the `oid` claim from the access token).
- **RBAC propagation lag** — the first `container create` after the role grant
  can return `ContainerNotFound`/auth errors for ~30–90s; retry.

---

## 4. Verify the backup (size check)

```bash
SA=<ACCOUNT>                              # private — contact authors
CONTAINER=giab-cyp2d6-artifacts
SRC=anukriti/data/giab_cyp2d6

az storage blob list --account-name "$SA" --container-name "$CONTAINER" \
  --auth-mode login \
  --query "[].{name:name,bytes:properties.contentLength}" -o tsv \
| while IFS=$'\t' read -r name rbytes; do
    lbytes=$(stat -c %s "$SRC/$name" 2>/dev/null || echo MISSING)
    [ "$lbytes" = "$rbytes" ] && m=OK || m=MISMATCH
    printf "%-34s %12s %12s  %s\n" "$name" "$lbytes" "$rbytes" "$m"
  done
```

Last verified: **2026-06-17 — 18/18 OK, 0 mismatches.**

> Size match is not a content hash. For stronger paper-grade integrity, also
> store SHA-256 sums (see §5).

---

## 5. Optional hardening (not yet done)

- **Read-only SAS for reviewers** (time-boxed, container-scoped):
  ```bash
  END=$(date -u -d "+365 days" '+%Y-%m-%dT%H:%MZ')
  az storage container generate-sas --account-name <ACCOUNT> \
    --name giab-cyp2d6-artifacts --permissions rl --expiry "$END" \
    --auth-mode login --as-user -o tsv
  # append "?<sas>" to each blob URL
  ```
- **Checksums:** ✅ **done (2026-06-17).** MD5 + SHA-256 computed for all 18
  data files (the two checksum files themselves are excluded — no
  self-hashing), saved locally to `anukriti/data/giab_cyp2d6/` and uploaded to
  the container. Format: standard `<hash>  <filename>` (basenames, sorted).
  - `[private Azure Blob Storage — contact authors]` (18 lines, 1,562 B)
  - `[private Azure Blob Storage — contact authors]` (18 lines, 986 B)

  Verify (after downloading the artifacts + both checksum files into the same dir):
  ```bash
  cd anukriti/data/giab_cyp2d6
  sha256sum -c checksums.sha256 && md5sum -c checksums.md5
  ```
- **DOI mirror:** for the camera-ready, mirror to Zenodo and cite the DOI
  instead of the private Azure URL.

---

## Companion docs

- [`CYP2D6_SV_PIPELINE.md`](CYP2D6_SV_PIPELINE.md) — end-to-end engine/endpoint/benchmark map (what produced these artifacts).
- [`STARPHASE_SETUP.md`](STARPHASE_SETUP.md) — StarPhase install + prebuilt-DB gotcha + the HG001/HG002 scored results.
- [`AZURE_VM_SETUP.md`](AZURE_VM_SETUP.md) — the genomics compute VM (note the `anukriti-lrs-01` name overlap, §0).
- [`RUNG2_CYP2D6_SV_PLAN.md`](RUNG2_CYP2D6_SV_PLAN.md) — the roadmap (Phase A/B′/C).
