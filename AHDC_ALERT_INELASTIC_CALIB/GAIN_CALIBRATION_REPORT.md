# CLAS12 ALERT AHDC Per-Wire ADC Gain Calibration — Final Analysis Report & Technical Note

**Workspace:** `<WORKSPACE_ROOT>`  
**Output Root:** `<WORKSPACE_ROOT>/results/gain_calibration_final/`  
**Datasets Analyzed:**
- `D2_ALL_FINAL.csv` (`5,706,742` valid numeric hit rows across `13` runs `21657–21768`, `2,163` files, `633,355` events; `5,706,738` rows with `ADC > 0`)
- `He4_ALL_FINAL.csv` (`5,408,305` valid numeric hit rows across `25` runs `21459–21782`, `2,693` files, `597,438` events; `5,408,304` rows with `ADC > 0`)

---

## Part I: Mandatory 17-Item Checkpoint Report

1. **Exact CSV paths used:**
   - Primary D2 CSV: `<DATA_DIR>/D2_ALL_FINAL.csv` (`895 MB`), linked into the project workspace at `<WORKSPACE_ROOT>/FINAL_MERGED/D2_ALL_FINAL.csv`.
   - Primary He4 CSV: `<DATA_DIR>/He4_ALL_FINAL.csv` (`733 MB`), linked into the project workspace at `<WORKSPACE_ROOT>/FINAL_MERGED/HE4_ALL_FINAL.csv`.
2. **Exact CSV column list:**
   - All 22 columns in order: `file_index, file, event_index, run, event, trackid, clusterid, pid, prob_2212, p_GeV, dEdx, nhits, chi2, superlayer, local_layer, raw_layer, wire, adc_sector, adc_order, wfType, ToT, ADC`.
3. **Total row count for D2 and He4:**
   - `D2_ALL_FINAL.csv`: `5,706,745` total lines (`1` header + `5,706,744` data lines). Exactly `2` lines (`5422582` and `5440678`) are parallel-job concatenation splices with `>22` fields; `5,706,742` rows are clean 22-column numeric rows (`4` rows have `ADC == 0`, leaving `5,706,738` clean `ADC > 0` hit rows). Zero exact duplicate rows exist.
   - `He4_ALL_FINAL.csv`: `5,408,308` total lines (`1` header + `5,408,307` data lines). Exactly `2` lines (`5138881` mid-line splice, `5408308` truncated EOF) have bad field counts and `1` row has a non-numeric field, leaving `5,408,305` clean 22-column numeric rows (`1` row has `ADC == 0`, leaving `5,408,304` clean `ADC > 0` hit rows). Zero exact duplicate rows exist.
4. **Distinct runs/files/events in D2 and He4:**
   - **D2:** `13` runs (`21657, 21660, 21661, 21662, 21663, 21708, 21709, 21710, 21712, 21737, 21765, 21766, 21768`), `2,163` distinct HIPO files, `633,355` distinct `(run, event)` pairs, `651,701` distinct `(run, event, trackid)` tracks.
   - **He4:** `25` runs (`21459, 21462, 21465, 21466, 21467, 21468, 21512, 21521, 21523, 21524, 21526, 21527, 21529, 21530, 21532, 21533, 21536, 21552, 21555, 21556, 21777, 21779, 21780, 21781, 21782`), `2,693` distinct HIPO files, `597,438` distinct `(run, event)` pairs, `611,039` distinct `(run, event, trackid)` tracks.
5. **Confirmation of how `raw_layer` relates to `superlayer` and `local_layer`:**
   - Verified across 100% of rows in both D2 (`5,706,742/5,706,742`) and He4 (`5,408,305/5,408,305`): `raw_layer == 10 * superlayer + local_layer` with **zero mismatches** (`superlayer` $\in \{1,2,3,4,5\}$, `local_layer` $\in \{1,2\}$, yielding the 8 physical layers `11, 21, 22, 31, 32, 41, 42, 51`).
6. **Table of expected vs observed wire counts per layer for D2 and He4:**

| Physical Layer | Superlayer | Local Layer | Expected Wires (`1..N`) | D2 Populated (All $p$) | D2 Populated ($0.15\text{–}0.25\text{ GeV}$) | He4 Populated (All $p$) | He4 Populated ($0.15\text{–}0.25\text{ GeV}$) | D2 Inactive Wires (DAQ Sector Masked in Runs $\ge 21552$) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **11** | 1 | 1 | 47 (`1..47`) | 41 | 41 | 47 | 47 | `42..47` (6 wires) |
| **21** | 2 | 1 | 56 (`1..56`) | 46 | 46 | 56 | 56 | `1`, `48..56` (10 wires) |
| **22** | 2 | 2 | 56 (`1..56`) | 47 | 46 | 56 | 55 | `48..56` (9 wires; `W01` has 2 hits outside window) |
| **31** | 3 | 1 | 72 (`1..72`) | 61 | 60 | 72 | 72 | `62..72` (11 wires; `W01` has 2 hits outside window) |
| **32** | 3 | 2 | 72 (`1..72`) | 63 | 61 | 72 | 72 | `64..72` (9 wires; `W62, W63` have 1–4 hits outside window) |
| **41** | 4 | 1 | 87 (`1..87`) | 72 | 72 | 87 | 87 | `73..87` (15 wires) |
| **42** | 4 | 2 | 87 (`1..87`) | 73 | 73 | 87 | 87 | `75..87` (13 wires; `W74` has 1 hit in window) |
| **51** | 5 | 1 | 99 (`1..99`) | 86 | 85 | 99 | 99 | `1..2`, `88..99` (14 wires; `W87` has 1 hit outside window) |
| **Total** | **1–5** | **1–2** | **576** | **489** | **484** | **576** | **575** | **87 completely empty channels in D2 (`0/87` in He4)** |

