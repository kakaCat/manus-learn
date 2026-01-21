"""Tool implementations for Shell MCP server."""

import os
import subprocess
import tempfile
import time
import signal
from pathlib import Path
from typing import List, Optional, Dict, Any

import psutil

from common.security import validate_command, validate_path
from common.types import CommandResult, ProcessInfo, ErrorCode
from common.logging_config import setup_logging
from shell_mcp.config import DEFAULT_TIMEOUT, DEFAULT_CWD, MAX_OUTPUT_SIZE

logger = setup_logging("shell-mcp-tools")


async def execute_command(
    command: str,
    args: Optional[List[str]] = None,
    cwd: str = DEFAULT_CWD,
    timeout: int = DEFAULT_TIMEOUT,
    env: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Execute a shell command safely with timeout.

    Args:
        command: Command to execute (must be in allowed list)
        args: Command arguments (optional)
        cwd: Working directory (default: /root/shared/workspace)
        timeout: Maximum execution time in seconds (default: 60)
        env: Additional environment variables (optional)

    Returns:
        Dictionary with stdout, stderr, exit_code, and execution_time

    Raises:
        ValueError: If command is not allowed or inputs are invalid
        subprocess.TimeoutExpired: If execution exceeds timeout
    """
    logger.info(f"Executing command: {command} {args or []}")

    # Validate command
    validate_command(command, args)

    # Validate working directory
    cwd_path = validate_path(cwd)

    # Build command list (never use shell=True for security)
    cmd_list = [command]
    if args:
        cmd_list.extend(args)

    # Prepare environment
    exec_env = None
    if env:
        exec_env = dict(os.environ)
        exec_env.update(env)

    # Execute command
    start_time = time.time()
    try:
        result = subprocess.run(
            cmd_list,
            cwd=str(cwd_path),
            capture_output=True,
            text=True,
            timeout=timeout,
            env=exec_env,
            shell=False  # CRITICAL: never use shell=True
        )
        execution_time = time.time() - start_time

        # Truncate output if too large
        stdout = result.stdout
        stderr = result.stderr
        if len(stdout) > MAX_OUTPUT_SIZE:
            stdout = stdout[:MAX_OUTPUT_SIZE] + "\n[OUTPUT TRUNCATED]"
        if len(stderr) > MAX_OUTPUT_SIZE:
            stderr = stderr[:MAX_OUTPUT_SIZE] + "\n[OUTPUT TRUNCATED]"

        logger.info(
            f"Command completed: {command}, exit_code={result.returncode}, "
            f"time={execution_time:.2f}s"
        )

        return {
            "stdout": stdout,
            "stderr": stderr,
            "exit_code": result.returncode,
            "execution_time": execution_time
        }

    except subprocess.TimeoutExpired as e:
        execution_time = time.time() - start_time
        logger.error(f"Command timed out after {timeout}s: {command}")
        raise ValueError(
            f"Command execution timed out after {timeout} seconds"
        ) from e

    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"Command execution failed: {command}, error: {e}")
        raise


async def execute_shell_script(
    script: str,
    cwd: str = DEFAULT_CWD,
    timeout: int = DEFAULT_TIMEOUT
) -> Dict[str, Any]:
    """
    Execute a bash script safely.

    Args:
        script: Shell script content
        cwd: Working directory
        timeout: Maximum execution time in seconds

    Returns:
        Dictionary with stdout, stderr, exit_code, and execution_time
    """
    logger.info("Executing shell script")

    # Validate working directory
    cwd_path = validate_path(cwd)

    # Create temporary script file
    with tempfile.NamedTemporaryFile(
        mode='w',
        suffix='.sh',
        delete=False,
        dir='/tmp'
    ) as f:
        f.write(script)
        script_path = f.name

    try:
        # Make script executable
        os.chmod(script_path, 0o755)

        # Execute script with bash
        start_time = time.time()
        result = subprocess.run(
            ['bash', script_path],
            cwd=str(cwd_path),
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=False
        )
        execution_time = time.time() - start_time

        logger.info(f"Script completed, exit_code={result.returncode}")

        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.returncode,
            "execution_time": execution_time
        }

    except subprocess.TimeoutExpired as e:
        logger.error(f"Script timed out after {timeout}s")
        raise ValueError(
            f"Script execution timed out after {timeout} seconds"
        ) from e

    finally:
        # Clean up temporary file
        try:
            os.unlink(script_path)
        except Exception as e:
            logger.warning(f"Failed to delete temp script: {e}")


async def get_running_processes() -> List[Dict[str, Any]]:
    """
    Get list of running processes.

    Returns:
        List of process information dictionaries
    """
    logger.info("Getting running processes")

    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'status', 'cpu_percent', 'memory_percent', 'username']):
        try:
            info = proc.info
            processes.append({
                "pid": info['pid'],
                "name": info['name'],
                "status": info['status'],
                "cpu_percent": info['cpu_percent'],
                "memory_percent": info['memory_percent'],
                "username": info['username']
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            # Process terminated or access denied
            continue

    logger.info(f"Found {len(processes)} processes")
    return processes


async def kill_process(pid: int, signal_name: str = "SIGTERM") -> Dict[str, Any]:
    """
    Kill a process by PID.

    Args:
        pid: Process ID to kill
        signal_name: Signal to send (SIGTERM, SIGKILL, etc.)

    Returns:
        Dictionary with success status and message

    Raises:
        ValueError: If trying to kill protected processes
    """
    logger.info(f"Attempting to kill process {pid} with signal {signal_name}")

    # Protected PIDs (supervisord, init, etc.)
    PROTECTED_PIDS = {1}  # PID 1 is init/supervisord

    if pid in PROTECTED_PIDS:
        raise ValueError(f"Cannot kill protected process: PID {pid}")

    try:
        process = psutil.Process(pid)

        # Don't allow killing supervisord or its children
        if 'supervisor' in process.name().lower():
            raise ValueError(f"Cannot kill supervisor process: {process.name()}")

        # Get signal
        sig = getattr(signal, signal_name, signal.SIGTERM)

        # Send signal
        process.send_signal(sig)

        logger.info(f"Signal {signal_name} sent to process {pid}")

        return {
            "success": True,
            "message": f"Signal {signal_name} sent to process {pid}"
        }

    except psutil.NoSuchProcess:
        raise ValueError(f"No such process: PID {pid}")

    except psutil.AccessDenied:
        raise ValueError(f"Access denied: Cannot kill process {pid}")

    except Exception as e:
        logger.error(f"Failed to kill process {pid}: {e}")
        raise
