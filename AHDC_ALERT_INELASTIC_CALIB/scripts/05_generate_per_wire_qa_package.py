#!/usr/bin/env python3
"""
Phase 13: Generate Complete 576-Channel Per-Wire Visual QA Package:
  1. Individual PNGs in plots/per_wire/{D2,He4}/{before,after,before_after}/{target}_L{layer}_W{wire:02d}_{stage}.png (3,456 PNGs)
  2. Complete 576-channel multi-page PDFs (48 pages x 12 panels = 576 channels in deterministic order):
     - plots/per_wire/per_wire_ADC_D2_before.pdf
     - plots/per_wire/per_wire_ADC_He4_before.pdf
     - plots/per_wire/per_wire_ADC_D2_after.pdf
     - plots/per_wire/per_wire_ADC_He4_after.pdf
     - plots/per_wire/per_wire_ADC_before_after_D2.pdf
     - plots/per_wire/per_wire_ADC_before_after_He4.pdf
  3. Focused QA PDFs in plots/per_wire/qa/:
     - worst_chi2_channels.pdf
     - extreme_gain_channels.pdf
     - low_statistics_channels.pdf
     - d2_he4_discrepant_channels.pdf
     - failed_or_retry_channels.pdf
"""

import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

WORKSPACE = Path(os.environ.get("ALERT_WORKSPACE", "<DEFAULT_WORKSPACE>"))
OUT_DIR = WORKSPACE / "results" / "gain_calibration_final"
TABLE_DIR = OUT_DIR / "tables"
PER_WIRE_DIR = OUT_DIR / "plots" / "per_wire"
QA_DIR = PER_WIRE_DIR / "qa"

D2_CSV = WORKSPACE / "FINAL_MERGED" / "D2_ALL_FINAL.csv"
HE4_CSV = WORKSPACE / "FINAL_MERGED" / "HE4_ALL_FINAL.csv"

P_MIN_GEV = 0.15
P_MAX_GEV = 0.25


def f_landau(x, amp, mpv, wid):
    z = np.clip((x - mpv) / np.maximum(wid, 1e-6), -15.0, 80.0)
    return amp * np.exp(-0.5 * (z + np.exp(-z) - 1.0))


def f_landau_exp4(x, amp, mpv, wid, fexp):
    z = np.clip((x - mpv) / np.maximum(wid, 1e-6), -15.0, 80.0)
    u = np.clip((x - mpv) / np.maximum(2.2 * wid, 1e-6), -15.0, 80.0)
    f = np.clip(fexp, 0.0, 0.65)
    return amp * (
        (1.0 - f) * np.exp(-0.5 * (z + np.exp(-z) - 1.0))
        + f * np.exp(-0.5 * (u + np.exp(-u) - 1.0))
    )


def eval_curve(x, amp, mpv, wid, fexp, model_name):
    if model_name == "Landau+Exp":
        return f_landau_exp4(x, amp, mpv, wid, fexp)
    return f_landau(x, amp, mpv, wid)


