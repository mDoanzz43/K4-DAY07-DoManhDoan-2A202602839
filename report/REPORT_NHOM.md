# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** C3D
**Thành viên:** 
- Đỗ Mạnh Đoan - 2A202602839
- Nguyễn Mạnh Cường - 2A202602823
- Hoàng Thái Đạt - 2A202602959
- Vi Hùng Đức - 2A202602512

**Ngày:** 19/9/2026

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Chủ đề (Domain) & Lý Do Chọn

**Chủ đề:** Dịch vụ và chính sách đại học của RMIT Việt Nam

**Tại sao nhóm chọn chủ đề này?**
> Nhóm chọn chủ đề này vì các tài liệu về học phí, học bổng, hỗ trợ sinh viên, mốc thời gian học tập, khiếu nại và phúc lợi nhân viên có cấu trúc rõ ràng, phù hợp để thử nghiệm retrieval theo chunk và metadata. Bộ tài liệu cũng có nhiều nhóm đối tượng khác nhau (`student`, `staff`, `all`), giúp kiểm tra xem metadata filter có cải thiện độ chính xác truy xuất hay không. Các nguồn đều là trang công khai, có URL truy vết và không chứa dữ liệu cá nhân hay nội dung cần đăng nhập.

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | Chính sách học phí đặc biệt | https://www.rmit.edu.vn/vi/hoc-tap-tai-rmit/hoc-phi/chinh-sach-hoc-phi-dac-biet | 2026-09-19 / not-stated | 8,336 | `doc_id`, `title`, `source_url`, `retrieved_at`, `document_version`, `audience=student`, `department=student-services`, `category=tuition`, `language=vi` |
| 2 | Thông tin và chính sách học phí RMIT | https://www.rmit.edu.vn/vi/hoc-tap-tai-rmit/hoc-phi | 2026-09-19 / not-stated | 6,842 | `doc_id`, `title`, `source_url`, `retrieved_at`, `document_version`, `audience=student`, `department=student-services`, `category=tuition`, `language=vi` |
| 3 | Dịch vụ hỗ trợ sinh viên RMIT | https://www.rmit.edu.vn/vi/doi-song-sinh-vien/ho-tro-sinh-vien | 2026-09-19 / not-stated | 1,165 | `doc_id`, `title`, `source_url`, `retrieved_at`, `document_version`, `audience=student`, `department=student-services`, `category=support`, `language=vi` |
| 4 | Thông tin học bổng RMIT Việt Nam | https://www.rmit.edu.vn/vi/hoc-tap-tai-rmit/hoc-bong | 2026-09-19 / not-stated | 1,566 | `doc_id`, `title`, `source_url`, `retrieved_at`, `document_version`, `audience=student`, `department=student-services`, `category=scholarship`, `language=vi` |
| 5 | Những mốc thời gian quan trọng của sinh viên | https://www.rmit.edu.vn/vi/hoc-tap-tai-rmit/nhung-moc-thoi-gian-quan-trong | 2026-09-19 / not-stated | 1,262 | `doc_id`, `title`, `source_url`, `retrieved_at`, `document_version`, `audience=student`, `department=academic-services`, `category=academic-calendar`, `language=vi` |
| 6 | Phúc lợi dành cho nhân viên RMIT | https://www.rmit.edu.vn/vi/gioi-thieu-chung/lam-viec-tai-rmit/phuc-loi-nhan-vien | 2026-09-19 / not-stated | 4,207 | `doc_id`, `title`, `source_url`, `retrieved_at`, `document_version`, `audience=staff`, `department=human-resources`, `category=staff-benefits`, `language=vi` |
| 7 | Thông tin khiếu nại tại RMIT | https://www.rmit.edu.vn/vi/utilities/khieu-nai | 2026-09-19 / not-stated | 1,504 | `doc_id`, `title`, `source_url`, `retrieved_at`, `document_version`, `audience=all`, `department=student-services`, `category=complaints`, `language=vi` |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `doc_id` | string | `hoc-bong-rmit-vietnam` | Định danh ổn định cho tài liệu gốc, dùng để liên kết chunk với file nguồn và kiểm tra `sources.csv`. |
| `title` | string | `Thông tin học bổng RMIT Việt Nam` | Giúp người đọc hiểu nhanh nội dung tài liệu và hỗ trợ hiển thị nguồn trong kết quả retrieval. |
| `source_url` | string | `https://www.rmit.edu.vn/vi/hoc-tap-tai-rmit/hoc-bong` | Cho phép truy vết câu trả lời về nguồn công khai ban đầu. |
| `retrieved_at` | date string | `2026-09-19` | Ghi lại ngày nhóm thu thập tài liệu để đánh giá độ mới của dữ liệu. |
| `document_version` | string | `not-stated` | Lưu phiên bản/ngày hiệu lực nếu nguồn có nêu; nếu không có thì ghi rõ `not-stated` thay vì tự suy đoán. |
| `audience` | enum string | `student`, `staff`, `all` | Trường lọc quan trọng nhất trong benchmark; giúp tránh lấy nhầm tài liệu cho đối tượng khác. |
| `department` | string | `student-services`, `academic-services`, `human-resources` | Giúp thu hẹp phạm vi tìm kiếm theo đơn vị phụ trách dịch vụ/chính sách. |
| `category` | string | `tuition`, `scholarship`, `support`, `complaints` | Giúp phân nhóm tài liệu theo loại câu hỏi, ví dụ học phí, học bổng, hỗ trợ hoặc khiếu nại. |
| `language` | string | `vi` | Cho biết ngôn ngữ tài liệu, hữu ích nếu corpus sau này mở rộng sang song ngữ. |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| `chinh-sach-hoc-phi-rmit.md` | FixedSizeChunker (`fixed_size`) | 10 | 683.8 | Trung bình; có thể cắt ngang bảng học phí hoặc mục thanh toán. |
| `chinh-sach-hoc-phi-rmit.md` | SentenceChunker (`by_sentences`) | 8 | 853.0 | Khá mạch lạc theo câu, nhưng chunk hơi dài. |
| `chinh-sach-hoc-phi-rmit.md` | RecursiveChunker (`recursive`) | 11 | 618.3 | Tốt; cân bằng giữa độ dài và ranh giới đoạn/mục. |
| `hoc-bong-rmit-vietnam.md` | FixedSizeChunker (`fixed_size`) | 3 | 520.7 | Chấp nhận được vì tài liệu ngắn. |
| `hoc-bong-rmit-vietnam.md` | SentenceChunker (`by_sentences`) | 5 | 310.8 | Mạch lạc, dễ đọc, nhưng tạo nhiều chunk nhỏ hơn. |
| `hoc-bong-rmit-vietnam.md` | RecursiveChunker (`recursive`) | 3 | 516.0 | Tốt; giữ được phần giới thiệu và các bước nộp hồ sơ. |
| `phuc-loi-nhan-vien-rmit.md` | FixedSizeChunker (`fixed_size`) | 7 | 600.4 | Trung bình; có thể cắt giữa các nhóm phúc lợi. |
| `phuc-loi-nhan-vien-rmit.md` | SentenceChunker (`by_sentences`) | 6 | 699.3 | Khá ổn nhưng có chunk dài. |
| `phuc-loi-nhan-vien-rmit.md` | RecursiveChunker (`recursive`) | 8 | 521.9 | Tốt nhất trong baseline vì giữ đoạn ngắn và dễ truy xuất. |

