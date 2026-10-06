# Báo cáo Lab: Self evolving Agentic

> Sao chép tệp này thành `report/REPORT.md` (đã làm ở Phần 0) và điền dần qua các Phần của lab. Xóa các dòng hướng dẫn dạng trích dẫn (bắt đầu bằng `>`). Văn phong kỹ thuật, ngắn gọn, mọi nhận định đi kèm số liệu hoặc bằng chứng. Trong buổi học: điền mục 1 đến 7 (bản nháp). Sau buổi học: hoàn thiện mục 8 đến 10.

## 1. Thông tin nhóm và cấu hình

| Họ tên | Mã sinh viên | Phần đóng góp |
|---|---|---|
| Đinh Văn Bình | 2A202602830 | 100% |

- Mô hình: `gpt-4o-mini` (Azure/OpenAI Gateway), `LAB_TEMPERATURE=0`, `recursion_limit=60`
- Phiên bản Deep Agents: `deepagents==0.7.21`, hệ điều hành: Windows 11 (Git Bash POSIX shell)
- Số lần chạy tác vụ đã dùng / ngân sách: 9 / không giới hạn
- Commit của tag `freeze`: (sẽ cập nhật sau khi tạo tag `freeze`)

## 2. Giả thuyết (commit TRƯỚC tag `freeze`, Phần 4.0)

- H1 (subagents so với baseline): Điểm số của subagents trên tác vụ đánh giá sẽ tương đương hoặc chênh lệch không đáng kể so với baseline (do các tác vụ đơn lẻ có phạm vi hẹp khiến mô hình có xu hướng tự giải quyết thay vì ủy quyền qua công cụ task), nhưng chi phí token sẽ cao hơn do overhead của prompt mô tả hệ thống tác tử con.
- H2 (skills-auto so với baseline): Điểm số của skills-auto trên tác vụ đánh giá sẽ cải thiện ở các quy ước dùng chung đã được học (chuẩn hóa schema, định dạng log, kiểm tra chất lượng code), nhưng mức độ cải thiện sẽ thấp hơn so với tác vụ học do hiện tượng quá khớp (overfitting) và thiếu khả năng thích ứng với các quy ước mới chưa từng xuất hiện trong failure traces (phù hợp với phát hiện từ SkillEvolBench).
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
| `code-learn` | `tests_not_modified` | E (Vi phạm quy ước tổ chức) | `the original files in tests/ must not be modified (new test files are allowed)` |
| `code-learn` | `parse_price_all_formats` | C (Vá triệu chứng) | `wrong for: ['(12.00)']` - mô hình chỉ xử lý dấu phẩy nghìn, bỏ qua định dạng số âm kế toán trong ngoặc đơn. |
| `code-learn` | `changelog_updated` | E (Vi phạm quy ước tổ chức) | `RULE: describe every fix in CHANGELOG.md under '## Unreleased' with at least three bullet points.` |
| `logs-learn` | `rule_schema_version` | E (Vi phạm quy ước tổ chức) | `RULE: errors.json has "schema_version": 2` - quy ước ẩn không có trong file đề bài ban đầu. |
| `logs-learn` | `rule_service_naming` | E (Vi phạm quy ước tổ chức) | `RULE: service names in errors.json are lowercase snake_case (e.g. payment_service)` |

