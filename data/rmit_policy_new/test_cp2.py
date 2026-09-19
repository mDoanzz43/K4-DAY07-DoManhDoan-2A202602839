import argparse
import csv
import re
import sys
from pathlib import Path


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


REQUIRED_METADATA = [
    "doc_id",
    "title",
    "source_url",
    "retrieved_at",
    "document_version",
    "audience",
]

ALLOWED_AUDIENCES = {"student", "faculty", "staff", "all"}


def clean_value(value: str | None) -> str:
    """Loại bỏ khoảng trắng và dấu nháy quanh giá trị frontmatter."""
    if value is None:
        return ""

    value = value.strip()

    if len(value) >= 2:
        if (value[0] == value[-1]) and value[0] in {'"', "'"}:
            value = value[1:-1].strip()

    return value


def read_frontmatter(path: Path) -> dict[str, str]:
    """Đọc YAML frontmatter đơn giản, không cần cài PyYAML."""
    content = path.read_text(encoding="utf-8")

    match = re.match(r"^\s*---\s*\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return {}

    frontmatter_text = match.group(1)
    metadata = {}

    for line in frontmatter_text.splitlines():
        field_match = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)

        if field_match:
            key = field_match.group(1).strip()
            value = clean_value(field_match.group(2))
            metadata[key] = value

    return metadata


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Kiểm tra corpus theo yêu cầu CHECKPOINT 2."
    )
    parser.add_argument(
        "data_dir",
        nargs="?",
        default="data/rmit_policy_new",
        help="Thư mục corpus, mặc định: data/rmit_policy_new",
    )
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    sources_path = data_dir / "sources.csv"

    if not data_dir.exists():
        print(f"[FAIL] Không tìm thấy thư mục: {data_dir}")
        return 1

    if not sources_path.exists():
        print(f"[FAIL] Không tìm thấy file: {sources_path}")
        return 1

    markdown_files = sorted(data_dir.glob("*.md"))

    with sources_path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as csv_file:
        source_rows = list(csv.DictReader(csv_file))

    document_ids = []
    audiences: dict[str, int] = {}
    has_error = False

    print(f"\nKiểm tra corpus: {data_dir}")
    print("=" * 75)

    for path in markdown_files:
        metadata = read_frontmatter(path)
        errors = []

        missing_fields = [
            field
            for field in REQUIRED_METADATA
            if not metadata.get(field)
        ]

        if missing_fields:
            errors.append(f"thiếu: {', '.join(missing_fields)}")

        doc_id = metadata.get("doc_id", "")
        audience = metadata.get("audience", "")

        if doc_id != path.stem:
            errors.append(
                f"doc_id='{doc_id}' không khớp tên file '{path.stem}'"
            )

        if audience not in ALLOWED_AUDIENCES:
            errors.append(
                f"audience='{audience}' không hợp lệ"
            )

        if doc_id:
            document_ids.append(doc_id)

        if audience:
            audiences[audience] = audiences.get(audience, 0) + 1

        if errors:
            has_error = True
            status = "FAIL - " + "; ".join(errors)
        else:
            status = "OK"

        print(f"{path.name:45} {status}")

    print("=" * 75)

    # Kiểm tra số lượng tài liệu
    file_count_ok = 5 <= len(markdown_files) <= 10
    print(
        f"Số file Markdown : {len(markdown_files)} "
        f"({'OK' if file_count_ok else 'FAIL - cần 5 đến 10 file'})"
    )

    if not file_count_ok:
        has_error = True

    # Kiểm tra doc_id trùng nhau
    duplicate_ids = sorted({
        doc_id
        for doc_id in document_ids
        if document_ids.count(doc_id) > 1
    })

    if duplicate_ids:
        print(f"Doc ID duy nhất   : FAIL - bị trùng {duplicate_ids}")
        has_error = True
    else:
        print("Doc ID duy nhất   : OK")

    # Kiểm tra sources.csv
    csv_ids = [
        clean_value(row.get("doc_id"))
        for row in source_rows
        if clean_value(row.get("doc_id"))
    ]

    markdown_id_set = set(document_ids)
    csv_id_set = set(csv_ids)

    missing_in_csv = sorted(markdown_id_set - csv_id_set)
    extra_in_csv = sorted(csv_id_set - markdown_id_set)

    csv_matches = (
        sorted(csv_ids) == sorted(document_ids)
        and len(csv_ids) == len(document_ids)
    )

    if csv_matches:
        print("sources.csv       : OK - khớp 1-1")
    else:
        print("sources.csv       : FAIL - không khớp")
        has_error = True

        if missing_in_csv:
            print(f"  Thiếu trong CSV : {missing_in_csv}")

        if extra_in_csv:
            print(f"  Thừa trong CSV  : {extra_in_csv}")

    # Kiểm tra audience
    audience_ok = len(audiences) >= 2

    print(f"Audience          : {audiences}")

    if audience_ok:
        print("Độ đa dạng audience: OK")
    else:
        print("Độ đa dạng audience: FAIL - cần ít nhất 2 giá trị khác nhau")
        has_error = True

    print("=" * 75)

    if has_error:
        print("KẾT QUẢ CP2: FAIL")
        return 1

    print("KẾT QUẢ CP2: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
