import json
import os
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

CONFIG_PATH = Path("config/xiaojia.yaml")
ACTIVITY_PATH = Path("memory/user_activity.json")
STATE_PATH = Path("memory/state.json")

SHANGHAI_TZ = ZoneInfo("Asia/Shanghai")


def parse_time(value):
    if not value:
        return None

    try:
        return datetime.fromisoformat(
            value.replace("Z", "+00:00")
        )
    except ValueError:
        return None


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


def read_config():
    """
    读取小家 YAML 中当前脚本需要的简单配置。

    这里不依赖 PyYAML，避免 GitHub Runner
    因额外依赖导致执行失败。
    """

    config = {}

    if not CONFIG_PATH.exists():
        return config

    section = None
    subsection = None

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.rstrip()

            if not line:
                continue

            if line.lstrip().startswith("#"):
                continue

            stripped = line.strip()

            # 一级标题
            if not line.startswith(" ") and stripped.endswith(":"):
                section = stripped[:-1]
                subsection = None
                continue

            # 二级标题
            if (
                line.startswith("  ")
                and not line.startswith("    ")
                and stripped.endswith(":")
            ):
                subsection = stripped[:-1]
                continue

            if ":" not in stripped:
                continue

            key, value = stripped.split(":", 1)

            key = key.strip()
            value = value.strip().strip('"').strip("'")

            if section and subsection:
                config[
                    f"{section}.{subsection}.{key}"
                ] = value
            elif section:
                config[
                    f"{section}.{key}"
                ] = value

    return config


def get_int(config, key, default):
    try:
        return int(config.get(key, default))
    except (TypeError, ValueError):
        return default


def get_bool(config, key, default=False):
    value = str(
        config.get(key, str(default))
    ).lower()

    if value in ("true", "yes", "1", "on"):
        return True

    if value in ("false", "no", "0", "off"):
        return False

    return default


def is_authoritative_ai_wake():
    """
    判断这次 GitHub Actions 是否由 Cloudflare Worker
    发出的 AI_WAKE 事件触发。

    如果是：

        Cloudflare Worker 已经完成空闲时间判断

    GitHub 不再重复使用 30/60 分钟规则拦截。

    这样可以避免：

        Worker 3分钟
             ↓
        GitHub 又要求30分钟
             ↓
        永远无法测试成功
    """

    event_name = os.environ.get(
        "GITHUB_EVENT_NAME",
        ""
    )

    if event_name != "repository_dispatch":
        return False

    event_path = os.environ.get(
        "GITHUB_EVENT_PATH"
    )

    if not event_path:
        return True

    try:
        with open(
            event_path,
            "r",
            encoding="utf-8"
        ) as f:
            event = json.load(f)

        event_type = event.get(
            "action"
        )

        if event_type == "AI_WAKE":
            return True

        client_payload = event.get(
            "client_payload",
            {}
        )

        if (
            isinstance(client_payload, dict)
            and client_payload.get("event") == "AI_WAKE"
        ):
            return True

    except Exception as e:
        print(
            f"⚠️ 无法读取 GitHub 事件内容：{e}"
        )

    # repository_dispatch 本身已经代表
    # 外部主动层发来的唤醒请求。
    return True


def normal_idle_check(state, activity, config):
    """
    GitHub 手动执行 workflow 时，
    仍然保留本地空闲时间检查。
    """

    now = datetime.now(timezone.utc)

    last_return = parse_time(
        activity.get("last_user_return")
    )

    if last_return is None:
        print("⚠️ 还没有 USER_RETURN 记录")

        state["pending_wake"] = False
        state["status"] = "waiting_no_activity"

        return state

    # 明确使用小家配置的时区，
    # 不再依赖 Runner 自身时区。
    local_now = now.astimezone(
        SHANGHAI_TZ
    )

    hour = local_now.hour

    is_night = hour < 8

    if is_night:
        idle_delay = get_int(
            config,
            "schedule.nighttime.idle_delay_minutes",
            60
        )
        period = "night"
    else:
        idle_delay = get_int(
            config,
            "schedule.daytime.idle_delay_minutes",
            30
        )
        period = "day"

    # 测试模式优先级最高
    test_enabled = get_bool(
        config,
        "test.enabled",
        False
    )

    if test_enabled:
        idle_delay = get_int(
            config,
            "test.idle_delay_minutes",
            idle_delay
        )
        period = "test"

    idle_seconds = (
        now - last_return
    ).total_seconds()

    idle_minutes = idle_seconds / 60

    print(
        f"🕐 当前 UTC：{now.isoformat()}"
    )

    print(
        f"🇨🇳 当前北京时间："
        f"{local_now.strftime('%Y-%m-%d %H:%M:%S')}"
    )

    print(
        f"👤 最后一次 USER_RETURN："
        f"{last_return.isoformat()}"
    )

    print(
        f"🌗 当前时段：{period}"
    )

    print(
        f"⏱️ 当前空闲："
        f"{idle_minutes:.2f} 分钟"
    )

    print(
        f"🎯 当前所需空闲："
        f"{idle_delay} 分钟"
    )

    state["current_period"] = period
    state["idle_minutes"] = round(
        idle_minutes,
        2
    )
    state["idle_delay_minutes"] = idle_delay

    if idle_minutes >= idle_delay:
        print(
            "🌙 已达到主动唤醒判断时间"
        )

        state["pending_wake"] = True
        state["status"] = "idle_ready"

    else:
        remaining = (
            idle_delay - idle_minutes
        )

        print(
            f"⏳ 还需要等待约 "
            f"{remaining:.2f} 分钟"
        )

        state["pending_wake"] = False
        state["status"] = "waiting"

    return state


def main():
    print("================================")
    print("🏠 小家 · 空闲检查")
    print("================================")

    state = load_json(STATE_PATH)
    activity = load_json(ACTIVITY_PATH)
    config = read_config()

    # ---------------------------------
    # 情况一：
    # Cloudflare Worker → AI_WAKE
    # ---------------------------------

    if is_authoritative_ai_wake():

        print(
            "⚡ 检测到 Cloudflare 发来的 AI_WAKE"
        )

        print(
            "✅ Cloudflare 已完成空闲时间判断"
        )

        print(
            "🌙 本次直接进入自主唤醒判断"
        )

        state["pending_wake"] = True
        state["status"] = "idle_ready"
        state["wake_source"] = "cloudflare"

    # ---------------------------------
    # 情况二：
    # 手动 workflow_dispatch
    # ---------------------------------

    else:

        print(
            "🖐️ 当前不是外部 AI_WAKE"
        )

        print(
            "📐 执行 GitHub 本地空闲时间检查"
        )

        state = normal_idle_check(
            state,
            activity,
            config
        )

        state["wake_source"] = "github_local"

    state["last_check"] = (
        datetime.now(timezone.utc)
        .strftime("%Y-%m-%dT%H:%M:%SZ")
    )

    save_json(
        STATE_PATH,
        state
    )

    print("================================")
    print("📊 空闲检查完成")
    print(
        f"pending_wake = "
        f"{state.get('pending_wake')}"
    )
    print(
        f"status = "
        f"{state.get('status')}"
    )
    print(
        f"wake_source = "
        f"{state.get('wake_source')}"
    )
    print("================================")


if __name__ == "__main__":
    main()
