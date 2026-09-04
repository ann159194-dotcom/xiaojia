import json
from datetime import datetime, timezone

STATE_PATH = "memory/state.json"


def main():
    with open(STATE_PATH, "r", encoding="utf-8") as f:
        state = json.load(f)

    now = datetime.now(timezone.utc)

    if state.get("pending_wake") is True:
        print("🌙 小家：已经达到主动唤醒条件")

        state["status"] = "wake_candidate"
        state["last_decision"] = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        state["wake_decision"] = "candidate"

        print("💭 决策结果：wake_candidate")

    else:
        print("💤 小家：暂时不需要主动醒来")

        state["status"] = "waiting"
        state["last_decision"] = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        state["wake_decision"] = "wait"

    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
        f.write("\n")


if __name__ == "__main__":
    main()