7. **Summary of extractor cuts verified from `dump_p0v12_AHDC_ATOF_GAIN_ALLRUNS.groovy` / CSV empirical audit:**
   - `pid == 2212` (100% of rows), `prob_2212 >= 0.238` (`[0.238, 1.000]`), `clusterid >= 0` (track-associated cluster hit), `nhits >= 8` (`[8, 19]`), `chi2 <= 50.0` (`[0.025, 50.0]`), `0.02 < p_GeV <= 0.60`, `adc_sector == 1`, `adc_order == 0`, `wfType` $\in \{0, 1, 2\}$, `300 <= ToT <= 750`, `ADC >= 0`.
8. **Momentum-window statistics table:**
   - Saved in full (`28 rows`) at `results/gain_calibration_final/tables/momentum_window_statistics.csv`. Key summary rows:
     - `0.02–0.07 GeV` (old D2 window): D2 has only `64/576` channels with $N \ge 80$ (`0` with $N \ge 200$, median entries `19.0`); He4 has `0/576` channels with $N \ge 80$ (median entries `9.0`).
     - `0.02–0.08 GeV` (old He4 window): D2 has `288/576` channels with $N \ge 80$ (median `79.5`); He4 has `129/576` channels with $N \ge 80$ (`4` with $N \ge 200$, median `38.0`).
     - `0.15–0.25 GeV` (**selected window**): D2 has `484` populated channels, **`440` with $N \ge 80$**, `413` with $N \ge 200$, `398` with $N \ge 500$, `349` with $N \ge 1000$, median entries **`2,048.0`**; He4 has `575` populated channels, **`553` with $N \ge 80$**, `534` with $N \ge 200$, `510` with $N \ge 500$, `481` with $N \ge 1000$, median entries **`2,457.5`**.
9. **Candidate selection decision table and chosen final calibration selection:**
   - Saved at `results/gain_calibration_final/tables/candidate_selection_decision_table.csv`.
   - **Chosen Final Calibration Selection:** `0.15 <= p_GeV <= 0.25 GeV` with `ADC > 0` (retaining all `pid == 2212` track-associated AHDC hits extracted in the CSVs). This window lies in the clean proton ionization regime above the low-momentum saturation/threshold region (`p < 0.10 GeV`) and below the high-momentum relativistic plateau (`p > 0.30 GeV`), increasing median per-wire statistics by **>60x** relative to `0.02–0.08 GeV` while avoiding `dE/dx` selection bias (since `dE/dx` is itself derived from uncalibrated AHDC cluster ADC).
10. **Exact per-wire fit model and fit procedure:**
    - **Primary Model (3-parameter Moyal Landau parameterized by exact peak `MPV`):**
      $$f_{\text{L}}(A; A_0, \text{MPV}, w) = A_0 \exp\!\left[-\frac{1}{2}\left(z + e^{-z} - 1\right)\right], \qquad z = \frac{A - \text{MPV}}{w}$$
      where $f_{\text{L}}(\text{MPV}) = A_0$ and $\left.\frac{\partial f_{\text{L}}}{\partial A}\right|_{A=\text{MPV}} = 0$ identically.
    - **Extended Model (4-parameter Scale-Invariant Landau + Exponential Tail):**
      $$f_{\text{LE}}(A; A_0, \text{MPV}, w, f_{\text{exp}}) = A_0 \left[(1 - f_{\text{exp}})\exp\!\left(-\frac{1}{2}(z + e^{-z} - 1)\right) + f_{\text{exp}}\exp\!\left(-\frac{1}{2}(u + e^{-u} - 1)\right)\right], \qquad u = \frac{A - \text{MPV}}{2.2\,w}$$
      Both components have zero first derivative and negative second derivative at $A = \text{MPV}$, so $A = \text{MPV}$ is the **exact analytical global maximum** for all $f_{\text{exp}} \in [0, 0.65]$, while the second component provides an exponential tail with decay constant $4.4\,w$ to capture high-ADC ionization/avalanche tails.
    - **Two-Stage Quantile-Anchored Bounded Fitting & Retry Procedure:**
      1. Common detector binning: $\Delta A = 35\text{ ADC}$ ($N \ge 300$), $50\text{ ADC}$ ($140 \le N < 300$), or $70\text{ ADC}$ ($80 \le N < 140$) on $[0, 3500]\text{ ADC}$ ($[0, 4900]\text{ ADC}$ if $q_{50} \ge 1200$).
      2. Channels with $N = 0$ are flagged `NO_DATA`; $0 < N < 80$ are flagged `LOW_STAT`; $q_{50} < 180\text{ ADC}$ (collapsed preamplifier noise-floor channels) are flagged `MPV_OUTLIER`.
      3. **Stage 1:** Fit $f_{\text{L}}$ over the quantile-anchored window $[0.24\,q_{50}, 1.95\,q_{50}]$ (above the low-ADC threshold turn-on roll-off) with bounds $\text{MPV} \in [0.22\,q_{50}, 0.92\,q_{50}]$ and $w \in [0.06\,q_{50}, 1.45\,q_{50}]$ to obtain $\text{MPV}_1, w_1$.
      4. **Stage 2:** Fit $f_{\text{L}}$ over the refined peak-and-slope window $[0.38\,\text{MPV}_1, 2.45\,\text{MPV}_1]$ with Poisson weights $\sigma_i = \sqrt{\max(y_i, 1)}$.
      5. **Automated Retry:** If Stage 2 exhibits $\chi^2/\text{ndf} > 1.60$, relative MPV uncertainty $\sigma_{\text{MPV}}/\text{MPV} > 16\%$, or parameter-bound proximity ($<1.5\%$ of bound span), retry across candidate windows (`[0.16*q50, 2.00*q50]`, `[0.18*q50, 2.15*q50]`, `[0.20*q50, 2.20*q50]`, `[0.14*q50, 1.90*q50]`) testing both Pure Landau ($f_{\text{L}}$) and Landau + Exponential ($f_{\text{LE}}$). Converged retry fits are labeled `RETRY_GOOD`.