Nhận xét: Nhóm lỗi E (Vi phạm quy ước tổ chức) chiếm đa số tuyệt đối (khoảng 70% các check thất bại). Các check kỹ thuật cơ bản (A, B) phần lớn đều đạt. Điều này chứng minh rằng năng lực lập trình cơ bản của LLM (gpt-4o-mini) là tốt, nhưng mô hình không thể tự đoán các quy ước nội bộ ẩn nếu không có tri thức thủ tục bổ sung. Một skill do curator tự sinh có thể giải quyết triệt để nhóm lỗi E bằng cách cung cấp danh sách checklist và quy ước định dạng cần tuân thủ.

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
| `code-quality-checks` | Tổng quát | Đúng (nhắc nhở giữ nguyên test gốc, cập nhật CHANGELOG dưới ## Unreleased, định dạng CSV và docstring). | 12 dòng, mô tả chuẩn: "Use this skill to ensure code adheres to quality standards and conventions.", `skills_read` = 0 (tác tử không tự động mở file skill nhưng đọc chỉ dẫn chung). |
| `data-cleaning-guidelines` | Tổng quát | Đúng (hướng dẫn chuẩn hóa ngày tháng UTC, chuẩn hóa tên danh mục, xử lý giá trị khuyết và loại bỏ trùng lặp). | 12 dòng, mô tả chuẩn: "Use this skill to standardize data cleaning processes for consistency and accuracy.", `skills_read` = 0. |
| `logging-standards` | Tổng quát | Đúng (hướng dẫn chuẩn hóa log level, timestamp UTC, quy ước đặt tên service dạng snake_case, tuân thủ schema). | 12 dòng, mô tả chuẩn: "Use this skill to ensure logs are structured and contain necessary information for troubleshooting.", `skills_read` = 0. |

## 7. Kết quả so sánh (Phần 4.3, 4.4)

> Dán nội dung `report/table.md` và kết quả `python scripts/check_breakdown.py`. Nêu các lần chạy có `error` hoặc `skills_modified = true` (nếu có) và cách xử lý.

```text
(dán bảng ở đây)
```

## 8. Phân tích

> Trả lời từng câu bằng số liệu từ mục 7 và bằng chứng từ vết. Kết quả âm hoặc không có khác biệt vẫn hợp lệ nếu được phân tích tốt.

1. So với `baseline`, điều kiện nào cải thiện điểm tác vụ **học**? Điều kiện nào cải thiện điểm tác vụ **đánh giá**? Có điều kiện nào cải thiện tác vụ học nhưng không cải thiện tác vụ đánh giá? Nếu có, đó là dấu hiệu gì?
2. Tách điểm thành check kỹ thuật và check quy ước (`rule_`). Skill do curator sinh giúp nhóm check nào? Check quy ước **mới** của tác vụ đánh giá có được skill giúp không, và vì sao?
3. Dựa vào vết và `skills_read`, giải thích một check mà skill giúp đạt và một check mà skill không giúp (skill chưa được đọc, đọc nhưng không làm theo, skill thiếu hoặc sai).
4. Chi phí: so sánh số token trung bình giữa các điều kiện. Điều kiện nào có hiệu quả tốt nhất theo điểm trên mỗi token? Đa tác tử có đáng chi phí trong thí nghiệm này không?
5. Có dấu hiệu rò rỉ dữ liệu hoặc quá khớp nào trong skill sinh ra không? Nhóm đã phòng tránh như thế nào?
6. Nhiễu: so sánh điểm tác vụ học của cùng bộ skill ở Phần 3.4 (đã sao lưu) và sau đóng băng. Chênh lệch bao nhiêu? Nó cho biết điều gì về độ tin cậy của các chênh lệch trong bảng ở mục 7?

## 9. Hạn chế và tính hợp lệ

> Nêu ít nhất 3 hạn chế và ảnh hưởng của từng hạn chế đến kết luận (ví dụ: chỉ 3 tác vụ mỗi vai trò, mỗi cấu hình chạy một lần, nhiễu của mô hình, tác vụ do giảng viên thiết kế sẵn quy ước, chỉ một mô hình).

1.
2.
3.

## 10. Kết luận

> Tối đa 5 câu. Chỉ khẳng định điều số liệu hỗ trợ. Nêu một đề xuất cải tiến tiếp theo.

## Phụ lục

- Lệnh đã chạy (theo thứ tự):
- Thử thách mở rộng (nếu có): hướng chọn, kết quả, nhận xét.
- Ghi chú khác:
