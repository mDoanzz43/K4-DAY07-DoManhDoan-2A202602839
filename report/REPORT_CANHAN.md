# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Đỗ Mạnh Đoan
**Nhóm:** C3D
**Ngày:** 19/9/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Cosine similarity cao có nghĩa là 2 vector embedding có hướng gần giống nhau, tức là chúng có *ngữ nghĩa gần giống nhau* hoặc ý nghĩa ngữ nghĩa tương đồng, dù có thể sử dụng các từ ngữ khác nhau.
**Ví dụ có độ tương tự CAO:**
- Câu A: “Học sinh cần chuẩn bị gì để học tại RMIT?”
- Câu B: “Những gì sinh viên cần chuẩn bị khi vào học tại RMIT?”
- Tại sao tương đồng: Cả hai câu đều hỏi về việc học tập tại RMIT, chỉ khác ở cách dùng từ và cấu trúc câu.

**Ví dụ có độ tương tự THẤP:**
- Câu A: “Học sinh cần chuẩn bị gì để học tại RMIT?”
- Câu B: “Học bổng dành cho sinh viên tại RMIT là gì?”
- Tại sao khác: Câu A hỏi về việc chuẩn bị, câu B hỏi về học bổng.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Cosin Similarity phù hợp với text embedding vì nó quan tâm chủ yếu đến *hướng biểu diễn ngữ nghĩa*, ít bị ảnh hưởng bởi độ lớn vector theo công thức toán học của nó. Euclid thì đo *khoảng cách tuyệt đối* nên có thể coi hai vector cùng hướng nhưng khác độ dài là xa nhau, không phản ánh đúng ngữ nghĩa. 
### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> Số chunks = [ (tổng số ký tự - overlap) / (chunk_size - overlap)]  (làm tròn lên)
 
> *Đáp án:* [(10000-50)/(500-50)] = [9950/450]  = [22.11] => làm tròn lên thành 23 chunks

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Khi overlap tăng lên, bước nhảy giữa hai chunk giảm từ `450` xuống `400`, nên số lượng chunk tăng từ 23 lên 25:
chunks = `ceil((10000 - 100) / (500 - 100)) = ceil(9900 / 400) = 25`. Overlap lớn hơn giúp giữ ngữ cảnh ở ranh giới giữa hai chunk, đặc biệt khi câu trả lời nằm đúng vùng bị cắt, nhưng đổi lại sẽ tạo thêm chunk và tốn thêm chi phí lưu trữ/tìm kiếm.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Tôi strip văn bản đầu vào trước, nếu chuỗi rỗng thì trả về `[]` để tránh tạo chunk rỗng. Sau đó tôi dùng regex `(?<=[.!?])(?:\s+|\n+)` để tách tại khoảng trắng hoặc xuống dòng đứng sau dấu kết thúc câu `.`, `!`, `?`, nhờ vậy dấu câu vẫn được giữ lại trong câu. Cuối cùng tôi gom tối đa `max_sentences_per_chunk` câu vào một chunk và strip lại từng chunk để loại bỏ khoảng trắng thừa.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Tôi triển khai chia nhỏ đệ quy theo thứ tự separator ưu tiên: đoạn văn, dòng, câu, khoảng trắng, rồi fallback cắt cứng theo `chunk_size`. Base case là văn bản rỗng trả về `[]`, văn bản đã ngắn hơn hoặc bằng `chunk_size` trả về một chunk, hoặc khi hết separator thì cắt trực tiếp theo kích thước cố định. Sau khi `_split` tạo các mảnh nhỏ, tôi dùng `_merge_splits` để ghép các mảnh liền kề lại gần `chunk_size` nhất có thể mà không vượt quá giới hạn.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Dùng in-memory store, mỗi `Document` được chuyển thành một record gồm `id`, `content`, `metadata`, `embedding` và `index`. Trong `_make_record`, nếu metadata chưa có `doc_id` thì gán mặc định bằng `doc.id` để các hàm xóa và truy vết nguồn hoạt động ổn định. Khi `search`, embed câu hỏi, tính dot product giữa query embedding và embedding của từng record, rồi sắp xếp giảm dần theo `score` để lấy top-k kết quả.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> Với `search_with_filter`, lọc metadata trước rồi mới chạy similarity search trên tập ứng viên đã lọc; cách này tránh việc top-k bị chiếm bởi tài liệu sai metadata. Nếu không truyền filter, hàm gọi lại `search` thường để đảm bảo kết quả nhất quán. Với `delete_document`, tạo lại danh sách `_store` và loại bỏ mọi record có `metadata["doc_id"]` trùng với `doc_id` cần xóa, sau đó trả về `True` nếu số lượng record giảm.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Trong `answer`, tôi truy xuất top-k chunk liên quan từ `EmbeddingStore` trước, nếu không có kết quả thì trả thông báo không tìm thấy ngữ cảnh. Với mỗi chunk truy xuất được, tôi dựng một block ngữ cảnh có đánh số `[1]`, kèm `source_url` hoặc `doc_id` để câu trả lời có thể truy vết nguồn. Prompt yêu cầu mô hình chỉ trả lời dựa trên context được cung cấp và nói rõ nếu context không chứa đáp án, sau đó mới gọi `llm_fn(prompt)`.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
============================= test session starts =============================
platform win32 -- Python 3.10.0, pytest-9.1.1
collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED
...
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED

