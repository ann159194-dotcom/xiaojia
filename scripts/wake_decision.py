import json
from datetime import datetime, timezone
from pathlib import Path

STATE_PATH = Path("memory/state.json")


def load_json(path):
    if not path.exists():
        return {}

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2
        )
        f.write("\n")


def main():
    state = load_json(STATE_PATH)

    now = datetime.now(timezone.utc)

    print("================================")
    print("🧠 小家 · 自主判断")
    print("================================")

    pending_wake = (
        state.get("pending_wake")
        is True
    )

    if not pending_wake:

        print(
            "💤 当前没有达到自主唤醒条件"
        )

        state["status"] = "waiting"
        state["wake_decision"] = "wait"

        save_json(
            STATE_PATH,
            state
        )

        print(
            "📊 判断结果：wait"
        )

        return

    print(
        "🌙 已达到自主唤醒条件"
    )

    print(
        "💭 开始判断这一次是否真的值得主动说话"
    )

    # ---------------------------------
    # 当前阶段：
    # 只要进入自主唤醒阶段，
    # 就产生一个消息候选。
    #
    # 后续接入真正 AI 后，
    # 可以把这里替换成：
    #
    # context → AI → candidate / wait
    # ---------------------------------

    decision = "candidate"

    state["wake_decision"] = decision

    state["last_decision"] = (
        now.strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
    )

    if decision == "candidate":

        state["status"] = "wake_candidate"

        print(
            "✅ 判断结果：存在自主消息候选"
        )

    else:

        state["status"] = "waiting"
        state["pending_wake"] = False

        print(
            "💤 这一次没有值得主动说的话"
        )

    save_json(
        STATE_PATH,
        state
    )

    print("================================")
    print("📊 状态已保存")
    print(
        f"wake_decision = "
        f"{state.get('wake_decision')}"
    )
    print(
        f"status = "
        f"{state.get('status')}"
    )
    print("================================")


if __name__ == "__main__":
    main()
