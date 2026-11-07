import os
from pathlib import Path

WORKSPACE = Path(os.environ.get("ALERT_WORKSPACE", "<DEFAULT_WORKSPACE>"))
BASE = WORKSPACE / "ALERT_AHDC_GAIN_CALIBRATION_CLAS12"
D2_PATH = BASE / "FINAL_MERGED/D2_ALL_FINAL.csv"
HE4_PATH = BASE / "FINAL_MERGED/HE4_ALL_FINAL.csv"
TAB_DIR = BASE / "results/gain_calibration_final/tables"

EXPECTED_WIRES = {11: 47, 21: 56, 22: 56, 31: 72, 32: 72, 41: 87, 42: 87, 51: 99}
LAYERS = [11, 21, 22, 31, 32, 41, 42, 51]

GLOBAL_MAP = {}
gidx = 1
for lay in LAYERS:
    for w in range(1, EXPECTED_WIRES[lay] + 1):
        GLOBAL_MAP[(lay, w)] = gidx
        gidx += 1
assert len(GLOBAL_MAP) == 576

def load_clean_csv(path: Path, name: str) -> pd.DataFrame:
    df = pd.read_csv(path, on_bad_lines="skip", low_memory=False)
    # Coerce any rows where a column failed numeric conversion
    num_cols = ["file_index", "event_index", "run", "event", "trackid", "clusterid",
                "pid", "prob_2212", "p_GeV", "dEdx", "nhits", "chi2",
                "superlayer", "local_layer", "raw_layer", "wire",
                "adc_sector", "adc_order", "wfType", "ToT", "ADC"]
    before = len(df)
    for c in num_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    bad_num = int(df[num_cols].isna().any(axis=1).sum())
    if bad_num > 0:
        print(f"[{name}] Dropping {bad_num} rows with non-numeric coerced values")
        df = df.dropna(subset=num_cols).copy()
    int_cols = ["file_index", "event_index", "run", "event", "trackid", "clusterid",
                "pid", "nhits", "superlayer", "local_layer", "raw_layer", "wire",
                "adc_sector", "adc_order", "wfType"]
    for c in int_cols:
        df[c] = df[c].astype(np.int64)
    # Check physical layer & wire validity
    valid_lw = df["raw_layer"].isin(LAYERS) & (df["wire"] >= 1) & (df["wire"] <= df["raw_layer"].map(EXPECTED_WIRES).fillna(0))
    bad_lw = int((~valid_lw).sum())
    if bad_lw > 0:
        print(f"[{name}] Dropping {bad_lw} rows with out-of-range (raw_layer, wire)")
        df = df[valid_lw].copy()
    print(f"[{name}] Loaded {len(df):,} clean rows (from {before:,} 22-field rows).")
    return df

d2 = load_clean_csv(D2_PATH, "D2")
he4 = load_clean_csv(HE4_PATH, "He4")

for name, df in [("D2", d2), ("He4", he4)]:
    print(f"\n==================== {name} AUDIT ====================")
    print("Clean rows:", f"{len(df):,}")
    print("Columns & dtypes:\n", df.dtypes.to_string())
    print(f"Unique runs ({df['run'].nunique()}):", sorted(df["run"].unique().tolist()))
    print("Unique files:", df["file"].nunique())
    print("Unique (run, event):", f"{len(df.drop_duplicates(['run', 'event'])):,}")
    print("Unique (run, event, trackid):", f"{len(df.drop_duplicates(['run', 'event', 'trackid'])):,}")
    dup_all = int(df.duplicated().sum())
    dup_hit = int(df.duplicated(subset=["run", "event", "trackid", "raw_layer", "wire", "ADC", "ToT"]).sum())
    dup_lw_trk = int(df.duplicated(subset=["run", "event", "trackid", "raw_layer", "wire"]).sum())
    print(f"Exact duplicate rows: {dup_all:,} | duplicate (run,event,trackid,layer,wire,ADC,ToT): {dup_hit:,} | multiple hits same (run,event,trackid,layer,wire): {dup_lw_trk:,}")
    print("pid unique:", df["pid"].unique().tolist())
    print("adc_sector unique:", df["adc_sector"].unique().tolist())
    print("adc_order unique:", df["adc_order"].unique().tolist())
    print("wfType value_counts:", df["wfType"].value_counts().sort_index().to_dict())
    print("superlayer*10+local_layer == raw_layer all True?:", bool(((df["superlayer"] * 10 + df["local_layer"]) == df["raw_layer"]).all()))
    for col in ["ADC", "p_GeV", "dEdx", "nhits", "chi2", "prob_2212", "ToT"]:
        q = np.quantile(df[col], [0.0, 0.01, 0.05, 0.25, 0.50, 0.75, 0.95, 0.99, 1.0])
        print(f"  {col:10s}: min={q[0]:.4f} q01={q[1]:.4f} q05={q[2]:.4f} q25={q[3]:.4f} med={q[4]:.4f} q75={q[5]:.4f} q95={q[6]:.4f} q99={q[7]:.4f} max={q[8]:.4f}")