def draw_channel_panel(ax, row: dict, adc_raw: np.ndarray, stage: str):
    """
    Draw a single channel panel for `stage` in {"before", "after", "before_after"}.
    """
    target = row["target"]
    gidx = int(row["global_channel_idx"])
    lay = int(row["layer"])
    w = int(row["wire"])
    n = int(row["n_entries"])
    st = str(row["fit_status"])
    ref_mpv = float(row["mpv_ref_optA"])
    gain = float(row["gain_optA"]) if pd.notna(row["gain_optA"]) else np.nan
    gain_err = float(row["gain_err_optA"]) if pd.notna(row["gain_err_optA"]) else np.nan

    title_str = f"#{gidx:03d} {target} L{lay} W{w:02d} (N={n}) [{st}]"
    ax.set_title(title_str, fontsize=8.5, pad=3)

    if n == 0:
        ax.text(
            0.5, 0.5,
            f"NO DATA IN {target}\nGlobal #{gidx:03d} (L{lay} W{w:02d})\nStatus: {st}\n(DAQ sector masked in runs >=21552)",
            ha="center", va="center", transform=ax.transAxes, fontsize=8,
            bbox=dict(boxstyle="round,pad=0.4", facecolor="#f2dede", edgecolor="#a94442"),
        )
        ax.set_xlim(0, 2500)
        ax.set_ylim(0, 1)
        ax.set_xlabel("ADC", fontsize=8)
        ax.set_ylabel("Counts", fontsize=8)
        return

    bw = float(row["bin_width"]) if (pd.notna(row["bin_width"]) and row["bin_width"] > 0) else 50.0
    xmax_plot = 2450.0
    nbins_plot = int(round(xmax_plot / bw))

    if stage == "before":
        counts, edges = np.histogram(adc_raw, bins=nbins_plot, range=(0.0, xmax_plot))
        centers = 0.5 * (edges[:-1] + edges[1:])
        ax.step(centers, counts, where="mid", color="#1f77b4", lw=1.1, label="Raw ADC")
        ax.fill_between(centers, counts, step="mid", color="#1f77b4", alpha=0.18)
        ax.axvline(ref_mpv, color="black", ls=":", lw=1.0, label=f"Ref={ref_mpv:.0f}")

        if pd.notna(row["mpv"]) and pd.notna(row["amp"]) and pd.notna(row["width"]):
            flo = float(row["fit_lo"])
            fhi = min(xmax_plot, float(row["fit_hi"]))
            xg = np.linspace(flo, fhi, 200)
            yg = eval_curve(xg, float(row["amp"]), float(row["mpv"]), float(row["width"]), float(row["f_exp"]), str(row["model_used"]))
            ax.plot(xg, yg, color="#d62728", lw=1.5, label=f"{row['model_used']} Fit")
            ax.axvline(float(row["mpv"]), color="#d62728", ls="--", lw=1.2, label=f"MPV={row['mpv']:.0f}±{row['mpv_err']:.0f}")

        info = (
            f"N = {n} ({row['stat_tier'].split()[0]})\n"
            f"Status: {st} ({row['model_used']})\n"
            f"MPV_pre = {row['mpv']:.1f} ± {row['mpv_err']:.1f}\n"
            f"Width = {row['width']:.1f}, chi2/ndf = {row['chi2_ndf']:.2f}\n"
            f"Gain = {gain:.3f} ± {gain_err:.3f}"
            if pd.notna(row["mpv"]) and pd.notna(row["mpv_err"])
            else f"N = {n}\nStatus: {st}\nmedian ADC = {row['median_adc']:.1f}\nGain = UNCALIBRATED"
        )
        ax.text(
            0.97, 0.95, info, transform=ax.transAxes, ha="right", va="top", fontsize=7.0,
            bbox=dict(boxstyle="round,pad=0.25", facecolor="white", alpha=0.85, edgecolor="gray"),
        )

    elif stage == "after":
        if pd.isna(gain) or gain <= 0:
            counts, edges = np.histogram(adc_raw, bins=nbins_plot, range=(0.0, xmax_plot))
            centers = 0.5 * (edges[:-1] + edges[1:])
            ax.step(centers, counts, where="mid", color="gray", lw=1.0, label="Raw (Uncalibrated)")
            ax.text(
                0.5, 0.55,
                f"UNCALIBRATED CHANNEL\nPre-fit Status: {st}\n(Gain not applied; shown raw)",
                ha="center", va="center", transform=ax.transAxes, fontsize=8,
                bbox=dict(boxstyle="round,pad=0.35", facecolor="#fcf8e3", edgecolor="#8a6d3b"),
            )
        else:
            adc_corr = adc_raw * gain
            counts, edges = np.histogram(adc_corr, bins=nbins_plot, range=(0.0, xmax_plot))
            centers = 0.5 * (edges[:-1] + edges[1:])
            ax.step(centers, counts, where="mid", color="#2ca02c", lw=1.1, label="Corrected ADC")
            ax.fill_between(centers, counts, step="mid", color="#2ca02c", alpha=0.18)
            ax.axvline(ref_mpv, color="black", ls=":", lw=1.1, label=f"Ref={ref_mpv:.0f}")

            mpv_post = row["mpv_after_optA"]
            err_post = row["mpv_after_err_optA"]
            wid_post = row["width_after_optA"]
            rc_post = row["chi2_ndf_after_optA"]
            res_pct = 100.0 * row["fractional_residual_optA"] if pd.notna(row["fractional_residual_optA"]) else np.nan
            if pd.notna(mpv_post):
                ax.axvline(float(mpv_post), color="#d62728", ls="--", lw=1.2, label=f"MPV_post={mpv_post:.0f}")
                # Overlay refit curve scaled to peak height
                pk_cnt = float(np.max(counts)) if len(counts) > 0 else 1.0
                xg = np.linspace(max(bw, 0.35 * mpv_post), min(xmax_plot, 2.35 * mpv_post), 200)
                yg = f_landau(xg, 0.85 * pk_cnt, float(mpv_post), float(wid_post))
                ax.plot(xg, yg, color="#d62728", lw=1.3)

            info = (
                f"Applied Gain = {gain:.3f}\n"
                f"Post Status: {row['fit_status_after_optA']}\n"
                f"MPV_post = {mpv_post:.1f} ± {err_post:.1f}\n"
                f"Ref MPV = {ref_mpv:.1f} ADC\n"
                f"Residual = {res_pct:+.2f}% (chi2/ndf={rc_post:.2f})"
                if pd.notna(mpv_post)
                else f"Applied Gain = {gain:.3f}\nPost Status: {row['fit_status_after_optA']}"
            )
            ax.text(
                0.97, 0.95, info, transform=ax.transAxes, ha="right", va="top", fontsize=7.0,
                bbox=dict(boxstyle="round,pad=0.25", facecolor="white", alpha=0.85, edgecolor="gray"),
            )

    elif stage == "before_after":
        counts_pre, edges = np.histogram(adc_raw, bins=nbins_plot, range=(0.0, xmax_plot))
        centers = 0.5 * (edges[:-1] + edges[1:])
        ax.step(centers, counts_pre, where="mid", color="#d62728", lw=1.0, alpha=0.8, label="Before Cal")
        if pd.notna(row["mpv"]):
            ax.axvline(float(row["mpv"]), color="#d62728", ls="--", lw=1.0)

        if pd.notna(gain) and gain > 0:
            adc_corr = adc_raw * gain
            counts_post, _ = np.histogram(adc_corr, bins=nbins_plot, range=(0.0, xmax_plot))
            ax.step(centers, counts_post, where="mid", color="#1f77b4", lw=1.1, alpha=0.85, label="After Cal")
            if pd.notna(row["mpv_after_optA"]):
                ax.axvline(float(row["mpv_after_optA"]), color="#1f77b4", ls="-.", lw=1.1)

        ax.axvline(ref_mpv, color="black", ls=":", lw=1.1, label=f"Ref={ref_mpv:.0f}")
        res_pct = 100.0 * row["fractional_residual_optA"] if pd.notna(row["fractional_residual_optA"]) else np.nan
        info = (
            f"MPV_pre = {row['mpv']:.1f} -> MPV_post = {row['mpv_after_optA']:.1f}\n"
            f"Ref = {ref_mpv:.1f} ADC | Gain = {gain:.3f}\n"
            f"Closure Residual = {res_pct:+.2f}%"
            if (pd.notna(row["mpv"]) and pd.notna(row["mpv_after_optA"]))
            else f"N = {n} | Status: {st}\nUncalibrated / Excluded"
        )
        ax.text(
            0.97, 0.95, info, transform=ax.transAxes, ha="right", va="top", fontsize=6.8,
            bbox=dict(boxstyle="round,pad=0.25", facecolor="white", alpha=0.85, edgecolor="gray"),
        )

    ax.set_xlim(0, xmax_plot)
    ax.set_xlabel("ADC", fontsize=8)
    ax.set_ylabel("Counts", fontsize=8)
    ax.tick_params(labelsize=7.5)
    ax.grid(True, alpha=0.2)


