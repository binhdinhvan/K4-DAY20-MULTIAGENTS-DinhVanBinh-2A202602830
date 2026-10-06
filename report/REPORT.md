# Báo cáo Lab: Self evolving Agentic


## 1. Thông tin nhóm và cấu hình

| Họ tên | Mã sinh viên | Phần đóng góp |
|---|---|---|
| Đinh Văn Bình | 2A202602830 | 100% |

- Mô hình: `gpt-4o-mini` (Azure/OpenAI Gateway), `LAB_TEMPERATURE=0`, `recursion_limit=60`
- Phiên bản Deep Agents: `deepagents==0.7.21`, hệ điều hành: Windows 11 (Git Bash POSIX shell)
- Số lần chạy tác vụ đã dùng / ngân sách: 9 / không giới hạn
- Commit của tag `freeze`: `92067fd`

## 2. Giả thuyết (commit TRƯỚC tag `freeze`, Phần 4.0)

- H1 (subagents so với baseline): Điểm số của subagents trên tác vụ đánh giá sẽ tương đương hoặc chênh lệch không đáng kể so với baseline (do các tác vụ đơn lẻ có phạm vi hẹp khiến mô hình có xu hướng tự giải quyết thay vì ủy quyền qua công cụ task), nhưng chi phí token sẽ cao hơn do overhead của prompt mô tả hệ thống tác tử con.
- H2 (skills-auto so với baseline): Điểm số của skills-auto trên tác vụ đánh giá sẽ cải thiện ở các quy ước dùng chung đã được học (chuẩn hóa schema, định dạng log, kiểm tra chất lượng code), nhưng mức độ cải thiện sẽ thấp hơn so với tác vụ học do hiện tượng quá khớp (overfitting) và thiếu khả năng thích ứng với các quy ước mới chưa từng xuất hiện trong failure traces (phù hợp với phần tổng quan nghiên cứu về SkillEvolBench trong `guides/pseudocode/04_curator.md`; tài liệu lab không cung cấp trích dẫn thư mục đầy đủ).
- H3 (tác vụ học so với tác vụ đánh giá): Điểm số của điều kiện skills-auto trên tác vụ học sẽ cao hơn rõ rệt so với tác vụ đánh giá vì curator trích xuất quy tắc trực tiếp từ vết phản hồi lỗi của tác vụ học, trong khi tác vụ đánh giá có thêm các biến thể và quy ước riêng chưa được nạp vào skill.

## 3. Làm quen Deep Agents (Phần 0.3)

1. Tác tử mặc định cung cấp các công cụ tệp `ls`, `read_file`, `write_file`,
   `edit_file`, `delete`, `glob`, `grep`, công cụ shell `execute`, và công cụ
   subagent `task`. `execute` cho phép chạy lệnh shell trong sandbox.
2. Mô tả của `task` cho biết đây là công cụ khởi chạy một subagent tạm thời để
   xử lý một tác vụ phức tạp, nhiều bước; subagent có loại
   `general-purpose` và có quyền truy cập các công cụ như tác tử chính. Mỗi
   lần gọi mặc định là stateless: subagent chỉ thấy nội dung trong prompt được
   gửi cho nó, không tự động thấy toàn bộ ngữ cảnh hội thoại của tác tử chính.
3. System prompt mặc định là chuỗi rỗng (`''`). Một câu hướng dẫn từ mô tả
   `task` là: “Launch an ephemeral subagent to handle a complex, multi-step
   task.” Một câu từ mô tả `execute` là: “Executes a shell command in an
   isolated sandbox and returns combined stdout/stderr with the exit code.”

## 4. Đường cơ sở và phân loại lỗi (Phần 2.2)

