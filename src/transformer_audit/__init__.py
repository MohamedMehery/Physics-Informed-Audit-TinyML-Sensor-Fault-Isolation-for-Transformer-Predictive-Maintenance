"""transformer_audit: evidence-first audit pipeline for the Kaggle
'Distributed Transformer Monitoring' dataset (sreshta140/ai-transformer-monitoring).

Phase 1 scope: data inventory, timestamp integrity, duplicate analysis,
event-definition sensitivity, and electrical context. No thermal modelling,
no hardware root-cause claims.
"""

__version__ = "0.1.0"

from .io import read_table, canonicalize, sensor_columns, RAW_TS_COLUMN, PARSED_TS_COLUMN, RAW_LINE_COLUMN
from .timestamps import parse_timestamp, interval_minutes, safe_rate
from .provenance import sha256_file, build_manifest, verify_raw_files, load_manifest, utc_now_iso
from .audit import (
    inventory_file,
    interval_summary,
    duplicate_timestamp_report,
    value_distribution,
    onset_counts,
    onset_counts_policy_sensitivity,
    value_gap_analysis,
    threshold_separability,
    autocorrelation_by_lag,
    rate_summary,
    cross_file_alignment,
    all_files_intersection,
    top_rate_transitions,
)
from .events import primitive_events, merge_events, event_sensitivity
from .electrical import apparent_power_estimates, power_approximation_errors, excursion_electrical_context
from . import records
from . import physics
from .records import (
    multiplicity_table, repeated_timestamps_shared, repeated_group_report,
    conflict_summary, high_oti_repeated_intersection, per_record_flag_consistency,
    apply_policy, policy_metrics, policy_sensitivity, occurrence_report,
    neighbor_continuity_fit, value_band_unimodality, POLICIES,
)
from . import plausibility_filter
from . import filter_metrics
from . import replay
from .replay import (
    calibrate, split_chronological, guard_no_test_leakage, valid_pairs,
    quantile, clopper_pearson, day_block_bootstrap, horizon_features,
    sliding_windows, sustained_alert_times, CAL_RULES, FIRST_CROSSING_ISO,
)
from .plausibility_filter import PlausibilityFilter, FilterDecision, FILTER_TYPES
from .filter_metrics import (
    find_rising_crossings, evaluate_flags, pareto_frontier, build_zone_index,
    normal_zones,
    b1_trivial_threshold_flags, b2_random_flags, b3_percentile_flags,
    OP_COUNTS, est_cycles_m0, mlp_28_16_8_1, gbdt_100_trees, total_ops,
)
from .physics import (
    energy_kj, critical_mass_kg, required_power_kw, achievable_delta_t_units,
    apparent_time_constant_minutes, tau_domain_status, tau_sensitivity,
)

__all__ = [
    "read_table", "canonicalize", "RAW_TS_COLUMN", "PARSED_TS_COLUMN", "RAW_LINE_COLUMN",
    "parse_timestamp", "interval_minutes", "safe_rate",
    "sha256_file", "build_manifest", "verify_raw_files", "load_manifest", "utc_now_iso",
    "inventory_file", "interval_summary", "duplicate_timestamp_report",
    "value_distribution", "onset_counts", "value_gap_analysis",
    "threshold_separability", "autocorrelation_by_lag", "rate_summary",
    "cross_file_alignment", "all_files_intersection", "top_rate_transitions",
    "primitive_events", "merge_events", "event_sensitivity",
    "apparent_power_estimates", "power_approximation_errors",
    "excursion_electrical_context",
    "records", "physics",
    "multiplicity_table", "repeated_timestamps_shared", "repeated_group_report",
    "conflict_summary", "high_oti_repeated_intersection", "per_record_flag_consistency",
    "apply_policy", "policy_metrics", "policy_sensitivity", "occurrence_report",
    "neighbor_continuity_fit", "value_band_unimodality", "POLICIES",
    "energy_kj", "critical_mass_kg", "required_power_kw", "achievable_delta_t_units",
    "apparent_time_constant_minutes", "tau_domain_status", "tau_sensitivity",
    "plausibility_filter", "filter_metrics", "replay",
    "calibrate", "split_chronological", "guard_no_test_leakage",
    "clopper_pearson", "day_block_bootstrap", "horizon_features",
    "sliding_windows", "sustained_alert_times", "CAL_RULES",
    "PlausibilityFilter", "FilterDecision",
    "find_rising_crossings", "evaluate_flags", "pareto_frontier", "build_zone_index",
    "normal_zones",
    "b1_trivial_threshold_flags", "b2_random_flags", "b3_percentile_flags",
    "OP_COUNTS", "est_cycles_m0", "mlp_28_16_8_1", "gbdt_100_trees", "total_ops",
]
