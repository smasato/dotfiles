"""Check local integration before and after updating Herdr plugins."""
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
CHECK = [sys.executable, str(ROOT / "scripts/check-worktrunk.py")]
INSTALLER = ROOT / "dot_config/herdr/scripts/executable_update-plugins.sh"


def record_validation(report_file, after):
    report = json.loads(report_file.read_text())
    report["validation"] = dict(before="passed", after=after)
    if after != "not-run":
        report["status"] = "verified" if after == "passed" else "validation-failed"
    temporary = report_file.with_suffix(".tmp")
    temporary.write_text(json.dumps(report))
    temporary.replace(report_file)
    return report["status"]


def main():
    subprocess.run(CHECK, check=True, cwd=ROOT)
    result = subprocess.run(["bash", str(INSTALLER)], text=True, stdout=subprocess.PIPE, cwd=ROOT)
    if not result.stdout.strip():
        return result.returncode or 1
    report_file = Path(json.loads(result.stdout)["report"])
    if result.returncode:
        record_validation(report_file, "not-run")
        return result.returncode
    validation = subprocess.run(CHECK, cwd=ROOT)
    status = record_validation(report_file, "passed" if validation.returncode == 0 else "failed")
    print(f"Herdr plugin update: {status}\nReport: {report_file}")
    return validation.returncode


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(error, file=sys.stderr)
        sys.exit(1)
