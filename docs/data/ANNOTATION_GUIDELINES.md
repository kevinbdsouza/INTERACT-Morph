# MVP-010: Annotation Guidelines (Family A)

## Scope
These rules define how to annotate Family A runs for regime and failure-mode supervision.

## Primary Labels
- `encapsulation_success`: `true` if stable shell closure with retained core after transient settling window
- `regime_label`:
  - `stable_wrapping`
  - `trapping`
  - `penetration_no_wrap`
  - `partial_wrapping`
  - `rupture_after_wrap`
- `failure_mode`:
  - `none`
  - `trapping`
  - `partial_wrapping`
  - `premature_rupture`
  - `lateral_spreading`
  - `asymmetry`
  - `other`

## Event Time Annotations (ms)
Record if observable; leave null only when impossible to determine.
- `lamella_onset_ms`
- `first_contact_ms`
- `neck_formation_ms`
- `closure_time_ms`
- `detachment_time_ms`
- `rupture_time_ms`

## Measurement Guidance
- `shell_thickness_mean_um`: measured from post-closure frame window, minimum 3 angular samples
- `capsule_eccentricity`: compute from fitted ellipse major/minor axes

## Labeling Protocol
1. Review full-speed and slow-motion playback.
2. Mark first-contact and closure/rupture events.
3. Assign regime label using definitions above.
4. Assign failure mode consistent with regime.
5. Record confidence (`high`, `medium`, `low`) in notes.
6. If uncertain, mark for adjudication and do not force label.

## Quality Control
- 10% weekly double-annotation audit
- Resolve disagreements in adjudication log
- Re-annotate model-disagreement outliers prioritized by active learning queue
