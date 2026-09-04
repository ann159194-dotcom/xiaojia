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


def read_config():
    config = {}

    section = None
    subsection = None

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.rstrip()

            if not line or line.lstrip().startswith("#"):
                continue

            stripped = line.strip()

            if not line.startswith(" ") and stripped.endswith(":"):
                section = stripped[:-1]
                subsection = None
                continue

            if line.startswith("  ") and not line.startswith("    ") and stripped.endswith(":"):
                subsection = stripped[:-1]
                continue

            if ":" in stripped:
                key, value = stripped.split(":", 1)
                value = value.strip().strip('"')

                if section and subsection:
                    config[f"{section}.{subsection}.{key}"] = value
                elif section:
                    config[f"{section}.{key}"] = value

    return config


def get_minutes(config, key, default):
    try:
        return int(config.get(key, default))
    except (TypeError, ValueError):
        return default


def main():
    now = datetime.now(timezone.utc)

    config = read_config()

    with open(ACTIVITY_PATH, "r", encoding="utf-8") as f:
        activity = json.load(f)

    with open(STATE_PATH, "r", encoding="utf-8") as f:
        state = json.load(f)

    last_return = parse_time(activity.get("last_user_return"))

    if last_return is None:
        print("⚠️ 还没有 USER_RETURN 记录")
        state["pending_wake"] = False
        state["status"] = "waiting_no_activity"

    else:
        # 转换成北京时间
        local_now = now.astimezone()
        hour = local_now.hour

        # 00:00 - 08:00 为夜间
        is_night = hour < 8

        if is_night:
            idle_delay = get_minutes(
                config,
                "schedule.nighttime.idle_delay_minutes",
                60
            )
            period = "night"
        else:
            idle_delay = get_minutes(
                config,
                "schedule.daytime.idle_delay_minutes",
                30
            )
            period = "day"

        idle_seconds = (now - last_return).total_seconds()
        idle_minutes = idle_seconds / 60

        print(f"🕐 当前 UTC：{now.isoformat()}")
        print(f"👤 最后一次 USER_RETURN：{last_return.isoformat()}")
        print(f"🌗 当前时段：{period}")
        print(f"⏱️ 当前空闲：{idle_minutes:.2f} 分钟")
        print(f"🎯 当前所需空闲：{idle_delay} 分钟")

        state["current_period"] = period
        state["idle_minutes"] = round(idle_minutes, 2)
        state["idle_delay_minutes"] = idle_delay

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
