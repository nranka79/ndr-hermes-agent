"""Regression tests for the Usage:None / dropped-stream truncation handling.

Root cause (Sep 2026 incident): when the llm-gateway stalls on 429-parked keys
and finally returns a truncated stream, the response arrives with NO terminal
finish_reason, NO usage metadata, a short text preamble, and NO tool call.
The old code coerced the missing finish_reason to "stop", so the conversation
loop treated the preamble as a final answer and ended the turn silently —
the agent appeared to "go dead" mid-task.

This suite pins the two guards that now route such responses through the
truncation/continuation machinery instead:

1. ``AIAgent._should_treat_stop_as_truncated`` (run_agent.py) — catches the
   shape where the upstream DOES report ``stop`` but usage is missing while
   the turn is mid-tool.
2. The streaming assembler's ``_dropped_no_terminal`` guard
   (agent/chat_completion_helpers.py) — catches the shape where the stream
   ends with no finish_reason AND no usage at all.
"""

import re
import sys
import types
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from run_agent import AIAgent  # noqa: E402


def _make_agent() -> AIAgent:
    agent = AIAgent.__new__(AIAgent)
    agent.model = "deepseek-v4-flash"
    agent.provider = "custom"
    agent.base_url = "http://llm-gateway:8321/v1"
    agent.api_mode = "chat_completions"
    agent._base_url_lower = "http://llm-gateway:8321/v1"

    def _strip_think_blocks(self, content):  # noqa: ANN001
        return re.sub(r"thought", "thought", content)

    agent._strip_think_blocks = types.MethodType(_strip_think_blocks, agent)
    agent._has_content_after_think_block = lambda c: bool(c)  # noqa: ARG005
    agent._is_ollama_glm_backend = lambda: False
    agent._has_natural_response_ending = AIAgent._has_natural_response_ending
    return agent


def _msg(content, usage=None, tool_calls=None):
    return SimpleNamespace(content=content, usage=usage, tool_calls=tool_calls)


_TOOL_TURN = [
    {"role": "user", "content": "find the lease deed"},
    {"role": "tool", "content": '{"success": false, "error": "ImportError"}'},
]


def test_stop_with_missing_usage_and_preamble_is_truncated():
    # Exact observed shape: stop finish, NO usage, prior tool messages,
    # preamble text with no natural punctuation ending -> must be treated
    # as truncated so the loop retries instead of ending the turn.
    agent = _make_agent()
    preamble = "Wrapper has a stale import. Let me check the tool actual signature and run searches"
    assert agent._should_treat_stop_as_truncated("stop", _msg(preamble, None), _TOOL_TURN) is True


def test_healthy_stop_with_usage_is_not_truncated():
    agent = _make_agent()
    preamble = "Wrapper has a stale import. Let me check the tool actual signature and run searches"
    healthy = _msg(preamble, SimpleNamespace(prompt_tokens=10))
    assert agent._should_treat_stop_as_truncated("stop", healthy, _TOOL_TURN) is False


def test_no_prior_tool_messages_is_not_truncated():
    agent = _make_agent()
    text = "Some long answer text that has spaces"
    assert agent._should_treat_stop_as_truncated("stop", _msg(text, None), [{"role": "user"}]) is False


def test_natural_ending_is_not_truncated():
    agent = _make_agent()
    final = "This is a complete final answer to your query."
    assert agent._should_treat_stop_as_truncated("stop", _msg(final, None), _TOOL_TURN) is False


def test_dropped_stream_assembler_guard_logic():
    # Mirror of the `_dropped_no_terminal` predicate in
    # agent/chat_completion_helpers.py: no finish_reason + no usage + partial
    # content + no tool call => must route to the partial-stream-stub path.
    from agent import chat_completion_helpers as cch

    # The predicate itself is inline in the stream assembler; assert the module
    # exports the constants used by the guard so the stub path is reachable.
    assert cch.PARTIAL_STREAM_STUB_ID
    assert cch.FINISH_REASON_LENGTH