# Save deterministic channel mapping table
ch_rows = []
for (lay, w), gch in GLOBAL_MAP.items():
    ch_rows.append({
        "global_channel": gch,
        "physical_layer": lay,
        "superlayer": lay // 10,
        "local_layer": lay % 10,
        "wire": w,
        "wires_in_layer": EXPECTED_WIRES[lay],
    })
pd.DataFrame(ch_rows).to_csv(TAB_DIR / "global_channel_map_576.csv", index=False)

map_rows = []
for lay in LAYERS:
    sub_d2 = d2[d2["raw_layer"] == lay]
    sub_he4 = he4[he4["raw_layer"] == lay]
    w_d2 = set(sub_d2["wire"].unique())
    w_he4 = set(sub_he4["wire"].unique())
    w_d2_pos = set(sub_d2[sub_d2["ADC"] > 0]["wire"].unique())
    w_he4_pos = set(sub_he4[sub_he4["ADC"] > 0]["wire"].unique())
    exp_set = set(range(1, EXPECTED_WIRES[lay] + 1))
    map_rows.append({
        "physical_layer": lay,
        "wire_min": 1,
        "wire_max": EXPECTED_WIRES[lay],
        "expected_channels": EXPECTED_WIRES[lay],
        "D2_populated_channels": len(w_d2 & exp_set),
        "D2_ADCgt0_channels": len(w_d2_pos & exp_set),
        "He4_populated_channels": len(w_he4 & exp_set),
        "He4_ADCgt0_channels": len(w_he4_pos & exp_set),
        "D2_missing_wires": str(sorted(exp_set - w_d2)),
        "He4_missing_wires": str(sorted(exp_set - w_he4)),
        "D2_rows": len(sub_d2),
        "He4_rows": len(sub_he4),
    })
df_map = pd.DataFrame(map_rows)
print("\n==================== LAYER / WIRE MAPPING TABLE ====================")
print(df_map.to_string(index=False))
df_map.to_csv(TAB_DIR / "layer_wire_mapping_audit.csv", index=False)

for name, df in [("D2", d2), ("He4", he4)]:
    print(f"{name}: ADC<=0 rows = {(df['ADC'] <= 0).sum():,} ({100*(df['ADC']<=0).mean():.2f}%), ADC>0 rows = {(df['ADC'] > 0).sum():,}, wfType<=2 rows = {(df['wfType'] <= 2).sum():,} ({100*(df['wfType']<=2).mean():.2f}%)")

WINDOWS = [
    ("full_broad", 0.0, 10.0),
    ("0.02-0.05", 0.02, 0.05),
    ("0.02-0.07", 0.02, 0.07),
    ("0.02-0.08", 0.02, 0.08),
    ("0.05-0.08", 0.05, 0.08),
    ("0.08-0.12", 0.08, 0.12),
    ("0.12-0.15", 0.12, 0.15),
    ("0.15-0.20", 0.15, 0.20),
    ("0.15-0.25", 0.15, 0.25),
    ("0.20-0.30", 0.20, 0.30),
    ("0.10-0.20", 0.10, 0.20),
    ("0.12-0.22", 0.12, 0.22),
    ("0.12-0.25", 0.12, 0.25),
    ("0.05-0.25", 0.05, 0.25),
]

all_channels_idx = pd.MultiIndex.from_tuples(list(GLOBAL_MAP.keys()), names=["raw_layer", "wire"])

stat_rows = []
for target, df in [("D2", d2), ("He4", he4)]:
    df_pos = df[df["ADC"] > 0]
    for wname, plo, phi in WINDOWS:
        sub = df_pos[(df_pos["p_GeV"] >= plo) & (df_pos["p_GeV"] <= phi)]
        cnt = sub.groupby(["raw_layer", "wire"]).size().reindex(all_channels_idx, fill_value=0).values
        pos_cnt = cnt[cnt > 0]
        stat_rows.append({
            "target": target,
            "window": wname,
            "p_min_GeV": plo,
            "p_max_GeV": phi,
            "total_rows_ADCgt0": int(len(sub)),
            "populated_channels": int((cnt > 0).sum()),
            "N_eq_0": int((cnt == 0).sum()),
            "N_lt_80": int((cnt < 80).sum()),
            "N_ge_80": int((cnt >= 80).sum()),
            "N_ge_200": int((cnt >= 200).sum()),
            "N_ge_500": int((cnt >= 500).sum()),
            "N_ge_1000": int((cnt >= 1000).sum()),
            "min_all576": int(cnt.min()),
            "min_populated": int(pos_cnt.min()) if len(pos_cnt) else 0,
            "q10_entries": float(np.quantile(cnt, 0.10)),
            "median_entries": float(np.median(cnt)),
            "mean_entries": float(np.mean(cnt)),
            "max_entries": int(cnt.max()),
            "median_ADC": float(sub["ADC"].median()) if len(sub) else np.nan,
            "median_dEdx": float(sub["dEdx"].median()) if len(sub) else np.nan,
        })

df_win = pd.DataFrame(stat_rows)
print("\n==================== MOMENTUM WINDOW STATISTICS (ADC > 0) ====================")
print(df_win.to_string(index=False))
df_win.to_csv(TAB_DIR / "momentum_window_statistics.csv", index=False)