11. **Count of channels in each fit-status category for D2 and He4:**

| Fit Status Category | D2 Channels (`/576`) | D2 Fraction (`%`) | He4 Channels (`/576`) | He4 Fraction (`%`) | Meaning / Physical Interpretation |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **`GOOD`** | **310** | 53.8% | **427** | 74.1% | Converged in primary two-stage Landau fit, well inside bounds, $\chi^2/\text{ndf} \le 3.5$, $\sigma_{\text{MPV}}/\text{MPV} \le 20\%$ |
| **`RETRY_GOOD`** | **78** | 13.5% | **92** | 16.0% | Converged via automated window/Landau+Exp retry (`54` Landau+Exp in D2, `79` Landau+Exp in He4) |
| **Total Calibrated (`GOOD` + `RETRY_GOOD`)** | **388** | **67.4%** (88.2% of $N\ge 80$) | **519** | **90.1%** (93.9% of $N\ge 80$) | Valid channels used for `MPV_reference`, gain derivation, and closure |
| **`NO_DATA`** | 92 | 16.0% | 1 | 0.2% | Zero hits in `0.15–0.25 GeV` (`87` D2 wires masked in DAQ for runs $\ge 21552$; `5` D2 wires & `1` He4 wire `L22 W53` empty in window) |
| **`LOW_STAT`** | 44 | 7.6% | 22 | 3.8% | $0 < N < 80$ in `0.15–0.25 GeV` (insufficient entries for reliable Landau fit) |
| **`MPV_OUTLIER`** | 17 | 3.0% | 3 | 0.5% | Collapsed low-ADC hardware noise floor ($q_{50} < 180\text{ ADC}$, e.g. `med_ADC ~ 42–97 ADC` dead/attenuated preamp) |
| **`MPV_BOUNDARY_HIT`** | 16 | 2.8% | 12 | 2.1% | Fitted MPV within $1.5\%$ of lower/upper parameter bound (broad/threshold-dominated spectrum) |
| **`WIDTH_BOUNDARY_HIT`** | 0 | 0.0% | 2 | 0.3% | Fitted width within $1.5\%$ of parameter bound |
| **`UNSTABLE`** | 10 | 1.7% | 17 | 3.0% | Relative MPV uncertainty $\sigma_{\text{MPV}}/\text{MPV} > 20\%$ (flat peak) |
| **`BAD_CHI2`** | 7 | 1.2% | 0 | 0.0% | Reduced $\chi^2/\text{ndf} > 3.5$ after retry |
| **`FIT_FAILED`** | 2 | 0.3% | 0 | 0.0% | Optimizer did not converge |

