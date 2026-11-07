#!/usr/bin/env python3
"""
Phase 2 & Phase 3: Pre-Calibration Physics QA and Momentum-Window Statistics Plots.

Generates publication-quality global 1D and 2D distributions for D2 and He4
independently (linear and log scales where informative), channel statistics
heatmaps across candidate momentum windows, and ADC spectral shape comparisons
across momentum windows.
"""
import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from pathlib import Path

WORKSPACE = Path(os.environ.get("ALERT_WORKSPACE", "<DEFAULT_WORKSPACE>"))
BASE = WORKSPACE / "ALERT_AHDC_GAIN_CALIBRATION_CLAS12"
D2_PATH = BASE / "FINAL_MERGED/D2_ALL_FINAL.csv"
HE4_PATH = BASE / "FINAL_MERGED/HE4_ALL_FINAL.csv"
OUT_BASE = BASE / "results/gain_calibration_final"
PLOT_PRESEL = OUT_BASE / "plots/preselection"
PLOT_STATS = OUT_BASE / "plots/statistics"
TAB_DIR = OUT_BASE / "tables"

EXPECTED_WIRES = {11: 47, 21: 56, 22: 56, 31: 72, 32: 72, 41: 87, 42: 87, 51: 99}
LAYERS = [11, 21, 22, 31, 32, 41, 42, 51]

GLOBAL_MAP = {}
gidx = 1
for lay in LAYERS:
    for w in range(1, EXPECTED_WIRES[lay] + 1):
        GLOBAL_MAP[(lay, w)] = gidx
        gidx += 1

LAYER_BOUNDS = []
acc = 0
for lay in LAYERS:
    LAYER_BOUNDS.append((lay, acc + 1, acc + EXPECTED_WIRES[lay]))
    acc += EXPECTED_WIRES[lay]

plt.rcParams.update({
    "font.size": 10,
    "axes.titlesize": 11,
    "axes.labelsize": 10,
    "figure.dpi": 140,
})

def load_clean_csv(path: Path, name: str) -> pd.DataFrame:
    df = pd.read_csv(path, on_bad_lines="skip", low_memory=False)
    num_cols = ["file_index", "event_index", "run", "event", "trackid", "clusterid",
                "pid", "prob_2212", "p_GeV", "dEdx", "nhits", "chi2",
                "superlayer", "local_layer", "raw_layer", "wire",
                "adc_sector", "adc_order", "wfType", "ToT", "ADC"]
    for c in num_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=num_cols).copy()
    for c in ["run", "event", "trackid", "clusterid", "pid", "nhits",
              "superlayer", "local_layer", "raw_layer", "wire", "wfType"]:
        df[c] = df[c].astype(np.int64)
    valid_lw = df["raw_layer"].isin(LAYERS) & (df["wire"] >= 1) & (df["wire"] <= df["raw_layer"].map(EXPECTED_WIRES).fillna(0))
    df = df[valid_lw & (df["ADC"] > 0)].copy()
    df["global_channel"] = [GLOBAL_MAP[(l, w)] for l, w in zip(df["raw_layer"].values, df["wire"].values)]
    print(f"[{name}] Loaded {len(df):,} clean ADC>0 rows.")
    return df

d2 = load_clean_csv(D2_PATH, "D2")
he4 = load_clean_csv(HE4_PATH, "He4")

SEL_PMIN, SEL_PMAX = 0.15, 0.25

