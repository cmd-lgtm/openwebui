"""
Code execution service
"""
import asyncio
import logging
import subprocess
import tempfile
import os
from typing import Dict, Any, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


class CodeExecutor:
    """Execute code in sandboxed environments"""

    SUPPORTED_LANGUAGES = {
        "python": "python3",
        "javascript": "node",
        "bash": "bash",
        "shell": "sh",
    }

    async def execute(
        self,
        code: str,
        language: str = "python",
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Execute code and return output.

        Args:
            code: Code to execute
            language: Programming language
            timeout: Timeout in seconds

        Returns:
            Dict with output, error, and execution_time
        """
        if not settings.CODE_EXECUTION_ENABLED:
            return {
                "output": "",
                "error": "Code execution is disabled",
                "execution_time": 0,
            }

        timeout = timeout or settings.CODE_EXECUTION_TIMEOUT

        # Get executable
        executable = self.SUPPORTED_LANGUAGES.get(language.lower())
        if not executable:
            return {
                "output": "",
                "error": f"Unsupported language: {language}",
                "execution_time": 0,
            }

        # Create temp file for execution
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=f".{language}",
            delete=False
        ) as f:
            f.write(code)
            temp_file = f.name

        try:
            # Execute with timeout
            start_time = asyncio.get_event_loop().time()

            process = await asyncio.create_subprocess_exec(
                executable,
                temp_file,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
                execution_time = asyncio.get_event_loop().time() - start_time

                return {
                    "output": stdout.decode() if stdout else "",
                    "error": stderr.decode() if stderr else "",
                    "execution_time": execution_time,
                    "exit_code": process.returncode,
                }

            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                execution_time = asyncio.get_event_loop().time() - start_time

                return {
                    "output": "",
                    "error": f"Execution timed out after {timeout} seconds",
                    "execution_time": execution_time,
                    "exit_code": -1,
                }

        except Exception as e:
            logger.error(f"Code execution error: {e}")
            return {
                "output": "",
                "error": str(e),
                "execution_time": 0,
            }

        finally:
            # Cleanup temp file
            try:
                os.unlink(temp_file)
            except Exception:
                pass


# Singleton instance
_code_executor: Optional[CodeExecutor] = None


def get_code_executor() -> CodeExecutor:
    """Get code executor instance"""
    global _code_executor
    if _code_executor is None:
        _code_executor = CodeExecutor()
    return _code_executor
