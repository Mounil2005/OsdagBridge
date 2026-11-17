**Reproduced on Windows**

I can confirm this on Windows 11 / Python 3.12 (`dev` @ d74f56d). I took the default bridge (span 30 m, carriageway 7.5 m, 4 girders, Ahmedabad) and changed only the skew angle:

| Result | Skew +15° | Skew −15° | Difference |
|---|---|---|---|
| Flexure utilisation | 19.49 % | 18.17 % | −7 % |
| Shear utilisation | 41.73 % | 53.27 % | **+28 %** |
| Fatigue utilisation | 157.07 % | 145.93 % | −7 % |
| LTB utilisation | 22.70 % | 22.70 % | same |

The bridge and the loading are symmetric, so a +15° and a −15° skew are mirror images and should give the same governing values. Shear is the most affected: the −15° case is 28 % higher. So depending on which way the user enters the skew, the design can come out quite differently.

Both runs completed without errors. Input and output dictionaries for both cases are available if that helps with tracing it.
