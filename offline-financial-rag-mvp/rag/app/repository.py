from __future__ import annotations

import json
import uuid
from typing import Dict, List
from .db import get_conn


def vector_literal(values: List[float]) -> str:
    return '[' + ','.join(f'{float(v):.8f}' for v in values) + ']'


def insert_document_with_chunks(document: Dict, embeddings: List[List[float]]) -> str:
    doc_id = str(uuid.uuid4())
    chunks = document['chunks']
    if len(chunks) != len(embeddings):
        raise ValueError('chunks and embeddings length mismatch')

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO documents (id, file_name, file_path, title, company_name, fiscal_year, checksum)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    doc_id,
                    document['file_name'],
                    document['file_path'],
                    document['title'],
                    document['company_name'],
                    document['fiscal_year'],
                    document['checksum'],
                ),
            )
            for idx, (chunk, emb) in enumerate(zip(chunks, embeddings)):
                chunk_id = str(uuid.uuid4())
                cur.execute(
                    """
                    INSERT INTO chunks (
                      id, document_id, chunk_index, page_no, section, chunk_text, chunk_type, table_markdown, metadata, embedding
                    ) VALUES (
                      %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s::vector
                    )
                    """,
                    (
                        chunk_id,
                        doc_id,
                        idx,
                        chunk.get('page_no'),
                        chunk.get('section'),
                        chunk['chunk_text'],
                        chunk.get('chunk_type', 'text'),
                        chunk.get('table_markdown'),
                        json.dumps(chunk.get('metadata', {})),
                        vector_literal(emb),
                    ),
                )
    return doc_id


def search_chunks(query_embedding: List[float], limit: int = 6):
    qv = vector_literal(query_embedding)
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT c.id, c.document_id, c.chunk_index, c.page_no, c.section, c.chunk_text, c.chunk_type,
                       c.table_markdown, c.metadata,
                       d.file_name,
                       1 - (c.embedding <=> %s::vector) AS similarity
                FROM chunks c
                JOIN documents d ON d.id = c.document_id
                ORDER BY c.embedding <=> %s::vector
                LIMIT %s
                """,
                (qv, qv, limit),
            )
            return cur.fetchall()
