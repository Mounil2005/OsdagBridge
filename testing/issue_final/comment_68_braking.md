**Another cause for the Braking Load "N/A"**

While working on the Chapter 3 load tables I found a second reason why the braking force never shows up, besides the missing lane count described above. The function that calculates it crashes for every lane count:

```python
from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017
IRC6_2017.cl_211_2_braking_force(2)
# UnboundLocalError: cannot access local variable 'braking_force_2'
#                    where it is not associated with a value
```
I tried 1, 2, 3 and 4 lanes and all four fail the same way.

**Why:** in `src/osdagbridge/core/utils/codes/irc6_2017.py` (line 888), `braking_force_2` is only set when `lane > 2`, but the line `total_braking_force = braking_force_1 + braking_force_2` sits inside the `for` loop, so it already runs on the first lane, before `braking_force_2` exists. `reports/chap3.py` catches the exception and prints `N/A`, which hides the error.

One more thing worth knowing: the vehicle functions return wheel loads in N (`t = kN * g`), so even without the crash the result would not be in tonnes, as the docstring says.

**Possible fix:** IRC 6 Cl. 211.2 takes 20 % of the vehicle's own load. Computing that per vehicle avoids the loop altogether. For the default vehicles that gives:
- Class A (543.47 kN): **108.69 kN**
- Class 70R wheeled (981 kN): **196.20 kN**

If the per-lane version is kept, moving the sum out of the loop (and starting both terms at 0) fixes the crash.
