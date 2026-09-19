from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from src import Document, EmbeddingStore, FixedSizeChunker, RecursiveChunker, SentenceChunker


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


DATA_DIR = Path("data/rmit_data_ver01")

BENCHMARK_QUERIES = [
    {
        "id": 1,
        "query": "Học phí tại RMIT được thanh toán theo cách nào?",
        "gold_answer": "Học phí được thanh toán theo từng học kỳ, dựa trên số môn sinh viên học trong từng học kỳ.",
        "gold_doc": "chinh-sach-hoc-phi-rmit",
        "filter": {"audience": "student"},
    },
    {
        "id": 2,
        "query": "Sinh viên có người thân đang học hoặc đã tốt nghiệp tại RMIT được chiết khấu học phí bao nhiêu?",
        "gold_answer": "Sinh viên có anh chị em ruột, vợ chồng, cha mẹ hoặc con đang học hoặc đã tốt nghiệp tại RMIT Việt Nam được chiết khấu 5% học phí khi bắt đầu nhập học trong năm 2026.",
        "gold_doc": "chinh-sach-hoc-phi-dac-biet",
        "filter": {"audience": "student"},
    },
    {
        "id": 3,
        "query": "RMIT đã trao học bổng tổng giá trị bao nhiêu và cho hơn bao nhiêu bạn trẻ?",
        "gold_answer": "RMIT đã trao các học bổng với tổng giá trị hơn 613 tỉ đồng cho hơn 1.900 bạn trẻ.",
        "gold_doc": "hoc-bong-rmit-vietnam",
        "filter": {"audience": "student"},
    },
    {
        "id": 4,
        "query": "Nhân viên RMIT có những ngày nghỉ phép và nghỉ ốm có lương nào?",
        "gold_answer": "Nhân viên có 20 ngày nghỉ phép có lương, 10 ngày nghỉ ốm có lương, 05 ngày nghỉ lễ Giáng Sinh có lương mỗi năm và một số ngày nghỉ bổ sung theo điều kiện.",
        "gold_doc": "phuc-loi-nhan-vien-rmit",
        "filter": {"audience": "staff"},
    },
    {
        "id": 5,
        "query": "Sinh viên hiện tại hoặc cựu sinh viên RMIT gửi khiếu nại bằng cách nào?",
        "gold_answer": "Sinh viên hiện tại hoặc cựu sinh viên RMIT có thể gửi khiếu nại đến cổng thông tin khiếu nại trên trang dành cho sinh viên RMIT.",
        "gold_doc": "quy-trinh-khieu-nai-rmit",
        "filter": None,
    },
]


def tokenize(text: str) -> list[str]:
    return re.findall(r"\w+", text.lower(), flags=re.UNICODE)


class LexicalEmbedder:
    """Small deterministic embedder for CP5 benchmark without external APIs."""

    def __init__(self, texts: list[str]) -> None:
        tokens = sorted({token for text in texts for token in tokenize(text)})
        self.vocab = {token: index for index, token in enumerate(tokens)}

    def __call__(self, text: str) -> list[float]:
        vector = [0.0] * len(self.vocab)
        for token in tokenize(text):
            index = self.vocab.get(token)
            if index is not None:
                vector[index] += 1.0

        norm = sum(value * value for value in vector) ** 0.5
        if norm == 0:
            return vector
        return [value / norm for value in vector]


class HeadingChunker:
    """Split Markdown by headings, falling back to RecursiveChunker for long sections."""

    def __init__(self, chunk_size: int = 700) -> None:
        self.chunk_size = chunk_size
        self.fallback = RecursiveChunker(chunk_size=chunk_size)

    def chunk(self, text: str) -> list[str]:
        text = text.strip()
        if not text:
            return []

        sections = [section.strip() for section in re.split(r"(?=^#{1,3}\s+)", text, flags=re.MULTILINE) if section.strip()]
        chunks: list[str] = []
        for section in sections:
            if len(section) <= self.chunk_size:
                chunks.append(section)
                continue

            heading_match = re.match(r"^(#{1,3}\s+.+)$", section, flags=re.MULTILINE)
            heading = heading_match.group(1).strip() if heading_match else ""
            for sub_chunk in self.fallback.chunk(section):
                if heading and not sub_chunk.startswith(heading):
                    chunks.append(f"{heading}\n{sub_chunk}")
                else:
                    chunks.append(sub_chunk)
        return chunks


def clean_value(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1].strip()
    return value


def parse_markdown(path: Path) -> tuple[dict[str, str], str]:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^\s*---\s*\n(.*?)\n---\s*\n?(.*)$", text, re.DOTALL)
    if not match:
        return {"doc_id": path.stem, "title": path.stem}, text

    frontmatter, body = match.groups()
    metadata: dict[str, str] = {}
    for line in frontmatter.splitlines():
        field_match = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if field_match:
            metadata[field_match.group(1)] = clean_value(field_match.group(2))
    metadata.setdefault("doc_id", path.stem)
    metadata.setdefault("title", path.stem)
    return metadata, body.strip()


def make_chunker(strategy: str, chunk_size: int):
    if strategy == "fixed_size":
        return FixedSizeChunker(chunk_size=chunk_size, overlap=80)
    if strategy == "by_sentences":
        return SentenceChunker(max_sentences_per_chunk=4)
    if strategy == "recursive":
        return RecursiveChunker(chunk_size=chunk_size)
    if strategy == "heading_section":
        return HeadingChunker(chunk_size=chunk_size)
    raise ValueError(f"Unknown strategy: {strategy}")


