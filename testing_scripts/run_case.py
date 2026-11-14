"""Run one OsdagBridge design from code and audit the dictionaries.

Usage (inside the osdagbridge-env environment):

    python testing_scripts/run_case.py CASE_ID INPUT.osi OUT_DIR [--set key=value ...] [--runs N]

What it does
  1. loads an .osi file (the YAML written by the "Save Input" button) and applies
     --set overrides (the values you would type in the UI)
  2. re-derives dependent inputs with the same solver the GUI uses
  3. runs the design pipeline (N consecutive times on the SAME bridge object, to
     expose state that leaks from one run into the next)
  4. diffs the input dictionary BEFORE vs AFTER design(): any key that the
     pipeline silently changed, added or removed is reported
  5. writes <CASE_ID>_input.json / _output.json / _audit.json to OUT_DIR

Design output printed by the app is hidden (written to <CASE_ID>_stdout.log).
"""
import argparse
import contextlib
import copy
import io
import json
import os
import sys

import yaml

from osdagbridge.core.bridge_types.plate_girder.plategirderbridge import PlateGirderBridge
from osdagbridge.core.bridge_types.plate_girder.defaults import solve_extend_basic_input_dict


class _Log(io.StringIO):
    """StringIO that also accepts the reconfigure() call the app makes on sys.stdout."""
    def reconfigure(self, *args, **kwargs):
        pass


def parse_overrides(pairs):
    out = {}
    for p in pairs or []:
        k, _, v = p.partition("=")
        if v.lower() in ("true", "false"):
            out[k] = v.lower() == "true"
        else:
            out[k] = v
    return out


def same(a, b):
    """Equal after the numeric coercion the bridge applies."""
    try:
        return float(a) == float(b)
    except (TypeError, ValueError):
        return a == b


def diff_dicts(before, after):
    changed, added, removed = {}, {}, {}
    for k in before:
        if k not in after:
            removed[k] = before[k]
        elif not same(before[k], after[k]) and before[k] != after[k]:
            changed[k] = {"before": before[k], "after": after[k]}
    for k in after:
        if k not in before:
            added[k] = after[k]
    return changed, added, removed


def run_design(bridge, inputs, log):
    bridge.set_input(copy.deepcopy(inputs))
    before = copy.deepcopy(bridge.input_dict)
    error = None
    with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
        try:
            bridge.design()
        except Exception as exc:  # report, do not hide
            error = f"{type(exc).__name__}: {exc}"
    after = copy.deepcopy(bridge.input_dict)
    output = dict(bridge.output_dict)
    return before, after, output, error


def utils(output):
    return {k: v for k, v in output.items() if str(k).startswith("util")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("case_id")
    ap.add_argument("osi")
    ap.add_argument("out_dir")
    ap.add_argument("--set", action="append", default=[])
    ap.add_argument("--runs", type=int, default=1)
    ap.add_argument("--after", action="append", default=[],
                    help="override applied AFTER dependent inputs are derived (e.g. a derived value the user edits later)")
    ap.add_argument("--fresh", action="store_true",
                    help="also run every run on a brand-new bridge and compare (stale-state check)")
    ap.add_argument("--then", action="append", default=[],
                    help="overrides for run 2, 3, ... as 'k=v,k=v' (one flag per extra run)")
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    with open(args.osi, "r", encoding="utf-8") as fh:
        base = yaml.safe_load(fh)

    ui = dict(base)
    ui.update(parse_overrides(args.set))
    with contextlib.redirect_stdout(io.StringIO()):
        solve_extend_basic_input_dict(ui)

    ui.update(parse_overrides(args.after))
    bridge = PlateGirderBridge()
    log = _Log()
    runs = []
    current = ui
    n_runs = max(args.runs, 1 + len(args.then))
    for i in range(n_runs):
        if i > 0 and i - 1 < len(args.then):
            current = dict(current)
            current.update(parse_overrides(args.then[i - 1].split(",")))
            with contextlib.redirect_stdout(io.StringIO()):
                solve_extend_basic_input_dict(current)
        before, after, output, error = run_design(bridge, current, log)
        changed, added, removed = diff_dicts(before, after)
        stale = None
        if args.fresh and i > 0:
            _, _, fresh_out, fresh_err = run_design(PlateGirderBridge(), current, _Log())
            stale = {k: {"reused_bridge": v, "fresh_bridge": fresh_out.get(k)}
                     for k, v in utils(output).items()
                     if not same(v, fresh_out.get(k))}
            if fresh_err != error:
                stale["__error__"] = {"reused_bridge": error, "fresh_bridge": fresh_err}
        runs.append({
            "stale_state_diff": stale,
            "run": i + 1, "error": error, "utilisation": utils(output),
            "n_output_keys": len(output),
            "input_changed_by_design": changed, "input_added_by_design": added,
            "input_removed_by_design": removed,
        })
        with open(os.path.join(args.out_dir, f"{args.case_id}_run{i+1}_input.json"), "w", encoding="utf-8") as fh:
            json.dump(before, fh, indent=1, default=str)
        with open(os.path.join(args.out_dir, f"{args.case_id}_run{i+1}_output.json"), "w", encoding="utf-8") as fh:
            json.dump(output, fh, indent=1, default=str)

    with open(os.path.join(args.out_dir, f"{args.case_id}_audit.json"), "w", encoding="utf-8") as fh:
        json.dump({"case": args.case_id, "overrides": parse_overrides(args.set), "runs": runs}, fh, indent=1, default=str)
    with open(os.path.join(args.out_dir, f"{args.case_id}_stdout.log"), "w", encoding="utf-8") as fh:
        fh.write(log.getvalue())

    for r in runs:
        print(f"[{args.case_id}] run {r['run']}: error={r['error']}  output_keys={r['n_output_keys']}")
        print("   util:", {k: (round(v, 2) if isinstance(v, (int, float)) else v) for k, v in r["utilisation"].items()})
        print(f"   input changed by design: {len(r['input_changed_by_design'])}, "
              f"added: {len(r['input_added_by_design'])}, removed: {len(r['input_removed_by_design'])}")
        if r.get("stale_state_diff") is not None:
            print("   STALE-STATE DIFF (reused vs fresh bridge):", r["stale_state_diff"] or "none")
        for k, v in list(r["input_changed_by_design"].items())[:3]:
            print(f"     CHANGED {k}: {v['before']!r} -> {v['after']!r}")


if __name__ == "__main__":
    main()