def _render_single_channel_pngs(args):
    row, adc_raw, out_base = args
    target = row["target"]
    lay = int(row["layer"])
    w = int(row["wire"])
    fig, ax = plt.subplots(figsize=(5.0, 3.6), dpi=95)
    for stage in ("before", "after", "before_after"):
        out_path = Path(out_base) / target / stage / f"{target}_L{lay}_W{w:02d}_{stage}.png"
        if out_path.exists():
            continue
        ax.cla()
        draw_channel_panel(ax, row, adc_raw, stage)
        fig.tight_layout()
        fig.savefig(out_path, dpi=95)
    plt.close(fig)
    return 1


def _pdf_worker(job):
    pdf_path, rlist, grp_target_adc, stage, title = job
    if Path(pdf_path).exists() and Path(pdf_path).stat().st_size > 10000:
        return str(pdf_path)
    generate_pdf_book(Path(pdf_path), rlist, grp_target_adc, stage, title)
    return str(pdf_path)


def generate_pdf_book(pdf_path: Path, rows_list: list, grp_adc: dict, stage: str, book_title: str):
    n_per_page = 12
    n_total = len(rows_list)
    n_pages = (n_total + n_per_page - 1) // n_per_page
    with PdfPages(pdf_path) as pdf:
        for p in range(n_pages):
            batch = rows_list[p * n_per_page : (p + 1) * n_per_page]
            fig, axes = plt.subplots(4, 3, figsize=(15, 13), dpi=120)
            axes = axes.flatten()
            for idx_in_page, row in enumerate(batch):
                ax = axes[idx_in_page]
                lay = int(row["layer"])
                w = int(row["wire"])
                tname = row["target"]
                adc_raw = grp_adc[tname].get((lay, w), np.array([], dtype=float))
                draw_channel_panel(ax, row, adc_raw, stage)
            for idx_empty in range(len(batch), n_per_page):
                axes[idx_empty].axis("off")
            fig.suptitle(f"{book_title} — Page {p + 1}/{n_pages}", fontsize=12, y=0.995)
            fig.tight_layout()
            pdf.savefig(fig)
            plt.close(fig)