12. **Comparison of Reference MPV Option A (Global) and Option B (Per-Layer):**
    - Saved at `results/gain_calibration_final/tables/reference_option_A_vs_B_comparison.csv`.
    - **Option A (Global Robust Median `MPV_reference`):**
      - **D2:** $\text{MPV}_{\text{ref}}^{\text{Option A}} = \mathbf{334.90\text{ ADC}}$ (10–90% trimmed mean $= 357.38\text{ ADC}$, Huber M-estimator $= 349.12\text{ ADC}$). Across the 388 calibrated channels (`381` good closure refits), MPV dispersion drops from **$\text{std} = 157.92\text{ ADC}$, $\text{MAD} = 82.29\text{ ADC}$, $\text{IQR} = 135.82\text{ ADC}$, $\text{CV} = 41.28\%$** before calibration to **$\text{std} = 21.98\text{ ADC}$, $\text{MAD} = 10.17\text{ ADC}$, $\text{IQR} = 13.57\text{ ADC}$, $\text{CV} = 6.53\%$** after calibration!
      - **He4:** $\text{MPV}_{\text{ref}}^{\text{Option A}} = \mathbf{386.08\text{ ADC}}$ (10–90% trimmed mean $= 416.89\text{ ADC}$, Huber M-estimator $= 404.95\text{ ADC}$). Across the 519 calibrated channels (`508` good closure refits), MPV dispersion drops from **$\text{std} = 145.68\text{ ADC}$, $\text{MAD} = 93.02\text{ ADC}$, $\text{IQR} = 180.80\text{ ADC}$, $\text{CV} = 33.12\%$** before calibration to **$\text{std} = 26.10\text{ ADC}$, $\text{MAD} = 12.67\text{ ADC}$, $\text{IQR} = 16.92\text{ ADC}$, $\text{CV} = 6.76\%$** after calibration!
    - **Option B (Per-Layer Robust Median `MPV_reference(layer)`):**
      - **D2:** Layer reference MPVs are `290.4, 297.5, 306.8, 297.5, 303.5, 315.0, 397.0, 482.4 ADC` for layers `11..51`. Within each layer, wire-to-wire MAD drops from `30–100 ADC` to `7.4–19.6 ADC` (`closure_median_abs_residual = 2.36%`), while global post-calibration $\text{CV} = 22.10\%$ because Option B intentionally preserves the higher average ADC of outer layers `42` and `51` (which have larger drift cell radii and longer track path lengths per layer).
      - **He4:** Layer reference MPVs are `357.2, 355.2, 360.2, 338.3, 358.3, 354.1, 493.8, 668.8 ADC` for layers `11..51`. Within each layer, wire-to-wire MAD drops from `42–113 ADC` to `8.8–19.3 ADC` (`closure_median_abs_residual = 2.53%`), while global post-calibration $\text{CV} = 29.21\%$.
    - **Recommendation:** **Option A (Global Reference)** is recommended as the primary gain table when downstream reconstruction expects a uniform ADC scale across all 8 layers (`ADC_corrected` peaked at a single detector-wide reference MPV), whereas **Option B (Per-Layer Reference)** is provided in parallel in `gain_constants_final.csv` for reconstruction algorithms that already apply a geometric path-length / cell-size correction by layer.
13. **Before/After MPV Dispersion and True Second-Pass Closure Metrics:**
    - Every corrected histogram was refilled from row-level `ADC_corrected = ADC_raw * gain_wire` and refit independently from scratch:
      - **D2 (Option A, 381 refit channels):** $\text{median }|\Delta\text{MPV}/\text{MPV}_{\text{ref}}| = \mathbf{2.02\%}$, $\text{MAD} = \mathbf{3.04\%}$, $\text{RMS} = \mathbf{6.58\%}$; global MPV MAD reduced by **8.09x** (`82.29 -> 10.17 ADC`) and CV reduced by **6.32x** (`41.28% -> 6.53%`).
      - **He4 (Option A, 508 refit channels):** $\text{median }|\Delta\text{MPV}/\text{MPV}_{\text{ref}}| = \mathbf{2.21\%}$, $\text{MAD} = \mathbf{3.28\%}$, $\text{RMS} = \mathbf{6.76\%}$; global MPV MAD reduced by **7.34x** (`93.02 -> 12.67 ADC`) and CV reduced by **4.90x** (`33.12% -> 6.76%`).
14. **D2 vs He4 Correlation and Difference Metrics:**
    - Across **`380` common calibrated channels** (`GOOD` or `RETRY_GOOD` in both D2 and He4):
      - Pre-calibration MPV correlation: **Pearson $r = 0.599$**, **Spearman $\rho = 0.745$**.
      - Derived Gain (Option A) correlation: **Pearson $r = 0.743$**, **Spearman $\rho = 0.745$**.
      - Gain difference $\Delta g = g_{\text{D2}} - g_{\text{He4}}$: **$\text{median} = +0.0056$**, **$\text{MAD} = 0.1469$**, **$\text{RMS} = 0.1932$**.
      - Gain ratio $g_{\text{D2}} / g_{\text{He4}}$: **$\text{median} = 1.0060$**, **$\text{MAD} = 0.1492$**, **$\text{IQR} = 0.2030$**.
      - Normalized Pull $(g_{\text{D2}} - g_{\text{He4}})/\sqrt{\sigma_{g,\text{D2}}^2 + \sigma_{g,\text{He4}}^2}$: **$\text{median} = +0.07\sigma$**, **$\text{MAD} = 1.48\sigma$**.
      - Out of the 380 common channels, **`341` (89.7%)** are statistically compatible (`COMPATIBLE`), while **`39` (10.3%)** exhibit a genuine run-period hardware gain shift between early He4 runs (`21459–21536`) and late D2 runs (`21657–21768`) (`RUN_PERIOD_GAIN_DRIFT`).