def build_documents(data_dir: Path, chunk_size: int, strategy: str) -> list[Document]:
    chunker = make_chunker(strategy, chunk_size)
    documents: list[Document] = []

    for path in sorted(data_dir.glob("*.md")):
        metadata, content = parse_markdown(path)
        chunks = chunker.chunk(content)
        for index, chunk in enumerate(chunks):
            chunk_metadata = {
                **metadata,
                "doc_id": metadata["doc_id"],
                "chunk_index": str(index),
                "source_file": str(path),
            }
            documents.append(
                Document(
                    id=f"{metadata['doc_id']}#{index}",
                    content=chunk,
                    metadata=chunk_metadata,
                )
            )
    return documents


def format_result(result: dict, rank: int, gold_doc: str) -> str:
    metadata = result.get("metadata", {})
    doc_id = metadata.get("doc_id", "")
    chunk_index = metadata.get("chunk_index", "?")
    marker = "GOLD" if doc_id == gold_doc else "----"
    preview = " ".join(result.get("content", "").split())[:220]
    return (
        f"  {rank}. score={result['score']:.4f} doc_id={doc_id} "
        f"chunk={chunk_index} {marker}\n"
        f"     {preview}"
    )


def score_results(results: list[dict], gold_doc: str) -> int:
    for index, result in enumerate(results):
        if result.get("metadata", {}).get("doc_id") == gold_doc:
            return 2 if index == 0 else 1
    return 0


def run_single_strategy(data_dir: Path, chunk_size: int, top_k: int, strategy: str) -> tuple[str, int]:
    documents = build_documents(data_dir, chunk_size, strategy)
    embedder = LexicalEmbedder(
        [doc.content for doc in documents]
        + [item["query"] for item in BENCHMARK_QUERIES]
        + [item["gold_answer"] for item in BENCHMARK_QUERIES]
    )
    store = EmbeddingStore(collection_name=f"rmit_policy_benchmark_{strategy}", embedding_fn=embedder)
    store.add_documents(documents)

    lines = [
        f"=== Benchmark: {strategy} ===",
        f"Corpus: {data_dir}",
        f"Chunker strategy: {strategy}",
        "Embedder: LexicalEmbedder(term-frequency cosine, local)",
        f"Loaded chunks: {store.get_collection_size()}",
        "",
    ]

    total_score = 0
    for item in BENCHMARK_QUERIES:
        metadata_filter = item["filter"]
        if metadata_filter:
            results = store.search_with_filter(item["query"], top_k=top_k, metadata_filter=metadata_filter)
        else:
            results = store.search(item["query"], top_k=top_k)
        question_score = score_results(results, item["gold_doc"])
        total_score += question_score

        lines.extend(
            [
                f"Q{item['id']}: {item['query']}",
                f"Gold answer: {item['gold_answer']}",
                f"Gold doc: {item['gold_doc']}",
                f"Metadata filter: {metadata_filter or 'None'}",
                f"Score: {question_score}/2",
                "Top results:",
            ]
        )
        for rank, result in enumerate(results, start=1):
            lines.append(format_result(result, rank, item["gold_doc"]))
        lines.append("")

    lines.append(f"Strategy score: {total_score}/10")
    return "\n".join(lines), total_score


def run_filter_ablation(data_dir: Path, chunk_size: int, top_k: int, strategy: str) -> list[str]:
    documents = build_documents(data_dir, chunk_size, strategy)
    embedder = LexicalEmbedder([doc.content for doc in documents] + [item["query"] for item in BENCHMARK_QUERIES])
    store = EmbeddingStore(collection_name=f"rmit_policy_filter_ablation_{strategy}", embedding_fn=embedder)
    store.add_documents(documents)

    lines = [
        "",
        "=== Metadata Filter A/B Check ===",
        f"Strategy: {strategy}",
    ]
    for item in BENCHMARK_QUERIES:
        if not item["filter"]:
            continue
        filtered = store.search_with_filter(item["query"], top_k=top_k, metadata_filter=item["filter"])
        unfiltered = store.search(item["query"], top_k=top_k)
        filtered_docs = [result["metadata"].get("doc_id") for result in filtered]
        unfiltered_docs = [result["metadata"].get("doc_id") for result in unfiltered]
        lines.append(f"Q{item['id']} filter={item['filter']}")
        lines.append(f"  with filter   : {filtered_docs}")
        lines.append(f"  without filter: {unfiltered_docs}")
    return lines


def run_benchmark(data_dir: Path, chunk_size: int, top_k: int) -> str:
    strategies = ["fixed_size", "by_sentences", "recursive", "heading_section"]
    outputs: list[str] = ["=== CP6 Benchmark and Strategy Comparison ==="]
    summary: list[tuple[str, int]] = []

    for strategy in strategies:
        strategy_output, score = run_single_strategy(data_dir, chunk_size, top_k, strategy)
        outputs.append(strategy_output)
        summary.append((strategy, score))

    outputs.append("")
    outputs.append("=== Strategy Summary ===")
    for strategy, score in summary:
        outputs.append(f"{strategy}: {score}/10")

    outputs.extend(run_filter_ablation(data_dir, chunk_size, top_k, "recursive"))
    return "\n\n".join(outputs)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run CP5 retrieval benchmark.")
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR)
    parser.add_argument("--chunk-size", type=int, default=700)
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--output", type=Path, default=Path("ket_qua_benchmark.txt"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.data_dir.exists():
        print(f"Data directory not found: {args.data_dir}", file=sys.stderr)
        return 1

    output = run_benchmark(args.data_dir, args.chunk_size, args.top_k)
    print(output)
    args.output.write_text(output + "\n", encoding="utf-8")
    print(f"Saved benchmark output to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
