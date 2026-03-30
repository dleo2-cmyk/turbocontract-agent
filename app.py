# -*- coding: utf-8 -*-
"""
TurboContract — Streamlit веб-интерфейс
"""

import os
import sys
import tempfile
from pathlib import Path

import streamlit as st

# ── Настройка страницы ──────────────────────────────────────────────────────
st.set_page_config(
    page_title="TurboContract — Анализ сложности",
    page_icon="📄",
    layout="wide",
)

# ── API-ключ: из Streamlit Secrets (продакшн) или переменной среды (локально) ──
try:
    api_key = st.secrets.get("OPENROUTER_API_KEY", "")
except Exception:
    api_key = ""
if not api_key:
    api_key = os.environ.get("OPENROUTER_API_KEY", "")

# Пробрасываем ключ в модуль до импорта
os.environ["OPENROUTER_API_KEY"] = api_key

# Импортируем логику агента
sys.path.insert(0, str(Path(__file__).parent))
from agent_prototype import (
    extract_docx,
    group_documents,
    analyse_group,
    OPENROUTER_API_KEY as _DEFAULT_KEY,
)
from openai import OpenAI

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# ── Заголовок ───────────────────────────────────────────────────────────────
st.title("📄 TurboContract — Анализ сложности шаблонов")
st.caption("Загрузи один или несколько .docx файлов договора — агент определит метрики сложности.")

st.divider()

# ── Загрузка файлов ─────────────────────────────────────────────────────────
uploaded_files = st.file_uploader(
    "Загрузи .docx файл(ы)",
    type=["docx"],
    accept_multiple_files=True,
    help="Можно загрузить несколько вариантов одного договора — агент сгруппирует их автоматически.",
)

run_btn = st.button("🔍 Анализировать", type="primary", disabled=not uploaded_files)

# ── Анализ ──────────────────────────────────────────────────────────────────
if run_btn and uploaded_files:

    # Проверяем ключ
    effective_key = api_key or _DEFAULT_KEY
    if not effective_key:
        st.error("❌ API-ключ OpenRouter не найден. Добавь OPENROUTER_API_KEY в Streamlit Secrets.")
        st.stop()

    client = OpenAI(api_key=effective_key, base_url=OPENROUTER_BASE_URL)

    # Сохраняем файлы во временную папку
    with tempfile.TemporaryDirectory() as tmp_dir:
        docs = []
        with st.spinner("Читаем документы..."):
            for uf in uploaded_files:
                path = Path(tmp_dir) / uf.name
                path.write_bytes(uf.read())
                try:
                    info = extract_docx(str(path))
                    docs.append(info)
                except Exception as e:
                    st.warning(f"⚠ Не удалось прочитать {uf.name}: {e}")

        if not docs:
            st.error("Не удалось прочитать ни одного документа.")
            st.stop()

        # Группируем
        groups = group_documents(docs)

        # Анализируем каждую группу
        all_results = []
        progress = st.progress(0, text="Анализируем с помощью LLM...")
        for i, g in enumerate(groups):
            result = analyse_group(g, client)
            if result:
                all_results.append(result)
            progress.progress((i + 1) / len(groups), text=f"Обработано {i+1} из {len(groups)}")
        progress.empty()

    if not all_results:
        st.error("Анализ не дал результатов.")
        st.stop()

    # ── Вывод результатов ───────────────────────────────────────────────────
    for res in all_results:
        st.divider()

        # Заголовок с типом документа
        doc_label = res.doc_type if res.doc_type else res.doc_name
        st.subheader(f"📋 {doc_label}")

        # ── Метрики ─────────────────────────────────────────────────────────
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        col1.metric("Переменных", res.variables)
        col2.metric("Вариативных блоков", res.variative_blocks)
        col3.metric("Расчётных полей", res.calculated_fields)
        col4.metric("Таблиц", res.tables)
        col5.metric("Приложений", res.appendices)
        col6.metric("Страниц", res.pages)

        # Сложность и уверенность
        complexity_color = {
            "Высокая": "🔴",
            "Средняя": "🟡",
            "Низкая": "🟢",
        }.get(res.complexity, "⚪")

        conf_pct = int(res.confidence * 100)
        st.markdown(
            f"**Сложность:** {complexity_color} **{res.complexity}** &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"**Уверенность агента:** {conf_pct}%"
        )

        if res.description:
            st.info(res.description)

        # ── Детализация ─────────────────────────────────────────────────────
        st.markdown("#### Детализация")

        col_left, col_right = st.columns(2)

        with col_left:
            if res.found_variables:
                with st.expander(f"📝 Переменные ({len(res.found_variables)})", expanded=True):
                    for i, v in enumerate(res.found_variables, 1):
                        st.markdown(f"{i}. {v}")

            if res.found_tables:
                with st.expander(f"📊 Таблицы ({len(res.found_tables)})", expanded=True):
                    for i, t in enumerate(res.found_tables, 1):
                        st.markdown(f"{i}. {t}")

        with col_right:
            if res.found_blocks:
                with st.expander(f"🔀 Вариативные блоки ({len(res.found_blocks)})", expanded=True):
                    for i, b in enumerate(res.found_blocks, 1):
                        st.markdown(f"{i}. {b}")

            if res.found_calculated:
                with st.expander(f"🧮 Расчётные поля ({len(res.found_calculated)})", expanded=True):
                    for i, c in enumerate(res.found_calculated, 1):
                        st.markdown(f"{i}. {c}")

        # Заметки агента
        notes = res.raw_llm.get("notes", "")
        if notes:
            with st.expander("💬 Заметки агента (что требует проверки)"):
                st.write(notes)

    st.success("✅ Анализ завершён")
