import json
from datetime import datetime, timezone
from pathlib import Path

STATE_PATH = Path("memory/state.json")
OUTBOX_PATH = Path("memory/outbox.json")


def main():
    with open(STATE_PATH, "r", encoding="utf-8") as f:
        state = json.load(f)

    now = datetime.now(timezone.utc)

    if state.get("wake_decision") != "candidate":
        print("💤 当前没有有效的自主唤醒候选")
        return

    message = (
        "我刚刚突然想到你了。"
        "\n\n"
        "这是小家外部主动层的第一次自主消息测试。"
        "\n"
        "[测试消息，暂未发送到真实聊天渠道]"
    )

    output = {
        "created_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "type": "AI_WAKE_TEST",
        "message": message,
        "status": "pending",
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