| Tác vụ | Check thất bại | Nhóm lỗi (A-G) | Bằng chứng (trích ngắn từ `detail` hoặc vết) |
|---|---|---|---|
| `data-learn` | `rule_money_in_cents` | E (Vi phạm quy ước tổ chức) | `RULE: money values in answer.json are integer cents (1606.67 USD is written 160667).` |
| `data-learn` | `rule_meta_block` | E (Vi phạm quy ước tổ chức) | `RULE: answer.json has an object meta = {"source": <input file name>, "rows_in": ..., "rows_used": ...}` |
| `data-learn` | `rule_clean_csv` | E (Vi phạm quy ước tổ chức) | `RULE: write workspace/clean.csv with the header order_id,timestamp_utc,region,amount_cents...` |
| `data-learn` | `north_q1_revenue` | D (Bỏ sót dữ liệu bẩn / định dạng) | `north_q1_revenue: wrong value (got 245.28)` do xử lý thiếu định dạng ngày tháng đa dạng và múi giờ ISO-8601 offset. |
| `code-learn` | `tests_not_modified` | G (Khác; chưa xác định nguyên nhân từ vết) | `the original files in tests/ must not be modified (new test files are allowed)` - đây là yêu cầu được nêu trong đề, không phải convention ẩn; vết không cho thấy nguyên nhân check thất bại. |
| `code-learn` | `parse_price_all_formats` | D (Bỏ sót định dạng) | `wrong for: ['(12.00)']` - xử lý được dấu phẩy nghìn nhưng bỏ sót định dạng số âm kế toán trong ngoặc đơn. |
| `code-learn` | `rule_changelog` | E (Vi phạm quy ước tổ chức) | `RULE: record each fix in CHANGELOG.md under '## Unreleased' ...` |
| `logs-learn` | `rule_schema_header` | E (Vi phạm quy ước tổ chức) | `RULE: the top-level object has "schema_version": 2 and "generated_by": "log-triage"` - quy ước không có trong đề bài ban đầu. |
| `logs-learn` | `rule_service_naming` | E (Vi phạm quy ước tổ chức) | `RULE: service names in errors.json are lowercase snake_case (e.g. payment_service)` |

Nhận xét: Không nên nói nhóm E chiếm đa số tuyệt đối: theo `check_breakdown.py`, baseline learn có 0/9 check `rule_` đạt và 5/18 check kỹ thuật đạt. E là một nguồn lỗi quan trọng, nhưng các lỗi kỹ thuật cũng phổ biến. Ví dụ, `parse_price_all_formats` bỏ sót định dạng ngoặc đơn; `north_q1_revenue` sai khi xử lý ngày/múi giờ; các check log như `timestamps_utc` và `exception_fields` cũng thất bại. Vì vậy, giả thuyết skill có thể giúp là hợp lý để kiểm tra, nhưng không thể kết luận trước rằng skill sẽ giải quyết triệt để các lỗi.

## 5. Điều kiện `subagents` (Phần 2.3)

- Các subagent đã định nghĩa (tên, vai trò, lý do thiết kế):
  1. `explorer`: Phụ trách khảo sát cấu trúc thư mục, đọc các tệp hướng dẫn và kiểm tra ban đầu mà không sửa đổi file.
  2. `implementer`: Phụ trách thực thi các sửa đổi mã nguồn, tính toán dữ liệu hoặc xử lý log trong thư mục workspace.
  3. `reviewer`: Phụ trách rà soát lại kết quả thực thi và chạy lại bộ test độc lập để đối chiếu với yêu cầu đề bài.
- `subagent_calls` ở từng tác vụ và nhận xét (kể cả trường hợp bằng 0):
  - `code-learn`: 0 lần gọi.
  - `data-learn`: 0 lần gọi.
  - `logs-learn`: 0 lần gọi.
  - Nhận xét: Mặc dù prompt chính đã được thêm chỉ dẫn `SUBAGENTS_NOTE`, tác tử chính (LLM gpt-4o-mini) nhận thấy các tác vụ chỉ gồm 1-2 tệp dữ liệu cụ thể và có thể thao tác trực tiếp thông qua các công cụ file (`read_file`, `write_file`) và `execute`. Do đó, tác tử chính lựa chọn không phân rã công việc cho subagent nhằm tiết kiệm lượt gọi.
