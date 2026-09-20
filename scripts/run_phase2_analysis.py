#!/usr/bin/env python3
"""Phase-2 analysis: repeated-record structure, latent-entity diagnostics,
variable semantics, conditional physics, and policy sensitivity.

Evidence rules baked in:
- repeated records are analyzed, never averaged away;
- no policy may create a state that never existed (no flag averaging);
- every physics number is conditional on stated assumptions;
- OTI values are reported in "OTI units" (unit unconfirmed);
- raw files are provenance-gated before and after the run.

Outputs -> reports/generated/ and reports/figures/.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from transformer_audit import (  # noqa: E402
    PARSED_TS_COLUMN, RAW_LINE_COLUMN,
    apply_policy, apparent_time_constant_minutes, conflict_summary,
    critical_mass_kg, energy_kj, high_oti_repeated_intersection,
    load_manifest, multiplicity_table, neighbor_continuity_fit,
    occurrence_report, per_record_flag_consistency, policy_sensitivity,
    read_table, repeated_group_report, repeated_timestamps_shared,
    required_power_kw, tau_domain_status, tau_sensitivity,
    achievable_delta_t_units, utc_now_iso, value_band_unimodality,
    verify_raw_files, interval_minutes,
)

RAW_DIR = REPO_ROOT / "data" / "raw"
MANIFEST = REPO_ROOT / "provenance" / "dataset_manifest.json"
OUT = REPO_ROOT / "reports" / "generated"
FIG = REPO_ROOT / "reports" / "figures"
FILES = ["CurrentVoltage.csv", "Overview.csv", "Power.csv", "PowerFactor.csv", "TotalPower.csv"]

# Conditional physics scenario band (labeled assumptions, not facts):
C_OIL_SCENARIOS = {  # kJ/(kg*K)
    "mineral_oil_typical_low": 1.8,
    "mineral_oil_typical_high": 2.1,
}
MASS_GRID_KG = np.array([50, 100, 200, 300, 500, 800, 1200, 2000, 3000], dtype=float)
POWER_GRID_KW = np.array([33.4, 50.0, 90.0, 103.0, 142.1, 200.0, 500.0, 1000.0])


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    FIG.mkdir(parents=True, exist_ok=True)
    manifest = load_manifest(MANIFEST)

    pre = verify_raw_files(manifest, RAW_DIR)
    if not pre["all_match"]:
        print("PROVENANCE GATE FAILED (pre-run).", file=sys.stderr)
        return 2
    print("[0] Pre-run provenance gate OK")

    tabs = {f: read_table(RAW_DIR / f) for f in FILES}
    ov = tabs["Overview.csv"]
    cv = tabs["CurrentVoltage.csv"]
    tp = tabs["TotalPower.csv"]

    # ---- 1. multiplicity -------------------------------------------------------
    mult_rows = []
    for f, df in tabs.items():
        m = multiplicity_table(df)
        m.insert(0, "filename", f)
        mult_rows.append(m)
    pd.concat(mult_rows, ignore_index=True).to_csv(OUT / "timestamp_multiplicity.csv", index=False)
    shared = repeated_timestamps_shared(tabs)
    shared.to_csv(OUT / "repeated_timestamps_shared.csv", index=False)

    # ---- 2. repeated-record conflicts ------------------------------------------
    rep = repeated_group_report(ov)
    rep.to_csv(OUT / "repeated_record_conflicts.csv", index=False)
    conf_rows = []
    for f, df in tabs.items():
        s = conflict_summary(df)
        s["filename"] = f
        conf_rows.append(s)
    pd.DataFrame(conf_rows).to_csv(OUT / "repeated_record_conflict_summary.csv", index=False)

    # ---- 3. high-OTI / repeated intersection ------------------------------------
    inter = high_oti_repeated_intersection(ov, threshold=236)
    flagcheck = per_record_flag_consistency(ov)
    pd.DataFrame([inter | flagcheck]).to_csv(OUT / "high_oti_duplicate_intersection.csv", index=False)

    # ---- 4. policy sensitivity ----------------------------------------------------
    sens = policy_sensitivity(ov)
    sens.to_csv(OUT / "duplicate_policy_sensitivity.csv", index=False)

    # ---- 5. latent-stream diagnostics ---------------------------------------------
    occ = {f: occurrence_report(tabs[f]) for f in FILES}
    fit = neighbor_continuity_fit(ov)
    vb = value_band_unimodality(cv, "VL1")
    vb2 = value_band_unimodality(cv, "VL12")
    monthly = rep["month"].value_counts().sort_index() if len(rep) else pd.Series(dtype=int)
    diag_rows = []
    for f, d in occ.items():
        diag_rows.append({"diagnostic": f"occurrence_report::{f}", **d})
    diag_rows.append({"diagnostic": "neighbor_continuity_fit::Overview", **fit})
    diag_rows.append({"diagnostic": "value_band_unimodality::VL1", **vb})
    diag_rows.append({"diagnostic": "value_band_unimodality::VL12", **vb2})
    diag_rows.append({"diagnostic": "monthly_repeated_group_counts::Overview",
                      "note": "; ".join(f"{k}:{v}" for k, v in monthly.items())})
    pd.DataFrame(diag_rows).to_csv(OUT / "latent_stream_diagnostics.csv", index=False)

    # ---- 6. variable semantics ------------------------------------------------------
    sem_rows = []
    semantics = {
        "OTI": ("0..250", "59", "discrete numeric; empty interval (54,236); 42 canonical zeros",
                "Oil Temperature Indicator", "unit not stated by any primary source"),
        "WTI": ("{0,1}", "2", "binary status channel; active only 2020-01..2020-04; 0 during all high-OTI rows",
                "Winding Temperature Indicator", "NOT a continuous temperature in this export; semantics unexplained by primary source"),
        "ATI": ("0..44", "34", "continuous-ish ambient; 43 zeros", "Ambient Temperature Indicator", "unit not stated (°C-consistent range)"),
        "OLI": ("36..100", "65", "discrete levels; mode 100; co-varies with MOG_A", "Oil Level Indicator", "unit unknown (percent-like); not confirmed"),
        "OTI_A": ("{0,1}", "2", "alarm flag; active at OTI 29-30 (2019-07-03/04) AND 236-250", "Oil Temperature Indicator Alarm", "not a pure function of shown OTI"),
        "OTI_T": ("{0,1}", "2", "trip flag; 47 rows, all with OTI 236-250 and OTI_A=1", "Oil Temperature Indicator Trip", "indication vs breaker command/status unknown"),
        "MOG_A": ("{0,1}", "2", "flag; active Jul-Aug 2019 only; implies OLI<=41", "Magnetic Oil Gauge Indicator (alarm)", "latch/hysteresis semantics unknown"),
    }
    source_defs = (
        "Kaggle dataset description (S1): 'OTI- Oil Temperature Indicator' etc.; "
        "Putchala et al. 2022 Table 2 lists the same names without units; "
        "Energies 2022 Sec. 7.1 describes OTI->alarm->OTT chain."
    )
    for col, (dom, nun, beh, srcdef, amb) in semantics.items():
        v = ov[col]
        sem_rows.append({
            "column": col,
            "raw_domain": dom,
            "n_unique": int(v.nunique()),
            "behaviour": beh,
            "missing_or_zero_coded": f"zeros={int((v == 0).sum())}; NaN=0",
            "source_definition": f"{srcdef} ({source_defs})",
            "confirmed_unit": "none",
            "unresolved_ambiguity": amb,
        })
    pd.DataFrame(sem_rows).to_csv(OUT / "variable_semantics.csv", index=False)

    # extra: OTI-ATI correlation on canonical first-policy (paper comparison: 0.914)
    c1 = ov.drop_duplicates(PARSED_TS_COLUMN, keep="first").sort_values(PARSED_TS_COLUMN)
    corr_all = float(c1["OTI"].corr(c1["ATI"]))
    corr_norm = float(c1.loc[c1["OTI"] < 100, "OTI"].corr(c1.loc[c1["OTI"] < 100, "ATI"]))

    # ---- 7. conditional physics -------------------------------------------------------
    # 10 falling transitions (canonical first policy): T0 (high), T1 (recovered), ATI nearby
    s = c1.reset_index(drop=True)
    dt = interval_minutes(s[PARSED_TS_COLUMN])
    trans = []
    for i in range(1, len(s)):
        if s.loc[i - 1, "OTI"] >= 100 and s.loc[i, "OTI"] < 100 and dt.loc[i] > 0:
            ta = float(s.loc[i, "ATI"])
            trans.append({
                "fall_timestamp": str(s.loc[i, PARSED_TS_COLUMN]),
                "T0": float(s.loc[i - 1, "OTI"]),
                "T1": float(s.loc[i, "OTI"]),
                "Ta_used_ATI": ta,
                "dt_minutes": float(dt.loc[i]),
            })
    tau_rows = []
    for t in trans:
        sensx = tau_sensitivity(t["T0"], t["T1"], t["Ta_used_ATI"], t["dt_minutes"])
        for r in sensx["rows"]:
            tau_rows.append({
                "fall_timestamp": t["fall_timestamp"],
                "T0": t["T0"], "T1": t["T1"], "Ta_base": t["Ta_used_ATI"],
                "ta_offset_units": r["ta_offset_units"],
                "ta_used": r["ta_used"],
                "dt_minutes": r["dt_minutes"],
                "tau_minutes": r["tau_minutes"],
                "domain_status": r["domain_status"],
            })
    tau_df = pd.DataFrame(tau_rows)
    tau_df.to_csv(OUT / "apparent_tau_per_transition.csv", index=False)

    # heating bound: for each rising transition, energies from power scenarios
    # rising transitions with dt and local power window (+-30 min KW)
    rises = []
    for i in range(1, len(s)):
        if s.loc[i - 1, "OTI"] < 100 and s.loc[i, "OTI"] >= 100 and dt.loc[i] > 0:
            t0 = s.loc[i, PARSED_TS_COLUMN]
            win = tp[
                (tp[PARSED_TS_COLUMN] >= t0 - pd.Timedelta("30min"))
                & (tp[PARSED_TS_COLUMN] <= t0 + pd.Timedelta("30min"))
            ]
            rises.append({
                "rise_timestamp": str(t0),
                "dt_minutes": float(dt.loc[i]),
                "dT_units": float(s.loc[i, "OTI"] - s.loc[i - 1, "OTI"]),
                "local_max_kw_30min": float(win["KW"].max()) if len(win) else np.nan,
            })
    rises_df = pd.DataFrame(rises)
    # merge rising/falling into one transitions table
    all_trans = pd.concat([
        rises_df.assign(direction="rising"),
        pd.DataFrame(trans).assign(direction="falling").rename(columns={"fall_timestamp": "rise_timestamp"}),
    ], ignore_index=True)
    all_trans.to_csv(OUT / "oti_transitions_phase2.csv", index=False)

    global_max_kw = float(tp["KW"].max())
    phys_rows = []
    for _, r in rises_df.iterrows():
        dT = r["dT_units"]
        for label, p in [
            ("local_max_kw_30min", r["local_max_kw_30min"]),
            ("global_max_kw", global_max_kw),
            ("parameterized_500kw", 500.0),
            ("parameterized_1500kw", 1500.0),
        ]:
            E = energy_kj(p, r["dt_minutes"])
            for cname, c in C_OIL_SCENARIOS.items():
                phys_rows.append({
                    "rise_timestamp": r["rise_timestamp"],
                    "dt_minutes": r["dt_minutes"],
                    "delta_T_oti_units": dT,
                    "power_scenario_kw": label,
                    "power_kw": p,
                    "energy_kj": E,
                    "c_oil_scenario": cname,
                    "c_kj_per_kg_k": c,
                    "critical_mass_kg": critical_mass_kg(E, c, dT),
                    "assumption": "100% of electrical energy into oil heat (EXTREME upper bound); OTI units unconfirmed; oil type unknown",
                })
    phys_df = pd.DataFrame(phys_rows)
    phys_df.to_csv(OUT / "physics_sensitivity.csv", index=False)

    # curves: required power vs mass (for observed median dT/dt) + achievable dT vs mass
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    median_dT = float(rises_df["dT_units"].median())
    median_dt = float(rises_df["dt_minutes"].median())

    fig, ax = plt.subplots(1, 1, figsize=(7, 4.5))
    for cname, c in C_OIL_SCENARIOS.items():
        req = [required_power_kw(m, c, median_dT, median_dt) / 1000.0 for m in MASS_GRID_KG]
        ax.plot(MASS_GRID_KG, req, marker="o", label=f"c={c} kJ/(kg·K)")
    ax.axhline(global_max_kw / 1000.0, color="r", ls="--",
               label=f"global max observed load {global_max_kw:.0f} kW")
    ax.set_xlabel("effective oil-equivalent thermal mass (kg)")
    ax.set_ylabel("required power (MW) for ΔT=%.0f OTI-units in %.0f min" % (median_dT, median_dt))
    ax.set_yscale("log")
    ax.set_title("Required thermal power vs effective thermal mass\n(100%-to-oil extreme bound; unit-conditional)")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(FIG / "physics_bounds_power_vs_mass.png", dpi=140)
    plt.close(fig)

    fig, ax = plt.subplots(1, 1, figsize=(7, 4.5))
    for p in [50.0, 103.0, global_max_kw]:
        ach = [achievable_delta_t_units(p, m, 2.0, median_dt) for m in MASS_GRID_KG]
        ax.plot(MASS_GRID_KG, ach, marker="o", label=f"load {p:.0f} kW (all to oil)")
    ax.axhline(182.0, color="k", ls=":", label="observed excursion jump ≈182 OTI-units")
    ax.set_xlabel("effective oil-equivalent thermal mass (kg)")
    ax.set_ylabel(f"achievable ΔT (OTI units) in {median_dt:.0f} min")
    ax.set_yscale("log")
    ax.set_title("Achievable ΔT vs effective thermal mass\n(100%-conversion extreme bound; c=2.0 kJ/(kg·K) scenario)")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(FIG / "physics_bounds_achievable_dT.png", dpi=140)
    plt.close(fig)

    fig, ax = plt.subplots(1, 1, figsize=(7, 4.5))
    for label, p in [("global max observed 142.1 kW", global_max_kw), ("parameterized 1500 kW", 1500.0)]:
        E = energy_kj(p, median_dt)
        masses = np.linspace(20, 3000, 300)
        mc = [critical_mass_kg(E, 2.0, median_dT) for _ in masses]
        ax.plot([critical_mass_kg(energy_kj(p, mdt), 2.0, median_dT) for mdt in [median_dt]],
                [p], "o")
        ax.axvline(critical_mass_kg(E, 2.0, median_dT), ls="--",
                   label=f"{label}: m_crit={critical_mass_kg(E, 2.0, median_dT):.0f} kg @ dt={median_dt:.0f} min")
    tau_valid = tau_df[tau_df["domain_status"] == "valid"] if len(tau_df) else pd.DataFrame()
    ax.set_xlabel("critical mass (kg)")
    ax.set_ylabel("available power (kW)")
    ax.set_title("Critical effective thermal mass vs available power\n(m_crit = E/(c·ΔT); 100%-conversion extreme bound)")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(FIG / "physics_bounds_critical_mass.png", dpi=140)
    plt.close(fig)

    # ---- 8. alternative explanations matrix ----------------------------------------
    alt = pd.DataFrame([
        {
            "explanation": "physical top-oil transient (single asset)",
            "supporting": "OTI/ATI correlated (r=%.3f canonical, exc. removed)" % corr_norm,
            "contradicting": "rise rates +11..+91 units/min >> normal-mode p99 0.33; no intermediate values in (54,236); no electrical disturbance visible; OTI_T implied trip did not de-energize LV",
            "missing_metadata": "nameplate; oil mass; cooling class; sensor chain; OTI units",
            "confidence": "weak",
            "falsification_test": "obtain asset specs and show m_crit/power consistent; or find intermediate samples at higher-rate source data",
        },
        {
            "explanation": "measurement-chain anomaly (sensor/transmitter/conversion)",
            "supporting": "empty interval (54,236); step-and-return shape; WTI=0 throughout excursions; Energies overheat marker is 90 C-scale while excursions reach 250",
            "contradicting": "no hardware metadata; channel id smooth otherwise (lag-1 ac 0.859)",
            "missing_metadata": "sensor type; transmitter range; scaling; error-code table",
            "confidence": "moderate (not established as root cause)",
            "falsification_test": "provider documents error codes / transmitter range covering 236-250",
        },
        {
            "explanation": "telemetry/ingestion corruption (H2)",
            "supporting": "931 repeated-timestamp groups, synchronized across files, conflicts ~1 OTI unit / 0.4 V; repeats concentrated in Jun 2019 (448/931)",
            "contradicting": "repeated records never contain high-OTI rows (0/47), so the excursions are not duplication artifacts",
            "missing_metadata": "ingestion logs; REST API behavior (paper: live REST API feed)",
            "confidence": "moderate for repeats; repeats do not explain excursions",
            "falsification_test": "provider confirms API retry semantics for repeated timestamps",
        },
        {
            "explanation": "multiple-asset mixing (H3) after device-ID removal",
            "supporting": "provider platform monitors 52 locations (Putchala Sec.4); export has no device ID",
            "contradicting": "multiplicity ~1-4 on only 2.3-4.9% of timestamps (not a constant second stream); VL1 band unimodal; conflicts are near-identical values; all 5 files share one timestamp axis",
            "missing_metadata": "device IDs; export query used to produce the Kaggle files",
            "confidence": "weak-to-moderate (cannot be excluded; diagnostics lean against within-file mixing)",
            "falsification_test": "provider states export scope (one location vs many)",
        },
        {
            "explanation": "multiple feeder measurements, one transformer (H4)",
            "supporting": "Energies system monitors per-feeder currents; paper describes feeder-level monitoring",
            "contradicting": "Kaggle has single VL/IL triple per timestamp, no feeder ID; TotalPower KW matches per-phase sum",
            "missing_metadata": "feeder mapping",
            "confidence": "weak",
            "falsification_test": "provider documents channel-to-feeder mapping",
        },
        {
            "explanation": "device error code / status encoding at 236-250",
            "supporting": "integer quantization; empty interval; values cluster tightly 236-250; platform OTI>65 trip band (paper) is far below 236",
            "contradicting": "no error-code table available; values vary smoothly within the band",
            "missing_metadata": "firmware/error-code documentation",
            "confidence": "moderate as a candidate representation hypothesis (not established)",
            "falsification_test": "error-code table from provider covering this range",
        },
        {
            "explanation": "export duplication (H2b)",
            "supporting": "adjacent raw lines; synchronized across files; mostly identical values",
            "contradicting": "many groups conflict slightly (405/437 in CurrentVoltage), so not byte-duplication",
            "missing_metadata": "export procedure",
            "confidence": "moderate for the repeats themselves",
            "falsification_test": "reproduce export and compare",
        },
        {
            "explanation": "timestamp/order corruption",
            "supporting": "irregular cadence (1-9 min intervals; 33.6-day gaps)",
            "contradicting": "rows are non-decreasing in time everywhere (no negative intervals); excursions have internally consistent local ordering",
            "missing_metadata": "device clock discipline",
            "confidence": "weak for excursions (cadence irregularity confirmed but does not create the OTI steps)",
            "falsification_test": "provider raw logs",
        },
        {
            "explanation": "unobserved short electrical event between samples",
            "supporting": "sampling is 15-min median with shorter gaps; any sub-interval transient could be missed",
            "contradicting": "even a full 2-min immersion at the global max load cannot heat plausible oil mass by 182 units (physics_sensitivity.csv); event would also need to explain exact step-and-return symmetry",
            "missing_metadata": "high-rate records; fault recorder data",
            "confidence": "cannot be excluded by sampled data (stated limitation)",
            "falsification_test": "obtain sub-minute data around 2019-07-16..09-03 windows",
        },
    ])
    alt.to_csv(OUT / "alternative_explanations.csv", index=False)

    # ---- 8b. curated evidence tables (source claims, bibliography, envelope) --
    pd.DataFrame([
        {"claim_id": "SC01",
         "claim": "Live data obtained from REST APIs at 52 locations, Tripura, India, via IoT devices, updated every 15 min, recorded from November 2020",
         "source": "Putchala et al. 2022 (S11)", "page_section": "Sec. 4",
         "source_role": "PRIMARY/ORIGINAL (dataset authors' platform statement)",
         "exact_support": "Verbatim: 'The data set is provided by a private company, KernelSphere Technologies. This live data is obtained from the REST APIs recorded from November 2020 up to date at 52 different locations at the State, Tripura, India, with IoT devices and is updated for every 15 min.'",
         "evidence_class": "CONFIRMED-SOURCE (PRIMARY)",
         "ambiguity": "Describes the paper's LIVE stream (Nov 2020+; ~237,687 rows), NOT the Kaggle export window (2019-06-25..2020-04-14); platform attribution of the export is an inference",
         "allowed_wording": "The dataset authors state their live platform recorded from Nov 2020 at 52 Tripura locations; the export window predates this statement"},
        {"claim_id": "SC02",
         "claim": "Column schema (OTI, WTI, ATI, OLI, OTI_A, OTI_T, MOG_A, VL*, IL*, KW, KVA...) matches the Kaggle export",
         "source": "Putchala et al. 2022 (S11)", "page_section": "Table 2",
         "source_role": "PRIMARY/ORIGINAL",
         "exact_support": "Table 2 lists the same channel names as the export columns",
         "evidence_class": "CONFIRMED-SOURCE (PRIMARY) + CONFIRMED-DATA (schema match)",
         "ambiguity": "Schema kinship establishes platform relationship, not entity identity or unit",
         "allowed_wording": "The paper's schema matches the export exactly (same platform family)"},
        {"claim_id": "SC03",
         "claim": "OTI > 65 used as trip threshold; OTI_T derived as binary failure-prediction target",
         "source": "Putchala et al. 2022 (S11)", "page_section": "Sec. 4.2",
         "source_role": "PRIMARY/ORIGINAL (their modelling choice on the live stream)",
         "exact_support": "Trip table: OTI>65 gives 17,830 Trip=True / 1,114 False; OTI<65 gives 0 True",
         "evidence_class": "CONFIRMED-SOURCE (PRIMARY)",
         "ambiguity": "In the Kaggle export OTI_T aligns exactly with OTI>=236 — a different threshold; the paper's OTI_T semantics do not transfer",
         "allowed_wording": "The paper's models used OTI>65 on their live stream; the export's OTI_T aligns with OTI>=236 instead"},
        {"claim_id": "SC04",
         "claim": "The monitored transformer is 1500 kVA, 11/0.4 kV",
         "source": "Ramesh et al., Energies 15(21):7981 (S7)", "page_section": "Sec. 5.1",
         "source_role": "SOURCE-ADJACENT (their own installed system)",
         "exact_support": "Describes THEIR Sharjah/University City monitoring system transformer",
         "evidence_class": "CONFIRMED-SOURCE (SOURCE-ADJACENT, own-system statement)",
         "ambiguity": "NOT a statement about the Kaggle asset; the Energies Data Availability Statement shows their experimental dataset is the Kaggle upload — two different objects in one paper",
         "allowed_wording": "The Energies authors' own system uses a 1500 kVA 11/0.4 kV transformer; no source applies this rating to the Kaggle asset"},
        {"claim_id": "SC05",
         "claim": "Historical data came from 'similar transformers sharing load capacity...'",
         "source": "Ramesh et al., Energies 15(21):7981 (S7)", "page_section": "Dataset description",
         "source_role": "SOURCE-ADJACENT",
         "exact_support": "Phrase 'similar transformers sharing load capacity manufactured age measuring units and installed environment conditions' (S7)",
         "evidence_class": "CONFIRMED-SOURCE (SOURCE-ADJACENT, ambiguous wording)",
         "ambiguity": "'Similar' is not a rating transfer; it does not defensibly establish that Kaggle assets were 1500 kVA — wording remains ambiguous",
         "allowed_wording": "The Energies paper describes the Kaggle data as from 'similar transformers'; this is not defensible evidence of a 1500 kVA rating for the Kaggle asset"},
        {"claim_id": "SC06",
         "claim": "OTT (oil-temperature trip) shuts off electrical flow",
         "source": "Ramesh et al., Energies 15(21):7981 (S7)", "page_section": "Sec. 7.1",
         "source_role": "SOURCE-ADJACENT (generic transformer behavior)",
         "exact_support": "Generic OTT description in their background section",
         "evidence_class": "CONFIRMED-SOURCE (SOURCE-ADJACENT, generic)",
         "ambiguity": "In the Kaggle export, voltage/current continue through OTI_T=1 windows — electrical continuity contradicts a breaker-open reading for THIS data; OTI_T semantics stay open",
         "allowed_wording": "A generic OTT description exists in the literature; this export's OTI_T behaved as an indication-consistent flag, not an observed de-energization"},
        {"claim_id": "SC07",
         "claim": "The audited dataset is the one used by the Energies experiments",
         "source": "Ramesh et al., Energies 15(21):7981 (S7)", "page_section": "Data Availability Statement",
         "source_role": "SOURCE-ADJACENT",
         "exact_support": "Verbatim: 'The dataset adopted in this research is openly available in [Kaggle] at https://www.kaggle.com/datasets/sreshta140/ai-transformer-monitoring (accessed on 20 June 2022).'",
         "evidence_class": "CONFIRMED-SOURCE (SOURCE-ADJACENT) + CONFIRMED-DATA (single-version v1 archive)",
         "ambiguity": "Their internal row counts (17,207; 14,169+3,471=17,640) do not match the file row counts — their preprocessing is undocumented",
         "allowed_wording": "The Energies study used the audited dataset (its Data Availability Statement names the exact upload)"},
        {"claim_id": "SC08",
         "claim": "The audited archive was uploaded by the first author of Putchala et al. 2022",
         "source": "Kaggle dataset owner + Springer chapter page", "page_section": "dataset page owner field; Springer author list",
         "source_role": "PRIMARY/ORIGINAL",
         "exact_support": "Kaggle owner 'Sreshta Putchala'; Springer authors 'Putchala, S.R., Kotha, R., Guda, V., Ramadevi, Y.' (CBIT Hyderabad)",
         "evidence_class": "CONFIRMED-SOURCE (PRIMARY)",
         "ambiguity": "Uploader identity links the export to the paper's group; the paper itself describes only the later live stream",
         "allowed_wording": "The dataset was uploaded by the paper's first author; the export window itself is not described in the paper"},
        {"claim_id": "SC09",
         "claim": "A byte-identical mirror circulates (pythonafroz/transformer-fault-analysis v3; Overview.csv renamed Alarm.csv)",
         "source": "Phase-1 mirror verification (S9)", "page_section": "hash comparison",
         "source_role": "SECONDARY (re-upload)",
         "exact_support": "SHA-256 match on all five files",
         "evidence_class": "CONFIRMED-DATA",
         "ambiguity": "None for identity; mirror carries no provenance information",
         "allowed_wording": "The files circulate as re-uploads; the audited archive is the original upload"},
        {"claim_id": "SC10",
         "claim": "The dataset is about one distribution transformer",
         "source": "NONE FOUND (community/project assumption)", "page_section": "—",
         "source_role": "SECONDARY (unstated assumption)",
         "exact_support": "No primary source states the export's entity scope",
         "evidence_class": "UNKNOWN",
         "ambiguity": "No device/location column; provider platform covers 52 locations",
         "allowed_wording": "Entity scope is unknown; the required unresolved-entity statement applies"},
        {"claim_id": "SC11",
         "claim": "KernelSphere Technologies is the platform provider (real Hyderabad IoT company)",
         "source": "Putchala et al. 2022 (S11) + public registries (S16)", "page_section": "Sec. 4 + CIN U72200TG2013PTC085215",
         "source_role": "PRIMARY-adjacent",
         "exact_support": "Named in S11 Sec. 4; corporate registry and public contact verified",
         "evidence_class": "CONFIRMED-SOURCE (PRIMARY-adjacent for provider identity)",
         "ambiguity": "Provider identity confirmed; whether/how this export was extracted from their platform is not documented",
         "allowed_wording": "KernelSphere is identified by the paper as the platform provider; the export's extraction path is undocumented"},
    ]).to_csv(OUT / "source_claim_matrix.csv", index=False)

    pd.DataFrame([
        {"id": "S1", "type": "dataset", "citation": "Kaggle: 'Distributed Transformer Monitoring' (sreshta140/ai-transformer-monitoring) v1, 2020-05-25, 'Data files © Original Authors' — THE AUDITED DATASET (official API download, hash-pinned); uploaded by Sreshta Putchala, first author of S11",
         "url": "kaggle.com/datasets/sreshta140/ai-transformer-monitoring", "license": "Data files © Original Authors",
         "full_text_accessed": "data files + description page + API metadata snapshot",
         "accessed_utc": "2026-09-20 (Phase-1 acquisition; Phase-2 re-verification)", "role": "PRIMARY (audited dataset; authors' own upload)"},
        {"id": "S11", "type": "paper", "citation": "Putchala, S.R., Kotha, R., Guda, V., Ramadevi, Y. 'Transformer Data Analysis for Predictive Maintenance.' ICCCE/ICACES 2021, Springer AIS, pp. 217-230. DOI 10.1007/978-981-16-7389-4_21",
         "url": "doi.org/10.1007/978-981-16-7389-4_21 (author-shared copy via ResearchGate)",
         "license": "Springer; short quotes with section numbers only; full text NOT committed",
         "full_text_accessed": "YES — complete full text read (all sections incl. Tables 2, 8, 9)",
         "accessed_utc": "2026-09-20", "role": "PRIMARY (dataset authors: data provided by KernelSphere to authors)"},
        {"id": "S7", "type": "paper", "citation": "Ramesh, J., Shahriar, S., Al-Ali, A.R., Osman, A., Shaaban, M. 'Forecasting and Anomaly Detection of Distribution Transformers Using GRU and Isolation Forest.' Energies 15(21):7981 (2022)",
         "url": "doi.org/10.3390/en15217981", "license": "CC BY 4.0",
         "full_text_accessed": "YES — nearly complete full text read (incl. Sec. 5.1, 6, 7.1, 8, 11)",
         "accessed_utc": "2026-09-20", "role": "SOURCE-ADJACENT (uses the audited dataset per its Data Availability Statement; describes own Sharjah system separately; cites [34]=S11)"},
        {"id": "S12", "type": "manufacturer", "citation": "Electrotech Transmission Pvt Ltd (ETT), Indore — distribution transformers page",
         "url": "ettgroups.com/distribution-transformers.html", "license": "public web",
         "full_text_accessed": "page text (ratings/weights)", "accessed_utc": "2026-09-20",
         "role": "SECONDARY envelope (official manufacturer, unrelated to dataset)"},
        {"id": "S13", "type": "utility spec", "citation": "BSES Delhi, Spec SP-TRDU-02-02 (rev 02, 2019-12-12) — procurement spec for distribution transformers",
         "url": "BSES Rajdhani Power Limited public procurement documents", "license": "public web",
         "full_text_accessed": "partial (main sections; Annexure D beyond parse limit)", "accessed_utc": "2026-09-20",
         "role": "SECONDARY envelope (utility procurement, unrelated to dataset)"},
        {"id": "S14", "type": "manufacturer", "citation": "Bharat Bijlee Ltd — transformers brochure (corporate)",
         "url": "bharatbijlee.com", "license": "public web",
         "full_text_accessed": "brochure (range-level only)", "accessed_utc": "2026-09-20",
         "role": "SECONDARY envelope (official manufacturer, unrelated to dataset)"},
        {"id": "S15", "type": "standard", "citation": "IS 1180:2014 Part 1 — oil-immersed distribution transformers up to 2500 kVA, 33 kV class (scope)",
         "url": "BIS (scope confirmed via official ITMA presentation)", "license": "public web summary",
         "full_text_accessed": "scope only; loss tables not from official source — not used", "accessed_utc": "2026-09-20",
         "role": "SECONDARY envelope"},
        {"id": "S16", "type": "company", "citation": "KernelSphere Technologies Pvt Ltd, Hyderabad (CIN U72200TG2013PTC085215) — IoT sensor platform company",
         "url": "kernelsphere.com/contact.html", "license": "public web",
         "full_text_accessed": "public contact/registry pages", "accessed_utc": "2026-09-20",
         "role": "PRIMARY-adjacent (dataset platform provider; outreach drafts prepared, NOT sent)"},
    ]).to_csv(OUT / "bibliography_register.csv", index=False)

    pd.DataFrame([
        {"parameter": "number of transformers in export", "value": "UNKNOWN", "evidence_class": "missing",
         "source": "no device/asset column; provider platform = 52 locations (S2 Sec. 4)",
         "assumptions": "none allowed", "confidence": "n/a", "physics_use": "NO"},
        {"parameter": "number of devices in export", "value": "UNKNOWN", "evidence_class": "missing",
         "source": "no device column; multiplicity structure (2.3-4.9% repeated timestamps) inconsistent with constant second stream",
         "assumptions": "none allowed", "confidence": "n/a", "physics_use": "NO"},
        {"parameter": "number of feeders", "value": "UNKNOWN", "evidence_class": "missing",
         "source": "single VL/IL triple per timestamp; no feeder ID",
         "assumptions": "none allowed", "confidence": "n/a", "physics_use": "NO"},
        {"parameter": "nameplate rating (kVA)", "value": "UNKNOWN (unbounded above; no lower bound beyond observed loading)",
         "evidence_class": "missing", "source": "1500 kVA figure belongs to S3's own system, NOT this export; 142.9 kVA observed load establishes nothing about rating",
         "assumptions": "observed loading != nameplate", "confidence": "n/a", "physics_use": "NO (parameterized scenarios only)"},
        {"parameter": "voltage ratio", "value": "UNKNOWN; secondary side measured ~240 V phase / ~415-445 V line",
         "evidence_class": "observed (secondary only)", "source": "CurrentVoltage.csv ranges",
         "assumptions": "nominal ratio cannot be inferred without primary-side measurement",
         "confidence": "high (measured), low (inference)", "physics_use": "context only"},
        {"parameter": "oil volume / oil mass", "value": "UNKNOWN — no official per-rating table obtained",
         "evidence_class": "missing", "source": "S11/S12/S13 official pages lack per-rating oil volumes; reseller tables rejected",
         "assumptions": "parameterized 50..3000 kg effective thermal mass in physics",
         "confidence": "n/a", "physics_use": "PARAMETERIZED"},
        {"parameter": "cooling mode", "value": "UNKNOWN for THIS asset; ONAN typical class for the envelope (S11/S12)",
         "evidence_class": "SECONDARY envelope", "source": "ETT + BSES specs",
         "assumptions": "not transferred to dataset asset", "confidence": "n/a for asset", "physics_use": "NO"},
        {"parameter": "OTI unit", "value": "UNCONFIRMED ('OTI units')",
         "evidence_class": "missing", "source": "no primary source states the unit; °C-scale readings of 236-250 exceed documented operating bands",
         "assumptions": "all physics uses 'OTI units'", "confidence": "n/a", "physics_use": "CONDITIONAL"},
        {"parameter": "sampling cadence", "value": "15-min median; observed 1-9 min intervals; 33.6-day gap 2019-07/08",
         "evidence_class": "observed", "source": "this export (Phase-1 interval summary)",
         "assumptions": "device-side aggregation unknown", "confidence": "high", "physics_use": "YES (dt in formulas)"},
        {"parameter": "max observed load", "value": "142.9 kVA / 142.1 kW (2020-01-27)",
         "evidence_class": "observed", "source": "TotalPower.csv",
         "assumptions": "instantaneous sample, not continuous", "confidence": "high", "physics_use": "YES (scenario bound)"},
        {"parameter": "losses / heat generation", "value": "UNKNOWN; parameterized 0-100% of load power",
         "evidence_class": "missing", "source": "no nameplate, no test report",
         "assumptions": "100%-to-oil used ONLY as extreme upper bound", "confidence": "n/a", "physics_use": "PARAMETERIZED"},
        {"parameter": "ambient temperature channel", "value": "ATI 0-44 (unit unconfirmed, °C-consistent)",
         "evidence_class": "observed", "source": "Overview.csv",
         "assumptions": "used as ambient proxy in tau analysis with +/-5 sensitivity",
         "confidence": "medium", "physics_use": "YES (conditional)"},
        {"parameter": "effective thermal mass range for scenarios", "value": "50-3000 kg (scenario grid, NOT a claim)",
         "evidence_class": "parameterized", "source": "covers distribution-transformer-scale oil+structure; no asset-specific value asserted",
         "assumptions": "grid only", "confidence": "n/a", "physics_use": "PARAMETERIZED"},
    ]).to_csv(OUT / "asset_parameter_evidence.csv", index=False)

    pd.DataFrame([
        {"manufacturer_spec": "ETT 200 kVA 11/0.433 kV ONAN, IS 1180/IS 2026", "official": True,
         "oil_volume": "not published on page", "total_mass_kg": "not published for 200 kVA",
         "relevance": "11 kV-class DT envelope exists in Indian market"},
        {"manufacturer_spec": "ETT 315 kVA 11/0.433 kV ONAN", "official": True,
         "oil_volume": "not published", "total_mass_kg": "not published",
         "relevance": "envelope"},
        {"manufacturer_spec": "ETT 1000 kVA (1 MVA) 11 kV/433 V", "official": True,
         "oil_volume": "not published", "total_mass_kg": 4065,
         "relevance": "mass scale reference for 11 kV DTs"},
        {"manufacturer_spec": "ETT 1600 kVA (1.6 MVA) 11/0.433 kV", "official": True,
         "oil_volume": "not published", "total_mass_kg": 6026,
         "relevance": "mass scale reference"},
        {"manufacturer_spec": "BSES Delhi SP-TRDU-02-02: 400/630/1000 kVA, 11/0.433 kV, ONAN, class A, 50 C design ambient, IS 2026/IS 1180; WTI/OTI scanner (Pecon/Precision) + MOG listed as standard accessories", "official": True,
         "oil_volume": "Annexure D (not parsed — beyond 30-page limit)", "total_mass_kg": "in Annexure D",
         "relevance": "confirms WTI/OTI/MOG channels are standard DT instrumentation in this market"},
        {"manufacturer_spec": "Bharat Bijlee: DTs up to 200 MVA/400 kV range (corporate brochure)", "official": True,
         "oil_volume": "not published", "total_mass_kg": "not published",
         "relevance": "manufacturer confirmation only, no per-rating data"},
        {"manufacturer_spec": "IS 1180:2014 Part 1 scope: oil-immersed DTs up to 2500 kVA, 33 kV class", "official": True,
         "oil_volume": "n/a", "total_mass_kg": "n/a",
         "relevance": "standard scope; per-rating values NOT taken from unofficial sources"},
    ]).to_csv(OUT / "manufacturer_spec_envelope.csv", index=False)

    # ---- 9. summary ------------------------------------------------------------
    summary = {
        "phase2_run_utc": utc_now_iso(),
        "provenance_gate": "PASS (pre-run; post-run verified below)",
        "repeated_records": {
            "overview_repeated_groups": int(len(rep)),
            "overview_identical": int(rep["identical_group"].sum()) if len(rep) else 0,
            "overview_conflicting": int((~rep["identical_group"]).sum()) if len(rep) else 0,
            "high_oti_rows_in_repeated_groups": inter["n_high_oti_records_in_repeated_groups"],
            "per_record_oti_t_rule_violations": flagcheck["violations"],
            "monthly_repeated_groups": {k: int(v) for k, v in monthly.items()},
        },
        "entity": {
            "occurrence_stream_supported": occ["Overview.csv"]["verdict_supports_stable_occurrence_streams"],
            "vl1_contiguous_band_clusters": vb["n_contiguous_band_clusters"],
            "neighbor_fit_first_vs_last": [fit.get("mean_fit_error_first_branch"), fit.get("mean_fit_error_last_branch")],
        },
        "oti_ati_correlation": {
            "canonical_all": corr_all,
            "canonical_normal_band_only": corr_norm,
            "paper_reported_putchala": 0.914,
            "note": "paper value computed on their Nov2020+ 52-location live stream, not this export",
        },
        "policy_sensitivity": sens.to_dict("records"),
    }
    with open(OUT / "phase_02_summary.json", "w") as fh:
        json.dump(summary, fh, indent=2, default=str)

    post = verify_raw_files(manifest, RAW_DIR)
    if not post["all_match"]:
        print("PROVENANCE GATE FAILED (post-run)!", file=sys.stderr)
        return 2
    print("[post] Post-run provenance gate OK (raw files unmodified)")
    print("Phase-2 outputs written to", OUT, "and", FIG)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
