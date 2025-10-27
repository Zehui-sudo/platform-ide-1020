#!/usr/bin/env python3

import contextlib
import io
import json
import signal
import sys
import time
import traceback

DEFAULT_TIMEOUT = 10.0
MAX_TIMEOUT = 25.0
OUTPUT_LIMIT = 10_000


class ExecutionTimeout(Exception):
    pass


def _parse_payload(raw: str) -> dict:
    if not raw.strip():
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"code": raw}


def _clamp_timeout(value) -> float:
    try:
        num = float(value)
    except (TypeError, ValueError):
        num = DEFAULT_TIMEOUT
    if num <= 0:
        num = DEFAULT_TIMEOUT
    return min(MAX_TIMEOUT, max(0.1, num))


def _truncate(text: str) -> str:
    if len(text) <= OUTPUT_LIMIT:
        return text
    return text[:OUTPUT_LIMIT] + "\n...[output truncated]..."


def main() -> int:
    raw = sys.stdin.read()
    payload = _parse_payload(raw)
    code = payload.get("code")
    if not isinstance(code, str) or not code.strip():
        print(
            json.dumps(
                {
                    "status": "error",
                    "stdout": "",
                    "stderr": "missing code",
                    "timedOut": False,
                    "duration": 0.0,
                    "exitCode": None,
                }
            )
        )
        return 1

    timeout = _clamp_timeout(payload.get("timeout", DEFAULT_TIMEOUT))

    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()
    globals_dict = {"__name__": "__main__"}
    status = "success"
    timed_out = False
    exit_code = 0

    def _timeout_handler(signum, frame):
        raise ExecutionTimeout()

    signal.signal(signal.SIGALRM, _timeout_handler)
    signal.setitimer(signal.ITIMER_REAL, timeout)
    start = time.monotonic()

    try:
        with contextlib.redirect_stdout(stdout_capture), contextlib.redirect_stderr(stderr_capture):
            exec(compile(code, "<sandbox>", "exec"), globals_dict)
    except ExecutionTimeout:
        status = "timeout"
        timed_out = True
        exit_code = None
    except Exception:
        status = "error"
        exit_code = 1
        traceback.print_exc(file=stderr_capture)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)

    duration = time.monotonic() - start
    result = {
        "status": status,
        "stdout": _truncate(stdout_capture.getvalue()),
        "stderr": _truncate(stderr_capture.getvalue()),
        "timedOut": timed_out,
        "duration": duration,
        "exitCode": exit_code,
    }
    print(json.dumps(result))
    return 0 if status == "success" else 1


if __name__ == "__main__":
    sys.exit(main())
