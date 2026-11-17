TITLE: [Bug] Footpath pedestrian load: the Custom pressure is ignored, and the load is added to the dead-load case instead of live load

## What is wrong
Additional Inputs > Loading has a "Footpath Pressure" field with two modes, "As per IRC 6" and "Custom". Whatever is chosen there, the analysis applies the same footpath load, and it puts that load in the wrong group:

1. **The Custom value is never used.** `analyser.py`, `create_footpath_load()` (line 613) takes the intensity from `footpath_dead_load_kN_m2()`, which returns `IRC6_2017.cl_206_1_footway_load()`. That function picks `FOOTWAY_LOADS[KEY_TYPE_FOOTWAY[0]]`, which is always the `'Default'` entry (500 kg/m², i.e. 4.905 kN/m²). `loading.live_load.footpath_pressure.mode` and `.value` are not read anywhere in the analysis.
2. **It is treated as dead load.** The pedestrian load of IRC 6 Cl. 206.1 is a live load, but the load case is called `DL_footpath` and is added to the dead-load combination (`create_dead_load_combination()`, line 1535 lists `"footpath_load_case"` together with self weight and deck). So it gets the dead-load factors and is present in every combination as if it were permanent.

## How to reproduce
1. Span 30, carriageway 7.5, Ahmedabad, **Footpath: Both Sides**, everything else default. Design.
2. Additional Inputs > Loading > Footpath Pressure: **Custom**, value **1.0**. Design again.

| Footpath pressure | Solver log | Flexure / shear / fatigue utilisation |
|---|---|---|
| As per IRC 6 | `Footpath load magnitude: 4905.00 N/m²` | 25.41 / 56.29 / 210.05 % |
| Custom, 1.0 kN/m² | `Footpath load magnitude: 4905.00 N/m²` | 25.41 / 56.29 / 210.05 % |

The second input dictionary really contains `loading.live_load.footpath_pressure.mode: Custom` and `value: 1.0`, but nothing changes.

Two smaller things in the same area:
- The field is labelled **"Footpath Pressure (kN/mm²)"** (`ui_fields_additional_input.py`, line 607). It should be kN/m². The validator accepts 0 to 5000, which only makes sense in kg/m², so it is not clear which unit the user is meant to type.
- Because of the constant `KEY_TYPE_FOOTWAY[0]`, the 400 kg/m² entry ("Regular Footway") in `FOOTWAY_LOADS` can never be selected, and the span-dependent reduction in Cl. 206.1 for longer spans is not applied.

## Environment
Windows 11, Python 3.12 (`environment.yml`), branch `dev` @ d74f56d.

## Suggested fix
- Read the footpath pressure from the inputs and fall back to the IRC value only when the mode is "As per IRC 6":
  ```python
  mode = d.get(KEY_LL_FOOTPATH_PRESSURE_MODE)
  p_kN_m2 = (float(d[KEY_LL_FOOTPATH_PRESSURE_VALUE]) if mode == "Custom"
             else IRC6_2017.cl_206_1_footway_load())
  ```
- Create the footpath load as a live-load case (for example `"LL Footpath"`) and include it in the ULS/SLS combinations with the live-load factors, instead of adding it to `create_dead_load_combination()`. The footpath slab's own weight (thickness x density) is the part that belongs in dead load.
- Fix the unit label to kN/m² and set the validator range to match.
