# Outreach Request Drafts — DO NOT SEND WITHOUT OWNER AUTHORIZATION

**Status: DRAFTS ONLY.** Nothing in this file has been sent. Per the project
rules, the assistant may ask the dataset owner / operators only for
*credentials or authorization* and for *destructive operations*; sending
these requests requires explicit user authorization.

**Targets and public contact points (verified 2026-09-20):**
- KernelSphere Technologies Pvt Ltd, Hyderabad — kernelsphere.com/contact.html,
  phone 040-40068195 / +91 9550418229, public email addresses on the contact
  page (info@ / jyoti@). CIN U72200TG2013PTC085215 (inc. 2013-01-03, ROC
  Hyderabad).
- Kaggle dataset page of the audited dataset (public comment/discussion
  thread): `sreshta140/ai-transformer-monitoring` (v1, the audited archive,
  uploaded by the Putchala et al. first author); the byte-identical mirror
  `pythonafroz/transformer-fault-analysis` (v3) has its own thread.

---

## Draft 1 — KernelSphere (data provider): entity scope & channel semantics

> Subject: Question about a public transformer telemetry export (2019–2020)
>
> Hello,
>
> We are auditing a publicly available distribution-transformer telemetry
> export (Kaggle, files CurrentVoltage/Overview/Power/PowerFactor/
> TotalPower.csv, window 25 Jun 2019 – 14 Apr 2020, 15-minute cadence,
> columns OTI/WTI/ATI/OLI/OTI_A/OTI_T/MOG_A and VL/IL/KW/KVA). A 2022
> Springer paper (Putchala et al., ICCCE/ICACES) describes live IoT data
> from your platform at 52 locations in Tripura with the same schema.
>
> We would be grateful if you could clarify, for the published export only:
> 1. Does one file correspond to one physical transformer, one location, or
>    several?
> 2. What are the units of OTI and OLI, and what do OTI_A/OTI_T represent
>    (indication vs command)?
> 3. Are repeated timestamps in the export expected (e.g., API
>    re-transmissions)?
> 4. What does the OTI band 236–250 with no values between 54 and 236
>    represent — a genuine temperature range, a status/error code, or a
>    sensor-chain behavior?
>
> We are happy to share our full audit (hashes, statistics, code) and will
> credit any clarification you provide.

## Draft 2 — KernelSphere: technical parameters (if a single asset is confirmed)

> Subject: Follow-up: nameplate/cooling parameters for the public export
>
> Hello,
>
> Following up on our earlier question: if the export can be tied to a
> single physical unit, could you share (or confirm you cannot share) its
> nameplate rating, voltage ratio, cooling class, oil volume/weight, and the
> WTI/OTI sensor make/model or transmitter range? These would let us replace
> the parameterized ranges in our conditional energy analysis with asset
> values. If the data cannot be attributed to a single asset, that answer
> itself is valuable to us and we will state it in the audit.

## Draft 3 — Kaggle uploader (sreshta140 / paper authors): export origin

> Subject: Origin of the "Distributed Transformer Monitoring" dataset
>
> Hello,
>
> We are auditing the transformer telemetry dataset you uploaded
> (sreshta140/ai-transformer-monitoring; v1 archive, five CSVs, hash-pinned
> in our audit). Your ICCCE/ICACES 2022 paper states the live data came
> from KernelSphere Technologies recorded from November 2020, while the
> Kaggle export covers 25 Jun 2019 – 14 Apr 2020.
>
> Could you clarify:
> 1. Is the Kaggle export from the same KernelSphere platform (an earlier
>    window), and how was it extracted (one device? one location? which
>    query)?
> 2. What are the units of OTI/OLI in the export, and what do OTI_A/OTI_T
>    mean operationally?
> 3. Are the repeated timestamps (e.g., 931 in Overview.csv) expected from
>    the API/export process?
>
> We will credit your answers in the public audit report.

## Draft 4 — Kaggle mirror uploader (pythonafroz): provenance of the copy

> Subject: Provenance of "Transformer fault Analysis" (v3)
>
> Hello,
>
> Your dataset "Transformer fault Analysis" contains the five CSV files of
> "Distributed Transformer Monitoring" (sreshta140/ai-transformer-
> monitoring), byte-identical by SHA-256, with Overview.csv renamed
> Alarm.csv. Could you confirm the source you copied from and the reason
> for the rename? We are documenting the dataset's lineage and will
> publish the audit with hashes.

---

**Owner-decision checklist before anything is sent:**
- [ ] user authorizes sending Draft(s) __ at all
- [ ] sender identity and return address to use
- [ ] whether to attach the audit report or link it
- [ ] any edits to wording
