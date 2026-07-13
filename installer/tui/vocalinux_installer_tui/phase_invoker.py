"""Phase script invoker."""

import asyncio
import glob
import os
from typing import Callable, Optional


async def run_phase(
    phase_script: str,
    on_line: Optional[Callable[[str], None]] = None,
    env: Optional[dict[str, str]] = None,
) -> int:
    """Run a bash phase script asynchronously, streaming output line by line."""
    phase_env = os.environ.copy()
    if env:
        phase_env.update(env)

    proc = await asyncio.create_subprocess_exec(
        "bash",
        phase_script,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        env=phase_env,
    )

    if proc.stdout:
        async for line in proc.stdout:
            decoded = line.decode("utf-8", errors="replace").rstrip()
            if on_line:
                on_line(decoded)

    return await proc.wait()


async def run_all_phases(
    phase_dir: str,
    on_phase_start: Optional[Callable[[str], None]] = None,
    on_line: Optional[Callable[[str], None]] = None,
    env: Optional[dict[str, str]] = None,
) -> bool:
    """Run all phases in order. Returns True if all succeeded."""
    phases = sorted(glob.glob(os.path.join(phase_dir, "*.sh")))

    for phase in phases:
        name = os.path.basename(phase)
        if on_phase_start:
            on_phase_start(name)

        rc = await run_phase(phase, on_line=on_line, env=env)
        if rc != 0:
            return False

    return True
