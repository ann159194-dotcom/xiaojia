import json
from datetime import datetime, timezone
from pathlib import Path

STATE_PATH = Path("memory/state.json")
CONTEXT_PATH = Path("memory/context.json")
OUTBOX_PATH = Path("memory/outbox.json")


def load_json(path):
    if not path.exists():
        return {}

    try:
        with open(
            path,
            "r",
            encoding="utf-8"
        ) as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(
            f"⚠️ JSON 文件无法解析：{path}"
        )
        return {}


def save_json(path, data):
    with open(
        path,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2
        )
        f.write("\n")


def choose_message(context):
    """
    当前还是规则式消息生成。

    后面接入真正 AI 时，
    只需要替换这个函数。
    """

    thoughts = context.get(
        "current_thoughts",
        []
    )

    unfinished = context.get(
        "unfinished_topics",
        []
    )

    recent = context.get(
        "recent_topics",
        []
    )

    if thoughts:

        return (
            "我刚刚突然想到一件事："
            f"{thoughts[0]}"
        )

    if unfinished:

        return (
            "刚才那个还没说完的东西，"
            f"我又想起来了：{unfinished[0]}"
        )

    if recent:

        return (
            "刚刚又想到我们之前聊的"
            f"「{recent[0]}」了。"
        )

    return "我刚刚突然想到你了。"


def main():

    print("================================")
    print("💬 小家 · 生成自主消息")
    print("================================")

    state = load_json(
        STATE_PATH
    )

    context = load_json(
        CONTEXT_PATH
    )

    wake_decision = state.get(
        "wake_decision"
    )

    if wake_decision != "candidate":

        print(
            "💤 当前没有有效的自主唤醒候选"
        )

        print(
            f"当前 wake_decision = "
            f"{wake_decision}"
        )

        return

    now = datetime.now(timezone.utc)

    message = choose_message(
        context
    )

    output = {
        "created_at": now.strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        ),
        "type": "AI_WAKE",
        "message": message,
        "status": "pending"
    }

    save_json(
        OUTBOX_PATH,
        output
    )

    # ---------------------------------
    # 更新状态
    # ---------------------------------

    state["last_autonomous_wake"] = (
        now.strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
    )

    state["wake_count"] = (
        state.get(
            "wake_count",
            0
        ) + 1
    )

    state["status"] = "wake_generated"

    state["pending_wake"] = False

    save_json(
        STATE_PATH,
        state
    )

    print(
        "🌙 小家已经生成自主消息"
    )

    print("================================")

    print(message)

    print("================================")

    print(
        "📦 已写入："
        "memory/outbox.json"
    )

    print(
        f"🔢 wake_count = "
        f"{state['wake_count']}"
    )

    print("================================")


if __name__ == "__main__":
    main()
