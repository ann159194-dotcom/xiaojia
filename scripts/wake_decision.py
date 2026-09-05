import json
from datetime import datetime, timezone
from pathlib import Path

STATE_PATH = Path("memory/state.json")
OUTBOX_PATH = Path("memory/outbox.json")


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def main():
    state = load_json(STATE_PATH)

    now = datetime.now(timezone.utc)

    print("================================")
    print("🧠 小家 · 自主判断")
    print("================================")

    # 还没有达到静默条件
    if state.get("pending_wake") is not True:
        print("💤 当前没有达到自主唤醒条件")

        state["status"] = "waiting"
        state["wake_decision"] = "wait"

        save_json(STATE_PATH, state)
        return

    print("🌙 已达到自主唤醒条件")
    print("💭 开始判断这一次是否真的值得主动说话")

    # 当前阶段先采用“上下文候选”机制。
    # 后续接入真正的 AI 判断后，这里会由 AI 决定。
    #
    # 当前测试规则：
    # 只要达到候选条件，就生成一次候选消息，
    # 但明确标记为 AI_WAKE_CANDIDATE，
    # 后续发送层可以继续进行最终过滤。

    decision = "candidate"

    state["wake_decision"] = decision
    state["last_decision"] = now.strftime("%Y-%m-%dT%H:%M:%SZ")

    if decision == "candidate":
        state["status"] = "wake_candidate"

        print("✅ 判断结果：存在自主消息候选")

        output = {
            "created_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "type": "AI_WAKE_CANDIDATE",
            "status": "pending",
            "message": None
        }

        save_json(OUTBOX_PATH, output)

    else:
        state["status"] = "waiting"
        state["pending_wake"] = False

        print("💤 这一次没有值得主动说的话")

    save_json(STATE_PATH, state)

    print("================================")
    print("📊 状态已保存")
    print("================================")


if __name__ == "__main__":
    main()
