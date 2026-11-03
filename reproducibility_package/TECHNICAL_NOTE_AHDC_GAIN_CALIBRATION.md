# CLAS12 Technical Note: Methodology and Code Architecture for ALERT AHDC Per-Wire ADC Gain Calibration

**Author:** CLAS12 ALERT Calibration Working Group  
**Date:** October 2026  
**Project Directory:** `/home/phys_365/cpaudel/NN/TRAINING/ALERT_AHDC_GAIN_CALIBRATION_CLAS12/results/gain_calibration_final/`

---

## 1. Introduction and Physics Motivation

The CLAS12 Low Energy Recoil Tracker (**ALERT**) consists of the hyperbolic drift chamber (**AHDC**) surrounded by the time-of-flight array (**ATOF**). Coherent and incoherent electroproduction measurements on light nuclei ($\text{D}_2$, $^4\text{He}$) rely on AHDC specific energy loss ($dE/dx$) combined with curvature in the $5\text{ T}$ solenoid field to separate recoil protons, deuterons, tritons, $^3\text{He}$, and $\alpha$ particles at low momenta ($0.05 \le p \le 0.40\text{ GeV}/c$).

Because gas multiplication, sense-wire tension/positioning, and front-end DREAM preamplifier response vary across the **576 physical sense wires** of the AHDC, raw pulse-height (`ADC`) distributions exhibit a $33\%\text{–}41\%$ wire-to-wire coefficient of variation in their Most Probable Value ($\text{MPV}$). The goal of this calibration is to determine a multiplicative gain constant $g_{\ell,w}$ for each physical channel $(\ell, w)$ (encoded layer $\ell \in \{11, 21, 22, 31, 32, 41, 42, 51\}$, wire $w \in \{1,\dots,N_{\text{wires}}(\ell)\}$):
$$\text{ADC}_{\text{corrected}} = g_{\ell,w} \times \text{ADC}_{\text{raw}}, \qquad g_{\ell,w} = \frac{\text{MPV}_{\text{ref}}}{\text{MPV}_{\ell,w}}$$
such that after row-level gain correction, refilling the per-wire ADC histograms, and independently refitting every wire spectrum, the post-calibration Landau peaks align at $\text{MPV}_{\text{ref}}$.

---

## 2. Dataset Provenance and Channel Indexing Conventions

### 2.1 Extracted Track-Associated Hit Tables
The calibration uses the p0v12 CalibTrain extracted track-hit datasets:
- **Deuterium ($\text{D}_2$):** `/home/phys_365/cpaudel/NN/TRAINING/26071/D2_ALL_FINAL.csv` (`5,706,742` clean numeric rows across 13 runs `21657–21768`; `5,706,738` rows with $\text{ADC} > 0$).
- **Helium-4 ($^4\text{He}$):** `/home/phys_365/cpaudel/NN/TRAINING/26071/He4_ALL_FINAL.csv` (`5,408,305` clean numeric rows across 25 runs `21459–21782`; `5,408,304` rows with $\text{ADC} > 0$).

Each row corresponds to an AHDC sense-wire hit associated with a reconstructed proton track (`pid == 2212`, `prob_2212 >= 0.238`, `clusterid >= 0`, `nhits >= 8`, $\chi^2 \le 50$, $0.02 < p \le 0.60\text{ GeV}/c$, `wfType` $\in \{0,1,2\}$, $300 \le \text{ToT} \le 750\text{ ns}$).

### 2.2 Deterministic 576-Channel Mapping
Never index or match AHDC hits by `wire` alone; every physical channel is uniquely identified by `(raw_layer, wire)` where `raw_layer = 10 * superlayer + local_layer`. The deterministic global channel index $k \in \{1,\dots,576\}$ (`tables/global_channel_map_576.csv`) is ordered by ascending `raw_layer` and ascending `wire`:
- Layer `11`: wires `1..47` (global `#001..#047`)
- Layer `21`: wires `1..56` (global `#048..#103`)
- Layer `22`: wires `1..56` (global `#104..#159`)
- Layer `31`: wires `1..72` (global `#160..#231`)
- Layer `32`: wires `1..72` (global `#232..#303`)
- Layer `41`: wires `1..87` (global `#304..#390`)
- Layer `42`: wires `1..87` (global `#391..#477`)
- Layer `51`: wires `1..99` (global `#478..#576`)

