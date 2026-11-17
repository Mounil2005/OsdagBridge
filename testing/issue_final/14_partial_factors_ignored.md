TITLE: [Bug] Partial safety factors γc, γs, γfl and the self-weight factor in Additional Inputs have no effect on the design

## What is wrong
Additional Inputs lets the user set the partial safety factors (Design Options (Cont.) > Partial Factors) and a self-weight factor (Loading > Permanent Load). Some of these are used by the design, but several are only stored and printed in the report, while the calculation keeps its own fixed values.

I changed each value and compared the results with the default run, all else equal:

| Input changed | Default → new | Effect on the design |
|---|---|---|
| γm0 (yielding and buckling), as a control | 1.10 → 1.20 | flexure 19.51 → **21.08 %**, LTB 22.81 → **24.89 %** (works) |
| γc basic (concrete) | 1.50 → 1.80 | **none**, all utilisations identical |
| γs (reinforcing steel) | 1.15 → 1.30 | **none** |
| γfl (fatigue load) | 1.00 → 1.50 | **none** (fatigue stays 157.26 %) |
| Self-weight factor | 1.00 → 1.50 | **none** |

The new values are really in the input dictionary (`design_options_cont.partial_factor.concrete_basic.gamma_c_basic: 1.8`, `...reinforcing_steel.gamma_s: 1.3`, `...fatigue_load.gamma_flt: 1.5`, `loading.permanent_load.dead_load.self_weight_factor: 1.5`), and the report (Chapter 2) prints them, so the report shows factors that were not used in the calculation.

## Why it happens
- γm0, γm1, γv and γmf are read by `designer.py` (for example `KEY_DO_GAMMA_MF` at line 362).
- `KEY_DO_GAMMA_C_BASIC`, `KEY_DO_GAMMA_C_ACCIDENTAL`, `KEY_DO_GAMMA_S`, `KEY_DO_GAMMA_FLT` and `KEY_PL_SELF_WEIGHT_FACTOR` are not read anywhere in the analysis or design code. Instead the values are fixed in the code, for example `gamma_c=1.50` and the accidental `1.20` in `irc22_2015.py` (lines 401 and 412), and `"steel_reinforcement_yield": {"ULS": 1.15, ...}` (line 41).

## How to reproduce
1. Span 30, carriageway 7.5, Ahmedabad, everything else default. Design and note the utilisations.
2. Additional Inputs > Design Options (Cont.): set γc (basic) to 1.80 and γs to 1.30. Design again: nothing changes.
3. Set γm0 to 1.20 instead and Design: flexure and LTB change, which shows the method itself is fine.

## Environment
Windows 11, Python 3.12 (`environment.yml`), branch `dev` @ d74f56d.

## Suggested fix
Pass the values from the inputs into the capacity functions the same way γm0 and γmf already are, for example:
```python
gamma_c = float(ai.get(KEY_DO_GAMMA_C_BASIC, 1.50))
gamma_c_acc = float(ai.get(KEY_DO_GAMMA_C_ACCIDENTAL, 1.20))
gamma_s = float(ai.get(KEY_DO_GAMMA_S, 1.15))
...
IRC22_2014.cl_603_3_1_positive_moment_capacity(..., gamma_c=gamma_c, gamma_c_accidental=gamma_c_acc, gamma_s=gamma_s)
```
apply γfl to the fatigue load effects, and multiply the self-weight load case by the self-weight factor. If some of these fields are meant to be informational only, they should be read-only in the dialog so users don't expect them to change the design.