15. **Count and List of Bad / Low-Stat / Excluded Channels:**
    - Saved in full (`235 rows` where either D2 or He4 is not `GOOD`/`RETRY_GOOD`) at `results/gain_calibration_final/tables/bad_channels.csv`.
    - Across the combined 576-channel detector map (`gain_constants_final.csv`):
      - **`527 / 576` channels (91.5%)** are successfully calibrated (`341 CALIBRATED_BOTH` compatible + `39 CALIBRATED_RUN_DRIFT` + `139 CALIBRATED_HE4_ONLY` + `8 CALIBRATED_D2_ONLY`).
      - **`49 / 576` channels (8.5%)** are `UNCALIBRATED` (`recommended_gain = NaN`, never silently set to `1.0`):
        - `1` channel with `NO_DATA` in both D2 and He4 in `0.15–0.25 GeV`: `L22 W53` (`#150`, only 3 hits in He4 at $p < 0.15\text{ GeV}$).
        - `22` channels with `LOW_STAT` ($N < 80$) in He4 and `NO_DATA`/`LOW_STAT`/`OUTLIER` in D2: `#005 L11 W05`, `#009 L11 W09`, `#048 L21 W01`, `#053 L21 W06`, `#054 L21 W07`, `#104 L22 W01`, `#109 L22 W06`, `#115 L22 W12`, `#127 L22 W24`, `#156 L22 W53`, `#160 L31 W01`, `#166 L31 W07`, `#167 L31 W08`, `#198 L31 W39`, `#222 L31 W63`, `#226 L31 W67`, `#269 L32 W38`, `#294 L32 W63`, `#297 L32 W66`, `#376 L41 W73`, `#478 L51 W01`, `#479 L51 W02`.
        - `3` channels with hardware `MPV_OUTLIER` (collapsed low-ADC noise floor in both datasets): `#254 L32 W23` ($\text{med ADC} = 68$), `#278 L32 W47` ($\text{med ADC} = 97$), `#364 L41 W61` ($\text{med ADC} = 53$).
        - `23` channels where He4 had `UNSTABLE`/`MPV_BOUNDARY_HIT`/`WIDTH_BOUNDARY_HIT` and D2 was uncalibrated (`NO_DATA`/`LOW_STAT`/`UNSTABLE`).
16. **Exact Output File Paths for All PDFs, Plots, Tables, Scripts, and Report:**
    - Documented in Section III below (all verified on disk under `<WORKSPACE_ROOT>/results/gain_calibration_final/`).
17. **Final Recommended Calibration Strategy:**
    - Deploy `tables/gain_constants_final.csv` (`recommended_gain_optA` for uniform detector-wide ADC normalization to `MPV_ref`, or `recommended_gain_optB` if reconstruction applies an independent layer cell-size normalization).
    - Because 87 azimuthal sector wires were masked in DAQ starting at run `21552` and 14–39 front-end channels experienced preamplifier attenuation/gain shifts between early He4 runs (`21459–21536`) and late D2/He4 runs (`21552–21782`), **CCDB run-range splitting** is recommended:
      - **Run Range `21459–21536` (Early He4 period, all 576 wires active):** Use `gain_He4_optA` (or `recommended_gain_optA` where `gain_He4_optA` is valid; covers `519/576` wires directly).
      - **Run Range `21552–21782` (Late He4 and all D2 runs):** Use `gain_D2_optA` for the 388 D2-calibrated wires (or `recommended_gain_optA` inverse-variance combined gain for the 341 compatible wires and `gain_D2_optA` for the 39 run-drift wires), while explicitly masking the 87 DAQ-inactive high-wire channels and the 17 dead-preamp `MPV_OUTLIER` wires in reconstruction.
      - Never substitute `gain = 1.0` for the 49 `UNCALIBRATED` channels without passing their `calibration_status = UNCALIBRATED` quality flag to the track/cluster dE/dx reconstructor so their hits are excluded from truncated-mean `dE/dx` calculation.

---

## Part II: Answers to All 17 Final Report Questions

1. **What exact cuts and conventions were used by the HIPO extractor?**
   - Every row in `D2_ALL_FINAL.csv` and `He4_ALL_FINAL.csv` represents a single AHDC wire hit belonging to a reconstructed ALERT track identified as a proton (`pid == 2212`, `prob_2212 >= 0.238`, `clusterid >= 0`, `nhits >= 8`, `chi2 <= 50.0`, `0.02 < p_GeV <= 0.60`), with valid pulse-shape/time-over-threshold (`wfType in {0, 1, 2}`, `300 <= ToT <= 750 ns`) and `raw_layer = 10 * superlayer + local_layer`.
2. **Are `D2_ALL_FINAL.csv` and `He4_ALL_FINAL.csv` complete, clean, and consistent?**
   - Both files are complete (`13` runs in D2, `25` runs in He4) with zero duplicate rows. Each file had `2` parallel-concatenation spliced lines (plus `1` non-numeric line in He4) from batch merging, which our parser (`on_bad_lines="skip"` + numeric coercion) cleanly filters out, leaving `5,706,738` (`ADC > 0`) rows in D2 and `5,408,304` (`ADC > 0`) rows in He4.
