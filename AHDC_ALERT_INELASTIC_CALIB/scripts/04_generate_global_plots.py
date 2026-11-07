#!/usr/bin/env python3
"""
Phase 9-12: Generate Publication-Quality Global Plots for Gains, Option A vs Option B,
True Second-Pass Closure, and D2-vs-He4 Cross-Calibration Comparison.
"""

import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

plt.rcParams.update({
    "font.size": 10,
    "axes.titlesize": 11,
    "axes.labelsize": 10,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "legend.fontsize": 8.5,
    "figure.dpi": 150,
})

WORKSPACE = Path(os.environ.get("ALERT_WORKSPACE", "<DEFAULT_WORKSPACE>"))
BASE_DIR = WORKSPACE / "ALERT_AHDC_GAIN_CALIBRATION_CLAS12"
OUT_DIR = BASE_DIR / "results" / "gain_calibration_final"
TABLE_DIR = OUT_DIR / "tables"
GAIN_PLOT_DIR = OUT_DIR / "plots" / "gains"
CLOS_PLOT_DIR = OUT_DIR / "plots" / "closure"
CMP_PLOT_DIR = OUT_DIR / "plots" / "d2_vs_he4"

for d in (GAIN_PLOT_DIR, CLOS_PLOT_DIR, CMP_PLOT_DIR):
    d.mkdir(parents=True, exist_ok=True)

LAYERS = [11, 21, 22, 31, 32, 41, 42, 51]
EXPECTED_WIRES = {11: 47, 21: 56, 22: 56, 31: 72, 32: 72, 41: 87, 42: 87, 51: 99}


def make_grid(df: pd.DataFrame, val_col: str) -> np.ndarray:
    grid = np.full((len(LAYERS), 99), np.nan)
    for il, lay in enumerate(LAYERS):
        sub = df[df["layer"] == lay]
        for _, r in sub.iterrows():
            w = int(r["wire"])
            if 1 <= w <= 99:
                grid[il, w - 1] = r[val_col]
    return grid


