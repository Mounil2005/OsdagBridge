"""Generate the OsdagBridge design report without the GUI.

Usage (inside the osdagbridge-env conda environment):

    python examples/generate_report_headless.py INPUT.osi OUTPUT_DIR [FILE_STEM]

Loads a saved ``.osi`` input file, runs the full design pipeline, builds the
report payload and compiles the PDF + .tex. CAD figures are not rendered in
headless mode, so figure slots show placeholders; every table, chart and
layout feature of the report is still produced, which makes this script handy
for before/after comparisons of the report generator.
"""
import os
import sys
import datetime

import yaml

from osdagbridge.core.bridge_types.plate_girder.plategirderbridge import PlateGirderBridge
from osdagbridge.core.reports.report_generator import (
    ReportMetadata, ReportOptions, ReportRequest, build_report_payload, generate_report,
)


def main(osi_path, out_dir, stem="Report"):
    with open(osi_path, "r", encoding="utf-8") as fh:
        inputs = yaml.safe_load(fh)

    bridge = PlateGirderBridge()
    bridge.set_input(inputs)
    bridge.design()

    meta = ReportMetadata(
        project_name="OsdagBridge Test Project",
        project_location="",   # empty: use the location stored in the .osi file
        designer="Designer",
        client="Client",
        company="Company",
        job_number="JOB-001",
        report_date=datetime.date.today().isoformat(),
    )
    options = ReportOptions(
        sections=["loads", "analysis", "design_checks", "drawings"],
        include_figures=True,
        include_toc=True,
        include_pdf=True,
    )
    request = ReportRequest(metadata=meta, options=options, output_dir=out_dir, file_stem=stem)

    report_inputs = bridge.input_dict.copy()
    output_dict = dict(bridge.output_dict)
    lc_sum = getattr(bridge, "_lc_summary", None)
    rxn_sum = getattr(bridge, "_reaction_summary", None)
    if lc_sum is not None or rxn_sum is not None:
        output_dict["analysis_summary"] = {"load_cases": lc_sum or {}, "reactions": rxn_sum or {}}

    payload = build_report_payload(request, report_inputs, output_dict)
    payload.figure_data = {}
    result = generate_report(payload, request)
    print("PDF:", result.pdf_path)
    print("TEX:", result.tex_path)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    os.makedirs(sys.argv[2], exist_ok=True)
    main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "Report")
