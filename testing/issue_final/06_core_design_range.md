TITLE: [Bug] design() accepts out-of-range Span (19.9 m, 45.1 m) and completes without an error

## Description
The UI and the `.osi` validator limit Span to 20.0 to 45.0 m ("software limitation"). The design pipeline itself does not check this: calling `set_input()` and `design()` with span 19.9 or 45.1 runs to the end with a full output dictionary and no error. Any caller that does not go through the UI or the OSI validator (a script, the CLI, a future web front-end) can therefore get results outside the supported range without a warning.

| span | `validate_osi_inputs()` | `design()` |
|---|---|---|
| 19.9 | rejected ("Span must be between 20.0 m and 45.0 m") | completes, no error (util.fatigue 221.29 %) |
| 45.1 | rejected (same message) | completes, no error (util.fatigue 108.58 %) |

The same applies to Carriageway Width (4.25 to 23.6 m) and Skew Angle (+-15 deg), which only the UI and the validator enforce.

## Steps to reproduce
```python
import yaml
from osdagbridge.core.bridge_types.plate_girder.plategirderbridge import PlateGirderBridge
from osdagbridge.core.bridge_types.plate_girder.defaults import solve_extend_basic_input_dict

inputs = yaml.safe_load(open("inputs.osi"))      # a saved default design
inputs["geometry.span"] = "19.9"
solve_extend_basic_input_dict(inputs)            # derive girders/spacing as the GUI does
bridge = PlateGirderBridge()
bridge.set_input(inputs)
bridge.design()                                  # completes, no error
```

## Environment
Windows 11, Python 3.12 (from `environment.yml`), branch `dev` @ d74f56d.

## Root cause
`PlateGirderBridge._validate_inputs()` (`src/osdagbridge/core/bridge_types/plate_girder/plategirderbridge.py`, lines 599-620) only checks that four keys are present, `span > 0`, `n_girders >= 2` and `spacing > 0`. The range rules live only in `src/osdagbridge/core/utils/osi_validator.py` and the UI validators.

## Suggested fix
Call the shared validator at the start of the pipeline so there is one source of truth:
```python
def _validate_inputs(self):
    from osdagbridge.core.utils.osi_validator import validate_osi_inputs
    result = validate_osi_inputs(self.input_dict)
    if not result.is_valid:
        raise ValueError(result.error_text(limit=10))
    # ...existing checks...
```