def plot_gains(df_d2: pd.DataFrame, df_he4: pd.DataFrame, df_final: pd.DataFrame):
    # 1. Pre-calibration MPV by wire and layer for D2 and He4
    for tname, dft, color in [("D2", df_d2, "#1f77b4"), ("He4", df_he4, "#d62728")]:
        fig, axes = plt.subplots(4, 2, figsize=(14, 13), sharey=True)
        axes = axes.flatten()
        ref_a = float(dft["mpv_ref_optA"].iloc[0])
        for i, lay in enumerate(LAYERS):
            ax = axes[i]
            sub = dft[dft["layer"] == lay]
            good = sub[sub["fit_status"].isin(["GOOD", "RETRY_GOOD"])]
            bad = sub[~sub["fit_status"].isin(["GOOD", "RETRY_GOOD", "NO_DATA"]) & sub["mpv"].notna()]
            ref_b = float(sub["mpv_ref_optB"].iloc[0])

            ax.errorbar(
                good["wire"], good["mpv"], yerr=good["mpv_err"],
                fmt="o", ms=4, color=color, ecolor=color, alpha=0.85, elinewidth=1.0, capsize=1.5,
                label=f"GOOD/RETRY_GOOD (n={len(good)})",
            )
            if len(bad) > 0:
                ax.scatter(
                    bad["wire"], bad["mpv"], marker="x", s=30, color="gray",
                    label=f"Excluded/Outlier (n={len(bad)})",
                )
            ax.axhline(ref_a, color="black", ls="--", lw=1.3, label=f"Global Ref Option A ({ref_a:.1f} ADC)")
            ax.axhline(ref_b, color="#2ca02c", ls=":", lw=1.4, label=f"Layer Ref Option B ({ref_b:.1f} ADC)")
            ax.set_title(f"{tname} Layer {lay} (Wires 1..{EXPECTED_WIRES[lay]})")
            ax.set_xlim(0, EXPECTED_WIRES[lay] + 2)
            ax.set_ylim(0, 1250)
            ax.grid(True, alpha=0.25)
            if i % 2 == 0:
                ax.set_ylabel("Fitted Pre-Cal MPV [ADC]")
            if i >= 6:
                ax.set_xlabel("Wire Number")
            ax.legend(loc="upper right", fontsize=7.5)
        fig.suptitle(f"{tname}: Pre-Calibration Fitted Landau MPV vs Wire by Layer (0.15 <= p <= 0.25 GeV)", fontsize=13, y=0.995)
        fig.tight_layout()
        fig.savefig(GAIN_PLOT_DIR / f"precal_mpv_by_wire_and_layer_{tname}.png", dpi=160)
        plt.close(fig)

    # 2. Gain vs wire by layer for D2 and He4 (Option A and Option B)
    for tname, dft in [("D2", df_d2), ("He4", df_he4)]:
        fig, axes = plt.subplots(4, 2, figsize=(14, 13), sharey=True)
        axes = axes.flatten()
        for i, lay in enumerate(LAYERS):
            ax = axes[i]
            sub = dft[(dft["layer"] == lay) & dft["fit_status"].isin(["GOOD", "RETRY_GOOD"])]
            ax.errorbar(
                sub["wire"], sub["gain_optA"], yerr=sub["gain_err_optA"],
                fmt="o", ms=4, color="#1f77b4", alpha=0.85, elinewidth=1.0, capsize=1.5,
                label="Option A (Global Ref)",
            )
            ax.plot(
                sub["wire"], sub["gain_optB"], "s", ms=3.5, color="#ff7f0e", alpha=0.80,
                label="Option B (Per-Layer Ref)",
            )
            ax.axhline(1.0, color="black", ls="--", lw=1.1, label="Unity Gain (1.0)")
            ax.set_title(f"{tname} Layer {lay} (Calibrated: {len(sub)}/{EXPECTED_WIRES[lay]})")
            ax.set_xlim(0, EXPECTED_WIRES[lay] + 2)
            ax.set_ylim(0.1, 2.5)
            ax.grid(True, alpha=0.25)
            if i % 2 == 0:
                ax.set_ylabel(r"Gain Constant $g_{\mathrm{wire}} = \mathrm{MPV}_{\mathrm{ref}} / \mathrm{MPV}_{\mathrm{wire}}$")
            if i >= 6:
                ax.set_xlabel("Wire Number")
            ax.legend(loc="upper right", fontsize=8)
        fig.suptitle(f"{tname}: Per-Wire Multiplicative ADC Gain Constants by Layer (Option A vs Option B)", fontsize=13, y=0.995)
        fig.tight_layout()
        fig.savefig(GAIN_PLOT_DIR / f"gain_by_wire_and_layer_{tname}.png", dpi=160)
        plt.close(fig)

    # 3. 2D Layer x Wire Heatmaps of Raw MPV, D2 Gain, He4 Gain, and Final Recommended Gain
    fig, axes = plt.subplots(3, 2, figsize=(15, 13))
    panels = [
        (axes[0, 0], make_grid(df_d2[df_d2["fit_status"].isin(["GOOD", "RETRY_GOOD"])], "mpv"), "D2 Pre-Calibration MPV [ADC]", "viridis", 200, 800),
        (axes[0, 1], make_grid(df_he4[df_he4["fit_status"].isin(["GOOD", "RETRY_GOOD"])], "mpv"), "He4 Pre-Calibration MPV [ADC]", "viridis", 200, 800),
        (axes[1, 0], make_grid(df_d2, "gain_optA"), "D2 Gain Constant (Option A Global Ref)", "coolwarm", 0.4, 1.8),
        (axes[1, 1], make_grid(df_he4, "gain_optA"), "He4 Gain Constant (Option A Global Ref)", "coolwarm", 0.4, 1.8),
        (axes[2, 0], make_grid(df_final, "recommended_gain_optA"), "Final Recommended Gain (Option A, 527/576 Calibrated)", "coolwarm", 0.4, 1.8),
        (axes[2, 1], make_grid(df_final, "recommended_gain_optB"), "Final Recommended Gain (Option B Per-Layer, 527/576 Calibrated)", "coolwarm", 0.4, 1.8),
    ]
    for ax, grid, title, cmap, vmin, vmax in panels:
        im = ax.imshow(grid, aspect="auto", origin="lower", cmap=cmap, vmin=vmin, vmax=vmax, extent=[0.5, 99.5, -0.5, 7.5])
        ax.set_yticks(range(len(LAYERS)))
        ax.set_yticklabels([str(l) for l in LAYERS])
        ax.set_xlabel("Wire Number")
        ax.set_ylabel("Physical Layer")
        ax.set_title(title)
        for il, lay in enumerate(LAYERS):
            ax.plot([EXPECTED_WIRES[lay] + 0.5, EXPECTED_WIRES[lay] + 0.5], [il - 0.5, il + 0.5], color="black", lw=1.5)
        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.suptitle("2D Layer-Wire Maps of Pre-Calibration MPV and Derived Gain Constants (Gray/Blank = Uncalibrated/Inactive)", fontsize=13, y=0.995)
    fig.tight_layout()
    fig.savefig(GAIN_PLOT_DIR / "gain_2d_layer_wire_heatmaps.png", dpi=160)
    plt.close(fig)

    # 4. 1D Distributions of MPV, Relative Uncertainty, Gain, and Fit Chi2/ndf
    fig, axes = plt.subplots(2, 2, figsize=(13, 10))
    g_d2 = df_d2[df_d2["fit_status"].isin(["GOOD", "RETRY_GOOD"])]
    g_he4 = df_he4[df_he4["fit_status"].isin(["GOOD", "RETRY_GOOD"])]

    axes[0, 0].hist(g_d2["mpv"], bins=35, range=(150, 1050), alpha=0.65, color="#1f77b4", label=f"D2 (n={len(g_d2)}, med={g_d2['mpv'].median():.1f})")
    axes[0, 0].hist(g_he4["mpv"], bins=35, range=(150, 1050), alpha=0.55, color="#d62728", label=f"He4 (n={len(g_he4)}, med={g_he4['mpv'].median():.1f})")
    axes[0, 0].set_xlabel("Pre-Calibration Fitted MPV [ADC]")
    axes[0, 0].set_ylabel("Number of Wires")
    axes[0, 0].set_title("Pre-Calibration MPV Distribution (GOOD + RETRY_GOOD)")
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.25)

    axes[0, 1].hist(g_d2["gain_optA"], bins=35, range=(0.2, 2.2), alpha=0.65, color="#1f77b4", label=f"D2 Option A (IQR={np.percentile(g_d2['gain_optA'],75)-np.percentile(g_d2['gain_optA'],25):.2f})")
    axes[0, 1].hist(g_he4["gain_optA"], bins=35, range=(0.2, 2.2), alpha=0.55, color="#d62728", label=f"He4 Option A (IQR={np.percentile(g_he4['gain_optA'],75)-np.percentile(g_he4['gain_optA'],25):.2f})")
    axes[0, 1].axvline(1.0, color="black", ls="--", lw=1.2)
    axes[0, 1].set_xlabel("Per-Wire Gain Constant (Option A)")
    axes[0, 1].set_ylabel("Number of Wires")
    axes[0, 1].set_title("Derived Per-Wire Gain Distribution")
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.25)

    axes[1, 0].hist(100.0 * g_d2["mpv_rel_err"], bins=30, range=(0, 20), alpha=0.65, color="#1f77b4", label=f"D2 (med={100*g_d2['mpv_rel_err'].median():.2f}%)")
    axes[1, 0].hist(100.0 * g_he4["mpv_rel_err"], bins=30, range=(0, 20), alpha=0.55, color="#d62728", label=f"He4 (med={100*g_he4['mpv_rel_err'].median():.2f}%)")
    axes[1, 0].set_xlabel(r"Relative MPV Fit Uncertainty $\sigma_{\mathrm{MPV}} / \mathrm{MPV}$ [%]")
    axes[1, 0].set_ylabel("Number of Wires")
    axes[1, 0].set_title("Relative MPV Fit Uncertainty Distribution")
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.25)

    axes[1, 1].hist(g_d2["chi2_ndf"], bins=30, range=(0, 3.5), alpha=0.65, color="#1f77b4", label=f"D2 (med={g_d2['chi2_ndf'].median():.2f})")
    axes[1, 1].hist(g_he4["chi2_ndf"], bins=30, range=(0, 3.5), alpha=0.55, color="#d62728", label=f"He4 (med={g_he4['chi2_ndf'].median():.2f})")
    axes[1, 1].axvline(1.0, color="black", ls="--", lw=1.2)
    axes[1, 1].set_xlabel(r"Reduced Fit $\chi^2 / \mathrm{ndf}$")
    axes[1, 1].set_ylabel("Number of Wires")
    axes[1, 1].set_title(r"Per-Wire Fit $\chi^2 / \mathrm{ndf}$ Distribution")
    axes[1, 1].legend()
    axes[1, 1].grid(True, alpha=0.25)

    fig.tight_layout()
    fig.savefig(GAIN_PLOT_DIR / "gain_distributions_and_uncertainties.png", dpi=160)
    plt.close(fig)

    # 5. Option A vs Option B Reference Comparison across Layers
    fig, axes = plt.subplots(2, 2, figsize=(14, 10), sharey="row")
    for col_idx, (tname, dft) in enumerate([("D2", df_d2), ("He4", df_he4)]):
        g = dft[dft["fit_status"].isin(["GOOD", "RETRY_GOOD"])]
        ref_a = float(dft["mpv_ref_optA"].iloc[0])

        # Top row: Pre-cal vs Post-cal Option A vs Post-cal Option B layer medians + IQR
        x = np.arange(len(LAYERS))
        pre_med = [g[g["layer"] == l]["mpv"].median() for l in LAYERS]
        pre_iqr = [0.5 * (np.percentile(g[g["layer"] == l]["mpv"], 75) - np.percentile(g[g["layer"] == l]["mpv"], 25)) for l in LAYERS]

        postA_med = [g[(g["layer"] == l) & g["mpv_after_optA"].notna()]["mpv_after_optA"].median() for l in LAYERS]
        postA_iqr = [0.5 * (np.percentile(g[(g["layer"] == l) & g["mpv_after_optA"].notna()]["mpv_after_optA"], 75) - np.percentile(g[(g["layer"] == l) & g["mpv_after_optA"].notna()]["mpv_after_optA"], 25)) for l in LAYERS]

        postB_med = [g[(g["layer"] == l) & g["mpv_after_optB"].notna()]["mpv_after_optB"].median() for l in LAYERS]
        postB_iqr = [0.5 * (np.percentile(g[(g["layer"] == l) & g["mpv_after_optB"].notna()]["mpv_after_optB"], 75) - np.percentile(g[(g["layer"] == l) & g["mpv_after_optB"].notna()]["mpv_after_optB"], 25)) for l in LAYERS]

        ax = axes[0, col_idx]
        ax.errorbar(x - 0.15, pre_med, yerr=pre_iqr, fmt="o-", color="gray", capsize=3, label="Before Calibration (Layer Median ± IQR/2)")
        ax.errorbar(x, postA_med, yerr=postA_iqr, fmt="s-", color="#1f77b4", capsize=3, label="After Option A (Global Ref)")
        ax.errorbar(x + 0.15, postB_med, yerr=postB_iqr, fmt="^-", color="#2ca02c", capsize=3, label="After Option B (Per-Layer Ref)")
        ax.axhline(ref_a, color="#1f77b4", ls="--", lw=1.1, label=f"Option A Target ({ref_a:.1f} ADC)")
        ax.set_xticks(x)
        ax.set_xticklabels([str(l) for l in LAYERS])
        ax.set_xlabel("Physical Layer")
        ax.set_ylabel("Layer MPV [ADC]")
        ax.set_title(f"{tname}: Layer MPV Progression Before vs Option A vs Option B")
        ax.grid(True, alpha=0.25)
        ax.legend(fontsize=8)

        # Bottom row: Fractional residual boxplot per layer for Option A vs Option B
        ax2 = axes[1, col_idx]
        data_a = [100.0 * g[(g["layer"] == l) & g["fractional_residual_optA"].notna()]["fractional_residual_optA"].values for l in LAYERS]
        data_b = [100.0 * g[(g["layer"] == l) & g["fractional_residual_optB"].notna()]["fractional_residual_optB"].values for l in LAYERS]
        bp1 = ax2.boxplot(data_a, positions=x - 0.16, widths=0.28, patch_artist=True, showfliers=False)
        bp2 = ax2.boxplot(data_b, positions=x + 0.16, widths=0.28, patch_artist=True, showfliers=False)
        for patch in bp1["boxes"]:
            patch.set_facecolor("#1f77b4")
            patch.set_alpha(0.65)
        for patch in bp2["boxes"]:
            patch.set_facecolor("#2ca02c")
            patch.set_alpha(0.65)
        ax2.axhline(0.0, color="black", ls="--", lw=1.1)
        ax2.set_xticks(x)
        ax2.set_xticklabels([str(l) for l in LAYERS])
        ax2.set_ylim(-15, 15)
        ax2.set_xlabel("Physical Layer")
        ax2.set_ylabel(r"Closure Residual $(\mathrm{MPV}_{\mathrm{post}} - \mathrm{MPV}_{\mathrm{ref}}) / \mathrm{MPV}_{\mathrm{ref}}$ [%]")
        ax2.set_title(f"{tname}: Second-Pass Closure Residuals by Layer (Blue=Opt A, Green=Opt B)")
        ax2.grid(True, alpha=0.25)

    fig.tight_layout()
    fig.savefig(GAIN_PLOT_DIR / "option_A_vs_option_B_reference_comparison.png", dpi=160)
    plt.close(fig)


