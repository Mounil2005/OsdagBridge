TITLE: [Bug] Turning off design checks in Design Options (Cont.) does nothing: with Fatigue unticked the design still fails on fatigue

## What is wrong
Additional Inputs > Design Options (Cont.) has tick boxes for the ULS and SLS checks (Bending Resistance, Vertical Shear, Lateral Torsional Buckling, Transverse Force, Longitudinal Shear, Fatigue, Stress Limitation, Deflection Control, Crack Width). They are all ticked by default. Unticking them has no effect: every check still runs, and an unticked check can still decide the overall result.

For example, I unticked **Fatigue**, **Bending Resistance** and **Deflection Control** and ran the default design:

- the input dictionary holds `design_options_cont.uls.fatigue: false`, `design_options_cont.uls.bending_resistance: false`, `design_options_cont.sls.deflection_control: false`;
- the design still runs and reports "ULS Flexure", "SLS Deflection (Live)", "SLS Deflection (Total)" and "Fatigue Normal Stress";
- the overall status is still **FAIL, governed by Fatigue Normal Stress**, the check the user switched off;
- all utilisations are identical to the default run (flexure 19.51 %, fatigue 157.26 %, ...).

## Why it happens
None of the `KEY_DO_ULS_*` / `KEY_DO_SLS_*` keys (`design_options_cont.uls.*`, `design_options_cont.sls.*`) is read by the design code (`designer.py`, `plategirderbridge.py`). They are only defined in `ui_fields_additional_input.py`, set in `defaults.py` (lines 376-384) and checked by the validator.

## How to reproduce
1. Span 30, carriageway 7.5, Ahmedabad, everything else default.
2. Additional Inputs > Design Options (Cont.): untick Fatigue (and optionally Bending Resistance and Deflection Control). Save.
3. Design. The output dock and the report still show the fatigue check, and the design status is Fail because of it.

## Environment
Windows 11, Python 3.12 (`environment.yml`), branch `dev` @ d74f56d.

## Suggested fix
Read the switches before building the check list, and leave a disabled check out of the overall status (or mark it "not checked" so it is visible in the report):
```python
enabled = {
    "fatigue":    ai.get(KEY_DO_ULS_FATIGUE, True),
    "flexure":    ai.get(KEY_DO_ULS_BENDING, True),
    "deflection": ai.get(KEY_DO_SLS_DEFLECTION, True),
    ...
}
checks = [c for c in checks if enabled.get(c.category, True)]
```
If switching checks off is not meant to be supported, the tick boxes should be removed or made read-only, because at the moment the dialog suggests an option that does not exist.
