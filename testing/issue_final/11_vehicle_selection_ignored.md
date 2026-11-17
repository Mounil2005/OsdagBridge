TITLE: [Bug] Vehicle choices in Additional Inputs > Loading are ignored: even with no vehicle ticked, the design uses Class 70R

## What is wrong
In Additional Inputs > Loading you can tick which vehicles to design for (Class A, Class AA wheeled/tracked, Class 70R wheeled/tracked/bogie, Class SV). The choices are saved in the input dictionary (`loading.live_load.irc.*`) and the report lists them, but the design never reads them.

I unticked vehicles one by one and the results did not move at all. Even with **nothing** ticked, the design still loads the bridge with Class 70R:

| Vehicles ticked | Governing live load (solver log) | Flexure / shear / fatigue utilisation |
|---|---|---|
| All (default) | Case2 1xClass70R, 922.50 kNm | 19.51 / 39.91 / 157.26 % |
| Only Class A | Case2 1xClass70R, 922.50 kNm | 19.51 / 39.91 / 157.26 % |
| None | Case2 1xClass70R, 922.50 kNm | 19.51 / 39.91 / 157.26 % |

In the last case the input dictionary really does contain `class_a: false`, `70r_wheeled: false`, `70r_tracked: false`, `70r_bogie: false`, `aa_wheeled: false`, `aa_tracked: false` and `class_sv: false`, but the results are identical to the default run, to every decimal, and no warning is shown.

The other side of the same problem: Class AA, 70R tracked, 70R bogie and Class SV are never analysed, even when they are ticked.

## Why it happens
- `analyser.py`, `vehicle_lane_coordinates()` (line 1612) builds the vehicle cases only from the carriageway width (IRC 6 Tables 6 and 6A), always as combinations of Class A and Class 70R.
- `deckdesign.py`, `_governing_vehicle()` (line 306) picks Class 70R(W) whenever a 70R fits in the width.

Neither function looks at `loading.live_load.irc.*`.

## How to reproduce
1. Span 30, carriageway 7.5, Ahmedabad, everything else default.
2. Additional Inputs > Loading: untick every vehicle, Save.
3. Design. Compare the utilisations and the solver log with a run where all vehicles are ticked.

## Environment
Windows 11, Python 3.12 (`environment.yml`), branch `dev` @ d74f56d.

## Suggested fix
Filter the Table 6A combinations by what the user ticked, and stop with a clear message if nothing is ticked:
```python
selected = {"ClassA": d.get(KEY_LL_IRC_CLASS_A),
            "Class70R": d.get(KEY_LL_IRC_70R_WHEELED)}
combos = [c for c in IRC6_2017.table_6A(cw)["vehicle_combinations"]
          if all(selected.get(v) for v in c)]
if not combos:
    raise ValueError("Select at least one vehicle in Additional Inputs > Loading.")
```
Use the same selection in `deckdesign._governing_vehicle()`. Until AA, 70R tracked/bogie and SV are supported by the analysis, it would help to grey them out in the dialog (or mark them "not analysed") so users don't assume they were checked.