- Thông tin thiếu hoặc thừa khi giao việc: Không phát sinh do tác tử chính không thực hiện giao việc.
- Ảnh hưởng đến token và thời gian: Khi tác tử chính không gọi subagent, số token sử dụng của `code-learn` (33.351 vs 32.303) và `logs-learn` (19.747 vs 19.727) gần như tương đương baseline, chỉ chênh lệch nhẹ do độ dài system prompt mở rộng thêm định nghĩa subagent. Ở `data-learn`, mô hình bị kẹt trong quá trình tự sửa script dẫn đến vượt recursion limit.

## 6. Self-evolving: skill do curator sinh (Phần 3)

- Số lần chạy curator: 1 lần. Số skill bị xóa: 0 (tất cả các skill sinh ra đều hợp lệ về cú pháp và nội dung).

| Skill | Tổng quát hay riêng cho tác vụ học? | Đúng hay sai (nêu chỗ sai nếu có) | Độ dài, `description` và `skills_read` ở Phần 3.4 |
|---|---|---|---|
| `code-quality-checks` | Tổng quát | Nội dung gồm checklist về test, type hints, changelog, CSV và docstring; không thấy hướng dẫn sai rõ ràng. | 12 dòng; description nói chung về quality standards/conventions nhưng chưa nêu rõ tình huống kích hoạt. `skills_read` = 0. |
| `data-cleaning-guidelines` | Tổng quát | Nêu các bước tổng quát về UTC, chuẩn hóa category, missing values và duplicates; không thấy hướng dẫn sai rõ ràng. | 12 dòng; description nói về data cleaning nói chung. `skills_read` = 0. |
| `logging-standards` | Tổng quát | Có hướng dẫn hữu ích về log level, UTC, tên service và schema; không thấy hướng dẫn sai rõ ràng. | 12 dòng; description nêu mục đích rộng, chưa nêu trigger cụ thể. `skills_read` = 0. |

## 7. Kết quả so sánh (Phần 4.3, 4.4)

### Bảng so sánh tổng hợp (`report/table.md`)

| Task | baseline | subagents | skills-auto |
|---|---|---|---|
| code-learn | 2/10 | 2/10 | 4/10 |
| data-learn | 2/8 | 0/8 | 3/8 |
| logs-learn | 1/9 | 1/9 | 1/9 |
| code-eval | 1/11 | 0/11 | 3/11 |
| data-eval | 0/9 | 0/9 | 3/9 |
| logs-eval | 0/10 | 0/10 | 1/10 |
| **Mean score - learning tasks** | 0.19 | 0.10 | 0.30 |
| **Mean score - evaluation tasks** | 0.03 | 0.00 | 0.24 |
| **Mean tokens per run** | 117,141 | 138,120 | 30,591 |
| **Runs that read a skill** | 0/6 | 0/6 | 0/6 |

### Phân tích chi tiết theo loại check (`scripts/check_breakdown.py`)

| Condition | Role | Technical checks | House rules (`rule_`) | Mean tokens | Read a skill |
|---|---|---|---|---|---|
| `baseline` | `eval` | 1/18 | 0/12 | 205,334 | 0/3 |
| `baseline` | `learn` | 5/18 | 0/9 | 28,948 | 0/3 |
| `subagents` | `eval` | 0/18 | 0/12 | 108,445 | 0/3 |
| `subagents` | `learn` | 3/18 | 0/9 | 167,795 | 0/3 |
| `skills-auto` | `eval` | 7/18 | 0/12 | 22,536 | 0/3 |
| `skills-auto` | `learn` | 8/18 | 0/9 | 38,646 | 0/3 |

### Ghi nhận các lần chạy có lỗi hoặc bất thường:
- Ở điều kiện `baseline`: `code-eval` và `data-eval` bị lỗi `GraphRecursionError` (chạm trần recursion limit = 60) do mô hình lặp lại các lệnh sửa code không hiệu quả, dẫn đến tiêu tốn ~200k - 400k tokens mỗi tác vụ.
- Ở điều kiện `subagents`: `data-learn` và `code-eval` bị lỗi `GraphRecursionError` (lặp kiểm thử không hội tụ).
- Ở điều kiện `skills-auto`: Cả 6/6 tác vụ đều chạy trơn tru, hoàn thành với mã thoát 0, không có lỗi `GraphRecursionError`, và `skills_modified` luôn bằng `false`.

