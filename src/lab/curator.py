"""GUIDE Phần 3 - Người tuyển chọn skill (skill curator): tự viết skill từ các lần chạy thất bại.   >>> SINH VIÊN CÀI ĐẶT curate_skills <<<

Pseudo-code: guides/pseudocode/04_curator.md
Kiểm tra:    pytest tests/test_04_curator.py
Chạy thật:   python -m lab.curator
"""
import re
from pathlib import Path

from .tasks import ROOT, eval_markers

# ---- CÓ SẴN, KHÔNG SỬA: kiểm tra và tách khối skill (phần dễ sai và liên quan bảo mật) ----------------
SAFE_NAME = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def validate_skill(text: str, expected_name: str | None = None) -> list[str]:
    """Kiểm tra nội dung một SKILL.md. Trả về danh sách vấn đề (rỗng = hợp lệ).

    Quy tắc: có khối YAML frontmatter; `name` chữ thường/số/gạch ngang (tối đa 64 ký tự) và bằng `expected_name`
    nếu được truyền; có `description` (tối đa 1024 ký tự); phần thân tối đa 80 dòng; không chứa chuỗi nào của
    `eval_markers()`. Quy tắc về `name` cũng là biện pháp bảo mật: tên khối do LLM sinh ra được dùng để tạo
    đường dẫn, nên `../evil` không được lọt qua.
    """
    problems = []
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text.strip() + "\n", re.S)
    if not m:
        return ["missing YAML frontmatter"]
    front, body = m.groups()
    name = re.search(r"^name:\s*(.+)$", front, re.M)
    desc = re.search(r"^description:\s*(.+)$", front, re.M)
    n = name.group(1).strip() if name else ""
    if not SAFE_NAME.fullmatch(n) or len(n) > 64:
        problems.append("invalid name")
    elif expected_name is not None and n != expected_name:
        problems.append("name differs from the block name")
    if not desc or len(desc.group(1).strip()) > 1024:
        problems.append("missing or too long description")
    if len(body.strip().splitlines()) > 80:
        problems.append("body longer than 80 lines")
    low = text.lower()
    for marker in eval_markers():
        if marker in low:
            problems.append(f"mentions evaluation material: {marker}")
    return problems


def parse_skill_blocks(reply: str) -> list[tuple[str, str]]:
    """Tách câu trả lời của LLM thành danh sách (name, nội dung SKILL.md).

    Khuôn dạng: `=== SKILL: <name> ===` ... `=== END ===`. Một khối kết thúc ở điểm nào đến trước trong ba điểm:
    `=== END ===`, tiêu đề `=== SKILL:` kế tiếp, hoặc cuối văn bản (LLM đôi khi quên dòng END).
    """
    pattern = re.compile(r"^=== SKILL: (\S+) ===[ \t]*\n(.*?)(?=^=== END ===|^=== SKILL: |\Z)", re.S | re.M)
    return [(name, text.strip()) for name, text in pattern.findall(str(reply))]
# --------------------------------------------------------------------------------------------------


def curate_skills(results_dir="results", source_condition="baseline", out_dir=None, model=None, max_skills: int = 3) -> list[Path]:
    """Đọc các lần chạy của TÁC VỤ HỌC (role == "learn") trong `source_condition`, nhờ LLM viết skill, ghi file.

    Các bước: nạp run.json + trace.md -> (nếu không có check nào thất bại: in cảnh báo và trả về [] mà KHÔNG gọi LLM)
    -> dựng prompt -> model.invoke(prompt) -> parse_skill_blocks -> validate_skill(text, expected_name=name)
    -> ghi `<out_dir>/<name>/SKILL.md`. Mặc định `out_dir` = <gốc lab>/skills/auto (dùng `ROOT` từ lab.tasks).
    Giữ tối đa `max_skills` skill hợp lệ; skill không hợp lệ bị bỏ qua.
    Prompt chứa, với mỗi check thất bại, TÊN và trường `detail` (lời nhận xét của bot đánh giá: phát biểu quy tắc bị vi phạm)
    cùng phần cuối của vết (trace). Với tác vụ học, `detail` chỉ phát biểu quy tắc, không chứa đáp án.
    Tuyệt đối KHÔNG đưa dữ liệu của tác vụ đánh giá (role == "eval") vào prompt.
    model mặc định: make_model() (lab.model).
    Trả về: danh sách đường dẫn SKILL.md đã ghi.
    """
    results_root = Path(results_dir)
    out_root = Path(out_dir) if out_dir is not None else ROOT / "skills" / "auto"
    failures = []
    for run_file in sorted((results_root / source_condition).glob("*/run.json")):
        run = __import__("json").loads(run_file.read_text(encoding="utf-8"))
        if run.get("role") != "learn":
            continue
        failed = [check for check in run.get("checks", []) if not check.get("passed")]
        if failed:
            trace_file = run_file.with_name("trace.md")
            trace = trace_file.read_text(encoding="utf-8") if trace_file.exists() else ""
            failures.append(
                f"Task: {run.get('task')}\n"
                + "\n".join(f"Check: {c.get('name')}\nDetail: {c.get('detail', '')}" for c in failed)
                + f"\nTrace tail:\n{trace[-3000:]}"
            )
    if not failures:
        print("warning: no failed checks in learning runs")
        return []
    if model is None:
        from .model import make_model
        model = make_model()
    prompt = (
        "You are writing reusable SKILLs for a software and data engineering agent.\n"
        "Below are the failed checks (check name and test feedback) and execution traces from training runs.\n"
        "Identify recurring procedural rules or conventions to prevent similar errors in future tasks.\n"
        "Rules:\n"
        "- Skills must be general: do not mention specific task IDs, private task filenames, or exact numbers.\n"
        "- Each skill MUST have YAML frontmatter with `name` (lowercase alphanumeric and hyphens only, e.g. code-conventions) and `description` (one sentence stating WHEN TO USE).\n"
        "- Body must be at most 40 lines of actionable instructions, checklists, or conventions.\n"
        "- Do not mention evaluation tasks, their data, filenames, or answers.\n"
        f"- Output up to {max_skills} skills, formatted exactly as:\n"
        "=== SKILL: <name> ===\n"
        "---\n"
        "name: <name>\n"
        "description: <when to use this skill>\n"
        "---\n"
        "<instructions>\n"
        "=== END ===\n\n"
        + "\n\n".join(failures)
    )
    reply = model.invoke(prompt)
    written = []
    for name, text in parse_skill_blocks(getattr(reply, "content", reply)):
        if len(written) >= max_skills or validate_skill(text, expected_name=name):
            continue
        destination = out_root / name
        destination.mkdir(parents=True, exist_ok=True)
        path = destination / "SKILL.md"
        path.write_text(text + "\n", encoding="utf-8")
        written.append(path)
    return written


if __name__ == "__main__":
    for p in curate_skills():
        print("wrote", p)