for target, df in [("D2", d2), ("He4", he4)]:
    df_sel = df[(df["p_GeV"] >= SEL_PMIN) & (df["p_GeV"] <= SEL_PMAX)]

    # 1-3, 7-9: Global 1D distributions (broad vs selected calibration window, linear & log)
    fig, axes = plt.subplots(2, 3, figsize=(15, 9))
    specs = [
        ("p_GeV", np.linspace(0.0, 0.62, 125), "Track Momentum p [GeV/c]", False),
        ("dEdx", np.linspace(0.0, 600.0, 121), "Track dE/dx [arb. units]", True),
        ("ADC", np.linspace(0.0, 6000.0, 121), "Matched AHDC ADC", True),
        ("nhits", np.arange(7.5, 17.5, 1.0), "Number of AHDC Track Hits (nhits)", False),
        ("chi2", np.linspace(0.0, 35.0, 106), "Track Fit $\\chi^2$", True),
        ("prob_2212", np.linspace(0.2, 1.01, 82), "ALERT::ai Proton Probability (prob_2212)", True),
    ]
    for ax, (col, bins, xlabel, use_log) in zip(axes.flat, specs):
        ax.hist(df[col], bins=bins, histtype="stepfilled", alpha=0.35, color="steelblue",
                label=f"Broad (N={len(df):,})")
        ax.hist(df_sel[col], bins=bins, histtype="step", lw=1.8, color="crimson",
                label=f"Selected 0.15-0.25 GeV (N={len(df_sel):,})")
        if col == "p_GeV":
            ax.axvspan(SEL_PMIN, SEL_PMAX, color="crimson", alpha=0.12, label="Calibration window")
        if use_log:
            ax.set_yscale("log")
        ax.set_xlabel(xlabel)
        ax.set_ylabel("Entries")
        ax.set_title(f"{target}: {col} Distribution")
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.25)
    fig.suptitle(f"CLAS12 ALERT AHDC Pre-Calibration 1D Distributions — {target}", fontsize=13, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    fig.savefig(PLOT_PRESEL / f"{target}_global_1D_distributions.png")
    plt.close(fig)

    # Also save linear-scale ADC and dEdx zoom for peak inspection
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
    axes[0].hist(df["ADC"], bins=np.linspace(0, 3500, 141), histtype="stepfilled", alpha=0.35, color="steelblue", label="Broad")
    axes[0].hist(df_sel["ADC"], bins=np.linspace(0, 3500, 141), histtype="step", lw=1.8, color="crimson", label="0.15-0.25 GeV")
    axes[0].set_xlabel("Matched AHDC ADC")
    axes[0].set_ylabel("Entries (linear)")
    axes[0].set_title(f"{target}: ADC Spectrum (Linear Scale)")
    axes[0].legend(fontsize=8)
    axes[0].grid(True, alpha=0.25)

    axes[1].hist(df["dEdx"], bins=np.linspace(0, 400, 121), histtype="stepfilled", alpha=0.35, color="steelblue", label="Broad")
    axes[1].hist(df_sel["dEdx"], bins=np.linspace(0, 400, 121), histtype="step", lw=1.8, color="crimson", label="0.15-0.25 GeV")
    axes[1].set_xlabel("Track dE/dx")
    axes[1].set_ylabel("Entries (linear)")
    axes[1].set_title(f"{target}: dE/dx Spectrum (Linear Scale)")
    axes[1].legend(fontsize=8)
    axes[1].grid(True, alpha=0.25)

    axes[2].hist(df["ToT"], bins=np.linspace(290, 760, 95), histtype="stepfilled", alpha=0.35, color="steelblue", label="Broad")
    axes[2].hist(df_sel["ToT"], bins=np.linspace(290, 760, 95), histtype="step", lw=1.8, color="crimson", label="0.15-0.25 GeV")
    axes[2].set_xlabel("AHDC Time-over-Threshold ToT [ns]")
    axes[2].set_ylabel("Entries")
    axes[2].set_title(f"{target}: ToT Distribution")
    axes[2].legend(fontsize=8)
    axes[2].grid(True, alpha=0.25)
    fig.tight_layout()
    fig.savefig(PLOT_PRESEL / f"{target}_linear_ADC_dEdx_ToT.png")
    plt.close(fig)

    # 4-6: 2D Correlations: dEdx vs p_GeV, ADC vs p_GeV, ADC vs dEdx
    fig, axes = plt.subplots(1, 3, figsize=(16, 4.8))
    h1 = axes[0].hist2d(df["p_GeV"], df["dEdx"], bins=[120, 120], range=[[0.02, 0.60], [0, 500]],
                        cmap="viridis", norm=LogNorm())
    axes[0].axvline(SEL_PMIN, color="red", ls="--", lw=1.5)
    axes[0].axvline(SEL_PMAX, color="red", ls="--", lw=1.5)
    axes[0].set_xlabel("p [GeV/c]")
    axes[0].set_ylabel("dE/dx")
    axes[0].set_title(f"{target}: dE/dx vs p_GeV (Red = 0.15-0.25 GeV)")
    plt.colorbar(h1[3], ax=axes[0], label="Counts")

    h2 = axes[1].hist2d(df["p_GeV"], df["ADC"], bins=[120, 120], range=[[0.02, 0.60], [0, 4500]],
                        cmap="viridis", norm=LogNorm())
    axes[1].axvline(SEL_PMIN, color="red", ls="--", lw=1.5)
    axes[1].axvline(SEL_PMAX, color="red", ls="--", lw=1.5)
    axes[1].set_xlabel("p [GeV/c]")
    axes[1].set_ylabel("Matched AHDC ADC")
    axes[1].set_title(f"{target}: ADC vs p_GeV (Red = 0.15-0.25 GeV)")
    plt.colorbar(h2[3], ax=axes[1], label="Counts")

    h3 = axes[2].hist2d(df_sel["dEdx"], df_sel["ADC"], bins=[110, 110], range=[[0, 350], [0, 4000]],
                        cmap="magma", norm=LogNorm())
    axes[2].set_xlabel("dE/dx (0.15-0.25 GeV)")
    axes[2].set_ylabel("Matched AHDC ADC")
    axes[2].set_title(f"{target}: ADC vs dE/dx (0.15-0.25 GeV)")
    plt.colorbar(h3[3], ax=axes[2], label="Counts")

    fig.suptitle(f"CLAS12 ALERT AHDC 2D Kinematic & Energy-Loss Correlations — {target}", fontsize=13, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(PLOT_PRESEL / f"{target}_2D_correlations_p_dEdx_ADC.png")
    plt.close(fig)

    # 10-12: Selected rows per physical layer, per global channel, and 2D layer vs wire occupancy map
    fig, axes = plt.subplots(1, 3, figsize=(16, 4.8))
    lay_broad = df.groupby("raw_layer").size().reindex(LAYERS, fill_value=0)
    lay_sel = df_sel.groupby("raw_layer").size().reindex(LAYERS, fill_value=0)
    x_lay = np.arange(len(LAYERS))
    axes[0].bar(x_lay - 0.18, lay_broad.values, width=0.35, color="steelblue", alpha=0.75, label="Broad")
    axes[0].bar(x_lay + 0.18, lay_sel.values, width=0.35, color="crimson", alpha=0.85, label="0.15-0.25 GeV")
    axes[0].set_xticks(x_lay)
    axes[0].set_xticklabels([str(l) for l in LAYERS])
    axes[0].set_xlabel("Encoded Physical Layer")
    axes[0].set_ylabel("Row Count")
    axes[0].set_title(f"{target}: Rows per Physical Layer")
    axes[0].legend(fontsize=8)
    axes[0].grid(True, alpha=0.25)

    ch_broad = df.groupby("global_channel").size().reindex(range(1, 577), fill_value=0)
    ch_sel = df_sel.groupby("global_channel").size().reindex(range(1, 577), fill_value=0)
    axes[1].plot(ch_broad.index, ch_broad.values, lw=0.9, color="steelblue", alpha=0.7, label="Broad")
    axes[1].plot(ch_sel.index, ch_sel.values, lw=1.0, color="crimson", label="0.15-0.25 GeV")
    axes[1].axhline(80, color="black", ls="--", lw=1.0, label="N=80 threshold")
    for lay, s, e in LAYER_BOUNDS:
        axes[1].axvline(s, color="gray", ls=":", lw=0.6)
    axes[1].set_xlabel("Global Channel Index (1..576)")
    axes[1].set_ylabel("Entries per Wire")
    axes[1].set_title(f"{target}: Entries per Channel")
    axes[1].legend(fontsize=8)
    axes[1].grid(True, alpha=0.25)

    occ = np.full((len(LAYERS), 99), np.nan)
    for il, lay in enumerate(LAYERS):
        sub_l = df_sel[df_sel["raw_layer"] == lay].groupby("wire").size()
        for w in range(1, EXPECTED_WIRES[lay] + 1):
            occ[il, w - 1] = sub_l.get(w, 0)
    im = axes[2].imshow(occ, aspect="auto", origin="lower", cmap="plasma", interpolation="nearest")
    axes[2].set_yticks(np.arange(len(LAYERS)))
    axes[2].set_yticklabels([f"L{l} (1..{EXPECTED_WIRES[l]})" for l in LAYERS])
    axes[2].set_xlabel("Wire Index (1..99)")
    axes[2].set_title(f"{target}: Layer vs Wire Occupancy (0.15-0.25 GeV)")
    plt.colorbar(im, ax=axes[2], label="Selected Entries")

    fig.suptitle(f"CLAS12 ALERT AHDC Channel & Layer Occupancy — {target}", fontsize=13, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(PLOT_PRESEL / f"{target}_layer_wire_occupancy.png")
    plt.close(fig)

# Candidate momentum windows ADC shape comparison + channel statistics heatmaps
CAND_WINDOWS = [
    ("0.02-0.05", 0.02, 0.05),
    ("0.02-0.07", 0.02, 0.07),
    ("0.02-0.08", 0.02, 0.08),
    ("0.05-0.08", 0.05, 0.08),
    ("0.08-0.12", 0.08, 0.12),
    ("0.12-0.15", 0.12, 0.15),
    ("0.15-0.20", 0.15, 0.20),
    ("0.15-0.25", 0.15, 0.25),
    ("0.20-0.30", 0.20, 0.30),
]

fig, axes = plt.subplots(1, 2, figsize=(15, 5.5))
bins_adc = np.linspace(0, 3500, 141)
for ax, (target, df) in zip(axes, [("D2", d2), ("He4", he4)]):
    for wname, plo, phi in CAND_WINDOWS:
        sub = df[(df["p_GeV"] >= plo) & (df["p_GeV"] <= phi)]
        if len(sub) < 500:
            continue
        hist, edges = np.histogram(sub["ADC"], bins=bins_adc, density=True)
        centers = 0.5 * (edges[:-1] + edges[1:])
        lw = 2.4 if wname == "0.15-0.25" else 1.2
        ax.plot(centers, hist, lw=lw, label=f"{wname} GeV (N={len(sub):,})")
    ax.set_xlabel("Matched AHDC ADC")
    ax.set_ylabel("Normalized Density")
    ax.set_title(f"{target}: Normalized ADC Spectral Shape vs Momentum Window")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.25)
fig.tight_layout()
fig.savefig(PLOT_PRESEL / "ADC_shape_vs_momentum_windows_D2_He4.png")
plt.close(fig)

# Heatmap of channel counts vs momentum window
fig, axes = plt.subplots(2, 1, figsize=(15, 8), sharex=True)
for ax, (target, df) in zip(axes, [("D2", d2), ("He4", he4)]):
    mat = np.zeros((len(CAND_WINDOWS), 576))
    for iw, (wname, plo, phi) in enumerate(CAND_WINDOWS):
        sub = df[(df["p_GeV"] >= plo) & (df["p_GeV"] <= phi)]
        cnt = sub.groupby("global_channel").size().reindex(range(1, 577), fill_value=0).values
        mat[iw, :] = cnt
    im = ax.imshow(np.log10(mat + 1.0), aspect="auto", origin="lower", cmap="viridis",
                   extent=[0.5, 576.5, -0.5, len(CAND_WINDOWS) - 0.5])
    ax.set_yticks(np.arange(len(CAND_WINDOWS)))
    ax.set_yticklabels([w[0] + " GeV" for w in CAND_WINDOWS])
    for lay, s, e in LAYER_BOUNDS:
        ax.axvline(s - 0.5, color="white", ls=":", lw=0.7)
        ax.text(0.5 * (s + e), len(CAND_WINDOWS) - 0.65, f"L{lay}", color="white",
                ha="center", va="top", fontsize=8, fontweight="bold")
    ax.set_title(f"{target}: Per-Channel Statistics Heatmap $\\log_{{10}}(N+1)$ Across Candidate Momentum Windows")
    plt.colorbar(im, ax=ax, label="$\\log_{10}(N_{\\mathrm{entries}}+1)$")
axes[1].set_xlabel("Global Channel Index (1..576)")
fig.tight_layout()
fig.savefig(PLOT_STATS / "momentum_window_channel_statistics_heatmap.png")
plt.close(fig)

# Summary bar chart of usable channels (N>=80, N>=200, N>=500, N>=1000) across momentum windows
df_win = pd.read_csv(TAB_DIR / "momentum_window_statistics.csv")
df_win_cand = df_win[df_win["window"].isin([w[0] for w in CAND_WINDOWS])].copy()

fig, axes = plt.subplots(1, 2, figsize=(15, 5.2), sharey=True)
for ax, target in zip(axes, ["D2", "He4"]):
    sub = df_win_cand[df_win_cand["target"] == target].set_index("window").loc[[w[0] for w in CAND_WINDOWS]]
    x = np.arange(len(CAND_WINDOWS))
    w = 0.2
    ax.bar(x - 1.5*w, sub["N_ge_80"], width=w, label="N >= 80", color="#2b83ba")
    ax.bar(x - 0.5*w, sub["N_ge_200"], width=w, label="N >= 200", color="#abdda4")
    ax.bar(x + 0.5*w, sub["N_ge_500"], width=w, label="N >= 500", color="#fdae61")
    ax.bar(x + 1.5*w, sub["N_ge_1000"], width=w, label="N >= 1000", color="#d7191c")
    ax.axhline(576, color="black", ls=":", lw=1.0, label="576 total channels")
    if target == "D2":
        ax.axhline(489, color="gray", ls="--", lw=1.0, label="489 D2-active channels")
    ax.set_xticks(x)
    ax.set_xticklabels([w[0] for w in CAND_WINDOWS], rotation=30, ha="right")
    ax.set_ylabel("Number of Physical Channels")
    ax.set_title(f"{target}: Channel Statistics Threshold Counts vs Momentum Window")
    ax.legend(fontsize=8, loc="upper left")
    ax.grid(True, alpha=0.25)
fig.tight_layout()
fig.savefig(PLOT_STATS / "momentum_window_threshold_counts.png")
plt.close(fig)

print("Phase 2 & Phase 3 global QA plots successfully generated.")
