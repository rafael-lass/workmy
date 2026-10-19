"""Fault injection, executed only inside the disposable CI application container."""
from pathlib import Path
import os
import signal

nodes = []
for process in Path('/proc').iterdir():
    if not process.name.isdigit():
        continue
    try:
        if (process / 'comm').read_text().strip() == 'node':
            nodes.append(int(process.name))
    except OSError:
        # Concurrent health probes can exit between directory listing and read.
        continue
if len(nodes) != 1:
    raise RuntimeError('Expected exactly one Node process in the CI container.')
os.kill(nodes[0], signal.SIGTERM)
