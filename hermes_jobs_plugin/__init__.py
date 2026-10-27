"""hermes-jobs plugin entry point.

Pilot scope: schema delta + the two job-mode tools. The runner, ingress
and board come in later increments; nothing here touches an interactive
code path, so Telegram / CLI / chat.ahfl.in behaviour is unchanged.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def register(ctx) -> None:
    # 1. Schema delta on the shared kanban board. Idempotent, additive only.
    try:
        from . import store

        added = store.ensure_schema()
        new_cols = sum(len(v) for v in added.values())
        if new_cols:
            logger.info(
                "hermes-jobs: added %d column(s) to the kanban board: %s",
                new_cols, added,
            )
    except Exception as exc:
        # A board that cannot be migrated must not take the gateway down.
        logger.warning("hermes-jobs: schema migration failed: %s", exc)
        return

    # 2. Job-mode tools. Gated by check_fn so they are invisible to
    #    interactive sessions.
    try:
        from . import tools

        tools.register_tools(ctx)
    except Exception as exc:
        logger.warning("hermes-jobs: tool registration failed: %s", exc)
        return

    # 3. Per-request gate. The job tools are registered unconditionally
    #    (check_fn is TTL-cached process-wide and cannot see the session), so
    #    this strips them from every request that is not a job run.
    try:
        ctx.register_middleware("llm_request", tools.strip_job_tools_middleware)
    except Exception as exc:
        logger.warning("hermes-jobs: middleware registration failed: %s", exc)

    # 4. Telegram /job and /jobs ingress + the background claim/run/poll/
    #    deliver loop. Hooks pre_gateway_dispatch -- fires before auth, the
    #    busy guard, and session keying, for every platform. Non-/job
    #    messages return None from the callback, so this is a no-op for
    #    every existing code path (R1).
    try:
        from . import ingress

        ctx.register_hook("pre_gateway_dispatch", ingress.on_pre_gateway_dispatch)
    except Exception as exc:
        logger.warning("hermes-jobs: ingress hook registration failed: %s", exc)
        ingress = None

    # 5. Register /job and /jobs as PLUGIN COMMANDS too -- not because
    #    their handlers run (the hook above always intercepts first), but
    #    because hermes_cli.commands.should_bypass_active_session() (see
    #    ops/patches/0002) checks whether a command is "recognized" via
    #    get_plugin_command_handler(). Without this registration, a /job
    #    sent while the user's own interactive session is busy falls
    #    through to the generic "interrupt the running agent" handler and
    #    NEVER reaches the hook at all -- this was found live: a /job sent
    #    during an active Telegram task got swallowed as free-text input
    #    to that unrelated task instead of creating a job.
    if ingress is not None:
        try:
            ctx.register_command(
                "job", ingress.register_command_job,
                description="Create a job that runs independently of this chat",
                args_hint="<instruction>",
            )
            ctx.register_command(
                "jobs", ingress.register_command_jobs,
                description="List/answer/continue/drop your jobs",
                args_hint="[answer|continue|drop <id> ...]",
            )
        except Exception as exc:
            logger.warning("hermes-jobs: command registration failed: %s", exc)
