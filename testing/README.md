# OsdagBridge testing (plate girder bridge module)

Test work for the OsdagBridge Software Testing & Issue Reporting task, run against `dev` @ d74f56d.

| Path | Content |
|---|---|
| `Testing_Report.pdf` / `.tex` | Testing report (scenarios, UI vs dictionary comparison, multi-run, CAD and plots, issues) |
| `test_case_log.csv` | Log of all 14 test cases with exact inputs, expected and actual results, status, issue links |
| `osi_files/` | Input files for the cases (`TC-baseline_inputs.osi`, `TC-010_empty_span.osi`, GUI runs `TC-012` to `TC-014`) |
| `evidence/` | Input and output dictionaries and audit files per case, validator boundary results, GUI report of the baseline |
| `issue_final/` | Text of the issues raised (#64 to #70, #84) |
| `issue_images/`, `video_frames/` | Screenshots used in the issues and in the report |
| `../testing_scripts/run_case.py`, `run_batch.sh` | Script that runs a design from code and diffs the input dictionary before and after `design()` |

Run one case (inside the `osdagbridge-env` environment):

    python testing_scripts/run_case.py TC-003 testing/osi_files/TC-baseline_inputs.osi testing/evidence --set geometry.span=45 --set geometry.carriageway_width=12

Issues: https://github.com/Nidhikhare12/OsdagBridge/issues/64, 65, 66, 67, 68, 69, 70, 84
