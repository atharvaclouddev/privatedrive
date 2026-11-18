import re
import subprocess
import threading
import time
import logging

logger = logging.getLogger("privatedrive.tunnel")

class SSHTunnel:
    def __init__(self, local_port=8080, on_ready=None):
        self.local_port = local_port
        self.public_url = None
        self.on_ready = on_ready
        self.proc = None
        self._thread = None
        self._stop_event = threading.Event()

    def start(self):
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_tunnel, daemon=True)
        self._thread.start()

    def _run_tunnel(self):
        while not self._stop_event.is_set():
            cmd = [
                "ssh",
                "-T",
                "-o", "StrictHostKeyChecking=no",
                "-o", "ServerAliveInterval=30",
                "-o", "ServerAliveCountMax=3",
                "-o", "ExitOnForwardFailure=yes",
                "-R", f"80:localhost:{self.local_port}",
                "nokey@localhost.run"
            ]
            try:
                self.proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1
                )
                logger.info("Connecting SSH tunnel to localhost.run...")

                for line in iter(self.proc.stdout.readline, ''):
                    if self._stop_event.is_set():
                        break
                    line_clean = line.strip()
                    match = re.search(r'https://[a-zA-Z0-9.-]+\.lhr\.life', line_clean)
                    if match:
                        url = match.group(0)
                        if self.public_url != url:
                            self.public_url = url
                            logger.info(f"Public tunnel URL established: {self.public_url}")
                            if self.on_ready:
                                try:
                                    self.on_ready(self.public_url)
                                except Exception as cb_err:
                                    logger.warning(f"on_ready error: {cb_err}")

                self.proc.wait()
            except Exception as e:
                logger.warning(f"Tunnel process encountered error: {e}")

            if not self._stop_event.is_set():
                time.sleep(3)

    def stop(self):
        self._stop_event.set()
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.proc.kill()
