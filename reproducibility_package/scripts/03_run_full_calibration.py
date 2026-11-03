#!/usr/bin/env python3
"""
Phase 5-12 & 15: Full 576-Channel Per-Wire ADC Fitting, Option A vs Option B Reference
Evaluation, True Row-Level Second-Pass Closure Refit, D2-vs-He4 Cross-Check, and
Generation of All Required Summary CSV Tables.
"""

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
from scipy.ndimage import gaussian_filter1d
from pathlib import Path

BASE_DIR = Path("/home/phys_365/cpaudel/NN/TRAINING/ALERT_AHDC_GAIN_CALIBRATION_CLAS12")
OUT_DIR = BASE_DIR / "results" / "gain_calibration_final"
TABLE_DIR = OUT_DIR / "tables"
TABLE_DIR.mkdir(parents=True, exist_ok=True)

D2_CSV = BASE_DIR / "FINAL_MERGED" / "D2_ALL_FINAL.csv"
HE4_CSV = BASE_DIR / "FINAL_MERGED" / "HE4_ALL_FINAL.csv"

EXPECTED_WIRES = {11: 47, 21: 56, 22: 56, 31: 72, 32: 72, 41: 87, 42: 87, 51: 99}
LAYERS = [11, 21, 22, 31, 32, 41, 42, 51]

# Selected calibration momentum window from Phase 4 decision table
P_MIN_GEV = 0.15
P_MAX_GEV = 0.25


def stat_tier(n: int) -> str:
    if n < 80:
        return "insufficient (<80)"
    elif n < 200:
        return "marginal (80-199)"
    elif n < 500:
        return "usable (200-499)"
    elif n < 1000:
        return "good (500-999)"
    else:
        return "excellent (>=1000)"


def f_landau(x, amp, mpv, wid):
    """
    Moyal analytical form of the Landau distribution parameterized directly by its
    exact mode (Most Probable Value) x = mpv and scale parameter wid:
      f_L(x; A, mpv, w) = A * exp(-0.5 * (z + exp(-z) - 1)),  z = (x - mpv) / w
    At x = mpv (z = 0): f_L(mpv) = A and df_L/dx|_{x=mpv} = 0.
    """
    z = np.clip((x - mpv) / np.maximum(wid, 1e-6), -15.0, 80.0)
    return amp * np.exp(-0.5 * (z + np.exp(-z) - 1.0))


def f_landau_exp4(x, amp, mpv, wid, fexp):
    """
    Two-component Landau + Exponential-tail model preserving the exact analytical peak
    at x = mpv:
      f_LE(x; A, mpv, w, f_exp) = A * [ (1 - f_exp) * L(x; mpv, w) + f_exp * L(x; mpv, 2.2*w) ]
    Both components have zero first derivative and negative second derivative at x = mpv,
    so x = mpv is the exact analytical global maximum for any f_exp in [0, 1], and the
    entire family is strictly scale-invariant under ADC -> g * ADC.
    """
    z = np.clip((x - mpv) / np.maximum(wid, 1e-6), -15.0, 80.0)
    u = np.clip((x - mpv) / np.maximum(2.2 * wid, 1e-6), -15.0, 80.0)
    f = np.clip(fexp, 0.0, 0.65)
    return amp * (
        (1.0 - f) * np.exp(-0.5 * (z + np.exp(-z) - 1.0))
        + f * np.exp(-0.5 * (u + np.exp(-u) - 1.0))
    )


