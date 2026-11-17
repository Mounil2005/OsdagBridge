TITLE: [Bug] Crash barrier and median loads from the inputs never reach the analysis (fixed 6.54 and 4.00 kN/m are used instead)

## What is wrong
The crash barrier and the median are applied to the grillage as line loads. The inputs already hold the right values for the selected barrier and median type (`typical_section.crash_barrier.load`, `typical_section.median.load`, worked out from the section area and density), and the report prints them. But the analysis does not use them. It always applies fixed defaults:

| Item | Value in the input dictionary (and in the report) | Value applied in the analysis (solver log) |
|---|---|---|
| Crash barrier (IRC 5 - RCC Crash Barrier) | 7.557 kN/m | **6.54 kN/m** |
| Median (IRC 5 - RCC Crash Barrier type, 1.2 m wide) | 14.08 kN/m | **4.00 kN/m** |

So the median load used in the design is less than a third of the real one, and changing the barrier or median type in Additional Inputs has no effect on the analysis at all.

## Why it happens
- `plategirderbridge.py`, `add_dead_loads()` (line 1328): the crash barrier load comes from `crash_barrier_load_from_inputs(self.input_dict)`, which looks for the key `"crash_barrier_load"` (`crash_barrier/geometry.py`, line 313). The input dictionary stores it as `"typical_section.crash_barrier.load"`, so the lookup returns `None` and `DEFAULT_CRASH_BARRIER_LOAD_kN_m` (6.54) is used.
- The same function calls `model.create_median_load()` with **no argument** (line 1338), so `median_dead_load_kN_m(None)` always returns the 4.00 kN/m default. `typical_section.median.load` is never read by the analysis.

## How to reproduce
1. Span 30, carriageway 7.5, Ahmedabad, **Include Median: Yes**, everything else default.
2. Design, and look at the solver log:
   ```
   Crash barrier line load magnitude: 6540.00 N/m
   Median line load magnitude: 4000.00 N/m
   ```
3. Compare with the input dictionary (or Save Input): `typical_section.crash_barrier.load: 7.557`, `typical_section.median.load: 14.079`.

## Environment
Windows 11, Python 3.12 (`environment.yml`), branch `dev` @ d74f56d.

Related: #86 has the same kind of key mismatch for the wind inputs, and #74 for the crash barrier width. This issue is about the crash barrier and median **loads**, which are not covered there.

## Suggested fix
Read the canonical keys and pass both values in:
```python
# plategirderbridge.py, add_dead_loads()
barrier_load_kN_m = _float_or_none(self.input_dict.get(KEY_CB_LOAD))
median_load_kN_m  = _float_or_none(self.input_dict.get(KEY_MD_LOAD))
...
model.create_crash_barrier_load(barrier_load_kN_per_m=barrier_load_kN_m)
model.create_median_load(median_load_kN_per_m=median_load_kN_m)
```
(or change `_KEY_CRASH_BARRIER_LOAD` to `"typical_section.crash_barrier.load"`). A short log line or warning when a default is used instead of the input would also make this kind of problem easy to spot.
