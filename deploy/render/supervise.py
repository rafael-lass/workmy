"""PID 1: migrate once, run both services, forward signals and reap children."""
import os
import signal
import subprocess
import sys
import time


def main():
    children = []
    stopping = False

    def stop(_signum=None, _frame=None):
        nonlocal stopping
        stopping = True
        for child in children:
            if child.poll() is None:
                child.terminate()

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    try:
        migration = subprocess.Popen([sys.executable, '-m', 'alembic', 'upgrade', 'head'])
        children.append(migration)
        if migration.wait() != 0 or stopping:
            return 1
        children.clear()
        commands = [
            [sys.executable, '-m', 'uvicorn', 'src.presentation.main:app', '--host', '127.0.0.1',
             '--port', '8000', '--workers', '1', '--proxy-headers', '--forwarded-allow-ips', '127.0.0.1'],
            ['node', '/app/bff/server.js'],
        ]
        for command in commands:
            children.append(subprocess.Popen(command, env=os.environ.copy()))
        while not stopping:
            if any(child.poll() is not None for child in children):
                print('Um serviço encerrou; reiniciando o container inteiro.', flush=True)
                return 1
            time.sleep(0.2)
        return 0
    finally:
        stop()
        deadline = time.monotonic() + 20
        for child in children:
            try:
                child.wait(timeout=max(0.1, deadline - time.monotonic()))
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()


if __name__ == '__main__':
    sys.exit(main())