def fit_channel_spectrum(adc: np.ndarray) -> dict:
    """
    Two-stage bounded Landau / Landau+Exponential fitting procedure with automated
    retry and explicit quality-status classification.
    """
    n = int(len(adc))
    base_res = {
        "n_entries": n,
        "stat_tier": stat_tier(n),
        "mean_adc": float(np.mean(adc)) if n > 0 else np.nan,
        "std_adc": float(np.std(adc)) if n > 0 else np.nan,
        "median_adc": float(np.median(adc)) if n > 0 else np.nan,
        "iqr_adc": float(np.percentile(adc, 75) - np.percentile(adc, 25)) if n > 0 else np.nan,
        "q10_adc": float(np.percentile(adc, 10)) if n > 0 else np.nan,
        "q25_adc": float(np.percentile(adc, 25)) if n > 0 else np.nan,
        "q75_adc": float(np.percentile(adc, 75)) if n > 0 else np.nan,
        "q90_adc": float(np.percentile(adc, 90)) if n > 0 else np.nan,
        "amp": np.nan,
        "mpv": np.nan,
        "mpv_err": np.nan,
        "mpv_rel_err": np.nan,
        "width": np.nan,
        "width_err": np.nan,
        "f_exp": 0.0,
        "chi2": np.nan,
        "ndf": 0,
        "chi2_ndf": np.nan,
        "fit_lo": np.nan,
        "fit_hi": np.nan,
        "nbins": 0,
        "bin_width": np.nan,
        "hist_max": np.nan,
        "model_used": "None",
        "fit_status": "NO_DATA" if n == 0 else "LOW_STAT",
    }
    if n == 0 or n < 80:
        return base_res

    q50 = base_res["median_adc"]
    # Hardware dead/attenuated preamplifier channels have collapsed spectra (median ADC ~ 45-100)
    if q50 < 180.0:
        base_res["fit_status"] = "MPV_OUTLIER"
        base_res["mpv"] = q50
        return base_res

    bw = 35.0 if n >= 300 else (50.0 if n >= 140 else 70.0)
    hmax = 3500.0 if q50 < 1200.0 else 4900.0
    nbins = int(round(hmax / bw))
    counts, edges = np.histogram(adc, bins=nbins, range=(0.0, hmax))
    centers = 0.5 * (edges[:-1] + edges[1:])

    base_res["nbins"] = nbins
    base_res["bin_width"] = bw
    base_res["hist_max"] = hmax

    smooth = gaussian_filter1d(counts.astype(float), sigma=2.2)
    valid = np.where((centers >= max(bw, 0.25 * q50)) & (centers <= 0.88 * q50))[0]
    if len(valid) == 0:
        valid = np.arange(len(centers))
    ipk = valid[int(np.argmax(smooth[valid]))]
    pk0 = float(centers[ipk])
    amp0 = float(max(smooth[ipk], 3.0))
    wid0 = float(np.clip(0.32 * q50, 35.0, 800.0))

    try:
        # Stage 1: Quantile-anchored window [0.24*q50, 1.95*q50]
        flo1 = max(0.5 * bw, 0.24 * q50)
        fhi1 = min(hmax - 0.5 * bw, 1.95 * q50)
        m1 = (centers >= flo1) & (centers <= fhi1) & (counts > 0)
        if m1.sum() < 5:
            base_res["fit_status"] = "FIT_FAILED"
            return base_res
        x1, y1 = centers[m1], counts[m1].astype(float)
        s1 = np.sqrt(np.maximum(y1, 1.0))
        b1 = ([0.1 * amp0, 0.22 * q50, 0.06 * q50],
              [5.0 * amp0, 0.92 * q50, 1.45 * q50])
        p0_1 = np.clip([amp0, pk0, wid0], np.array(b1[0]) + 1e-3, np.array(b1[1]) - 1e-3)
        popt1, _ = curve_fit(
            f_landau, x1, y1, p0=p0_1, sigma=s1, absolute_sigma=True, bounds=b1, maxfev=8000
        )
        mpv1, wid1 = float(popt1[1]), float(popt1[2])

        # Stage 2: Refined peak-and-slope window [0.38*mpv1, 2.45*mpv1]
        flo2 = max(0.5 * bw, 0.38 * mpv1)
        fhi2 = min(hmax - 0.5 * bw, 2.45 * mpv1)
        m2 = (centers >= flo2) & (centers <= fhi2) & (counts > 0)
        if m2.sum() < 5:
            base_res["fit_status"] = "FIT_FAILED"
            return base_res
        x2, y2 = centers[m2], counts[m2].astype(float)
        s2 = np.sqrt(np.maximum(y2, 1.0))
        b2 = ([0.1 * popt1[0], 0.22 * q50, 0.06 * q50],
              [5.0 * popt1[0], 0.95 * q50, 1.45 * q50])
        p0_2 = np.clip(popt1, np.array(b2[0]) + 1e-3, np.array(b2[1]) - 1e-3)
        popt2, pcov2 = curve_fit(
            f_landau, x2, y2, p0=p0_2, sigma=s2, absolute_sigma=True, bounds=b2, maxfev=8000
        )
        chi2 = float(np.sum(((y2 - f_landau(x2, *popt2)) / s2) ** 2))
        ndf = max(1, int(len(x2) - 3))
        rchi2 = chi2 / ndf
        perr2 = np.sqrt(np.diag(pcov2))
        mname = "Landau"
        f_exp_val = 0.0
        fit_lo_final, fit_hi_final = flo2, fhi2
        retry = False

        mpv_hit = (
            (popt2[1] - b2[0][1]) / (b2[1][1] - b2[0][1]) < 0.015
            or (b2[1][1] - popt2[1]) / (b2[1][1] - b2[0][1]) < 0.015
        )
        wid_hit = (
            (popt2[2] - b2[0][2]) / (b2[1][2] - b2[0][2]) < 0.015
            or (b2[1][2] - popt2[2]) / (b2[1][2] - b2[0][2]) < 0.015
        )
        rel_err = float(perr2[1] / max(popt2[1], 1.0))

        # Automated Retry with alternative windows and Landau+Exponential model
        if rchi2 > 1.60 or mpv_hit or wid_hit or rel_err > 0.16:
            for lo_f, hi_f, use_exp in [
                (0.16, 2.00, False),
                (0.18, 2.15, True),
                (0.20, 2.20, False),
                (0.14, 1.90, True),
            ]:
                flo_r = max(0.5 * bw, lo_f * q50)
                fhi_r = min(hmax - 0.5 * bw, hi_f * q50)
                mr = (centers >= flo_r) & (centers <= fhi_r) & (counts > 0)
                if mr.sum() < (6 if use_exp else 5):
                    continue
                xr, yr = centers[mr], counts[mr].astype(float)
                sr = np.sqrt(np.maximum(yr, 1.0))
                try:
                    if not use_exp:
                        br = (
                            [0.1 * amp0, 0.16 * q50, 0.05 * q50],
                            [5.0 * amp0, 0.95 * q50, 1.45 * q50],
                        )
                        p0_r = np.clip(
                            [amp0, pk0, wid0],
                            np.array(br[0]) + 1e-3,
                            np.array(br[1]) - 1e-3,
                        )
                        poptr, pcovr = curve_fit(
                            f_landau, xr, yr, p0=p0_r, sigma=sr, absolute_sigma=True, bounds=br, maxfev=8000
                        )
                        chi2_r = float(np.sum(((yr - f_landau(xr, *poptr)) / sr) ** 2))
                        ndf_r = max(1, int(len(xr) - 3))
                        rchi2_r = chi2_r / ndf_r
                        m_cand = "Landau"
                        f_exp_cand = 0.0
                    else:
                        br = (
                            [0.1 * amp0, 0.16 * q50, 0.05 * q50, 0.0],
                            [5.0 * amp0, 0.95 * q50, 1.35 * q50, 0.65],
                        )
                        p0_r = np.clip(
                            [amp0, pk0, 0.82 * wid0, 0.22],
                            np.array(br[0]) + 1e-3,
                            np.array(br[1]) - 1e-3,
                        )
                        poptr, pcovr = curve_fit(
                            f_landau_exp4, xr, yr, p0=p0_r, sigma=sr, absolute_sigma=True, bounds=br, maxfev=8000
                        )
                        chi2_r = float(np.sum(((yr - f_landau_exp4(xr, *poptr)) / sr) ** 2))
                        ndf_r = max(1, int(len(xr) - 4))
                        rchi2_r = chi2_r / ndf_r
                        m_cand = "Landau+Exp"
                        f_exp_cand = float(poptr[3])
                    perrr = np.sqrt(np.diag(pcovr))
                    mhit_r = (
                        (poptr[1] - br[0][1]) / (br[1][1] - br[0][1]) < 0.015
                        or (br[1][1] - poptr[1]) / (br[1][1] - br[0][1]) < 0.015
                    )
                    whit_r = (
                        (poptr[2] - br[0][2]) / (br[1][2] - br[0][2]) < 0.015
                        or (br[1][2] - poptr[2]) / (br[1][2] - br[0][2]) < 0.015
                    )
                    rerr_r = float(perrr[1] / max(poptr[1], 1.0))
                    if (not mhit_r) and (not whit_r) and rerr_r < 0.18 and (
                        mpv_hit or wid_hit or rel_err > 0.16 or rchi2_r < 0.90 * rchi2
                    ):
                        popt2, perr2, chi2, ndf, rchi2, b2 = poptr, perrr, chi2_r, ndf_r, rchi2_r, br
                        mpv_hit, wid_hit, rel_err = mhit_r, whit_r, rerr_r
                        mname = m_cand
                        f_exp_val = f_exp_cand
                        fit_lo_final, fit_hi_final = flo_r, fhi_r
                        retry = True
                        if (not mpv_hit) and rel_err < 0.12 and rchi2 < 1.50:
                            break
                except Exception:
                    pass

        status = "RETRY_GOOD" if retry else "GOOD"
        if mpv_hit:
            status = "MPV_BOUNDARY_HIT"
        elif wid_hit:
            status = "WIDTH_BOUNDARY_HIT"
        elif rchi2 > 3.5:
            status = "BAD_CHI2"
        elif rel_err > 0.20:
            status = "UNSTABLE"
        elif not (120.0 <= float(popt2[1]) <= 1800.0):
            status = "MPV_OUTLIER"

        base_res.update({
            "amp": float(popt2[0]),
            "mpv": float(popt2[1]),
            "mpv_err": float(perr2[1]),
            "mpv_rel_err": rel_err,
            "width": float(popt2[2]),
            "width_err": float(perr2[2]),
            "f_exp": f_exp_val,
            "chi2": chi2,
            "ndf": ndf,
            "chi2_ndf": rchi2,
            "fit_lo": fit_lo_final,
            "fit_hi": fit_hi_final,
            "model_used": mname,
            "fit_status": status,
        })
        return base_res
    except Exception:
        base_res["fit_status"] = "FIT_FAILED"
        return base_res


