"""Short-lived student code sandbox for Kimi-like workflow events."""
from __future__ import annotations

import asyncio
import base64
import re
import shutil
import sys
import tempfile
from collections.abc import AsyncIterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.config import Settings
from app.schemas.business import StudentChatAttachment


@dataclass(frozen=True, slots=True)
class SandboxStreamEvent:
    type: str
    payload: dict[str, Any]
    counts_as_tool: bool = False


@dataclass(frozen=True, slots=True)
class _CommandPlan:
    step_id: str
    title: str
    display: str
    args: list[str]


class StudentCodeSandboxRunner:
    """Run a short-lived, directory-limited code inspection workflow."""

    def __init__(
        self,
        *,
        attachments: list[StudentChatAttachment],
        message: str,
        settings: Settings,
    ) -> None:
        self._attachments = attachments[: settings.chat_sandbox_max_files]
        self._message = message
        self._settings = settings
        self.summary = ""
        self.ran = False
        self.failed = False

    @property
    def should_run(self) -> bool:
        if not self._settings.chat_sandbox_enabled:
            return False
        if self._attachments:
            return True
        text = self._message.lower()
        sandbox_keywords = ("运行", "测试", "pytest", "npm test", "node", "python")
        return any(keyword in text for keyword in sandbox_keywords)

    async def stream(self) -> AsyncIterator[SandboxStreamEvent]:
        steps = self._plan_steps()
        yield SandboxStreamEvent("workflow_plan", {"steps": steps})

        with tempfile.TemporaryDirectory(prefix="nchu-chat-sandbox-") as raw_workspace:
            workspace = Path(raw_workspace)
            yield self._step_started(
                "sandbox-prepare",
                "workspace",
                "初始化临时工作区",
                "创建一次性沙箱目录。",
            )
            yield self._artifact(
                "sandbox-prepare",
                "workspace",
                "临时目录",
                "已创建隔离工作区，结束后自动清理。",
            )
            yield self._step_done("sandbox-prepare", "workspace", "success", "临时工作区已就绪。")

            written_files = await self._write_attachments(workspace)
            if written_files:
                yield self._tool_started("read_uploaded_files", "读取上传文件")
                yield self._step_started(
                    "sandbox-read",
                    "read",
                    "读取上传文件",
                    "读取学生上传的作业或代码。",
                )
                for file_path in written_files:
                    preview = _read_text_preview(file_path)
                    self.summary = _join_summary(
                        self.summary,
                        f"已读取文件：{file_path.name}\n\n{preview}",
                    )
                    yield self._artifact("sandbox-read", "file", file_path.name, preview)
                yield self._tool_done(
                    "read_uploaded_files",
                    "success",
                    f"读取 {len(written_files)} 个文件。",
                    result_count=len(written_files),
                )
                yield self._step_done(
                    "sandbox-read",
                    "read",
                    "success",
                    f"已读取 {len(written_files)} 个上传文件。",
                    artifact_count=len(written_files),
                )
            else:
                yield self._step_done(
                    "sandbox-read",
                    "read",
                    "skipped",
                    "本轮没有可读取的上传文件。",
                )

            install_plan = self._dependency_install_plan(workspace)
            if install_plan is not None:
                async for event in self._run_command_step(workspace, install_plan):
                    yield event
            elif any((workspace / name).exists() for name in ("requirements.txt", "package.json")):
                yield self._step_done(
                    "sandbox-install",
                    "terminal",
                    "skipped",
                    "检测到依赖清单，但当前环境未开启依赖安装。",
                )
            else:
                yield self._step_done(
                    "sandbox-install",
                    "terminal",
                    "skipped",
                    "未发现依赖清单，跳过依赖安装。",
                )

            command = self._execution_plan(workspace)
            if command is not None:
                async for event in self._run_command_step(workspace, command):
                    yield event
            else:
                yield self._step_done(
                    "sandbox-run",
                    "terminal",
                    "skipped",
                    "未找到可安全执行的 Python、Node 或测试入口。",
                )

            yield self._step_started(
                "sandbox-think",
                "think",
                "整理执行结果",
                "汇总真实文件与命令输出。",
            )
            if not self.summary:
                self.summary = "沙箱没有产生可汇总的命令输出。"
            yield self._artifact("sandbox-think", "summary", "执行摘要", self.summary)
            yield self._step_done("sandbox-think", "think", "success", "沙箱执行摘要已整理。")

    def _plan_steps(self) -> list[dict[str, Any]]:
        return [
            {
                "step_id": "sandbox-prepare",
                "kind": "workspace",
                "title": "初始化临时工作区",
                "status": "queued",
            },
            {
                "step_id": "sandbox-read",
                "kind": "read",
                "title": "读取上传文件",
                "status": "queued",
            },
            {
                "step_id": "sandbox-install",
                "kind": "terminal",
                "title": "检查依赖安装",
                "status": "queued",
            },
            {
                "step_id": "sandbox-run",
                "kind": "terminal",
                "title": "运行代码或测试",
                "status": "queued",
            },
            {
                "step_id": "sandbox-think",
                "kind": "think",
                "title": "整理执行结果",
                "status": "queued",
            },
        ]

    async def _write_attachments(self, workspace: Path) -> list[Path]:
        files: list[Path] = []
        for index, attachment in enumerate(self._attachments, start=1):
            if not attachment.content:
                continue
            payload = _attachment_bytes(attachment)
            if len(payload) > self._settings.chat_sandbox_max_attachment_bytes:
                continue
            filename = _safe_filename(attachment.name or f"attachment-{index}.txt")
            path = workspace / filename
            path.write_bytes(payload)
            files.append(path)
        return files

    def _dependency_install_plan(self, workspace: Path) -> _CommandPlan | None:
        if not self._settings.chat_sandbox_dependency_install_enabled:
            return None
        requirements = workspace / "requirements.txt"
        if requirements.exists():
            return _CommandPlan(
                step_id="sandbox-install",
                title="安装 Python 依赖",
                display="python -m pip install -r requirements.txt",
                args=[sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
            )
        package = workspace / "package.json"
        npm = shutil.which("npm")
        if package.exists() and npm:
            return _CommandPlan(
                step_id="sandbox-install",
                title="安装 Node 依赖",
                display="npm install",
                args=[npm, "install"],
            )
        return None

    def _execution_plan(self, workspace: Path) -> _CommandPlan | None:
        python_tests = sorted(workspace.glob("test_*.py")) + sorted(
            (workspace / "tests").glob("*.py"),
        )
        has_pytest_config = (workspace / "pytest.ini").exists()
        has_pyproject = (workspace / "pyproject.toml").exists()
        if python_tests or has_pytest_config or has_pyproject:
            return _CommandPlan(
                step_id="sandbox-run",
                title="运行 Python 测试",
                display="python -m pytest -q",
                args=[sys.executable, "-m", "pytest", "-q"],
            )

        python_files = sorted(workspace.glob("*.py"))
        if python_files:
            filename = python_files[0].name
            return _CommandPlan(
                step_id="sandbox-run",
                title="运行 Python 文件",
                display=f"python {filename}",
                args=[sys.executable, filename],
            )

        package = workspace / "package.json"
        npm = shutil.which("npm")
        if package.exists() and npm:
            return _CommandPlan(
                step_id="sandbox-run",
                title="运行 npm test",
                display="npm test",
                args=[npm, "test"],
            )

        node = shutil.which("node")
        js_files = sorted(workspace.glob("*.js"))
        if js_files and node:
            filename = js_files[0].name
            return _CommandPlan(
                step_id="sandbox-run",
                title="运行 Node 文件",
                display=f"node {filename}",
                args=[node, filename],
            )
        return None

    async def _run_command_step(
        self,
        workspace: Path,
        command: _CommandPlan,
    ) -> AsyncIterator[SandboxStreamEvent]:
        yield self._tool_started("run_terminal", command.title)
        yield self._step_started(command.step_id, "terminal", command.title, command.display)
        output, return_code, timed_out = await _run_command(
            command.args,
            cwd=workspace,
            timeout=self._settings.chat_sandbox_timeout_seconds,
        )
        self.ran = True
        self.failed = self.failed or timed_out or return_code != 0
        status = "error" if timed_out or return_code != 0 else "success"
        title = f"{command.display} 输出"
        detail = f"退出码 {return_code}" if not timed_out else "执行超时，进程已终止。"
        yield self._artifact(command.step_id, "terminal", title, output or "(no output)")
        yield self._tool_done("run_terminal", status, detail, result_count=1)
        yield self._step_done(command.step_id, "terminal", status, detail, artifact_count=1)
        self.summary = _join_summary(
            self.summary,
            f"{command.display}\n{detail}\n{output or '(no output)'}",
        )

    @staticmethod
    def _step_started(
        step_id: str,
        kind: str,
        title: str,
        detail: str,
    ) -> SandboxStreamEvent:
        return SandboxStreamEvent(
            "workflow_step_started",
            {
                "step_id": step_id,
                "kind": kind,
                "title": title,
                "status": "running",
                "detail": detail,
            },
        )

    @staticmethod
    def _step_done(
        step_id: str,
        kind: str,
        status: str,
        summary: str,
        *,
        artifact_count: int | None = None,
    ) -> SandboxStreamEvent:
        payload: dict[str, Any] = {
            "step_id": step_id,
            "kind": kind,
            "status": status,
            "summary": summary,
        }
        if artifact_count is not None:
            payload["artifact_count"] = artifact_count
        return SandboxStreamEvent("workflow_step_done", payload)

    @staticmethod
    def _artifact(step_id: str, kind: str, title: str, content: str) -> SandboxStreamEvent:
        return SandboxStreamEvent(
            "workflow_artifact",
            {
                "artifact_id": f"{step_id}-{kind}-{abs(hash((title, content))) % 100000}",
                "step_id": step_id,
                "kind": kind,
                "title": title,
                "content": _truncate(content, 6000),
            },
        )

    @staticmethod
    def _tool_started(tool_name: str, title: str) -> SandboxStreamEvent:
        return SandboxStreamEvent(
            "tool_started",
            {
                "toolCallId": f"sandbox-{tool_name}",
                "toolName": tool_name,
                "title": title,
            },
            counts_as_tool=True,
        )

    @staticmethod
    def _tool_done(
        tool_name: str,
        status: str,
        detail: str,
        *,
        result_count: int | None = None,
    ) -> SandboxStreamEvent:
        payload: dict[str, Any] = {
            "toolCallId": f"sandbox-{tool_name}",
            "toolName": tool_name,
            "status": status,
            "detail": detail,
        }
        if result_count is not None:
            payload["resultCount"] = result_count
        return SandboxStreamEvent("tool_done", payload)


def _attachment_bytes(attachment: StudentChatAttachment) -> bytes:
    content = attachment.content or ""
    if attachment.encoding == "base64":
        return base64.b64decode(content.encode("ascii"), validate=True)
    return content.encode("utf-8")


def _safe_filename(value: str) -> str:
    name = Path(value).name.strip() or "attachment.txt"
    return re.sub(r"[^A-Za-z0-9._-]+", "_", name)[:80] or "attachment.txt"


async def _run_command(args: list[str], *, cwd: Path, timeout: float) -> tuple[str, int, bool]:
    process = await asyncio.create_subprocess_exec(
        *args,
        cwd=cwd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
    except TimeoutError:
        process.kill()
        stdout, stderr = await process.communicate()
        return _truncate(_decode(stdout) + _decode(stderr), 8000), -1, True
    output = _decode(stdout) + _decode(stderr)
    return _truncate(output, 8000), process.returncode, False


def _read_text_preview(path: Path) -> str:
    data = path.read_bytes()
    return _truncate(data.decode("utf-8", errors="replace"), 12000)


def _decode(value: bytes) -> str:
    return value.decode("utf-8", errors="replace")


def _truncate(value: str, limit: int) -> str:
    if len(value) <= limit:
        return value
    return f"{value[:limit]}\n...[truncated]"


def _join_summary(current: str, next_value: str) -> str:
    return _truncate("\n\n".join(part for part in (current, next_value) if part.strip()), 10000)