3. **How are the 576 physical channels indexed and mapped?**
   - Mapped deterministically by ascending `(layer, wire)` across the 8 physical layers `11 (47), 21 (56), 22 (56), 31 (72), 32 (72), 41 (87), 42 (87), 51 (99)`, yielding global channel indices `1..576` (`tables/global_channel_map_576.csv`).
4. **How many channels are populated in the full CSVs and in each momentum window?**
   - Across all momenta (`0.02–0.60 GeV`), He4 populates **all `576/576` channels** while D2 populates **`489/576` channels** (`87` high-wire-number channels were masked in DAQ starting at run `21552`). In the selected calibration window (`0.15 <= p_GeV <= 0.25 GeV`), He4 populates **`575/576`** channels (`553` with $N \ge 80$) and D2 populates **`484/576`** channels (`440` with $N \ge 80$).
5. **Why did the old `0.02–0.07` / `0.02–0.08 GeV` windows fail or underperform?**
   - Because reconstructed ALERT tracks with `nhits >= 8` have a steep momentum acceptance turn-on around `p ~ 0.08–0.10 GeV`: only `0.34%` of D2 hits and `0.15%` of He4 hits have `p <= 0.07 GeV`. In `0.02–0.07 GeV`, He4 has **zero** wires with $N \ge 80$ (median `9` hits/wire) and D2 has only `64/576` wires with $N \ge 80$ (median `19` hits/wire). Furthermore, at $p < 0.08\text{ GeV}$, heavy ionization causes pulse-shape saturation (`wfType = 1` overflow), distorting the Landau peak.
6. **What final calibration selection was chosen, and why?**
   - `0.15 <= p_GeV <= 0.25 GeV` with `ADC > 0`. This window provides **1.79 million hits in D2** (`median = 2,048 hits/wire`, `440` wires with $N \ge 80$) and **1.79 million hits in He4** (`median = 2,457.5 hits/wire`, `553` wires with $N \ge 80$), sits in a clean proton energy-loss regime where the Landau peak (`~335–386 ADC`) is well-separated from both the hardware threshold (`~60 ADC`) and ADC saturation (`>3000 ADC`), and avoids circular selection bias from cutting on uncalibrated `dE/dx`.
7. **What fit model, range, binning, initialization, bounds, and retry rules were used?**
   - Two-stage quantile-anchored bounded fitting using the exact-mode Moyal Landau function $f_{\text{L}}(A; A_0, \text{MPV}, w)$ in Stage 1 (`[0.24*q50, 1.95*q50]`) and Stage 2 (`[0.38*MPV1, 2.45*MPV1]`), with automated retry over alternative windows (`[0.16*q50, 2.00*q50]`, `[0.18*q50, 2.15*q50]`, `[0.20*q50, 2.20*q50]`, `[0.14*q50, 1.90*q50]`) and the 4-parameter scale-invariant Landau + Exponential-tail model $f_{\text{LE}}(A; A_0, \text{MPV}, w, f_{\text{exp}})$ when $\chi^2/\text{ndf} > 1.60$, relative error $>16\%$, or boundary proximity occurs.
8. **How many channels achieved `GOOD`, `RETRY_GOOD`, `LOW_STAT`, `FIT_FAILED`, etc.?**
   - **D2:** `310 GOOD`, `78 RETRY_GOOD` (`388` calibrated = `88.2%` of $N \ge 80$ channels; `92.0%` of the `423` non-dead $N \ge 80$ channels), `92 NO_DATA`, `44 LOW_STAT`, `17 MPV_OUTLIER`, `16 MPV_BOUNDARY_HIT`, `10 UNSTABLE`, `7 BAD_CHI2`, `2 FIT_FAILED`.
   - **He4:** `427 GOOD`, `92 RETRY_GOOD` (`519` calibrated = `93.9%` of $N \ge 80$ channels; `94.4%` of the `550` non-dead $N \ge 80$ channels), `1 NO_DATA`, `22 LOW_STAT`, `3 MPV_OUTLIER`, `12 MPV_BOUNDARY_HIT`, `2 WIDTH_BOUNDARY_HIT`, `17 UNSTABLE`, `0 BAD_CHI2`, `0 FIT_FAILED`.
9. **Were any MPVs near `~500 ADC` or any other value caused by fit-boundary clipping?**
   - **No.** In earlier naive studies, a hard upper/lower bound at `500 ADC` caused artificial pile-up at `MPV = 500 ADC`. In our study, bounds are anchored dynamically to each wire's sample median $q_{50}$, and any fit within $1.5\%$ of a parameter bound is explicitly flagged as `MPV_BOUNDARY_HIT` (`16` in D2, `12` in He4) and excluded from `MPV_reference` and gain tables. Inspection of `plots/gains/gain_distributions_and_uncertainties.png` confirms a smooth, unimodal MPV distribution with zero boundary spikes.