def load_selected_hits(csv_path: Path, target_name: str):
    print(f"[{target_name}] Loading {csv_path} ...")
    df = pd.read_csv(
        csv_path,
        usecols=["run", "raw_layer", "wire", "ADC", "p_GeV", "dEdx", "wfType", "ToT"],
        on_bad_lines="skip",
        low_memory=False,
    )
    for col in ["run", "raw_layer", "wire", "ADC", "p_GeV", "dEdx", "wfType", "ToT"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df.dropna(inplace=True)
    df["raw_layer"] = df["raw_layer"].astype(int)
    df["wire"] = df["wire"].astype(int)

    # Full dataset count per channel (ADC > 0)
    df_pos = df[df["ADC"] > 0]
    full_counts = df_pos.groupby(["raw_layer", "wire"]).size().to_dict()

    # Selected momentum window (0.15 <= p_GeV <= 0.25, ADC > 0)
    sub = df_pos[(df_pos["p_GeV"] >= P_MIN_GEV) & (df_pos["p_GeV"] <= P_MAX_GEV)]
    grouped_adc = {
        (int(l), int(w)): grp["ADC"].values.astype(float)
        for (l, w), grp in sub.groupby(["raw_layer", "wire"])
    }
    print(
        f"[{target_name}] Clean ADC>0 rows: {len(df_pos):,}; selected [{P_MIN_GEV}, {P_MAX_GEV}] GeV rows: {len(sub):,}; populated channels in window: {len(grouped_adc)}/576"
    )
    return full_counts, grouped_adc


def huber_location(vals: np.ndarray, c: float = 1.345, max_iter: int = 50) -> float:
    x = np.asarray(vals, dtype=float)
    mu = float(np.median(x))
    mad = float(1.4826 * np.median(np.abs(x - mu)))
    if mad < 1e-6:
        return mu
    for _ in range(max_iter):
        r = (x - mu) / mad
        w = np.where(np.abs(r) <= c, 1.0, c / np.maximum(np.abs(r), 1e-12))
        mu_new = float(np.sum(w * x) / np.sum(w))
        if abs(mu_new - mu) < 1e-4:
            return mu_new
        mu = mu_new
    return mu


def run_target_calibration(target_name: str, full_counts: dict, grouped_adc: dict) -> pd.DataFrame:
    rows = []
    gidx = 0
    for lay in LAYERS:
        for w in range(1, EXPECTED_WIRES[lay] + 1):
            gidx += 1
            adc = grouped_adc.get((lay, w), np.array([], dtype=float))
            res = fit_channel_spectrum(adc)
            res["target"] = target_name
            res["global_channel_idx"] = gidx
            res["layer"] = lay
            res["superlayer"] = lay // 10
            res["local_layer"] = lay % 10
            res["wire"] = w
            res["n_entries_all_p"] = int(full_counts.get((lay, w), 0))
            rows.append(res)

    df_res = pd.DataFrame(rows)
    good_mask = df_res["fit_status"].isin(["GOOD", "RETRY_GOOD"])
    good_mpvs = df_res.loc[good_mask, "mpv"].values

    # Global reference estimators (Option A)
    ref_global_median = float(np.median(good_mpvs))
    q10, q90 = np.percentile(good_mpvs, [10, 90])
    ref_global_trimmed = float(np.mean(good_mpvs[(good_mpvs >= q10) & (good_mpvs <= q90)]))
    ref_global_huber = huber_location(good_mpvs)

    df_res["mpv_ref_optA"] = ref_global_median
    df_res["mpv_ref_optA_trimmed"] = ref_global_trimmed
    df_res["mpv_ref_optA_huber"] = ref_global_huber

    # Per-layer reference estimators (Option B)
    layer_refs = {}
    for lay in LAYERS:
        l_mpvs = df_res.loc[good_mask & (df_res["layer"] == lay), "mpv"].values
        layer_refs[lay] = float(np.median(l_mpvs)) if len(l_mpvs) > 0 else ref_global_median
    df_res["mpv_ref_optB"] = df_res["layer"].map(layer_refs)

    # Compute gains and propagated uncertainties ONLY for GOOD and RETRY_GOOD channels
    # Never silently assign gain = 1.0 to failed/missing channels!
    df_res["gain_optA"] = np.where(good_mask, df_res["mpv_ref_optA"] / df_res["mpv"], np.nan)
    df_res["gain_err_optA"] = np.where(
        good_mask,
        df_res["gain_optA"] * (df_res["mpv_err"] / df_res["mpv"]),
        np.nan,
    )
    df_res["gain_optB"] = np.where(good_mask, df_res["mpv_ref_optB"] / df_res["mpv"], np.nan)
    df_res["gain_err_optB"] = np.where(
        good_mask,
        df_res["gain_optB"] * (df_res["mpv_err"] / df_res["mpv"]),
        np.nan,
    )

    # True Second-Pass Closure Refit for both Option A and Option B
    for opt_tag, gain_col, ref_col in [
        ("optA", "gain_optA", "mpv_ref_optA"),
        ("optB", "gain_optB", "mpv_ref_optB"),
    ]:
        mpv_after_list = []
        mpv_after_err_list = []
        wid_after_list = []
        rchi2_after_list = []
        status_after_list = []
        model_after_list = []
        res_frac_list = []

        for _, row in df_res.iterrows():
            lay = int(row["layer"])
            w = int(row["wire"])
            g_val = row[gain_col]
            ref_val = row[ref_col]
            if pd.isna(g_val) or g_val <= 0:
                mpv_after_list.append(np.nan)
                mpv_after_err_list.append(np.nan)
                wid_after_list.append(np.nan)
                rchi2_after_list.append(np.nan)
                status_after_list.append("NOT_CALIBRATED")
                model_after_list.append("None")
                res_frac_list.append(np.nan)
                continue

            adc_raw = grouped_adc.get((lay, w), np.array([], dtype=float))
            adc_corr = adc_raw * float(g_val)
            fit_post = fit_channel_spectrum(adc_corr)
            st_post = fit_post["fit_status"]
            mpv_post = fit_post["mpv"] if st_post in ("GOOD", "RETRY_GOOD") else np.nan
            err_post = fit_post["mpv_err"] if st_post in ("GOOD", "RETRY_GOOD") else np.nan
            wid_post = fit_post["width"] if st_post in ("GOOD", "RETRY_GOOD") else np.nan
            rc_post = fit_post["chi2_ndf"] if st_post in ("GOOD", "RETRY_GOOD") else np.nan
            mod_post = fit_post["model_used"]
            frac_res = (mpv_post - ref_val) / ref_val if pd.notna(mpv_post) else np.nan

            mpv_after_list.append(mpv_post)
            mpv_after_err_list.append(err_post)
            wid_after_list.append(wid_post)
            rchi2_after_list.append(rc_post)
            status_after_list.append(st_post)
            model_after_list.append(mod_post)
            res_frac_list.append(frac_res)

        df_res[f"mpv_after_{opt_tag}"] = mpv_after_list
        df_res[f"mpv_after_err_{opt_tag}"] = mpv_after_err_list
        df_res[f"width_after_{opt_tag}"] = wid_after_list
        df_res[f"chi2_ndf_after_{opt_tag}"] = rchi2_after_list
        df_res[f"fit_status_after_{opt_tag}"] = status_after_list
        df_res[f"model_after_{opt_tag}"] = model_after_list
        df_res[f"fractional_residual_{opt_tag}"] = res_frac_list

    return df_res


def main():
    full_d2, grp_d2 = load_selected_hits(D2_CSV, "D2")
    full_he4, grp_he4 = load_selected_hits(HE4_CSV, "He4")

    print("Running full 576-channel calibration and closure refits for D2 ...")
    df_d2 = run_target_calibration("D2", full_d2, grp_d2)

    print("Running full 576-channel calibration and closure refits for He4 ...")
    df_he4 = run_target_calibration("He4", full_he4, grp_he4)

    # Save gain_constants_D2.csv and gain_constants_He4.csv
    df_d2.to_csv(TABLE_DIR / "gain_constants_D2.csv", index=False)
    df_he4.to_csv(TABLE_DIR / "gain_constants_He4.csv", index=False)

    # 1. channel_statistics.csv (both targets, 1152 rows)
    stat_cols = [
        "target", "global_channel_idx", "layer", "superlayer", "local_layer", "wire",
        "n_entries_all_p", "n_entries", "stat_tier",
        "mean_adc", "std_adc", "median_adc", "iqr_adc", "q10_adc", "q25_adc", "q75_adc", "q90_adc",
        "mpv", "mpv_err", "mpv_rel_err", "width", "width_err", "f_exp",
        "chi2", "ndf", "chi2_ndf", "fit_lo", "fit_hi", "nbins", "bin_width", "model_used", "fit_status",
    ]
    df_stat = pd.concat([df_d2[stat_cols], df_he4[stat_cols]], ignore_index=True)
    df_stat.to_csv(TABLE_DIR / "channel_statistics.csv", index=False)

    # 2. Option A vs Option B comparison table
    opt_rows = []
    for tname, dft in [("D2", df_d2), ("He4", df_he4)]:
        gmask = dft["fit_status"].isin(["GOOD", "RETRY_GOOD"])
        mpv_pre = dft.loc[gmask, "mpv"].values
        for opt_tag, opt_desc, ref_col, post_col, res_col, gain_col in [
            ("Option_A_Global", "Global robust median MPV across all GOOD/RETRY_GOOD wires", "mpv_ref_optA", "mpv_after_optA", "fractional_residual_optA", "gain_optA"),
            ("Option_B_PerLayer", "Per-layer robust median MPV across GOOD/RETRY_GOOD wires in layer", "mpv_ref_optB", "mpv_after_optB", "fractional_residual_optB", "gain_optB"),
        ]:
            pmask = gmask & dft[post_col].notna()
            mpv_post = dft.loc[pmask, post_col].values
            res_vals = dft.loc[pmask, res_col].values
            g_vals = dft.loc[gmask, gain_col].values
            opt_rows.append({
                "target": tname,
                "reference_option": opt_tag,
                "description": opt_desc,
                "n_calibrated_channels": int(gmask.sum()),
                "n_closure_refit_good": int(pmask.sum()),
                "ref_mpv_median": float(np.median(dft.loc[gmask, ref_col])),
                "pre_mpv_mean": float(np.mean(mpv_pre)),
                "pre_mpv_std": float(np.std(mpv_pre)),
                "pre_mpv_mad": float(1.4826 * np.median(np.abs(mpv_pre - np.median(mpv_pre)))),
                "pre_mpv_iqr": float(np.percentile(mpv_pre, 75) - np.percentile(mpv_pre, 25)),
                "pre_mpv_cv_pct": float(100.0 * np.std(mpv_pre) / np.mean(mpv_pre)),
                "post_mpv_mean": float(np.mean(mpv_post)),
                "post_mpv_std": float(np.std(mpv_post)),
                "post_mpv_mad": float(1.4826 * np.median(np.abs(mpv_post - np.median(mpv_post)))),
                "post_mpv_iqr": float(np.percentile(mpv_post, 75) - np.percentile(mpv_post, 25)),
                "post_mpv_cv_pct": float(100.0 * np.std(mpv_post) / np.mean(mpv_post)),
                "closure_median_abs_residual_pct": float(100.0 * np.median(np.abs(res_vals))),
                "closure_mad_residual_pct": float(100.0 * 1.4826 * np.median(np.abs(res_vals - np.median(res_vals)))),
                "closure_rms_residual_pct": float(100.0 * np.sqrt(np.mean(res_vals ** 2))),
                "gain_median": float(np.median(g_vals)),
                "gain_iqr": float(np.percentile(g_vals, 75) - np.percentile(g_vals, 25)),
                "gain_min": float(np.min(g_vals)),
                "gain_max": float(np.max(g_vals)),
            })
    df_opt_cmp = pd.DataFrame(opt_rows)
    df_opt_cmp.to_csv(TABLE_DIR / "reference_option_A_vs_B_comparison.csv", index=False)

    # 3. layer_summary.csv
    lay_rows = []
    for tname, dft in [("D2", df_d2), ("He4", df_he4)]:
        for lay in LAYERS:
            sub_l = dft[dft["layer"] == lay]
            g_l = sub_l[sub_l["fit_status"].isin(["GOOD", "RETRY_GOOD"])]
            p_a = g_l[g_l["mpv_after_optA"].notna()]
            p_b = g_l[g_l["mpv_after_optB"].notna()]
            mpv_pre = g_l["mpv"].values
            lay_rows.append({
                "target": tname,
                "layer": lay,
                "expected_wires": EXPECTED_WIRES[lay],
                "populated_wires_window": int((sub_l["n_entries"] > 0).sum()),
                "wires_N>=80": int((sub_l["n_entries"] >= 80).sum()),
                "good_or_retry_good": int(len(g_l)),
                "low_stat": int((sub_l["fit_status"] == "LOW_STAT").sum()),
                "no_data": int((sub_l["fit_status"] == "NO_DATA").sum()),
                "failed_or_outlier": int(sub_l["fit_status"].isin(["MPV_OUTLIER", "MPV_BOUNDARY_HIT", "WIDTH_BOUNDARY_HIT", "BAD_CHI2", "UNSTABLE", "FIT_FAILED"]).sum()),
                "median_entries": float(sub_l["n_entries"].median()),
                "pre_mpv_median": float(np.median(mpv_pre)) if len(mpv_pre) else np.nan,
                "pre_mpv_mad": float(1.4826 * np.median(np.abs(mpv_pre - np.median(mpv_pre)))) if len(mpv_pre) else np.nan,
                "pre_mpv_std": float(np.std(mpv_pre)) if len(mpv_pre) else np.nan,
                "gain_optA_median": float(g_l["gain_optA"].median()) if len(g_l) else np.nan,
                "gain_optA_mad": float(1.4826 * np.median(np.abs(g_l["gain_optA"] - g_l["gain_optA"].median()))) if len(g_l) else np.nan,
                "post_mpv_optA_median": float(p_a["mpv_after_optA"].median()) if len(p_a) else np.nan,
                "post_mpv_optA_mad": float(1.4826 * np.median(np.abs(p_a["mpv_after_optA"] - p_a["mpv_after_optA"].median()))) if len(p_a) else np.nan,
                "closure_optA_med_abs_pct": float(100.0 * np.median(np.abs(p_a["fractional_residual_optA"]))) if len(p_a) else np.nan,
                "gain_optB_median": float(g_l["gain_optB"].median()) if len(g_l) else np.nan,
                "post_mpv_optB_median": float(p_b["mpv_after_optB"].median()) if len(p_b) else np.nan,
                "post_mpv_optB_mad": float(1.4826 * np.median(np.abs(p_b["mpv_after_optB"] - p_b["mpv_after_optB"].median()))) if len(p_b) else np.nan,
                "closure_optB_med_abs_pct": float(100.0 * np.median(np.abs(p_b["fractional_residual_optB"]))) if len(p_b) else np.nan,
            })
    df_lay = pd.DataFrame(lay_rows)
    df_lay.to_csv(TABLE_DIR / "layer_summary.csv", index=False)

    # 4. d2_he4_comparison.csv & 5. gain_constants_final.csv & 6. bad_channels.csv
    cmp_rows = []
    final_rows = []
    bad_rows = []

    for idx in range(576):
        rd = df_d2.iloc[idx]
        rh = df_he4.iloc[idx]
        lay = int(rd["layer"])
        w = int(rd["wire"])
        gidx = int(rd["global_channel_idx"])

        d_ok = rd["fit_status"] in ("GOOD", "RETRY_GOOD")
        h_ok = rh["fit_status"] in ("GOOD", "RETRY_GOOD")
        both_ok = d_ok and h_ok

        # Compare Option A and Option B gains between D2 and He4
        g_d_a, g_d_a_err = (float(rd["gain_optA"]), float(rd["gain_err_optA"])) if d_ok else (np.nan, np.nan)
        g_h_a, g_h_a_err = (float(rh["gain_optA"]), float(rh["gain_err_optA"])) if h_ok else (np.nan, np.nan)
        g_d_b, g_d_b_err = (float(rd["gain_optB"]), float(rd["gain_err_optB"])) if d_ok else (np.nan, np.nan)
        g_h_b, g_h_b_err = (float(rh["gain_optB"]), float(rh["gain_err_optB"])) if h_ok else (np.nan, np.nan)

        diff_a = g_d_a - g_h_a if both_ok else np.nan
        ratio_a = g_d_a / g_h_a if both_ok else np.nan
        comb_sigma_a = np.sqrt(g_d_a_err ** 2 + g_h_a_err ** 2) if both_ok else np.nan
        pull_a = diff_a / comb_sigma_a if (both_ok and comb_sigma_a > 0) else np.nan

        diff_b = g_d_b - g_h_b if both_ok else np.nan
        ratio_b = g_d_b / g_h_b if both_ok else np.nan

        if both_ok:
            if abs(diff_a) <= 0.25 or abs(pull_a) <= 2.5:
                compat_flag = "COMPATIBLE"
            else:
                compat_flag = "RUN_PERIOD_GAIN_DRIFT"
        elif h_ok and not d_ok:
            compat_flag = "HE4_ONLY_VALID"
        elif d_ok and not h_ok:
            compat_flag = "D2_ONLY_VALID"
        else:
            compat_flag = "NEITHER_VALID"

        cmp_rows.append({
            "global_channel_idx": gidx,
            "layer": lay,
            "wire": w,
            "n_entries_D2": int(rd["n_entries"]),
            "n_entries_He4": int(rh["n_entries"]),
            "status_D2": rd["fit_status"],
            "status_He4": rh["fit_status"],
            "model_D2": rd["model_used"],
            "model_He4": rh["model_used"],
            "mpv_D2": rd["mpv"],
            "mpv_err_D2": rd["mpv_err"],
            "mpv_He4": rh["mpv"],
            "mpv_err_He4": rh["mpv_err"],
            "gain_D2_optA": g_d_a,
            "gain_err_D2_optA": g_d_a_err,
            "gain_He4_optA": g_h_a,
            "gain_err_He4_optA": g_h_a_err,
            "gain_diff_optA": diff_a,
            "gain_ratio_optA": ratio_a,
            "gain_pull_optA": pull_a,
            "gain_D2_optB": g_d_b,
            "gain_He4_optB": g_h_b,
            "gain_diff_optB": diff_b,
            "gain_ratio_optB": ratio_b,
            "compatibility_flag": compat_flag,
        })

        # Recommended final gain constant:
        # 1. If both D2 and He4 are valid and compatible: inverse-variance weighted average of D2 and He4
        #    (and also provide target-specific columns g_D2 and g_He4 for run-specific calibration tables)
        # 2. If Both valid but run-period drift (>25% and >2.5 sigma): record inverse-variance weighted average
        #    with quality_flag = RUN_DEPENDENT_GAIN (use target-specific gain for D2 runs >=21657 vs early He4 runs <=21536)
        # 3. If only He4 is valid (e.g. the 87 high-wire channels masked in late runs, or D2 low-stat/failed):
        #    use He4 gain with gain_source = "He4_ONLY"
        # 4. If only D2 is valid: use D2 gain with gain_source = "D2_ONLY"
        # 5. If neither is valid: leave recommended_gain = NaN (NEVER silently assign 1.0!) and flag UNCALIBRATED_BAD_CHANNEL
        if both_ok:
            w_d = 1.0 / max(g_d_a_err ** 2, 1e-6)
            w_h = 1.0 / max(g_h_a_err ** 2, 1e-6)
            rec_g_a = (w_d * g_d_a + w_h * g_h_a) / (w_d + w_h)
            rec_err_a = float(np.sqrt(1.0 / (w_d + w_h)))

            wb_d = 1.0 / max(g_d_b_err ** 2, 1e-6)
            wb_h = 1.0 / max(g_h_b_err ** 2, 1e-6)
            rec_g_b = (wb_d * g_d_b + wb_h * g_h_b) / (wb_d + wb_h)
            rec_err_b = float(np.sqrt(1.0 / (wb_d + wb_h)))

            g_source = "COMBINED_D2_HE4"
            cal_status = "CALIBRATED_BOTH" if compat_flag == "COMPATIBLE" else "CALIBRATED_RUN_DRIFT"
        elif h_ok:
            rec_g_a, rec_err_a = g_h_a, g_h_a_err
            rec_g_b, rec_err_b = g_h_b, g_h_b_err
            g_source = "HE4_ONLY"
            cal_status = "CALIBRATED_HE4_ONLY"
        elif d_ok:
            rec_g_a, rec_err_a = g_d_a, g_d_a_err
            rec_g_b, rec_err_b = g_d_b, g_d_b_err
            g_source = "D2_ONLY"
            cal_status = "CALIBRATED_D2_ONLY"
        else:
            rec_g_a, rec_err_a = np.nan, np.nan
            rec_g_b, rec_err_b = np.nan, np.nan
            g_source = "NONE"
            cal_status = "UNCALIBRATED"

        final_rows.append({
            "global_channel_idx": gidx,
            "layer": lay,
            "superlayer": int(rd["superlayer"]),
            "local_layer": int(rd["local_layer"]),
            "wire": w,
            "calibration_status": cal_status,
            "gain_source": g_source,
            "compatibility_flag": compat_flag,
            "recommended_gain_optA": rec_g_a,
            "recommended_gain_err_optA": rec_err_a,
            "recommended_gain_optB": rec_g_b,
            "recommended_gain_err_optB": rec_err_b,
            "gain_D2_optA": g_d_a,
            "gain_err_D2_optA": g_d_a_err,
            "gain_He4_optA": g_h_a,
            "gain_err_He4_optA": g_h_a_err,
            "gain_D2_optB": g_d_b,
            "gain_He4_optB": g_h_b,
            "mpv_D2": rd["mpv"],
            "mpv_He4": rh["mpv"],
            "status_D2": rd["fit_status"],
            "status_He4": rh["fit_status"],
            "n_entries_D2": int(rd["n_entries"]),
            "n_entries_He4": int(rh["n_entries"]),
        })

        if (not d_ok) or (not h_ok):
            reasons = []
            if rd["fit_status"] == "NO_DATA":
                reasons.append("D2_NO_DATA (DAQ sector masked in runs >=21552)")
            elif not d_ok:
                reasons.append(f"D2_{rd['fit_status']} (N={int(rd['n_entries'])}, medADC={rd['median_adc']:.0f})")
            if not h_ok:
                reasons.append(f"He4_{rh['fit_status']} (N={int(rh['n_entries'])}, medADC={rh['median_adc']:.0f})")
            bad_rows.append({
                "global_channel_idx": gidx,
                "layer": lay,
                "wire": w,
                "status_D2": rd["fit_status"],
                "n_entries_D2": int(rd["n_entries"]),
                "median_adc_D2": rd["median_adc"],
                "status_He4": rh["fit_status"],
                "n_entries_He4": int(rh["n_entries"]),
                "median_adc_He4": rh["median_adc"],
                "calibration_status": cal_status,
                "gain_source": g_source,
                "diagnosis": "; ".join(reasons),
            })

    df_cmp = pd.DataFrame(cmp_rows)
    df_cmp.to_csv(TABLE_DIR / "d2_he4_comparison.csv", index=False)

    df_final = pd.DataFrame(final_rows)
    df_final.to_csv(TABLE_DIR / "gain_constants_final.csv", index=False)

    df_bad = pd.DataFrame(bad_rows)
    df_bad.to_csv(TABLE_DIR / "bad_channels.csv", index=False)

    print("\n=== SUMMARY OF CALIBRATION TABLES ===")
    print("Option A vs Option B comparison:")
    print(df_opt_cmp.to_string(index=False))
    print("\nFinal 576-channel calibration status breakdown:")
    print(df_final["calibration_status"].value_counts().to_string())
    print("\nD2 fit_status breakdown:")
    print(df_d2["fit_status"].value_counts().to_string())
    print("\nHe4 fit_status breakdown:")
    print(df_he4["fit_status"].value_counts().to_string())


if __name__ == "__main__":
    main()
