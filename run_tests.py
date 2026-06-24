#!/usr/bin/env python3
"""run_tests.py -- run every tests/test_*.py and report a pass/fail summary.

Each test file runs its own checks under __main__ (asserting as it goes), so we
just execute each as a subprocess, capture the result, and tally. Exits non-zero
if anything fails.

    python run_tests.py            # run all
    python run_tests.py combat     # run only files whose name contains 'combat'
"""
import glob
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
TESTS = os.path.join(ROOT, "tests")


def main() -> int:
    needle = sys.argv[1] if len(sys.argv) > 1 else ""
    files = sorted(glob.glob(os.path.join(TESTS, "test_*.py")))
    files = [f for f in files if needle in os.path.basename(f)]
    if not files:
        print("No test files match {!r}".format(needle))
        return 1

    passed, failed = [], []
    width = max(len(os.path.basename(f)) for f in files)
    print("Running {} test file(s)\n".format(len(files)))
    start = time.time()
    for f in files:
        name = os.path.basename(f)
        t0 = time.time()
        proc = subprocess.run([sys.executable, f], cwd=ROOT,
                              capture_output=True, text=True)
        dt = time.time() - t0
        ok = proc.returncode == 0
        (passed if ok else failed).append(name)
        mark = "PASS" if ok else "FAIL"
        print("  [{}] {:<{w}}  {:.2f}s".format(mark, name, dt, w=width))
        if not ok:
            tail = (proc.stdout + proc.stderr).strip().splitlines()[-12:]
            for line in tail:
                print("        | " + line)

    total_dt = time.time() - start
    print("\n{} passed, {} failed  ({} files, {:.1f}s)".format(
        len(passed), len(failed), len(files), total_dt))
    if failed:
        print("FAILED: " + ", ".join(failed))
        return 1
    print("All tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