10. **How do Option A (global reference MPV) and Option B (per-layer reference MPV) compare?**
    - Option A equalizes all 576 channels to a single detector-wide reference ($\text{MPV}_{\text{ref}} = 334.90\text{ ADC}$ in D2, $386.08\text{ ADC}$ in He4), reducing global post-calibration MPV CV to **6.53% (D2)** and **6.76% (He4)**. Option B equalizes wires within each layer to that layer's median MPV (`~290–315 ADC` in inner layers `11–41`, `~397–494 ADC` in layer `42`, `~482–669 ADC` in layer `51`), achieving equally tight within-layer closure (`median |res| = 2.36%` in D2, `2.53%` in He4) while preserving the geometric cell-size progression across layers.
11. **What is the true second-pass refit closure performance?**
    - Under true row-level scaling, histogram refilling, and blind second-pass refitting (`Option A`), the fractional residual $(\text{MPV}_{\text{after}} - \text{MPV}_{\text{ref}})/\text{MPV}_{\text{ref}}$ has:
      - **D2 (`381` channels):** $\text{median }|\text{residual}| = \mathbf{2.02\%}$, $\text{MAD} = \mathbf{3.04\%}$, $\text{RMS} = \mathbf{6.58\%}$.
      - **He4 (`508` channels):** $\text{median }|\text{residual}| = \mathbf{2.21\%}$, $\text{MAD} = \mathbf{3.28\%}$, $\text{RMS} = \mathbf{6.76\%}$.
12. **How much does calibration reduce wire-to-wire MPV dispersion?**
    - **D2 (Option A):** Standard deviation drops from **$157.92\text{ ADC} \to 21.98\text{ ADC}$** ($7.19\times$ reduction), MAD drops from **$82.29\text{ ADC} \to 10.17\text{ ADC}$** ($8.09\times$ reduction), IQR drops from **$135.82\text{ ADC} \to 13.57\text{ ADC}$** ($10.01\times$ reduction), and CV drops from **$41.28\% \to 6.53\%$** ($6.32\times$ reduction).
    - **He4 (Option A):** Standard deviation drops from **$145.68\text{ ADC} \to 26.10\text{ ADC}$** ($5.58\times$ reduction), MAD drops from **$93.02\text{ ADC} \to 12.67\text{ ADC}$** ($7.34\times$ reduction), IQR drops from **$180.80\text{ ADC} \to 16.92\text{ ADC}$** ($10.68\times$ reduction), and CV drops from **$33.12\% \to 6.76\%$** ($4.90\times$ reduction).
13. **How well do D2 and He4 gains agree?**
    - Across the `380` common calibrated wires, Option A gains show **Pearson $r = 0.743$** and **Spearman $\rho = 0.745$**, with zero systematic offset ($\text{median}(g_{\text{D2}} - g_{\text{He4}}) = +0.0056$, $\text{median}(g_{\text{D2}}/g_{\text{He4}}) = 1.0060$, $\text{MAD}(\Delta g) = 0.1469$, pull median $= +0.07\sigma$).
14. **Should final gains be target-specific, He4-primary, D2-primary, or combined?**
    - For a single static calibration table, the **combined inverse-variance weighted average** (`recommended_gain_optA` in `gain_constants_final.csv`, supplemented by `HE4_ONLY` for the 139 channels where D2 was masked/low-stat and `D2_ONLY` for 8 channels) provides **`527 / 576` (91.5%)** calibrated channels. For run-dependent CCDB deployment, splitting into **early run period (`21459–21536`, using `gain_He4_optA`)** and **late run period (`21552–21782`, using `gain_D2_optA` / combined)** properly accounts for the 39 wires with run-period preamplifier drift and the 87 wires masked in DAQ after run `21552`.
15. **Which channels are bad, noisy, dead, or uncalibratable?**
    - `87` high-wire channels masked in DAQ for runs $\ge 21552$ (calibrated in He4 early runs, empty in D2); `17` dead/attenuated preamplifier wires in D2 (`3` in He4: `L32 W23, L32 W47, L41 W61`, plus `14` that degraded between run `21536` and `21552` such as `L11 W05, L11 W10, L21 W06, L21 W07, L21 W12, L21 W25, L22 W06, L22 W13, L22 W25, L31 W39, L32 W38`); and `49` channels total that have neither a valid D2 nor He4 fit (`UNCALIBRATED` in `gain_constants_final.csv`).
16. **Where are all per-wire before, after, and overlay PDFs/PNGs located?**
    - Multi-page 576-channel PDFs: `results/gain_calibration_final/plots/per_wire/per_wire_ADC_{D2,He4}_{before,after}.pdf` and `per_wire_ADC_before_after_{D2,He4}.pdf`.
    - Focused QA PDFs: `results/gain_calibration_final/plots/per_wire/qa/{worst_chi2,extreme_gain,low_statistics,d2_he4_discrepant,failed_or_retry}_channels.pdf`.
    - Individual PNGs (`3,456` files): `results/gain_calibration_final/plots/per_wire/{D2,He4}/{before,after,before_after}/{target}_L{layer}_W{wire:02d}_{stage}.png`.