def plot_closure(df_d2: pd.DataFrame, df_he4: pd.DataFrame):
    # 1. MPV before vs after by wire for each layer (D2 and He4)
    for tname, dft in [("D2", df_d2), ("He4", df_he4)]:
        fig, axes = plt.subplots(4, 2, figsize=(14, 13), sharey=True)
        axes = axes.flatten()
        ref_a = float(dft["mpv_ref_optA"].iloc[0])
        for i, lay in enumerate(LAYERS):
            ax = axes[i]
            sub = dft[(dft["layer"] == lay) & dft["fit_status"].isin(["GOOD", "RETRY_GOOD"])]
            sub_post = sub[sub["mpv_after_optA"].notna()]
            ax.errorbar(
                sub["wire"], sub["mpv"], yerr=sub["mpv_err"],
                fmt="o", ms=3.8, color="#d62728", alpha=0.75, elinewidth=0.9, capsize=1.5,
                label=f"Before Cal (MAD={1.4826*np.median(np.abs(sub['mpv']-sub['mpv'].median())):.1f})",
            )
            ax.errorbar(
                sub_post["wire"], sub_post["mpv_after_optA"], yerr=sub_post["mpv_after_err_optA"],
                fmt="s", ms=3.8, color="#1f77b4", alpha=0.85, elinewidth=0.9, capsize=1.5,
                label=f"After Cal Refit (MAD={1.4826*np.median(np.abs(sub_post['mpv_after_optA']-sub_post['mpv_after_optA'].median())):.1f})",
            )
            ax.axhline(ref_a, color="black", ls="--", lw=1.2, label=f"Target Ref ({ref_a:.1f} ADC)")
            ax.set_title(f"{tname} Layer {lay} (Wires 1..{EXPECTED_WIRES[lay]})")
            ax.set_xlim(0, EXPECTED_WIRES[lay] + 2)
            ax.set_ylim(100, 1050)
            ax.grid(True, alpha=0.25)
            if i % 2 == 0:
                ax.set_ylabel("Fitted Landau MPV [ADC]")
            if i >= 6:
                ax.set_xlabel("Wire Number")
            ax.legend(loc="upper right", fontsize=7.5)
        fig.suptitle(f"{tname}: True Second-Pass Refit Closure — MPV Before vs After Calibration by Wire", fontsize=13, y=0.995)
        fig.tight_layout()
        fig.savefig(CLOS_PLOT_DIR / f"mpv_before_after_by_wire_{tname}.png", dpi=160)
        plt.close(fig)

    # 2. 1D Histograms and Per-Layer Boxplots of MPV Before vs After Calibration
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    for idx, (tname, dft) in enumerate([("D2", df_d2), ("He4", df_he4)]):
        g = dft[dft["fit_status"].isin(["GOOD", "RETRY_GOOD"])]
        gp = g[g["mpv_after_optA"].notna()]
        ref_a = float(dft["mpv_ref_optA"].iloc[0])

        ax_h = axes[0, idx]
        ax_h.hist(g["mpv"], bins=40, range=(150, 950), alpha=0.55, color="#d62728",
                  label=f"Before Cal (std={g['mpv'].std():.1f}, MAD={1.4826*np.median(np.abs(g['mpv']-g['mpv'].median())):.1f}, CV={100*g['mpv'].std()/g['mpv'].mean():.1f}%)")
        ax_h.hist(gp["mpv_after_optA"], bins=40, range=(150, 950), alpha=0.75, color="#1f77b4",
                  label=f"After Cal Refit (std={gp['mpv_after_optA'].std():.1f}, MAD={1.4826*np.median(np.abs(gp['mpv_after_optA']-gp['mpv_after_optA'].median())):.1f}, CV={100*gp['mpv_after_optA'].std()/gp['mpv_after_optA'].mean():.1f}%)")
        ax_h.axvline(ref_a, color="black", ls="--", lw=1.3, label=f"Reference MPV = {ref_a:.1f} ADC")
        ax_h.set_xlabel("Fitted Landau MPV [ADC]")
        ax_h.set_ylabel("Number of Wires")
        ax_h.set_title(f"{tname}: MPV Distribution Before vs After Second-Pass Refit")
        ax_h.legend(fontsize=8)
        ax_h.grid(True, alpha=0.25)

        ax_b = axes[1, idx]
        x = np.arange(len(LAYERS))
        pre_l = [g[g["layer"] == l]["mpv"].values for l in LAYERS]
        post_l = [gp[gp["layer"] == l]["mpv_after_optA"].values for l in LAYERS]
        bp_pre = ax_b.boxplot(pre_l, positions=x - 0.16, widths=0.28, patch_artist=True, showfliers=False)
        bp_post = ax_b.boxplot(post_l, positions=x + 0.16, widths=0.28, patch_artist=True, showfliers=False)
        for p in bp_pre["boxes"]:
            p.set_facecolor("#d62728")
            p.set_alpha(0.55)
        for p in bp_post["boxes"]:
            p.set_facecolor("#1f77b4")
            p.set_alpha(0.75)
        ax_b.axhline(ref_a, color="black", ls="--", lw=1.2)
        ax_b.set_xticks(x)
        ax_b.set_xticklabels([str(l) for l in LAYERS])
        ax_b.set_xlabel("Physical Layer")
        ax_b.set_ylabel("Fitted MPV [ADC]")
        ax_b.set_title(f"{tname}: Per-Layer MPV Boxplots (Red = Before, Blue = After Option A)")
        ax_b.grid(True, alpha=0.25)

    fig.tight_layout()
    fig.savefig(CLOS_PLOT_DIR / "mpv_before_after_histograms_and_boxplots.png", dpi=160)
    plt.close(fig)

    # 3. Fractional Closure Residuals by Global Channel Index and Histograms
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    for idx, (tname, dft, col) in enumerate([("D2", df_d2, "#1f77b4"), ("He4", df_he4, "#2ca02c")]):
        gp = dft[dft["fractional_residual_optA"].notna()]
        res_pct = 100.0 * gp["fractional_residual_optA"].values
        med_abs = np.median(np.abs(res_pct))
        mad_val = 1.4826 * np.median(np.abs(res_pct - np.median(res_pct)))
        rms_val = np.sqrt(np.mean(res_pct ** 2))

        ax_s = axes[0, idx]
        ax_s.scatter(gp["global_channel_idx"], res_pct, s=14, color=col, alpha=0.8)
        ax_s.axhline(0.0, color="black", ls="--", lw=1.2)
        ax_s.axhline(5.0, color="gray", ls=":", lw=1.0)
        ax_s.axhline(-5.0, color="gray", ls=":", lw=1.0)
        ax_s.set_xlim(0, 577)
        ax_s.set_ylim(-25, 25)
        ax_s.set_xlabel("Global Channel Index (1..576)")
        ax_s.set_ylabel(r"Fractional Residual $(\mathrm{MPV}_{\mathrm{after}} - \mathrm{MPV}_{\mathrm{ref}}) / \mathrm{MPV}_{\mathrm{ref}}$ [%]")
        ax_s.set_title(f"{tname}: Closure Residual vs Global Channel (n={len(gp)})")
        ax_s.grid(True, alpha=0.25)

        ax_h = axes[1, idx]
        ax_h.hist(res_pct, bins=40, range=(-20, 20), color=col, alpha=0.75, edgecolor="black", lw=0.5,
                  label=f"med|res| = {med_abs:.2f}%\nMAD = {mad_val:.2f}%\nRMS = {rms_val:.2f}%")
        ax_h.axvline(0.0, color="black", ls="--", lw=1.2)
        ax_h.set_xlabel(r"Fractional Closure Residual $(\mathrm{MPV}_{\mathrm{after}} - \mathrm{MPV}_{\mathrm{ref}}) / \mathrm{MPV}_{\mathrm{ref}}$ [%]")
        ax_h.set_ylabel("Number of Wires")
        ax_h.set_title(f"{tname}: Second-Pass Refit Closure Residual Distribution")
        ax_h.legend(fontsize=9)
        ax_h.grid(True, alpha=0.25)

    fig.tight_layout()
    fig.savefig(CLOS_PLOT_DIR / "closure_fractional_residuals_by_wire_and_layer.png", dpi=160)
    plt.close(fig)

    # 4. 2D Layer x Wire Closure Residual Heatmaps
    fig, axes = plt.subplots(2, 2, figsize=(15, 9.5))
    panels = [
        (axes[0, 0], make_grid(df_d2, "mpv_after_optA"), "D2 Post-Calibration Refit MPV [ADC] (Option A)", "viridis", 250, 420),
        (axes[0, 1], make_grid(df_he4, "mpv_after_optA"), "He4 Post-Calibration Refit MPV [ADC] (Option A)", "viridis", 300, 470),
        (axes[1, 0], 100.0 * make_grid(df_d2, "fractional_residual_optA"), "D2 Fractional Closure Residual [%] (Option A)", "RdBu_r", -12, 12),
        (axes[1, 1], 100.0 * make_grid(df_he4, "fractional_residual_optA"), "He4 Fractional Closure Residual [%] (Option A)", "RdBu_r", -12, 12),
    ]
    for ax, grid, title, cmap, vmin, vmax in panels:
        im = ax.imshow(grid, aspect="auto", origin="lower", cmap=cmap, vmin=vmin, vmax=vmax, extent=[0.5, 99.5, -0.5, 7.5])
        ax.set_yticks(range(len(LAYERS)))
        ax.set_yticklabels([str(l) for l in LAYERS])
        ax.set_xlabel("Wire Number")
        ax.set_ylabel("Physical Layer")
        ax.set_title(title)
        for il, lay in enumerate(LAYERS):
            ax.plot([EXPECTED_WIRES[lay] + 0.5, EXPECTED_WIRES[lay] + 0.5], [il - 0.5, il + 0.5], color="black", lw=1.5)
        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.suptitle("2D Layer-Wire Maps of Post-Calibration MPV and Second-Pass Fractional Closure Residuals", fontsize=13, y=0.995)
    fig.tight_layout()
    fig.savefig(CLOS_PLOT_DIR / "closure_2d_layer_wire_residual_maps.png", dpi=160)
    plt.close(fig)