============================= 42 passed in 0.09s ==============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Sinh viên nộp học phí theo từng học kỳ. | Học phí được thanh toán theo từng học kỳ. | cao | 0.8418 | Có |
| 2 | RMIT trao nhiều học bổng cho sinh viên. | Trường có các suất học bổng dành cho người học. | cao | 0.6739 | Tương đối |
| 3 | Nhân viên có ngày nghỉ phép có lương. | Cán bộ được hưởng các ngày nghỉ có lương. | cao | 0.8151 | Có |
| 4 | Học phí được thanh toán trực tuyến. | Thư viện có không gian học tập yên tĩnh. | thấp | 0.6821 | Không |
| 5 | Sinh viên gửi khiếu nại qua cổng thông tin. | Nhân viên được hỗ trợ bảo hiểm và phúc lợi. | thấp | 0.6658 | Tương đối |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Kết quả được chạy thực tế bằng `GeminiEmbedder` (`gemini-embedding-001`). Bất ngờ nhất là cặp 4 và cặp 5 tuy khác chủ đề chính nhưng vẫn có điểm khoảng 0.66-0.68, cao hơn mức tôi kỳ vọng cho nhóm "thấp". Điều này cho thấy embedding thật không chỉ bắt từ khóa trực tiếp mà còn nhận ra các câu đều thuộc cùng miền dịch vụ/chính sách đại học, nên khi đánh giá retrieval cần xem cả nội dung chunk chứ không chỉ nhìn score.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Học phí tại RMIT được thanh toán theo cách nào? | `chinh-sach-hoc-phi-rmit#10`: liệt kê các phương thức thanh toán như trực tuyến, ngân hàng trực tuyến, thẻ Mastercard/Visa và chuyển khoản. | 0.8311 | Có | Học phí có thể thanh toán trực tuyến, qua ngân hàng trực tuyến, bằng thẻ tại quầy thu ngân hoặc chuyển khoản; tài liệu cũng nêu học phí được tính theo từng học kỳ. |
| 2 | Sinh viên có người thân đang học hoặc đã tốt nghiệp tại RMIT được chiết khấu học phí bao nhiêu? | `chinh-sach-hoc-phi-dac-biet#1`: nói về trường hợp người thân đã hoàn thành/chưa hoàn thành chương trình học tại RMIT và mức chiết khấu học phí. | 0.8381 | Có | Sinh viên thuộc diện có người thân học hoặc đã tốt nghiệp tại RMIT được chiết khấu 5% học phí khi bắt đầu nhập học trong năm 2026. |
| 3 | RMIT đã trao học bổng tổng giá trị bao nhiêu và cho hơn bao nhiêu bạn trẻ? | `hoc-bong-rmit-vietnam#0`: nêu RMIT đã trao học bổng tổng giá trị hơn 613 tỉ đồng cho hơn 1.900 bạn trẻ. | 0.7990 | Có | RMIT đã trao học bổng tổng trị giá hơn 613 tỉ đồng cho hơn 1.900 bạn trẻ. |
| 4 | Nhân viên RMIT có những ngày nghỉ phép và nghỉ ốm có lương nào? | `phuc-loi-nhan-vien-rmit#0`: giới thiệu tổng quan phúc lợi nhân viên; chunk chứa câu trả lời chính xác nằm ở top-2 là `phuc-loi-nhan-vien-rmit#6`. | 0.8447 | Một phần | Dựa trên top-2, nhân viên có 20 ngày nghỉ phép có lương, 10 ngày nghỉ ốm có lương và 05 ngày nghỉ lễ Giáng Sinh có lương mỗi năm. |
| 5 | Sinh viên hiện tại hoặc cựu sinh viên RMIT gửi khiếu nại bằng cách nào? | `quy-trinh-khieu-nai-rmit#1`: chứa phần sinh viên hiện tại/cựu sinh viên và cổng thông tin khiếu nại dành cho sinh viên RMIT. | 0.7762 | Có | Sinh viên hiện tại hoặc cựu sinh viên có thể gửi khiếu nại qua cổng thông tin khiếu nại trên trang dành cho sinh viên RMIT. |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 5 / 5

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> Khi chạy bằng Gemini embedding thật, tôi thấy score cao chưa chắc đồng nghĩa top-1 chứa đúng câu trả lời chi tiết. Ví dụ câu hỏi về ngày nghỉ của nhân viên lấy đúng tài liệu ở top-1 nhưng đáp án cụ thể lại nằm ở top-2. Điều hay nhất tôi học được là phải đánh giá ở cấp chunk và nội dung câu trả lời, không chỉ ở cấp `doc_id` hay similarity score.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 10 / 10 |
| **Tổng phần cá nhân** | **60 / 60** |
