# CLAS12 ALERT AHDC Gain Calibration — Reproducibility Package

**Location:** `/home/phys_365/cpaudel/NN/TRAINING/ALERT_AHDC_GAIN_CALIBRATION_CLAS12/results/reproducibility_package/`

**Purpose:** This directory contains all files needed to reproduce the complete CLAS12 ALERT AHDC per-wire ADC gain calibration study. 
Anyone can checkout this directory and run the scripts to regenerate all results, plots, and tables from the raw CSV datasets.

---

## 1. Directory Structure

```
reproducibility_package/
├── README.md                                          (this file)
├── GAIN_CALIBRATION_REPORT.md                       (17-item checkpoint report + 17 final report questions)
├── TECHNICAL_NOTE_AHDC_GAIN_CALIBRATION.md          (full methodology and code architecture)
├── tables/                                          (13 summary CSV tables)
├── plots/
│   ├── gains/                                       (global gain plots)
│   ├── closure/                                     (closure residual plots)
│   ├── d2_vs_he4/                                   (D2 vs He4 comparison plots)
│   ├── preselection/                                (pre-calibration 1D/2D distributions)
│   ├── statistics/                                  (momentum window statistics heatmaps)
│   └── per_wire/
│       ├── per_wire_ADC_D2_before.pdf
│       ├── per_wire_ADC_He4_before.pdf
│       ├── per_wire_ADC_D2_after.pdf
│       ├── per_wire_ADC_He4_after.pdf
│       ├── per_wire_ADC_before_after_D2.pdf
│       ├── per_wire_ADC_before_after_He4.pdf
│       └── qa/                                      (5 focused QA PDFs)
└── scripts/                                         (5 analysis Python scripts)
```

---

## 2. Essential CSV Data Files (NOT copied — see paths below)

The raw CSV datasets are **not** included in this package due to their large size (~1.6 GB combined). They must be present on the system for the scripts to work.

**Required CSV paths (must exist on the system):**

| File | Path | Size | Description |
|------|------|------|-------------|
| `D2_ALL_FINAL.csv` | `/home/phys_365/cpaudel/NN/TRAINING/26071/D2_ALL_FINAL.csv` | ~895 MB | Primary D2 extracted CSV dataset |
| `HE4_ALL_FINAL.csv` | `/home/phys_365/cpaudel/NN/TRAINING/26071/He4_ALL_FINAL.csv` | ~733 MB | Primary He4 extracted CSV dataset |

**Symlinked paths (alternative locations, already set up in the workspace):**

| Symlink | Target | Description |
|---------|--------|-------------|
| `FINAL_MERGED/D2_ALL_FINAL.csv` | `../26071/D2_ALL_FINAL.csv` | Convenience symlink |
| `FINAL_MERGED/HE4_ALL_FINAL.csv` | `../26071/He4_ALL_FINAL.csv` | Convenience symlink |

**In the just-completed workspace**, the scripts expect the CSVs at:

```
BASE_DIR / "FINAL_MERGED" / "D2_ALL_FINAL.csv"
BASE_DIR / "FINAL_MERGED" / "HE4_ALL_FINAL.csv"
```

where `BASE_DIR = /home/phys_365/cpaudel/NN/TRAINING/ALERT_AHDC_GAIN_CALIBRATION_CLAS12`.

To make the scripts work from the reproducibility package, either:
1. Keep the CSVs at the above paths, **or**
2. Create symlinks inside the reproducibility package:
   ```bash
   ln -s /home/phys_365/cpaudel/NN/TRAINING/26071/D2_ALL_FINAL.csv ./FINAL_MERGED/D2_ALL_FINAL.csv
   ln -s /home/phys_365/cpaudel/NN/TRAINING/26071/He4_ALL_FINAL.csv ./FINAL_MERGED/HE4_ALL_FINAL.csv
   ```

---

## 3. Reproducibility Workflow

All results can be regenerated from scratch by running the five analysis scripts in order:

