TITLE: [Bug] Transverse wind force ignores the girder depth (only the deck slab is counted) and is applied to both outer girders at once

## What is wrong
The transverse wind force on the bridge (IRC 6:2017 Cl. 209.3.3) is FT = Pz x A1 x G x CD, where A1 is the area of the bridge you see from the side. For a plate girder bridge, most of that area is the girder itself. In the code, two things go wrong:

1. **The girder is not part of A1.** In `irc6_2017.py` (lines 681-685):
   ```python
   exposed_height = (max(railing_height, crash_barrier_height) + deck_thickness - openings_in_railing)
   A1 = span * exposed_height
   ```
   The girder depth is passed into the function, but it is only used for the drag coefficient CD, never for the area.
2. **The force is applied twice.** In `analyser.py` (line 1437 and the "WL Transverse" loop at lines 1456-1466), FT is applied to the nodes of **both** outer girders, in the same direction, in the same load case. The comment says this is to cover wind from either side, but since both act together, the model carries 2 x FT.

## How to reproduce
Span 30, carriageway 7.5, Ahmedabad, everything else default, then Design. The solver log prints:
```
Wind loads (IRC:6-2017): Pz=463.7 N/m²  FT=14.79 kN  FT/m=0.493 kN/m ...
```
Working backwards: with G = 2.0 and CD = 2(1 + 2.1 / (20 x 1.67)) = 2.126, an FT of 14.79 kN means A1 = 7.5 m², which is exactly 30 m x 0.25 m, **the deck slab alone**. The 1.67 m deep girder is missing.

With the girder included, A1 = 30 x (1.67 + 0.25) = 57.6 m² and FT is about 113.6 kN, roughly 7.7 times the value used. (The railing and crash barrier add nothing here because their heights arrive as 0, which is the input routing problem in #86.)

This is related to #86 but is a separate problem: #86 is about which wind speed, height and terrain reach the calculation, while this one is about the area formula and how the force is applied. Both would still be wrong after #86 is fixed.

## Environment
Windows 11, Python 3.12 (`environment.yml`), branch `dev` @ d74f56d.

## Suggested fix
Add the girder depth to the exposed height:
```python
# irc6_2017.py, cl_209_3_3_transverse_wind_load
exposed_height = ((d_depth or 0.0) + deck_thickness
                  + max(railing_height, crash_barrier_height) - openings_in_railing)
```
and in `create_wind_load()` apply FT only to the windward outer girder, with a second load case for wind from the other side if both directions should be checked:
```python
for z_target in ext_z[:1]:      # windward girder only
    ...
```