### 2.3 Run-Period Hardware Masking Discovery
A critical finding of the Phase 1–2 audit (`scripts/01_phase1_phase2_audit.py`) is that:
1. Early $^4\text{He}$ runs (`21459–21536`) had all azimuthal sectors active, populating **all 576 / 576 channels**.
2. Starting at run `21552` (which includes late $^4\text{He}$ runs `21552–21782` and all $\text{D}_2$ runs `21657–21768`), **87 channels** at the high-wire end of each layer (`L11: 42–47, L21: 1 & 48–56, L22: 48–56, L31: 62–72, L32: 64–72, L41: 73–87, L42: 75–87, L51: 1–2 & 88–99`) were masked in DAQ, leaving `489 / 576` populated channels in $\text{D}_2$.
3. In addition, 14 front-end channels that operated normally during early $^4\text{He}$ runs (`21459–21536`, median $\text{ADC} \sim 900\text{–}1200$) became severely attenuated/dead in runs $\ge 21552$ (median $\text{ADC} \sim 50\text{–}70$), joining 3 channels (`L32 W23, L32 W47, L41 W61`) that were attenuated in both periods.

---

## 3. Momentum Window Selection Methodology

Earlier exploratory studies used ultra-low momentum windows (`0.02–0.07 GeV` for $\text{D}_2$ and `0.02–0.08 GeV` for $^4\text{He}$). Our 14-window statistical audit (`tables/momentum_window_statistics.csv` and `tables/candidate_selection_decision_table.csv`) demonstrated why those windows failed:
- Reconstructed 8-hit AHDC tracks have a steep acceptance turn-on at $p \approx 0.08\text{–}0.10\text{ GeV}/c$. In `0.02–0.07 GeV`, $^4\text{He}$ has **0 channels** with $N \ge 80$ (median `9` hits/wire) and $\text{D}_2$ has only `64/576` channels with $N \ge 80$ (median `19` hits/wire).
- In contrast, the selected window **`0.15 <= p_GeV <= 0.25 GeV` ($\text{ADC} > 0$)** provides `1,789,065` hits in $\text{D}_2$ (median `2,048` hits/wire, `440` channels with $N \ge 80$) and `1,787,052` hits in $^4\text{He}$ (median `2,457.5` hits/wire, `553` channels with $N \ge 80$), while keeping the proton ionization peak in a clean linear dynamic range (`MPV ~ 300–450 ADC`).

---

## 4. Mathematical Formulation of Per-Wire ADC Fitting

### 4.1 Exact-Mode Moyal Landau Model (`Landau`)
To ensure that the fitted parameter $\text{MPV}$ is the exact mathematical peak (mode) of the curve without numerical shift approximations, we parameterize the Landau distribution via the normalized Moyal analytical form:
$$f_{\text{L}}(A; A_0, \text{MPV}, w) = A_0 \exp\!\left[-\frac{1}{2}\left(z + e^{-z} - 1\right)\right], \qquad z = \frac{A - \text{MPV}}{w}$$
At $A = \text{MPV}$ ($z = 0$), $f_{\text{L}}(\text{MPV}) = A_0$, $\left.\frac{\partial f_{\text{L}}}{\partial A}\right|_{A=\text{MPV}} = 0$, and $\left.\frac{\partial^2 f_{\text{L}}}{\partial A^2}\right|_{A=\text{MPV}} = -\frac{A_0}{2 w^2} < 0$.

### 4.2 Scale-Invariant Two-Component Landau + Exponential Tail Model (`Landau+Exp`)
In gas proportional drift chambers, delta-ray emission and avalanche fluctuations can produce an upper exponential tail broader than a single Moyal width $w$. If an unconstrained additive exponential $A_E e^{-A/\tau}$ is added directly to $f_{\text{L}}$, its non-zero derivative at $A = \text{MPV}$ shifts the true peak of the sum away from the parameter $\text{MPV}$ and breaks scale invariance under $\text{ADC} \to g \times \text{ADC}$.