```bash
cd /home/phys_365/cpaudel/NN/TRAINING/ALERT_AHDC_GAIN_CALIBRATION_CLAS12/results/reproducibility_package

# Step 1: Data audit, mapping, and momentum window statistics
python3 scripts/01_phase1_phase2_audit.py

# Step 2: Pre-calibration 1D/2D QA plots and channel occupancy maps
python3 scripts/02_phase2_phase3_qa_plots.py

# Step 3: Full 576-channel calibration, gain constants, Option A vs Option B, closure refits
python3 scripts/03_run_full_calibration.py

# Step 4: Global publication-quality plots (gains, closure, D2-vs-He4)
python3 scripts/04_generate_global_plots.py

# Step 5: Per-wire QA package (3,456 PNGs + 6 multi-page PDFs + 5 focused QA PDFs)
python3 scripts/05_generate_per_wire_qa_package.py
```

**Estimated total runtime:** ~3 minutes (steps 1–3) + ~10 minutes (step 4) + ~90 seconds (step 5).

---

## 4. What Each Script Produces

| Script | Key Outputs |
| :--- | :--- |
| `01_phase1_phase2_audit.py` | `tables/global_channel_map_576.csv`, `tables/layer_wire_mapping_audit.csv`, `tables/momentum_window_statistics.csv` |
| `02_phase2_phase3_qa_plots.py` | `plots/preselection/*.png`, `plots/statistics/*.png` |
| `03_run_full_calibration.py` | `tables/gain_constants_D2.csv`, `tables/gain_constants_He4.csv`, `tables/gain_constants_final.csv`, `tables/channel_statistics.csv`, `tables/layer_summary.csv`, `tables/bad_channels.csv`, `tables/d2_he4_comparison.csv`, `tables/reference_option_A_vs_B_comparison.csv` |
| `04_generate_global_plots.py` | `plots/gains/*.png`, `plots/closure/*.png`, `plots/d2_vs_he4/*.png` |
| `05_generate_per_wire_qa_package.py` | `plots/per_wire/per_wire_ADC_{D2,He4}_{before,after}.pdf`, `plots/per_wire/per_wire_ADC_before_after_{D2,He4}.pdf`, `plots/per_wire/qa/*.pdf`, 3,456 individual PNGs |

---

## 5. Output Summary (already generated in the parent workspace)

**CSV Tables (under `results/gain_calibration_final/tables/`):**
- `channel_statistics.csv` (1,152 rows: 576 channels × 2 targets)
- `gain_constants_D2.csv` (576 rows)
- `gain_constants_He4.csv` (576 rows)
- `gain_constants_final.csv` (576 rows) — recommended gains (`recommended_gain_optA` / `recommended_gain_optB`)
- `layer_summary.csv` (16 rows: 8 layers × 2 targets)
- `bad_channels.csv` (235 rows) — uncalibrated / low-stat / excluded channels
- `d2_he4_comparison.csv` (576 rows) — per-channel D2 vs He4 comparison
- `reference_option_A_vs_B_comparison.csv` (4 rows) — Option A global vs Option B per-layer
- `momentum_window_statistics.csv` (28 rows) — per-channel statistics across 14 windows
- `candidate_selection_decision_table.csv` (18 rows) — Phase 4 decision table
- `global_channel_map_576.csv` (576 rows) — deterministic 1–576 channel mapping

**Global Plots:**
- 576-channel multi-page PDFs: `per_wire_ADC_{D2,He4}_{before,after}.pdf` and `per_wire_ADC_before_after_{D2,He4}.pdf`
- 5 focused QA PDFs: `worst_chi2_channels.pdf`, `extreme_gain_channels.pdf`, `low_statistics_channels.pdf`, `d2_he4_discrepant_channels.pdf`, `failed_or_retry_channels.pdf`
- 3,456 individual per-wire PNGs: `plots/per_wire/{D2,He4}/{before,after,before_after}/D2_L{layer}_W{wire:02d}_{stage}.png`
- Global gain, closure, and D2-vs-He4 comparison plots under `plots/gains/`, `plots/closure/`, `plots/d2_vs_he4/`

**Reports:**
- `GAIN_CALIBRATION_REPORT.md` — 17-item checkpoint report + 17 final report questions
- `TECHNICAL_NOTE_AHDC_GAIN_CALIBRATION.md` — full methodology, code architecture, and fit model documentation

---

## 6. Known Dependencies

- Python 3.9+
- `numpy`, `pandas`, `scipy`, `matplotlib`, `scipy.optimize.curve_fit`
- Scripts tested on the just-completed workspace at `/home/phys_365/cpaudel/NN/TRAINING/ALERT_AHDC_GAIN_CALIBRATION_CLAS12/`