import json
from datetime import datetime, timezone
from pathlib import Path

STATE_PATH = Path("memory/state.json")
CONTEXT_PATH = Path("memory/context.json")
OUTBOX_PATH = Path("memory/outbox.json")


def load_json(path):
    if not path.exists():
        return {}

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def choose_message(context):
    thoughts = context.get("current_thoughts", [])
    unfinished = context.get("unfinished_topics", [])
    recent = context.get("recent_topics", [])

    if thoughts:
        return f"我刚刚突然想到一件事：{thoughts[0]}"

    if unfinished:
        return f"刚才那个还没说完的东西，我又想起来了：{unfinished[0]}"

    if recent:
        return f"刚刚又想到我们之前聊的「{recent[0]}」了。"

    return "我刚刚突然想到你了。"


def main():
    state = load_json(STATE_PATH)
    context = load_json(CONTEXT_PATH)

    if state.get("wake_decision") != "candidate":
        print("💤 当前没有有效的自主唤醒候选")
        return

    now = datetime.now(timezone.utc)
    message = choose_message(context)

    output = {
        "created_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "type": "AI_WAKE",
        "message": message,
        "status": "pending"
    }

    with open(OUTBOX_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
        f.write("\n")

    state["last_autonomous_wake"] = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    state["wake_count"] = state.get("wake_count", 0) + 1
    state["status"] = "wake_generated"
    state["pending_wake"] = False

    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print("🌙 小家已经生成自主消息")
    print("================================")
    print(message)
    print("================================")
    print("📦 已写入 memory/outbox.json")


if __name__ == "__main__":
    main()
