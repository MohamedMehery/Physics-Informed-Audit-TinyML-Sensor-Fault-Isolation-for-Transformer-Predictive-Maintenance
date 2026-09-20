# Outreach Request Drafts — DO NOT SEND WITHOUT OWNER AUTHORIZATION

**Status: DRAFTS ONLY.** Nothing in this file has been sent. Sending any of
these requires explicit authorization from the repository owner.

**Required question topics (from the Phase-2 protocol) covered across the
drafts:** (1) number of transformers represented; (2) presence/removal of
device IDs; (3) rating and voltage ratio; (4) location and time zone;
(5) OTI/ATI/OLI/WTI units and semantics; (6) cooling class; (7) sensor and
transmitter types; (8) meaning of OTI_A, OTI_T, and MOG_A; (9) whether
repeated timestamps represent different devices; (10) whether OTI_T was an
indication or a breaker command/status.

**Targets and public contact points (verified 2026-09-20):**
- Kaggle dataset owner: Sreshta Putchala (`sreshta140`) — dataset
  discussion thread / author profile (S6).
- Original-paper corresponding authors: Putchala, Kotha, Guda, Ramadevi —
  Chaitanya Bharathi Institute of Technology, Hyderabad (affiliation per
  Springer chapter page, S11); contactable via the publisher's
  corresponding-author route or institutional directories.
- Energies corresponding authors: Ramesh, Shahriar, Al-Ali, Osman, Shaaban
  (American University of Sharjah; per S7, CC BY paper).
- KernelSphere Technologies Pvt Ltd, Hyderabad — kernelsphere.com/contact.html,
  040-40068195 / +91 9550418229, public emails on the contact page
  (info@ / jyoti@). CIN U72200TG2013PTC085215 (inc. 2013-01-03, ROC
  Hyderabad). Verified as a real IoT-sensor company with distribution-
  transformer monitoring products.

---

## Draft 1 — Kaggle dataset owner (sreshta140 / S. Putchala)

> Subject: Questions about "Distributed Transformer Monitoring" (dataset origin)
>
> Hello,
>
> We are conducting a public, evidence-first audit of your Kaggle dataset
> "Distributed Transformer Monitoring" (v1, 25 Jun 2019 – 14 Apr 2020,
> five CSVs, hashes published). Could you help us with:
> 1. How many physical transformers/devices does the export represent, and
>    was a device or asset ID removed before publishing?
> 2. How was the export extracted (query, device, location), and from which
>    platform?
> 3. What location and time zone do the timestamps refer to?
> 4. What are the units of OTI, ATI, OLI, and why is WTI binary in this
>    export?
> 5. What do OTI_A, OTI_T, and MOG_A mean operationally — in particular,
>    was OTI_T an indication only or a breaker command/status?
> 6. Do the repeated timestamps (e.g., 931 in Overview.csv) represent
>    different devices, or re-transmissions from one device?
> 7. What could the OTI band 236–250 (no values between 54 and 236)
> represent?
>
> Any answer will be credited in the audit; "cannot disclose" is also a
> useful answer.

## Draft 2 — Corresponding authors, Putchala et al. 2022 (CBIT Hyderabad)

> Subject: Question about the 2019–2020 Kaggle export vs. the live stream in your ICCCE/ICACES paper
>
> Dear authors,
>
> We audited the Kaggle export "Distributed Transformer Monitoring"
> (uploaded by Sreshta Putchala) and read your paper "Transformer Data
> Analysis for Predictive Maintenance," which states the live data comes
> from KernelSphere Technologies (REST APIs, 52 locations, Tripura,
> 15-minute updates, recorded from November 2020). The Kaggle export,
> however, covers 25 Jun 2019 – 14 Apr 2020. Could you clarify:
> 1. Is the Kaggle export an earlier window from the same KernelSphere
>    platform, and how was it extracted (one transformer? one location?
>    one device)?
> 2. Were device/asset IDs present before export?
> 3. What are the units and semantics of OTI, WTI (binary in the export),
>    ATI, OLI, OTI_A, OTI_T, and MOG_A? Was OTI_T an indication or a
>    breaker command/status?
> 4. In the export, OTI_T aligns exactly with OTI ≥ 236 rather than the
>    OTI > 65 threshold used in your paper — can you explain the
>    difference?
> 5. Are the repeated timestamps expected re-transmissions?
>
> We will credit your answers in the public audit.

## Draft 3 — Corresponding authors, Energies 15(21):7981 (AUS Sharjah)

> Subject: Question about the Kaggle dataset used in your Energies 7981 study
>
> Dear authors,
>
> Your Data Availability Statement cites the Kaggle dataset
> sreshta140/ai-transformer-monitoring (accessed 20 June 2022), which we
> have audited. Your paper also describes your own 1500 kVA 11/0.4 kV
> system at University City, Sharjah. To keep these clearly separated in
> our audit, could you confirm:
> 1. All ML results (GRU forecasting, Isolation Forest) were computed on
>    the Kaggle data, not on measurements from your Sharjah installation?
> 2. What preprocessing produced your reported row counts (17,207 /
>    17,640) — the raw files contain 19,352–20,316 rows?
> 3. When you describe the Kaggle data as from "similar transformers
>    sharing load capacity…", does that imply a specific rating for the
>    Kaggle assets, or is it generic wording?
> 4. Did you observe the OTI 236–250 band (empty interval 54–236) in the
>    Kaggle data, and how did you treat it?
>
> We will credit your answers in the public audit.

## Draft 4 — KernelSphere Technologies (platform provider)

> Subject: Public Kaggle export of transformer telemetry (2019–2020) — scope questions
>
> Hello,
>
> A 2022 Springer paper (Putchala et al., ICCCE/ICACES) describes live IoT
> transformer telemetry from your platform (REST APIs, 52 locations,
> Tripura, 15-minute updates). A public Kaggle export with the same schema
> ("Distributed Transformer Monitoring", 25 Jun 2019 – 14 Apr 2020) is
> being audited by us. We would be grateful for:
> 1. Whether that export came from your platform, and how many
>    transformers/devices it represents (was a device ID removed?);
> 2. The nameplate rating, voltage ratio, and cooling class of the
>    monitored unit(s), if shareable;
> 3. The site location and time zone of the timestamps;
> 4. The units and semantics of OTI, WTI, ATI, OLI, OTI_A, OTI_T, MOG_A in
>    your system — especially whether OTI_T is an indication or a breaker
>    command/status, and what MOG_A latching means;
> 5. The sensor and transmitter types/ranges used (e.g., OTI scanner
>    make/model);
> 6. Whether repeated timestamps in exports are expected (API
>    re-transmissions) or would indicate multiple devices;
> 7. What the OTI band 236–250 (with no values between 54 and 236)
>    represents in your telemetry — an error/status code, saturation, or a
>    genuine temperature range.
>
> We will credit any clarification in the public audit and are happy to
> share the full audit report.

## Optional Draft 5 — Kaggle mirror uploader (pythonafroz)

> Subject: Provenance of "Transformer fault Analysis" (v3)
>
> Hello,
>
> Your dataset contains the five CSVs of "Distributed Transformer
> Monitoring" (sreshta140/ai-transformer-monitoring), byte-identical by
> SHA-256, with Overview.csv renamed Alarm.csv. Could you confirm the
> source you copied from and the reason for the rename? We are documenting
> the dataset's lineage and will publish the audit with hashes.

---

**Owner-decision checklist before anything is sent:**
- [ ] authorization to send Draft(s) __ (and via which channel/account)
- [ ] sender identity and return address to use
- [ ] whether to attach/link the audit report
- [ ] wording edits