def plot_d2_vs_he4(df_cmp: pd.DataFrame):
    both = df_cmp[df_cmp["gain_D2_optA"].notna() & df_cmp["gain_He4_optA"].notna()].copy()
    r_mpv = np.corrcoef(both["mpv_D2"], both["mpv_He4"])[0, 1]
    s_mpv = both["mpv_D2"].corr(both["mpv_He4"], method="spearman")
    r_g_a = np.corrcoef(both["gain_D2_optA"], both["gain_He4_optA"])[0, 1]
    s_g_a = both["gain_D2_optA"].corr(both["gain_He4_optA"], method="spearman")
    r_g_b = np.corrcoef(both["gain_D2_optB"], both["gain_He4_optB"])[0, 1]
    s_g_b = both["gain_D2_optB"].corr(both["gain_He4_optB"], method="spearman")

    # 1. Scatter plots of MPV and Gain (Option A & Option B)
    fig, axes = plt.subplots(1, 3, figsize=(16, 5.2))
    axes[0].errorbar(
        both["mpv_He4"], both["mpv_D2"], xerr=both["mpv_err_He4"], yerr=both["mpv_err_D2"],
        fmt="o", ms=3.5, color="#1f77b4", alpha=0.65, elinewidth=0.7,
        label=f"n={len(both)} common wires\nPearson r={r_mpv:.3f}\nSpearman r={s_mpv:.3f}",
    )
    axes[0].plot([150, 950], [150, 950], "k--", lw=1.2, label="y = x")
    axes[0].set_xlim(150, 950)
    axes[0].set_ylim(150, 950)
    axes[0].set_xlabel("He4 Fitted MPV [ADC]")
    axes[0].set_ylabel("D2 Fitted MPV [ADC]")
    axes[0].set_title("Pre-Calibration MPV: D2 vs He4")
    axes[0].legend(fontsize=8.5)
    axes[0].grid(True, alpha=0.25)

    axes[1].errorbar(
        both["gain_He4_optA"], both["gain_D2_optA"], xerr=both["gain_err_He4_optA"], yerr=both["gain_err_D2_optA"],
        fmt="o", ms=3.5, color="#2ca02c", alpha=0.65, elinewidth=0.7,
        label=f"n={len(both)} common wires\nPearson r={r_g_a:.3f}\nSpearman r={s_g_a:.3f}",
    )
    axes[1].plot([0.2, 2.0], [0.2, 2.0], "k--", lw=1.2, label="y = x")
    axes[1].set_xlim(0.2, 2.0)
    axes[1].set_ylim(0.2, 2.0)
    axes[1].set_xlabel(r"He4 Gain Constant $g_{\mathrm{He4}}$ (Option A)")
    axes[1].set_ylabel(r"D2 Gain Constant $g_{\mathrm{D2}}$ (Option A)")
    axes[1].set_title("Derived Gain (Option A Global): D2 vs He4")
    axes[1].legend(fontsize=8.5)
    axes[1].grid(True, alpha=0.25)

    axes[2].plot(
        both["gain_He4_optB"], both["gain_D2_optB"], "o", ms=3.8, color="#ff7f0e", alpha=0.75,
        label=f"n={len(both)} common wires\nPearson r={r_g_b:.3f}\nSpearman r={s_g_b:.3f}",
    )
    axes[2].plot([0.2, 2.0], [0.2, 2.0], "k--", lw=1.2, label="y = x")
    axes[2].set_xlim(0.2, 2.0)
    axes[2].set_ylim(0.2, 2.0)
    axes[2].set_xlabel(r"He4 Gain Constant $g_{\mathrm{He4}}$ (Option B)")
    axes[2].set_ylabel(r"D2 Gain Constant $g_{\mathrm{D2}}$ (Option B)")
    axes[2].set_title("Derived Gain (Option B Per-Layer): D2 vs He4")
    axes[2].legend(fontsize=8.5)
    axes[2].grid(True, alpha=0.25)

    fig.tight_layout()
    fig.savefig(CMP_PLOT_DIR / "d2_vs_he4_mpv_and_gain_scatter.png", dpi=160)
    plt.close(fig)

    # 2. Distributions of gain difference, gain ratio, pull, and per-layer difference boxplots
    fig, axes = plt.subplots(2, 2, figsize=(13, 10))
    diff = both["gain_diff_optA"].values
    ratio = both["gain_ratio_optA"].values
    pull = both["gain_pull_optA"].dropna().values

    axes[0, 0].hist(diff, bins=40, range=(-0.8, 0.8), color="#1f77b4", alpha=0.75, edgecolor="black", lw=0.5,
                    label=f"median = {np.median(diff):+.4f}\nMAD = {1.4826*np.median(np.abs(diff-np.median(diff))):.4f}\nRMS = {np.sqrt(np.mean(diff**2)):.4f}")
    axes[0, 0].axvline(0.0, color="black", ls="--", lw=1.2)
    axes[0, 0].set_xlabel(r"Gain Difference $\Delta g = g_{\mathrm{D2}} - g_{\mathrm{He4}}$ (Option A)")
    axes[0, 0].set_ylabel("Number of Common Wires")
    axes[0, 0].set_title("D2 vs He4 Gain Difference Distribution")
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.25)

    axes[0, 1].hist(ratio, bins=40, range=(0.3, 1.7), color="#2ca02c", alpha=0.75, edgecolor="black", lw=0.5,
                    label=f"median = {np.median(ratio):.4f}\nMAD = {1.4826*np.median(np.abs(ratio-np.median(ratio))):.4f}\nIQR = {np.percentile(ratio,75)-np.percentile(ratio,25):.4f}")
    axes[0, 1].axvline(1.0, color="black", ls="--", lw=1.2)
    axes[0, 1].set_xlabel(r"Gain Ratio $g_{\mathrm{D2}} / g_{\mathrm{He4}}$ (Option A)")
    axes[0, 1].set_ylabel("Number of Common Wires")
    axes[0, 1].set_title("D2 vs He4 Gain Ratio Distribution")
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.25)

    axes[1, 0].hist(pull, bins=40, range=(-6, 6), color="#9467bd", alpha=0.75, edgecolor="black", lw=0.5,
                    label=f"median = {np.median(pull):+.2f}\nMAD = {1.4826*np.median(np.abs(pull-np.median(pull))):.2f}")
    axes[1, 0].axvline(0.0, color="black", ls="--", lw=1.2)
    axes[1, 0].set_xlabel(r"Pull $(g_{\mathrm{D2}} - g_{\mathrm{He4}}) / \sqrt{\sigma_{g,\mathrm{D2}}^2 + \sigma_{g,\mathrm{He4}}^2}$")
    axes[1, 0].set_ylabel("Number of Common Wires")
    axes[1, 0].set_title("Normalized Gain Pull Distribution")
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.25)

    x = np.arange(len(LAYERS))
    diff_by_lay = [both[both["layer"] == l]["gain_diff_optA"].values for l in LAYERS]
    bp = axes[1, 1].boxplot(diff_by_lay, positions=x, widths=0.45, patch_artist=True, showfliers=True)
    for p in bp["boxes"]:
        p.set_facecolor("#1f77b4")
        p.set_alpha(0.65)
    axes[1, 1].axhline(0.0, color="black", ls="--", lw=1.2)
    axes[1, 1].set_xticks(x)
    axes[1, 1].set_xticklabels([str(l) for l in LAYERS])
    axes[1, 1].set_ylim(-0.6, 0.6)
    axes[1, 1].set_xlabel("Physical Layer")
    axes[1, 1].set_ylabel(r"$\Delta g = g_{\mathrm{D2}} - g_{\mathrm{He4}}$")
    axes[1, 1].set_title("D2 vs He4 Gain Difference by Layer")
    axes[1, 1].grid(True, alpha=0.25)

    fig.tight_layout()
    fig.savefig(CMP_PLOT_DIR / "d2_vs_he4_gain_diff_ratio_pull_distributions.png", dpi=160)
    plt.close(fig)

    # 3. 2D Layer x Wire Heatmap of Gain Difference & Compatibility Map
    fig, axes = plt.subplots(2, 1, figsize=(13, 8.5))
    grid_diff = make_grid(df_cmp, "gain_diff_optA")
    im0 = axes[0].imshow(grid_diff, aspect="auto", origin="lower", cmap="RdBu_r", vmin=-0.45, vmax=0.45, extent=[0.5, 99.5, -0.5, 7.5])
    axes[0].set_yticks(range(len(LAYERS)))
    axes[0].set_yticklabels([str(l) for l in LAYERS])
    axes[0].set_xlabel("Wire Number")
    axes[0].set_ylabel("Physical Layer")
    axes[0].set_title(r"2D Layer-Wire Map of Gain Difference $\Delta g = g_{\mathrm{D2}} - g_{\mathrm{He4}}$ (Option A)")
    for il, lay in enumerate(LAYERS):
        axes[0].plot([EXPECTED_WIRES[lay] + 0.5, EXPECTED_WIRES[lay] + 0.5], [il - 0.5, il + 0.5], color="black", lw=1.5)
    fig.colorbar(im0, ax=axes[0], fraction=0.046, pad=0.04)

    code_map = {
        "COMPATIBLE": 1.0,
        "RUN_PERIOD_GAIN_DRIFT": 2.0,
        "HE4_ONLY_VALID": 3.0,
        "D2_ONLY_VALID": 4.0,
        "NEITHER_VALID": 0.0,
    }
    df_cmp_coded = df_cmp.copy()
    df_cmp_coded["code"] = df_cmp_coded["compatibility_flag"].map(code_map)
    grid_code = make_grid(df_cmp_coded, "code")
    cmap_cat = matplotlib.colors.ListedColormap(["#d9d9d9", "#2ca02c", "#ff7f0e", "#1f77b4", "#9467bd"])
    bounds = [-0.5, 0.5, 1.5, 2.5, 3.5, 4.5]
    norm = matplotlib.colors.BoundaryNorm(bounds, cmap_cat.N)
    im1 = axes[1].imshow(grid_code, aspect="auto", origin="lower", cmap=cmap_cat, norm=norm, extent=[0.5, 99.5, -0.5, 7.5])
    axes[1].set_yticks(range(len(LAYERS)))
    axes[1].set_yticklabels([str(l) for l in LAYERS])
    axes[1].set_xlabel("Wire Number")
    axes[1].set_ylabel("Physical Layer")
    axes[1].set_title("576-Channel Calibration Coverage & D2-vs-He4 Compatibility Classification")
    for il, lay in enumerate(LAYERS):
        axes[1].plot([EXPECTED_WIRES[lay] + 0.5, EXPECTED_WIRES[lay] + 0.5], [il - 0.5, il + 0.5], color="black", lw=1.5)
    cbar = fig.colorbar(im1, ax=axes[1], ticks=[0, 1, 2, 3, 4], fraction=0.046, pad=0.04)
    cbar.ax.set_yticklabels(["Uncalibrated (49)", "Compatible Both (341)", "Run Drift Both (39)", "He4 Only (139)", "D2 Only (8)"])

    fig.tight_layout()
    fig.savefig(CMP_PLOT_DIR / "d2_vs_he4_layer_wire_difference_heatmap.png", dpi=160)
    plt.close(fig)


def main():
    df_d2 = pd.read_csv(TABLE_DIR / "gain_constants_D2.csv")
    df_he4 = pd.read_csv(TABLE_DIR / "gain_constants_He4.csv")
    df_final = pd.read_csv(TABLE_DIR / "gain_constants_final.csv")
    df_cmp = pd.read_csv(TABLE_DIR / "d2_he4_comparison.csv")

    print("Generating global gain plots ...")
    plot_gains(df_d2, df_he4, df_final)
    print("Generating global closure plots ...")
    plot_closure(df_d2, df_he4)
    print("Generating D2-vs-He4 comparison plots ...")
    plot_d2_vs_he4(df_cmp)
    print("All global plots generated successfully.")


if __name__ == "__main__":
    main()