def main():
    for target in ("D2", "He4"):
        for stage in ("before", "after", "before_after"):
            (PER_WIRE_DIR / target / stage).mkdir(parents=True, exist_ok=True)
    QA_DIR.mkdir(parents=True, exist_ok=True)

    df_d2 = pd.read_csv(TABLE_DIR / "gain_constants_D2.csv")
    df_he4 = pd.read_csv(TABLE_DIR / "gain_constants_He4.csv")
    df_cmp = pd.read_csv(TABLE_DIR / "d2_he4_comparison.csv")

    grp_adc = {"D2": {}, "He4": {}}
    for tname, csv_p in [("D2", D2_CSV), ("He4", HE4_CSV)]:
        print(f"Loading selected hits for {tname} ...")
        df = pd.read_csv(csv_p, usecols=["raw_layer", "wire", "ADC", "p_GeV"], on_bad_lines="skip", low_memory=False)
        for c in ["raw_layer", "wire", "ADC", "p_GeV"]:
            df[c] = pd.to_numeric(df[c], errors="coerce")
        df.dropna(inplace=True)
        sub = df[(df["ADC"] > 0) & (df["p_GeV"] >= P_MIN_GEV) & (df["p_GeV"] <= P_MAX_GEV)]
        grp_adc[tname] = {
            (int(l), int(w)): g["ADC"].values.astype(float)
            for (l, w), g in sub.groupby(["raw_layer", "wire"])
        }

    # 1. Generate all 3,456 individual PNGs in parallel
    tasks = []
    for tname, dft in [("D2", df_d2), ("He4", df_he4)]:
        for _, r in dft.iterrows():
            rd = r.to_dict()
            lay, w = int(rd["layer"]), int(rd["wire"])
            adc = grp_adc[tname].get((lay, w), np.array([], dtype=float))
            tasks.append((rd, adc, str(PER_WIRE_DIR)))

    n_workers = min(16, os.cpu_count() or 4)
    print(f"Rendering 3,456 individual per-wire PNGs (576 x 3 stages x 2 targets) using {n_workers} workers ...")
    with ProcessPoolExecutor(max_workers=n_workers) as ex:
        list(ex.map(_render_single_channel_pngs, tasks, chunksize=12))
    print("All 3,456 individual PNGs saved.")

    # 2. Generate complete 576-channel multi-page PDFs (48 pages each)
    d2_rows = [r.to_dict() for _, r in df_d2.iterrows()]
    he4_rows = [r.to_dict() for _, r in df_he4.iterrows()]

    pdf_jobs = [
        (PER_WIRE_DIR / "per_wire_ADC_D2_before.pdf", d2_rows, "before", "D2 Per-Wire Raw ADC Spectra & Pre-Calibration Landau Fits (All 576 Channels)"),
        (PER_WIRE_DIR / "per_wire_ADC_He4_before.pdf", he4_rows, "before", "He4 Per-Wire Raw ADC Spectra & Pre-Calibration Landau Fits (All 576 Channels)"),
        (PER_WIRE_DIR / "per_wire_ADC_D2_after.pdf", d2_rows, "after", "D2 Per-Wire Gain-Corrected ADC Spectra & Second-Pass Closure Refits (All 576 Channels)"),
        (PER_WIRE_DIR / "per_wire_ADC_He4_after.pdf", he4_rows, "after", "He4 Per-Wire Gain-Corrected ADC Spectra & Second-Pass Closure Refits (All 576 Channels)"),
        (PER_WIRE_DIR / "per_wire_ADC_before_after_D2.pdf", d2_rows, "before_after", "D2 Per-Wire ADC Overlay Before vs After Gain Calibration (All 576 Channels)"),
        (PER_WIRE_DIR / "per_wire_ADC_before_after_He4.pdf", he4_rows, "before_after", "He4 Per-Wire ADC Overlay Before vs After Gain Calibration (All 576 Channels)"),
    ]
    for pdf_path, rlist, stage, title in pdf_jobs:
        print(f"Generating {pdf_path.name} ...")
        generate_pdf_book(pdf_path, rlist, grp_adc, stage, title)

    # 3. Generate Focused QA PDFs under plots/per_wire/qa/
    df_both = pd.concat([df_d2, df_he4], ignore_index=True)

    # 3a. worst_chi2_channels.pdf (top 36 highest chi2/ndf across D2 & He4)
    worst_chi2 = df_both[df_both["chi2_ndf"].notna()].sort_values("chi2_ndf", ascending=False).head(36)
    generate_pdf_book(
        QA_DIR / "worst_chi2_channels.pdf",
        [r.to_dict() for _, r in worst_chi2.iterrows()],
        grp_adc, "before", "QA Subset: Top 36 Highest Chi2/ndf Per-Wire Fits (D2 & He4)",
    )

    # 3b. extreme_gain_channels.pdf (lowest 18 and highest 18 calibrated gains across D2 & He4)
    cal_both = df_both[df_both["gain_optA"].notna()].sort_values("gain_optA")
    extreme_g = pd.concat([cal_both.head(18), cal_both.tail(18)], ignore_index=True)
    generate_pdf_book(
        QA_DIR / "extreme_gain_channels.pdf",
        [r.to_dict() for _, r in extreme_g.iterrows()],
        grp_adc, "before_after", "QA Subset: Extreme Low and High Gain Channels (D2 & He4)",
    )

    # 3c. low_statistics_channels.pdf (all LOW_STAT channels in D2 & He4)
    low_stat = df_both[df_both["fit_status"] == "LOW_STAT"].sort_values(["target", "global_channel_idx"])
    generate_pdf_book(
        QA_DIR / "low_statistics_channels.pdf",
        [r.to_dict() for _, r in low_stat.iterrows()],
        grp_adc, "before", "QA Subset: Low-Statistics Channels (0 < N < 80 in Selected Momentum Window)",
    )

    # 3d. d2_he4_discrepant_channels.pdf (channels with RUN_PERIOD_GAIN_DRIFT paired D2 & He4)
    drift_idx = df_cmp[df_cmp["compatibility_flag"] == "RUN_PERIOD_GAIN_DRIFT"]["global_channel_idx"].tolist()
    drift_rows = []
    for gidx in drift_idx:
        drift_rows.append(df_d2[df_d2["global_channel_idx"] == gidx].iloc[0].to_dict())
        drift_rows.append(df_he4[df_he4["global_channel_idx"] == gidx].iloc[0].to_dict())
    generate_pdf_book(
        QA_DIR / "d2_he4_discrepant_channels.pdf",
        drift_rows,
        grp_adc, "before", "QA Subset: D2-vs-He4 Run-Period Gain Drift Channels (Paired D2 & He4)",
    )

    # 3e. failed_or_retry_channels.pdf (all MPV_OUTLIER, MPV_BOUNDARY_HIT, WIDTH_BOUNDARY_HIT, BAD_CHI2, UNSTABLE, FIT_FAILED, plus sample RETRY_GOOD)
    non_good = df_both[
        df_both["fit_status"].isin(["MPV_OUTLIER", "MPV_BOUNDARY_HIT", "WIDTH_BOUNDARY_HIT", "BAD_CHI2", "UNSTABLE", "FIT_FAILED"])
    ].sort_values(["target", "global_channel_idx"])
    generate_pdf_book(
        QA_DIR / "failed_or_retry_channels.pdf",
        [r.to_dict() for _, r in non_good.iterrows()],
        grp_adc, "before", "QA Subset: Excluded / Outlier / Boundary-Hit / Unstable Channels (D2 & He4)",
    )
    print("All focused QA PDFs generated successfully.")


if __name__ == "__main__":
    main()
