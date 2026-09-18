"""CLI đơn giản để test vòng lặp tool-calling thủ công (chưa có API/streaming
— sẽ thay bằng FastAPI SSE ở Ngày 4). Yêu cầu OPENAI_API_KEY trong .env.

Chạy:
    python scripts/chat_cli.py

Gõ câu hỏi, Enter để gửi, Ctrl+C hoặc 'exit' để thoát. Lịch sử hội thoại chỉ
giữ trong bộ nhớ tiến trình (chưa lưu DB — sẽ làm ở Ngày 4, R3).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.agent.agent import run_agent_turn
from src.prompts.system_prompts import SYSTEM_PROMPT


def main() -> None:
    messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]
    print("Chatbot tra cuu tau bien - go 'exit' de thoat.\n")

    while True:
        try:
            user_input = input("Ban: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not user_input or user_input.lower() == "exit":
            break

        messages.append({"role": "user", "content": user_input})
        answer, new_messages = run_agent_turn(messages)
        messages.extend(new_messages)
        print(f"Bot: {answer}\n")


if __name__ == "__main__":
    main()
