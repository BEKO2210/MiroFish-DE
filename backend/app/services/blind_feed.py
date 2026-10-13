"""Blind-Feed-Ablation: voller Aktionskatalog, Beobachtung fremder Beiträge leer.

OASIS füllt in ``Platform.update_rec_table`` die Tabelle ``rec``; die passive
Beobachtung holt Agenten über ``SocialEnvironment.get_posts_env`` → ``refresh``
(Twitter zusätzlich Followee-Posts). Es gibt keinen eingebauten Recommender
„nur eigene Beiträge“. Deshalb wird für ``blind_feed`` ``update_rec_table`` auf
leere ``rec`` gesetzt und ``refresh`` liefert nur eigene Posts — ohne Followee-
Zweig. Search/Trend bleiben als Aktionen nutzbar; die Standardbeobachtung nicht.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Sequence


def is_blind_feed(variant: str | None) -> bool:
    return str(variant or "") == "blind_feed"


def own_post_rows(posts: Sequence[Dict[str, Any]], user_id: int) -> List[Dict[str, Any]]:
    """Beiträge eines Nutzers (für Tests und refresh-Filter)."""
    return [post for post in posts if int(post.get("user_id", -1)) == int(user_id)]


def install_blind_feed(platform: Any) -> None:
    """Empfehlungstabelle leeren; refresh nur eigene Beiträge, kein Follow-Feed."""

    async def update_rec_table_blind() -> None:
        platform.pl_utils._execute_db_command("DELETE FROM rec", commit=True)

    async def refresh_own_only(agent_id: int) -> Dict[str, Any]:
        try:
            platform.pl_utils._execute_db_command(
                "SELECT post_id, user_id, original_post_id, content, "
                "quote_content, created_at, num_likes, num_dislikes, "
                "num_shares FROM post WHERE user_id = ? ORDER BY post_id",
                (agent_id,),
            )
            results = platform.db_cursor.fetchall()
            if not results:
                return {"success": False, "message": "No posts found."}
            results_with_comments = platform.pl_utils._add_comments_to_posts(results)
            return {"success": True, "posts": results_with_comments}
        except Exception as error:
            return {"success": False, "error": str(error)}

    platform.update_rec_table = update_rec_table_blind  # type: ignore[method-assign]
    platform.refresh = refresh_own_only  # type: ignore[method-assign]
    platform._blind_feed = True


def fetch_platform_posts(platform: Any) -> List[Dict[str, Any]]:
    platform.pl_utils._execute_db_command(
        "SELECT post_id, user_id, content FROM post ORDER BY post_id"
    )
    return [
        {
            "post_id": int(row[0]),
            "user_id": int(row[1]),
            "content": str(row[2] or ""),
        }
        for row in platform.db_cursor.fetchall()
    ]


def deliver_opening_stimulus(
    agent_graph: Any,
    posts: Sequence[Dict[str, Any]],
    log_path: str | Path,
    platform_name: str,
) -> Dict[str, Any]:
    """Startbeiträge je Agent einmal als gelesenen Stimulus eintragen und protokollieren."""
    from camel.messages import BaseMessage
    from camel.types import OpenAIBackendRole

    lines = []
    post_ids: List[int] = []
    for post in posts:
        pid = int(post.get("post_id", 0))
        post_ids.append(pid)
        lines.append(
            f"- [{pid}] user={post.get('user_id')}: {str(post.get('content') or '').strip()}"
        )
    body = (
        "You have read these opening posts on the platform (one-time stimulus):\n"
        + ("\n".join(lines) if lines else "- (none)")
    )
    agents_log: List[Dict[str, Any]] = []
    for agent_id, agent in agent_graph.get_agents():
        message = BaseMessage.make_user_message(role_name="User", content=body)
        agent.update_memory(message, OpenAIBackendRole.USER)
        agents_log.append({
            "agent_id": int(agent_id),
            "seen_post_ids": list(post_ids),
            "seen": True,
            "post_count": len(post_ids),
        })
    document = {
        "platform": platform_name,
        "stimulus": "opening_posts",
        "post_ids": post_ids,
        "agents": agents_log,
    }
    path = Path(log_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, ensure_ascii=False, indent=2), encoding="utf-8")
    return document