### Chiến lược của từng thành viên

> Mỗi thành viên điền một khối dưới đây (copy thêm nếu nhóm có nhiều hơn 3 người).

**Thành viên 1 — Đỗ Mạnh Đoan**
- **Loại chiến lược:** RecursiveChunker
- **Mô tả & lý do chọn cho chủ đề này:** Chiến lược recursive ưu tiên tách theo đoạn/mục trước, sau đó mới tách nhỏ hơn khi đoạn quá dài. Cách này phù hợp với tài liệu chính sách vì nội dung thường được viết theo đoạn giải thích và danh sách điều kiện.

**Thành viên 2 — Nguyễn Mạnh Cường**
- **Loại chiến lược:** FixedSizeChunker
- **Mô tả & lý do chọn:** Chiến lược fixed-size tạo chunk có kích thước ổn định và dễ kiểm soát số lượng. Nhược điểm là có thể cắt ngang bảng hoặc mục chính sách, nhưng đây là baseline tốt để so sánh với các chiến lược hiểu cấu trúc văn bản hơn.

**Thành viên 3 — Hoàng Thái Đạt**
- **Loại chiến lược:** SentenceChunker
- **Mô tả & lý do chọn:** Chiến lược theo câu giúp chunk dễ đọc và ít cắt ngang câu. Với các tài liệu mô tả dịch vụ, cách này giữ được ngữ nghĩa tự nhiên, nhưng đôi khi chunk dài hoặc ngắn không đều.

