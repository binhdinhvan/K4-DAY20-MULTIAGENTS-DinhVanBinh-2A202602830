"""GUIDE Phần 1 - Định nghĩa subagent (tác tử con).   >>> SINH VIÊN CÀI ĐẶT <<<

Pseudo-code: guides/pseudocode/02_subagents.md
Kiểm tra:    pytest tests/test_02_agent.py
"""


def get_subagents() -> list[dict]:
    """Trả về danh sách subagent (ít nhất 2, tên khác nhau).

    Mỗi phần tử là một dict có các khóa bắt buộc:
      "name":          tên duy nhất (chữ thường, có thể có dấu gạch ngang)
      "description":   khi nào tác tử chính nên giao việc cho subagent này (viết như một hướng dẫn hành động)
      "system_prompt": chỉ dẫn cho subagent
    Gợi ý vai trò: explorer (đọc và báo cáo), implementer (thực hiện), reviewer (kiểm tra độc lập).
    """
    return [
        {
            "name": "explorer",
            "description": "Use first when the task requires inspecting files, requirements, or existing tests; report verified facts without editing files.",
            "system_prompt": "Inspect the requested workspace carefully, read relevant instructions and tests, and return a concise report of verified facts. Do not modify files.",
        },
        {
            "name": "implementer",
            "description": "Use when the task requires making or testing a concrete implementation in the workspace.",
            "system_prompt": "Implement the requested change in the workspace, run relevant tests, and report exactly what changed and what passed or failed.",
        },
        {
            "name": "reviewer",
            "description": "Use after implementation to independently verify requirements, edge cases, and test results.",
            "system_prompt": "Review the current workspace against the supplied task requirements and tests. Identify defects or missing requirements and report evidence without modifying files.",
        },
    ]