17. **What are the main limitations and next steps before writing constants to CCDB?**
    - (i) Verify in the hardware logbook the exact HV/DAQ sector mask change between run `21536` and run `21552` that masked the 87 high-wire channels and attenuated 14 front-end channels; (ii) upload separate CCDB run-indexed tables for `21459–21536` and `21552–21782`; and (iii) validate cluster-level `dE/dx` resolution on independent deuteron/`He3`/`He4` recoil tracks after applying the wire-level gain constants inside `coatjava` AHDC reconstruction.

---

## Part III: Complete Inventory of Generated Deliverables

All deliverables are stored in `<WORKSPACE_ROOT>/results/gain_calibration_final/`:

### 1. Reproducible Analysis Scripts (`scripts/`)
- `scripts/01_phase1_phase2_audit.py` — Data integrity audit, 576-channel mapping verification, and 14-window momentum scan.
- `scripts/02_phase2_phase3_qa_plots.py` — Pre-calibration physics QA 1D/2D distributions and channel occupancy/statistics maps.
- `scripts/03_run_full_calibration.py` — Two-stage bounded Landau / Landau+Exponential fitting across all 576 channels, Option A & Option B reference computation, true row-level second-pass closure refits, and summary CSV table generation.
- `scripts/04_generate_global_plots.py` — Publication-quality global gain, Option A vs B, closure, and D2-vs-He4 comparison plots.
- `scripts/05_generate_per_wire_qa_package.py` — Parallel generator for all 3,456 individual per-wire PNGs, 6 complete 576-channel PDFs, and 5 focused QA PDFs.

### 2. Summary CSV Tables (`tables/`)
- `tables/global_channel_map_576.csv` (`576 rows`)
- `tables/layer_wire_mapping_audit.csv` (`8 rows`)
- `tables/momentum_window_statistics.csv` (`28 rows`)
- `tables/candidate_selection_decision_table.csv` (`18 rows`)
- `tables/channel_statistics.csv` (`1,152 rows`: all 576 channels $\times$ 2 targets)
- `tables/gain_constants_D2.csv` (`576 rows`)
- `tables/gain_constants_He4.csv` (`576 rows`)
- `tables/gain_constants_final.csv` (`576 rows`)
- `tables/reference_option_A_vs_B_comparison.csv` (`4 rows`)
- `tables/layer_summary.csv` (`16 rows`: 8 layers $\times$ 2 targets)
- `tables/bad_channels.csv` (`235 rows`)
- `tables/d2_he4_comparison.csv` (`576 rows`)

### 3. Global & Per-Wire Visual QA Plots (`plots/`)
- **Preselection (`plots/preselection/`):**
  - `global_1d_distributions_D2_He4.png`
  - `global_2d_correlations_D2_He4.png`
  - `adc_by_layer_and_momentum_windows.png`
- **Statistics (`plots/statistics/`):**
  - `occupancy_and_median_adc_2d_maps.png`
  - `entries_per_wire_by_layer_D2_He4.png`
  - `momentum_window_coverage_comparison.png`
  - `per_wire_entries_across_momentum_windows_heatmap.png`
- **Gains (`plots/gains/`):**
  - `precal_mpv_by_wire_and_layer_D2.png`
  - `precal_mpv_by_wire_and_layer_He4.png`
  - `gain_by_wire_and_layer_D2.png`
  - `gain_by_wire_and_layer_He4.png`
  - `gain_2d_layer_wire_heatmaps.png`
  - `gain_distributions_and_uncertainties.png`
  - `option_A_vs_option_B_reference_comparison.png`
- **Closure (`plots/closure/`):**
  - `mpv_before_after_by_wire_D2.png`
  - `mpv_before_after_by_wire_He4.png`
  - `mpv_before_after_histograms_and_boxplots.png`
  - `closure_fractional_residuals_by_wire_and_layer.png`
  - `closure_2d_layer_wire_residual_maps.png`
- **D2 vs He4 (`plots/d2_vs_he4/`):**
  - `d2_vs_he4_mpv_and_gain_scatter.png`
  - `d2_vs_he4_gain_diff_ratio_pull_distributions.png`
  - `d2_vs_he4_layer_wire_difference_heatmap.png`
- **Per-Wire Complete Books & Individual PNGs (`plots/per_wire/`):**
  - `per_wire_ADC_D2_before.pdf` (48 pages, 576 channels)
  - `per_wire_ADC_He4_before.pdf` (48 pages, 576 channels)
  - `per_wire_ADC_D2_after.pdf` (48 pages, 576 channels)
  - `per_wire_ADC_He4_after.pdf` (48 pages, 576 channels)
  - `per_wire_ADC_before_after_D2.pdf` (48 pages, 576 channels)
  - `per_wire_ADC_before_after_He4.pdf` (48 pages, 576 channels)
  - `qa/worst_chi2_channels.pdf`
  - `qa/extreme_gain_channels.pdf`
  - `qa/low_statistics_channels.pdf`
  - `qa/d2_he4_discrepant_channels.pdf`
  - `qa/failed_or_retry_channels.pdf`
  - `D2/{before,after,before_after}/D2_L{layer}_W{wire:02d}_{stage}.png` (`1,728` PNGs)
  - `He4/{before,after,before_after}/He4_L{layer}_W{wire:02d}_{stage}.png` (`1,728` PNGs)
