"""Tests 6, 7: contiguous-event construction and merging at multiple
tolerances."""

from conftest import make_table


class TestPrimitiveEvents:
    def test_contiguous_run_single_event(self):
        df = make_table([
            ("2019-01-01T00:00", 30.0, 0.0, 0.0, 0.0, 0.0),
            ("2019-01-01T00:15", 240.0, 1.0, 1.0, 0.0, 0.0),
            ("2019-01-01T00:30", 245.0, 1.0, 1.0, 0.0, 0.0),
            ("2019-01-01T00:45", 250.0, 1.0, 1.0, 0.0, 0.0),
            ("2019-01-01T01:00", 31.0, 0.0, 0.0, 0.0, 0.0),
        ])
        from transformer_audit import primitive_events
        ev = primitive_events(df, "OTI_T", max_continuity_gap_minutes=15.0)
        assert len(ev) == 1
        assert ev.iloc[0]["n_samples"] == 3
        assert ev.iloc[0]["duration_minutes"] == 30.0

    def test_gap_splits_events_per_continuity_definition(self):
        # active samples separated by 20 min: one event at gap<=30, two at gap<=15
        df = make_table([
            ("2019-01-01T00:00", 240.0, 1.0, 1.0, 0.0, 0.0),
            ("2019-01-01T00:20", 245.0, 1.0, 1.0, 0.0, 0.0),
        ])
        from transformer_audit import primitive_events
        assert len(primitive_events(df, "OTI_T", max_continuity_gap_minutes=30.0)) == 1
        assert len(primitive_events(df, "OTI_T", max_continuity_gap_minutes=15.0)) == 2

    def test_intra_event_gap_recorded(self):
        df = make_table([
            ("2019-01-01T00:00", 240.0, 1.0, 1.0, 0.0, 0.0),
            ("2019-01-01T00:20", 245.0, 1.0, 1.0, 0.0, 0.0),
        ])
        from transformer_audit import primitive_events
        ev = primitive_events(df, "OTI_T", max_continuity_gap_minutes=30.0)
        assert ev.iloc[0]["max_intra_event_gap_minutes"] == 20.0

    def test_no_active_rows(self):
        df = make_table([
            ("2019-01-01T00:00", 30.0, 0.0, 0.0, 0.0, 0.0),
            ("2019-01-01T00:15", 31.0, 0.0, 0.0, 0.0, 0.0),
        ])
        from transformer_audit import primitive_events
        ev = primitive_events(df, "OTI_T", max_continuity_gap_minutes=15.0)
        assert len(ev) == 0


class TestEventMerging:
    def make_two_close_events(self):
        # two primitive events separated by 30 inactive minutes
        return make_table([
            ("2019-01-01T00:00", 240.0, 1.0, 1.0, 0.0, 0.0),
            ("2019-01-01T00:15", 245.0, 1.0, 1.0, 0.0, 0.0),
            ("2019-01-01T00:45", 246.0, 1.0, 1.0, 0.0, 0.0),  # 30 min later
            ("2019-01-01T01:00", 250.0, 1.0, 1.0, 0.0, 0.0),
        ])

    def test_no_merge_below_tolerance(self):
        from transformer_audit import merge_events, primitive_events
        df = self.make_two_close_events()
        prim = primitive_events(df, "OTI_T", max_continuity_gap_minutes=15.0)
        assert len(prim) == 2
        m = merge_events(prim, merge_tolerance_minutes=15.0)
        assert len(m) == 2

    def test_merge_at_30min_tolerance(self):
        from transformer_audit import merge_events, primitive_events
        df = self.make_two_close_events()
        prim = primitive_events(df, "OTI_T", max_continuity_gap_minutes=15.0)
        m = merge_events(prim, merge_tolerance_minutes=30.0)
        assert len(m) == 1
        assert m.iloc[0]["n_primitive_events"] == 2
        assert m.iloc[0]["n_samples"] == 4
        assert m.iloc[0]["duration_minutes"] == 60.0

    def test_merge_monotonic_in_tolerance(self):
        from transformer_audit import event_sensitivity
        df = self.make_two_close_events()
        sens = event_sensitivity(df, ["OTI_T"], continuity_gaps_minutes=(15.0,),
                                 merge_tolerances_minutes=(0.0, 15.0, 30.0, 60.0, 360.0))
        counts = dict(zip(sens["merge_tolerance_minutes"], sens["n_events_after_merge"]))
        assert counts == {0.0: 2, 15.0: 2, 30.0: 1, 60.0: 1, 360.0: 1}