To solve both problems rigorously, we formulate the 4-parameter scale-invariant **Landau + Exponential-Tail** model:
$$f_{\text{LE}}(A; A_0, \text{MPV}, w, f_{\text{exp}}) = A_0 \left[(1 - f_{\text{exp}})\exp\!\left(-\frac{1}{2}(z + e^{-z} - 1)\right) + f_{\text{exp}}\exp\!\left(-\frac{1}{2}(u + e^{-u} - 1)\right)\right], \qquad u = \frac{A - \text{MPV}}{2.2\,w}$$
where $f_{\text{exp}} \in [0, 0.65]$ is the tail fraction. Because both terms have vanishing first derivative at $A = \text{MPV}$, $A = \text{MPV}$ is the **exact analytical peak** of $f_{\text{LE}}$ for any $f_{\text{exp}}$, and because $u$ scales proportionally with $w$, $f_{\text{LE}}$ is **100% scale-invariant** under multiplicative gain calibration ($A \to g A \implies \text{MPV} \to g\,\text{MPV},\; w \to g\,w,\; f_{\text{exp}} \to f_{\text{exp}}$).

### 4.3 Two-Stage Quantile-Anchored Bounded Fitting & Retry Algorithm
Implemented in `fit_channel_spectrum()` inside `scripts/03_run_full_calibration.py`:
1. **Pre-fit Screening:**
   - $N = 0 \implies \texttt{NO\_DATA}$
   - $0 < N < 80 \implies \texttt{LOW\_STAT}$
   - Sample median $q_{50} < 180\text{ ADC} \implies \texttt{MPV\_OUTLIER}$ (identifies collapsed preamplifier noise-floor channels with $q_{50} \sim 45\text{–}100\text{ ADC}$).
2. **Histogram Construction:**
   - Bin width $\Delta A = 35\text{ ADC}$ ($N \ge 300$), $50\text{ ADC}$ ($140 \le N < 300$), or $70\text{ ADC}$ ($80 \le N < 140$) over $[0, 3500]\text{ ADC}$ ($[0, 4900]\text{ ADC}$ if $q_{50} \ge 1200\text{ ADC}$).
3. **Stage 1 (Quantile-Anchored Localization):**
   - Smooth histogram with a $\sigma = 2.2$-bin Gaussian filter to find initial peak $p_0 \in [0.25\,q_{50}, 0.88\,q_{50}]$.
   - Fit $f_{\text{L}}$ over $[0.24\,q_{50}, 1.95\,q_{50}]$ (which stays above the low-ADC hardware threshold turn-on roll-off at $A \lesssim 0.20\,q_{50}$) with bounds $\text{MPV} \in [0.22\,q_{50}, 0.92\,q_{50}]$ and $w \in [0.06\,q_{50}, 1.45\,q_{50}]$.
4. **Stage 2 (Refined Peak-and-Slope Fit):**
   - Fit $f_{\text{L}}$ over $[0.38\,\text{MPV}_1, 2.45\,\text{MPV}_1]$ using Poisson bin uncertainties $\sigma_i = \sqrt{\max(y_i, 1)}$ (`absolute_sigma=True`).
5. **Automated Retry (`RETRY_GOOD`):**
   - Triggered if Stage 2 has $\chi^2/\text{ndf} > 1.60$, relative MPV uncertainty $\sigma_{\text{MPV}}/\text{MPV} > 16\%$, or parameter-bound proximity ($<1.5\%$ of bound range).
   - Evaluates 4 retry candidates (`[0.16*q50, 2.00*q50]` with `Landau`, `[0.18*q50, 2.15*q50]` with `Landau+Exp`, `[0.20*q50, 2.20*q50]` with `Landau`, `[0.14*q50, 1.90*q50]` with `Landau+Exp`) and accepts the candidate that resolves boundary/uncertainty issues and reduces $\chi^2/\text{ndf}$.
6. **Final Post-Fit Quality Gate:**
   - Flag `MPV_BOUNDARY_HIT` or `WIDTH_BOUNDARY_HIT` if the final parameter lies within $1.5\%$ of its bound; `BAD_CHI2` if $\chi^2/\text{ndf} > 3.5$; `UNSTABLE` if $\sigma_{\text{MPV}}/\text{MPV} > 20\%$; otherwise `GOOD` (or `RETRY_GOOD`).

---

## 5. Reference Normalization (Option A vs Option B) and True Closure Verification