## 8. Phân tích

1. **So sánh điểm số giữa các điều kiện:**
   - Trên tác vụ **học**: `skills-auto` đạt điểm trung bình cao nhất (0.30), vượt trội so với `baseline` (0.19) và `subagents` (0.10).
   - Trên tác vụ **đánh giá**: `skills-auto` cũng đạt điểm trung bình cao nhất (0.24), vượt trội hoàn toàn so với `baseline` (0.03) và `subagents` (0.00).
   - `skills-auto` có điểm trung bình 0.24 trên eval (so với 0.30 trên learn), nhưng cả hai tập đều chỉ có ba tác vụ. Hơn nữa, `skills_read` bằng 0/6 ở điều kiện này, nên kết quả chỉ cho thấy điểm số của điều kiện `skills-auto` cao hơn trong lần chạy này; chưa chứng minh nội dung skill được dùng hay tri thức skill tổng quát hóa tốt.

2. **Tách điểm kỹ thuật và quy ước (`rule_`):**
   - Sự vượt trội của `skills-auto` đến hoàn toàn từ **nhóm check kỹ thuật**: trên tập eval, `skills-auto` đạt 7/18 check kỹ thuật (trong khi baseline chỉ đạt 1/18 và subagents đạt 0/18); trên tập learn đạt 8/18 (so với 5/18 ở baseline).
   - Ngược lại, nhóm **check quy ước nhà** (`house rules` / `rule_`) ở tập đánh giá đều đạt 0/12 cho cả 3 điều kiện. Lý do: các tác vụ đánh giá được thiết kế với các quy ước ẩn mới (ví dụ quy ước schema khác hoặc cách định dạng khác) chưa từng xuất hiện trong các phản hồi lỗi của tác vụ học. Bộ skill sau khi đóng băng không thể tự đoán trước các quy ước mới này.

3. **Cơ chế hoạt động qua vết và `skills_read`:**
   - Đúng là các trace có bằng chứng về những thao tác phù hợp với một số skill: `results/skills-auto/data-eval/trace.md` cho thấy agent chuẩn hóa category, loại order trùng và bỏ qua total thiếu; `run.json` đạt các check `top_category`, `missing_total_orders`, `duplicate_events_removed` (3/9). Các thao tác này tương ứng một phần với `data-cleaning-guidelines`.
   - Tuy nhiên, `skills_read` = 0/6 nghĩa là runner không ghi nhận lần `read_file` nào vào `skills/`; trace `data-eval` chỉ cho thấy đọc đề, README và dữ liệu. Hơn nữa, các thao tác trên cũng được yêu cầu rõ trong đề bài. Vì vậy có thể ghi nhận sự tương đồng giữa hành vi và skill, nhưng chưa thể quy kết agent làm vậy nhờ đã đọc skill. Cần phân biệt bằng chứng hành vi với bằng chứng skill được nạp/đọc khi đánh giá cơ chế nhân quả.

4. **Phân tích chi phí (Token efficiency):**
   - `skills-auto` có chi phí token trung bình thấp nhất: **30.591 tokens/run**, chỉ bằng 26% so với `baseline` (117.141 tokens) và 22% so với `subagents` (138.120 tokens).
   - Baseline và subagents có một số lần chạm `GraphRecursionError` với token cao; cả 6 run skills-auto chính thức không có lỗi đó. Đây là lời giải thích phù hợp với chênh lệch token quan sát được, nhưng chưa chứng minh skill là nguyên nhân, vì `skills_read` ghi nhận 0 ở mọi run skills-auto.
   - Đa tác tử (`subagents`): Không đáng chi phí trong thí nghiệm này. Mô hình gpt-4o-mini thường tự giải quyết trực tiếp (0 lần ủy quyền) nhưng vẫn phải gánh thêm overhead chi phí token của định nghĩa subagent trong prompt.

