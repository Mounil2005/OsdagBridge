TITLE: [Bug] Bearing length (Support Conditions) and Construction Stage = No (Design Options) are not used by the design

## What is wrong
Two more Additional Inputs fields are saved but have no effect on the design:

1. **Support Conditions > Bearing Length** (default 400 mm). The bearing stiffener check needs the stiff bearing length b1. In `designer.py` (lines 1650-1654) b1 comes from `cfg.bs_b1_mm`, and when that is 0 it is computed automatically with IS 800 Cl. 8.7.1.3. `bs_b1_mm` is never filled from `support_conditions.bearing_length`, so it always stays 0 and the user's bearing length is never used.
2. **Design Options > Construction Stage** (Yes / No). With "No", the design still runs and reports the check "LTB (Construction Stage)". The key `design_options.construction.stage` is not read anywhere in the design code.

## How to reproduce
Span 30, carriageway 7.5, Ahmedabad, everything else default.

| Change | Result compared with the default run |
|---|---|
| Bearing length 400 → **100 mm** | all outputs identical (only the echoed input value differs); "Brg.Stiff: Bearing Contact" unchanged |
| Construction Stage Yes → **No** | all outputs identical; "LTB (Construction Stage)" still checked and reported |

In both runs the new value is in the input dictionary (`support_conditions.bearing_length: 100`, `design_options.construction.stage: No`).

## Environment
Windows 11, Python 3.12 (`environment.yml`), branch `dev` @ d74f56d.

## Suggested fix
```python
# when building the design config
cfg.bs_b1_mm = float(ai.get(KEY_SC_BEARING_LENGTH) or 0.0)

# when building the check list
if str(ai.get(KEY_DS_CONSTRUCTION_STAGE, "Yes")).lower() == "no":
    checks = [c for c in checks if c.name != "LTB (Construction Stage)"]
```
If the construction stage check is always required, the option could be removed from the dialog instead.
