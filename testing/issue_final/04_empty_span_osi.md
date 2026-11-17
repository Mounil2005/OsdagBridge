TITLE: [Bug] An .osi file with an empty Span passes validation, then solve_extend_basic_input_dict raises ValueError

## Description
`validate_osi_inputs()` reports an `.osi` file with `geometry.span: ''` as valid, although Span is a required field (the Design button refuses to run with an empty span: "Empty Required Fields"). The step that re-derives the dependent inputs then crashes on the empty value.

Other invalid values are rejected correctly, so only the empty case slips through:

| `geometry.span` | `validate_osi_inputs()` |
|---|---|
| `abc` | invalid ("Span must be a numeric value") |
| `19.9`, `45.1`, `0`, `-5` | invalid ("Span must be between 20.0 m and 45.0 m") |
| `''` (empty) | **valid** |

## Steps to reproduce
Take a saved `.osi` file, set `geometry.span: ''`, then:
```python
import yaml
from osdagbridge.core.utils.osi_validator import validate_osi_inputs
from osdagbridge.core.bridge_types.plate_girder.defaults import solve_extend_basic_input_dict

d = yaml.safe_load(open("inputs.osi"))
d["geometry.span"] = ""
validate_osi_inputs(d).is_valid        # True
solve_extend_basic_input_dict(d)       # ValueError
```
In the GUI the same file goes through File > Load Input.

## Environment
Windows 11, Python 3.12 (from `environment.yml`), branch `dev` @ d74f56d.

## Proof
```
File ".../plate_girder/defaults.py", line 938, in solve_extend_basic_input_dict
    _on_no_of_girders_changed(basic_input_dict)
File ".../plate_girder/defaults.py", line 531, in _on_no_of_girders_changed
    span = float(working_input_dict.get(KEY_SPAN))
ValueError: could not convert string to float: ''
```

## Root cause
1. `src/osdagbridge/core/utils/osi_validator.py`: an empty string for a required key is accepted instead of failing.
2. `src/osdagbridge/core/bridge_types/plate_girder/defaults.py`, line 531: `float(working_input_dict.get(KEY_SPAN))` has no guard for `''` or `None`.
3. `src/osdagbridge/desktop/ui/template_page.py`, `loadOSI_inputs()`: the re-derive step is wrapped in `try: ... except Exception: pass`, so (from reading the code) the user would still see "Loaded OSI Successfully!" while the girder count, spacing and 2D CAD are not updated.

## Suggested fix
```python
# osi_validator.py: required keys must not be empty
if key in REQUIRED_KEYS and str(value).strip() == "":
    errors.append(f"{key}: required field is empty")

# defaults.py, line 531
raw = working_input_dict.get(KEY_SPAN)
if raw in (None, ""):
    return                      # nothing to derive until the user enters a span
span = float(raw)
```
and log the swallowed exception in `loadOSI_inputs` instead of `pass`.