5. **Rò rỉ dữ liệu và quá khớp (Data leakage & Overfitting):**
   - Quy trình phân lập tuyệt đối: `curator` chỉ đọc các tệp `run.json` có `role == "learn"`, hoàn toàn không truy cập kết quả của tác vụ đánh giá.
   - Hàm `validate_skill` với `eval_markers()` đảm bảo không có từ khóa hoặc tên file bài eval nào xuất hiện trong `skills/auto/`.
   - Các skill sinh ra hoàn toàn tổng quát (chuẩn hóa UTC, checklist docstrings, xử lý duplicate), không chứa giá trị hằng số cứng hay dữ liệu riêng của tác vụ học.

6. **Đo lường nhiễu (Noise estimation):**
   - Điểm trung bình của `skills-auto` trên tác vụ học trước đóng băng (lần dev ở Phần 3.4 lưu tại `results/skills-auto-dev`) là 0.133 (do `data-learn` bị recursion loop trong lần dev đầu).
   - Điểm trung bình sau đóng băng (lần chạy chính thức ở Phần 4.2) là 0.30.
   - Chênh lệch 0.167 phản ánh tính bất định (stochasticity) trong quá trình mô hình LLM giải quyết vấn đề bằng công cụ qua nhiều bước. Điều này khẳng định kết quả thực nghiệm cần được nhìn nhận qua xu hướng thống kê tổng thể thay vì một lần chạy đơn lẻ.

## 9. Hạn chế và tính hợp lệ

1. **Kích thước mẫu tác vụ nhỏ:** Thí nghiệm chỉ gồm 3 họ tác vụ (tổng 6 tác vụ). Cỡ mẫu này đủ để quan sát cơ chế hoạt động nhưng chưa đủ lớn để đạt ý nghĩa thống kê định lượng cao (statistical significance).
2. **Số lần chạy lặp lại giới hạn:** Bảng kết quả chính thức có một lần chạy cho mỗi điều kiện/task; phần thưởng chỉ lặp thêm `skills-auto` trên eval, không lặp baseline hay subagents. Vì vậy, phép so sánh chính chịu ảnh hưởng của dao động ngẫu nhiên và các lần lặp bổ sung không đủ để ước lượng phương sai giữa mọi điều kiện.
3. **Quy ước ẩn chủ quan:** Các check quy ước nhà (`rule_`) được thiết kế riêng biệt và cố tình không đưa vào đề bài ban đầu. Bản chất của các quy tắc này là không thể suy luận logic nếu không có thông tin đầu vào, khiến tác tử chỉ có thể đạt được nếu đã được cung cấp trước hoặc học từ chính môi trường đó.

## 10. Kết luận

Trong các lần chạy được lưu, điều kiện `skills-auto` đạt điểm eval trung bình 0.24 so với 0.03 ở baseline và có token/run trung bình thấp hơn (30.591 so với 117.141). Tuy nhiên, `skills_read` = 0/6 nên chưa thể kết luận mức cải thiện do skill tự sinh gây ra; số lần chạy nhỏ và recursion errors ở các điều kiện khác cũng có thể ảnh hưởng đáng kể. Điều kiện subagents không cải thiện điểm trong mẫu này và không có lần ủy quyền nào ở các run learn. Bước tiếp theo nên xác minh cơ chế nạp/đọc skill, ghi trace đọc skill rõ ràng, rồi lặp lại thí nghiệm trước khi kết luận nhân quả.

## Phụ lục

- Lệnh đã chạy (theo thứ tự):
  1. `pytest tests/test_01_provided.py`
  2. `pytest tests/test_02_agent.py`
  3. `pytest tests/test_03_runner.py`
  4. `python -m lab.runner --condition baseline --tasks data-learn`
  5. `python -m lab.runner --condition baseline --tasks code-learn logs-learn`
  6. `python -m lab.runner --condition subagents --tasks learn`
  7. `pytest tests/test_04_curator.py`
  8. `python -m lab.curator`
  9. `python -m lab.runner --condition skills-auto --tasks learn`
  10. `git add -A && git commit -m "hypotheses"`
  11. `git add -A && git commit --allow-empty -m "freeze skills" && git tag freeze`
  12. `python -m lab.runner --condition baseline --tasks eval`
  13. `python -m lab.runner --condition subagents --tasks eval`
  14. `python -m lab.runner --condition skills-auto --tasks all`
  15. `python scripts/verify_freeze.py`
  16. `python -m lab.compare > report/table.md`
  17. `python scripts/check_breakdown.py`
  18. `python -m lab.runner --condition skills-auto --tasks eval --results results/bonus_noise/run2`
  19. `python -m lab.runner --condition skills-auto --tasks eval --results results/bonus_noise/run3`

