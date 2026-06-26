"""Runs the full extraction pipeline over every file in documents/.

For each SUPPORTED image type (png/jpg/jpeg), classifies + extracts fields.
PDF files are reported as skipped with a clear reason (see README - the 2
extra PDFs in this set are outside the 10 required document types anyway).

Outputs:
  output/<filename>.json         - one structured result per document
  output/flagging_report.json    - every flagged document/field in one place
  output/flagging_report.md      - same thing, human-readable
"""
import json
from pathlib import Path

from pipeline import process_document
from schemas import CONFIDENCE_THRESHOLD

DOCS_DIR = Path("documents")
OUTPUT_DIR = Path("output")
SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg"}


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    all_results = []
    skipped = []

    for path in sorted(DOCS_DIR.iterdir()):
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            skipped.append(
                {"file": path.name, "reason": "Unsupported file type for this pipeline (PDF) - "
                                               "see README, these are outside the 10 required types anyway."}
            )
            print(f"SKIP  {path.name} (not an image)")
            continue

        print(f"PROCESSING  {path.name} ...", end=" ", flush=True)
        try:
            result = process_document(path)
        except Exception as e:
            result = {
                "file": path.name,
                "document_type": "error",
                "error": str(e),
                "document_flagged_for_review": True,
                "flag_reason": f"Processing error: {e}",
            }
            print(f"ERROR: {e}")
        else:
            flag = "FLAGGED" if result["document_flagged_for_review"] else "ok"
            print(f"-> {result['document_type']} ({flag})")

        all_results.append(result)
        out_path = OUTPUT_DIR / f"{path.stem}.json"
        out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    build_flagging_report(all_results, skipped)
    print(f"\nDone. {len(all_results)} document(s) processed, {len(skipped)} skipped.")
    print(f"Results saved in {OUTPUT_DIR}/")


def build_flagging_report(results: list, skipped: list):
    report = {
        "confidence_threshold": CONFIDENCE_THRESHOLD,
        "total_documents": len(results),
        "documents_flagged": sum(1 for r in results if r.get("document_flagged_for_review")),
        "skipped_files": skipped,
        "details": [],
    }
    for r in results:
        if r.get("document_flagged_for_review"):
            report["details"].append(
                {
                    "file": r["file"],
                    "document_type": r.get("document_type"),
                    "type_confidence": r.get("type_confidence"),
                    "flag_reason": r.get("flag_reason"),
                    "flagged_fields": r.get("flagged_fields", []),
                }
            )

    (OUTPUT_DIR / "flagging_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    lines = [
        "# Flagging Report",
        f"\nConfidence threshold: **{CONFIDENCE_THRESHOLD}**",
        f"\nDocuments processed: {report['total_documents']}",
        f"Documents flagged for human review: {report['documents_flagged']}",
        "\n## Flagged items\n",
    ]
    for d in report["details"]:
        lines.append(f"### {d['file']} -> `{d['document_type']}`")
        lines.append(f"- Reason: {d['flag_reason']}")
        for f in d["flagged_fields"]:
            lines.append(f"  - **{f['field']}**: value=`{f['value']}`, confidence={f['confidence']}, reason={f['reason']}")
        lines.append("")
    (OUTPUT_DIR / "flagging_report.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
