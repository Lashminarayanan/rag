from __future__ import annotations

import json
import os
from pathlib import Path
import requests
import streamlit as st
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / '.env')
BACKEND_URL = os.getenv('STREAMLIT_BACKEND_URL', 'http://localhost:8080')

st.set_page_config(page_title='Offline Financial RAG MVP', layout='wide')
st.title('Offline Financial RAG MVP')
st.caption('Research annual reports offline with citations and streaming answers')

if 'sources' not in st.session_state:
    st.session_state.sources = []
if 'answer' not in st.session_state:
    st.session_state.answer = ''
if 'plan' not in st.session_state:
    st.session_state.plan = []
if 'warnings' not in st.session_state:
    st.session_state.warnings = []

query = st.text_area(
    'Research query',
    value='Compare revenue trend, margin movement, and top risks mentioned in the annual report. Include evidence citations and key extracted metrics.',
    height=100,
)

left, right = st.columns([1.5, 1])

with left:
    run = st.button('Run query', type='primary', use_container_width=True)
    answer_container = st.empty()
    plan_container = st.container()

with right:
    st.subheader('Evidence')
    evidence_container = st.container()


def stream_query(q: str):
    st.session_state.answer = ''
    st.session_state.sources = []
    st.session_state.plan = []
    st.session_state.warnings = []
    with requests.post(f'{BACKEND_URL}/api/query/stream', json={'query': q}, stream=True, timeout=600) as response:
        response.raise_for_status()
        event_type = None
        for raw in response.iter_lines(decode_unicode=True):
            if not raw:
                continue
            if raw.startswith('event:'):
                event_type = raw.split(':', 1)[1].strip()
                continue
            if raw.startswith('data:'):
                payload = json.loads(raw.split(':', 1)[1].strip())
                yield event_type, payload


if run and query.strip():
    with st.spinner('Running offline research pipeline...'):
        for event_type, payload in stream_query(query.strip()):
            if event_type == 'plan':
                st.session_state.plan = payload.get('plan', [])
            elif event_type == 'sources':
                st.session_state.sources = payload.get('sources', [])
            elif event_type == 'token':
                st.session_state.answer += payload.get('token', '')
            elif event_type == 'final':
                st.session_state.answer = payload.get('answer', st.session_state.answer)
                st.session_state.warnings = payload.get('warnings', [])

            answer_container.markdown(st.session_state.answer or '_Waiting for answer stream..._')
            with plan_container:
                if st.session_state.plan:
                    st.subheader('Plan')
                    for idx, step in enumerate(st.session_state.plan, start=1):
                        st.write(f'{idx}. {step}')
                if st.session_state.warnings:
                    st.warning('\n'.join(st.session_state.warnings))
            with evidence_container:
                if not st.session_state.sources:
                    st.info('Evidence will appear here')
                for src in st.session_state.sources:
                    with st.expander(f"{src.get('file_name', 'Document')} • page {src.get('page_no') or 'n/a'} • score {round(src.get('similarity', 0), 3)}"):
                        st.caption(src.get('section') or 'Unknown section')
                        st.write(src.get('chunk_text', ''))
                        if src.get('table_markdown'):
                            st.markdown(src['table_markdown'])

st.divider()
st.subheader('Usage notes')
st.markdown(
    """
- Start PostgreSQL + Ollama first.
- Run ingestion before querying.
- This MVP displays extracted source chunks and streamed answer text.
- Citations are expected in the answer as `[1]`, `[2]`, etc.
"""
)
