"""Science AI Lab — 벡터 저장/검색 (numpy 코사인, sqlite-vss 대체)

임베딩을 float32 BLOB로 저장하고, 검색 시 메모리에 올려 코사인 유사도 brute-force.
교실 데이터 규모(수천 건)에서 충분히 빠르고 aarch64 빌드 의존성이 없다.
인터페이스는 sqlite-vss로 교체 가능하게 단순 유지.
"""

from __future__ import annotations

import struct
from datetime import datetime

import numpy as np

from .db import get_conn


def _pack(vec: list[float]) -> bytes:
    return struct.pack(f"{len(vec)}f", *vec)


def _unpack(blob: bytes) -> np.ndarray:
    n = len(blob) // 4
    return np.array(struct.unpack(f"{n}f", blob), dtype=np.float32)


def add(source_type: str, source_id: str, content: str, embedding: list[float],
        grade=None, unit_id=None, experiment_id=None, answer=None, curated_status="pending") -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO vector_embeddings (source_type, source_id, grade, unit_id, experiment_id, content, answer, embedding, curated_status, created_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?)",
            (source_type, source_id, grade, unit_id, experiment_id, content, answer,
             _pack(embedding), curated_status, datetime.now().isoformat(timespec="seconds")),
        )


def search(query_vec: list[float], top_k: int = 3, grade=None, unit_id=None) -> list[dict]:
    """코사인 유사도 top_k. 같은 학년/단원 가중, approved ×2, 최신 가중."""
    q = np.array(query_vec, dtype=np.float32)
    qn = np.linalg.norm(q) or 1.0
    rows = []
    with get_conn() as conn:
        for r in conn.execute(
            "SELECT id, content, answer, grade, unit_id, experiment_id, curated_status, created_at, embedding "
            "FROM vector_embeddings WHERE curated_status != 'rejected'"
        ):
            v = _unpack(r["embedding"])
            vn = np.linalg.norm(v) or 1.0
            sim = float(np.dot(q, v) / (qn * vn))
            # 가중치
            w = 1.0
            if grade is not None and r["grade"] == grade:
                w *= 1.3
            if unit_id and r["unit_id"] == unit_id:
                w *= 1.3
            if r["curated_status"] == "approved":
                w *= 2.0
            rows.append({
                "id": r["id"], "content": r["content"], "answer": r["answer"],
                "grade": r["grade"], "unit_id": r["unit_id"],
                "curated_status": r["curated_status"], "score": sim * w, "raw_sim": sim,
            })
    rows.sort(key=lambda x: x["score"], reverse=True)
    return rows[:top_k]


def count() -> int:
    with get_conn() as conn:
        return conn.execute("SELECT COUNT(*) n FROM vector_embeddings").fetchone()["n"]
