import json
from datetime import datetime, timezone

CONFIG_PATH = "config/xiaojia.yaml"
ACTIVITY_PATH = "memory/user_activity.json"
STATE_PATH = "memory/state.json"


def parse_time(value):
    if not value:
        return None

    return datetime.fromisoformat(
        value.replace("Z", "+00:00")
    )


def main():
    now = datetime.now(timezone.utc)

    with open(ACTIVITY_PATH, "r", encoding="utf-8") as f:
        activity = json.load(f)

    with open(STATE_PATH, "r", encoding="utf-8") as f:
        state = json.load(f)

    last_return = parse_time(activity.get("last_user_return"))

    if last_return is None:
        print("⚠️ 还没有 USER_RETURN 记录")
        state["pending_wake"] = False
    else:
        idle_seconds = (now - last_return).total_seconds()
        idle_minutes = idle_seconds / 60

        print(f"🕐 当前时间：{now.isoformat()}")
        print(f"👤 最后一次 USER_RETURN：{last_return.isoformat()}")
        print(f"💤 已空闲：{idle_minutes:.2f} 分钟")

        # 当前先使用白天 30 分钟作为测试判断
        idle_delay = 30

        if idle_minutes >= idle_delay:
            print("🌙 已达到主动唤醒判断时间")
            state["pending_wake"] = True
            state["status"] = "idle_ready"
        else:
            remaining = idle_delay - idle_minutes
            print(f"⏳ 还需要等待约 {remaining:.2f} 分钟")
            state["pending_wake"] = False
            state["status"] = "waiting"

    state["last_check"] = now.strftime("%Y-%m-%dT%H:%M:%SZ")

    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
        f.write("\n")


if __name__ == "__main__":
    main()
