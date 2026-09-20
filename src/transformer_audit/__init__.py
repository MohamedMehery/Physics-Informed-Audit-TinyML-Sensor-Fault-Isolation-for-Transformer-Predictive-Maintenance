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
]