**Thành viên 4 — Vi Hùng Đức**
- **Loại chiến lược:** custom HeadingChunker
- **Mô tả & lý do chọn:** Chiến lược custom tách theo heading Markdown (`#`, `##`, `###`), nếu section quá dài thì fallback sang recursive và gắn lại heading vào chunk con. Cách này phù hợp với tài liệu quy định vì heading thường là tín hiệu mạnh cho từng nhóm nội dung như học phí, học bổng, nghỉ phép hoặc khiếu nại.
- **Code snippet (nếu custom):**
```python
class HeadingChunker:
    def chunk(self, text):
        sections = re.split(r"(?=^#{1,3}\\s+)", text, flags=re.MULTILINE)
        # section dài quá chunk_size thì dùng RecursiveChunker để cắt tiếp
```

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Đỗ Mạnh Đoan | RecursiveChunker | 10/10 | Cân bằng độ dài và ngữ cảnh; top-1 đúng cả 5 câu trong benchmark. | Một số câu vẫn có chunk đúng tài liệu nhưng không phải section chính xác nhất ở top-2/top-3. |
| Nguyễn Mạnh Cường | FixedSizeChunker | 10/10 | Kích thước ổn định, dễ kiểm soát, chạy nhanh. | Có thể cắt ngang câu/bảng; một số preview bắt đầu giữa câu nên kém mạch lạc. |
| Hoàng Thái Đạt | SentenceChunker | 10/10 | Chunk dễ đọc, giữ ranh giới câu tốt. | Độ dài chunk không đều; có chunk dài hơn mong muốn. |
| Vi Hùng Đức | HeadingChunker | 10/10 | Giữ heading nên ngữ cảnh rõ nhất; Q4 và Q5 có top-1 rất đúng section. | Tạo nhiều chunk hơn (81 chunk), tốn thêm lưu trữ và thời gian search. |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> Trên bộ câu hỏi hiện tại, cả bốn chiến lược đều đạt 10/10 khi dùng lexical embedding, nhưng nhóm đánh giá `HeadingChunker` tốt nhất về chất lượng giải thích vì top-1 thường nằm đúng section có tiêu đề rõ ràng, ví dụ `## Nghỉ phép` hoặc `## Sinh viên RMIT`. Tuy nhiên, nếu cần cân bằng giữa số lượng chunk và chất lượng truy xuất, `RecursiveChunker` là lựa chọn thực tế hơn vì đạt cùng điểm với số chunk ít hơn đáng kể. Failure case quan trọng của CP6 là A/B metadata filter chưa tạo khác biệt lớn ở top-3 do câu hỏi đã chứa từ khóa rất rõ; lần sau nhóm cần thiết kế một câu mơ hồ hơn để filter chứng minh tác dụng mạnh hơn.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Đây là bộ câu hỏi chung cho mọi thành viên chạy.

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | Học phí tại RMIT được thanh toán theo cách nào? | Học phí được thanh toán theo từng học kỳ, dựa trên số môn sinh viên học trong từng học kỳ. | `chinh-sach-hoc-phi-rmit#0` |
| 2 | Sinh viên có người thân đang học hoặc đã tốt nghiệp tại RMIT được chiết khấu học phí bao nhiêu? | Sinh viên có anh chị em ruột, vợ chồng, cha mẹ hoặc con đang học hoặc đã tốt nghiệp tại RMIT Việt Nam được chiết khấu 5% học phí khi bắt đầu nhập học trong năm 2026. | `chinh-sach-hoc-phi-dac-biet#0`, `chinh-sach-hoc-phi-dac-biet#1` |
| 3 | RMIT đã trao học bổng tổng giá trị bao nhiêu và cho hơn bao nhiêu bạn trẻ? | RMIT đã trao các học bổng với tổng giá trị hơn 613 tỉ đồng cho hơn 1.900 bạn trẻ. | `hoc-bong-rmit-vietnam#0` |
| 4 | Nhân viên RMIT có những ngày nghỉ phép và nghỉ ốm có lương nào? | Nhân viên có 20 ngày nghỉ phép có lương, 10 ngày nghỉ ốm có lương, 05 ngày nghỉ lễ Giáng Sinh có lương mỗi năm và một số ngày nghỉ bổ sung theo điều kiện. | `phuc-loi-nhan-vien-rmit#6` |
| 5 | Sinh viên hiện tại hoặc cựu sinh viên RMIT gửi khiếu nại bằng cách nào? | Sinh viên hiện tại hoặc cựu sinh viên RMIT có thể gửi khiếu nại đến cổng thông tin khiếu nại trên trang dành cho sinh viên RMIT. | `quy-trinh-khieu-nai-rmit#0`, `quy-trinh-khieu-nai-rmit#1` |

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | Học phí tại RMIT được thanh toán theo cách nào? | HeadingChunker + lexical embedding | Có, top-1 là chunk đúng | Dùng `metadata_filter={"audience": "student"}`; HeadingChunker có score top-1 cao nhất. |
| 2 | Người thân học/tốt nghiệp RMIT được chiết khấu bao nhiêu? | FixedSizeChunker + lexical embedding | Có, top-1 và top-2 đều đúng tài liệu | Dùng `metadata_filter={"audience": "student"}`; fixed-size nhỉnh hơn rất nhẹ về score. |
| 3 | Tổng giá trị học bổng RMIT đã trao là bao nhiêu? | HeadingChunker + lexical embedding | Có, top-1 là chunk đúng | Dùng `metadata_filter={"audience": "student"}`. |
| 4 | Nhân viên RMIT có ngày nghỉ phép/nghỉ ốm nào? | HeadingChunker + lexical embedding | Có, top-1 là chunk đúng section `## Nghỉ phép` | Dùng `metadata_filter={"audience": "staff"}`. |
| 5 | Sinh viên/cựu sinh viên gửi khiếu nại bằng cách nào? | HeadingChunker + lexical embedding | Có, top-1 đúng section `## Sinh viên RMIT` | Không dùng filter để kiểm tra truy xuất chung. |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> Về thiết kế hệ thống, metadata filter vẫn hữu ích vì nó giới hạn không gian tìm kiếm theo đúng đối tượng (`student`, `staff`, `all`). Tuy nhiên, A/B trong `ket_qua_benchmark.txt` cho thấy các câu hiện tại có từ khóa quá rõ nên top-3 gần như không đổi giữa có filter và không filter. Đây là failure case của benchmark: nhóm đã dùng filter ở câu 1-4, nhưng cần thiết kế thêm câu hỏi mơ hồ hơn để chứng minh tác dụng của filter rõ ràng hơn.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
> - Chunk theo heading giúp kết quả dễ truy vết nguồn hơn vì chunk giữ lại tiêu đề section.
> - RecursiveChunker là lựa chọn cân bằng: ít chunk hơn HeadingChunker nhưng vẫn giữ ngữ cảnh tốt.
> - Metadata filter là lớp bảo vệ hữu ích, nhưng benchmark hiện tại chưa đủ mơ hồ để chứng minh khác biệt A/B thật rõ.