### 5.1 Option A (Global Reference) vs Option B (Per-Layer Reference)
- **Option A:** $\text{MPV}_{\text{ref}}^{\text{Option A}} = \text{median}_{(\ell,w) \in \mathcal{G}}(\text{MPV}_{\ell,w})$ across all `GOOD` + `RETRY_GOOD` channels $\mathcal{G}$ in the detector ($334.90\text{ ADC}$ in $\text{D}_2$, $386.08\text{ ADC}$ in $^4\text{He}$). Equalizes all 8 layers to a single uniform ADC response.
- **Option B:** $\text{MPV}_{\text{ref}}^{\text{Option B}}(\ell) = \text{median}_{w \in \mathcal{G}_\ell}(\text{MPV}_{\ell,w})$ computed separately within each layer $\ell$. Equalizes wire-to-wire variations within each layer while preserving the natural geometric progression of MPV across layers (`~295–358 ADC` in layers `11–41`, `~397–494 ADC` in layer `42`, `~482–669 ADC` in layer `51`).

### 5.2 True Row-Level Second-Pass Closure Procedure
In `run_target_calibration()` (`scripts/03_run_full_calibration.py`), closure is **never** evaluated algebraically. Instead, for every calibrated channel $(\ell, w)$:
1. Multiply raw hit-level ADC values by the derived gain: $A_i^{\text{corr}} = g_{\ell,w} \times A_i^{\text{raw}}$.
2. Call `fit_channel_spectrum(adc_corr)` blindly from scratch (re-computing quantiles, histogram binning, Stage-1 localization, Stage-2 fit, and retry).
3. Extract the refitted peak $\text{MPV}_{\ell,w}^{\text{after}}$ and compute:
   $$\delta_{\ell,w} = \frac{\text{MPV}_{\ell,w}^{\text{after}} - \text{MPV}_{\text{ref}}}{\text{MPV}_{\text{ref}}}$$
This true second-pass refit achieves $\text{median }|\delta_{\ell,w}| = 2.02\%$ ($\text{MAD} = 3.04\%$) in $\text{D}_2$ and $\text{median }|\delta_{\ell,w}| = 2.21\%$ ($\text{MAD} = 3.28\%$) in $^4\text{He}$.

---

## 6. Code Architecture and Reproducibility Guide

The analysis pipeline is modularized into five standalone Python scripts in `results/gain_calibration_final/scripts/`:

| Script | Purpose | Execution Time | Key Outputs |
| :--- | :--- | :---: | :--- |
| `01_phase1_phase2_audit.py` | Audits CSV line integrity, verifies 22 columns and `raw_layer = 10*superlayer + local_layer`, builds 576-channel map, and scans 14 momentum windows. | `~35 s` | `global_channel_map_576.csv`, `layer_wire_mapping_audit.csv`, `momentum_window_statistics.csv` |
| `02_phase2_phase3_qa_plots.py` | Generates global 1D/2D physics preselection distributions and 576-channel occupancy/median-ADC heatmaps. | `~40 s` | `plots/preselection/*.png`, `plots/statistics/*.png` |
| `03_run_full_calibration.py` | Runs 576-channel two-stage Landau / Landau+Exp fits, evaluates Option A & Option B, performs true second-pass closure refits, and writes all summary CSVs. | `~25 s` | `gain_constants_{D2,He4,final}.csv`, `channel_statistics.csv`, `layer_summary.csv`, `bad_channels.csv`, `d2_he4_comparison.csv`, `reference_option_A_vs_B_comparison.csv` |
| `04_generate_global_plots.py` | Generates publication-quality global plots for pre/post MPV, gains, Option A vs B, closure residuals, and $\text{D}_2$-vs-$^4\text{He}$ agreement. | `~10 s` | `plots/gains/*.png`, `plots/closure/*.png`, `plots/d2_vs_he4/*.png` |
| `05_generate_per_wire_qa_package.py` | Renders all 3,456 individual per-wire PNGs (`before`, `after`, `before_after`), 6 complete 576-channel PDFs (48 pages each), and 5 focused QA PDFs. | `~90 s` | `plots/per_wire/{D2,He4}/{before,after,before_after}/*.png`, `plots/per_wire/*.pdf`, `plots/per_wire/qa/*.pdf` |

To reproduce the entire study from scratch without touching HIPO files:
```bash
cd /home/phys_365/cpaudel/NN/TRAINING/ALERT_AHDC_GAIN_CALIBRATION_CLAS12/results/gain_calibration_final
python3 scripts/01_phase1_phase2_audit.py
python3 scripts/02_phase2_phase3_qa_plots.py
python3 scripts/03_run_full_calibration.py
python3 scripts/04_generate_global_plots.py
python3 scripts/05_generate_per_wire_qa_package.py
```