- Thử thách mở rộng: **Hướng 6e - Lặp để đo nhiễu và độ biến thiên ngẫu nhiên (Stochastic Variance)**

  1. **Thiết kế thí nghiệm:** Thực hiện lặp lại điều kiện `skills-auto` trên toàn bộ 3 tác vụ đánh giá (`code-eval`, `data-eval`, `logs-eval`) thêm 2 lần độc lập (tổng cộng 3 lần chạy), kết quả lưu tại thư mục riêng biệt: `results/bonus_noise/run2` và `results/bonus_noise/run3` (hoàn toàn tách biệt khỏi kết quả chính thức ở `results/skills-auto/`).
  
  2. **Số liệu so sánh chi tiết:**

     | Tác vụ | Lần 1 (Chính thức) | Lần 2 (Replicate 2) | Lần 3 (Replicate 3) | Điểm trung bình | Khoảng dao động |
     |---|---|---|---|---|---|
     | `code-eval` | 3/11 (30.870 tokens) | 1/11 (229.092 tokens) | 2/11 (253.258 tokens) | **0.182** | 1/11 - 3/11 |
     | `data-eval` | 3/9 (21.392 tokens) | 2/9 (217.277 tokens) | 3/9 (21.344 tokens) | **0.296** | 2/9 - 3/9 |
     | `logs-eval` | 1/10 (15.348 tokens) | 1/10 (15.451 tokens) | 0/10 (15.463 tokens) | **0.067** | 0/10 - 1/10 |
     | **Mean Eval Score** | **0.235** | **0.138** | **0.172** | **0.182** | **0.138 - 0.235** |
     | **Mean Tokens** | **22.536** | **153.940** | **96.688** | **91.055** | **22.536 - 153.940** |

  3. **Phân tích cơ chế dựa trên vết (Trace analysis):**
     - Ở tác vụ `data-eval`, điểm số dao động từ 2/9 đến 3/9. Tuy nhiên, các run ghi `skills_read` = 0; do đó không thể dùng độ ổn định điểm số này làm bằng chứng rằng `data-cleaning-guidelines` được áp dụng.
     - Ở tác vụ `code-eval`, quan sát vết thực thi cho thấy trong Lần 2 và 3, khi gặp phải ca kiểm thử biên phức tạp (`pricing`), mô hình có xác suất bị vướng vào chuỗi lệnh debug lặp lại dẫn đến chạm trần `recursion_limit` (60 bước), làm tăng vọt lượng token tiêu thụ. Khi mô hình dừng đúng lúc (như Lần 1), lượng token chỉ là ~30k với điểm số tối ưu 3/11.
     - Ba lần lặp `skills-auto` cho mean eval score 0.182 (các run lần lượt 0.235, 0.138, 0.172), cao hơn một lần chạy baseline (0.03) và subagents (0.00). Với số mẫu nhỏ và chưa xác nhận skill được đọc, đây là tín hiệu cần kiểm tra thêm, không chứng minh hiệu quả hay tính bền vững của cơ chế tự tiến hóa.

  4. **Hạn chế và đề xuất bước tiếp theo:**
     - *Hạn chế:* Sự bất định của LLM trong việc dừng vòng lặp (stopping criteria) khiến phương sai token giữa các lần chạy là đáng kể.
     - *Đề xuất:* Bổ sung cơ chế phát hiện vòng lặp (loop detector middleware) trong Agent Harness để chủ động cảnh báo hoặc ngắt sớm các chuỗi lệnh thử-sai không tiến triển, giúp cố định chi phí token ở mức tối ưu.

  5. **Khả năng tái lập:** Thí nghiệm có thể tái lập 100% bằng cách chạy các lệnh CLI đã liệt kê ở trên.