**Bài học rút ra khi so sánh trong nhóm:**
> Cùng một corpus nhưng chiến lược chunking làm thay đổi mức độ dễ đọc của kết quả top-3. Fixed-size đôi khi lấy đúng tài liệu nhưng preview bị cắt giữa câu, trong khi HeadingChunker cho chunk có tiêu đề rõ hơn và dễ giải thích trong demo. Nhóm cũng thấy rằng điểm retrieval /10 chưa đủ; cần nhìn trực tiếp nội dung chunk để biết nó có thật sự chứa câu trả lời hay chỉ đúng `doc_id`.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> Nhóm sẽ thiết kế thêm ít nhất một cặp tài liệu có cùng chủ đề và từ vựng nhưng khác `audience`, ví dụ cùng là quyền lợi nhưng một file cho sinh viên và một file cho nhân viên. Khi đó câu hỏi không nêu đối tượng sẽ cho thấy rõ khác biệt giữa có filter và không filter. Nhóm cũng sẽ làm sạch một số bảng dài hơn để chunk không chứa quá nhiều số liệu không liên quan trong cùng một đoạn.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | 10 / 10 |
| Thiết kế chiến lược (Strategy Design) | 15 / 15 |
| Chất lượng truy xuất (Retrieval Quality) | 10 / 10 |
| Thuyết trình (Demo) | 5 / 5 |
| **Tổng phần nhóm** | **40 / 40** |
