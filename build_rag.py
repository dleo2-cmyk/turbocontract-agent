"""Build full RAG database from 11 labeled .docx + .txt annotation files."""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from agent_prototype import extract_docx
from pathlib import Path

DOCS = [
    {
        "docx": r"C:\Users\dleo2\Downloads\Шаблоны 1\Лицензионный договор_СФТ_лицензиар.docx",
        "txt":  r"C:\Users\dleo2\Downloads\Шаблоны 1\Лицензионный договор_СФТ_лицензиар.txt",
        "doc_name": "Лицензионный договор (простой, лицензиар)",
        "doc_type": "Лицензионный договор",
        "keywords": ["лицензия", "лицензиар", "лицензиат", "программное обеспечение", "реестр", "гарантийная поддержка", "исключительные права"],
        "variables": 25, "variative_blocks": 0, "calculated_fields": 0,
        "tables": 1, "appendices": 3, "complexity": "Низкая",
    },
    {
        "docx": r"C:\Users\dleo2\Downloads\Шаблоны 1\NDA_Концерн_передающаясторона_КИ_от имени всей группы.docx",
        "txt":  r"C:\Users\dleo2\Downloads\Шаблоны 1\NDA_Концерн_передающаясторона_КИ_от имени всей группы.txt",
        "doc_name": "NDA (соглашение о конфиденциальности, Концерн)",
        "doc_type": "Соглашение о конфиденциальности",
        "keywords": ["конфиденциальность", "тайна", "раскрытие", "конфиденциальная информация", "концерн", "группа", "передающая сторона"],
        "variables": 46, "variative_blocks": 0, "calculated_fields": 0,
        "tables": 1, "appendices": 1, "complexity": "Низкая",
    },
    {
        "docx": r"C:\Users\dleo2\Downloads\Шаблоны 1\Договор оказания услуг (Разовый)V2.docx",
        "txt":  r"C:\Users\dleo2\Downloads\Шаблоны 1\Договор оказания услуг (Разовый)V2.txt",
        "doc_name": "Договор оказания услуг (разовый) V2",
        "doc_type": "Договор оказания услуг",
        "keywords": ["услуги", "оказание услуг", "исполнитель", "заказчик", "разовый", "акт сдачи", "соисполнитель", "неустойка"],
        "variables": 55, "variative_blocks": 3, "calculated_fields": 1,
        "tables": 0, "appendices": 1, "complexity": "Низкая",
    },
    {
        "docx": r"C:\Users\dleo2\Downloads\Шаблоны 1\Форма  договора аренды  нежилые помещения (сроком до года).docx",
        "txt":  r"C:\Users\dleo2\Downloads\Шаблоны 1\Форма  договора аренды  нежилые помещения (сроком до года).txt",
        "doc_name": "Договор аренды нежилых помещений (до года)",
        "doc_type": "Договор аренды",
        "keywords": ["аренда", "арендатор", "арендодатель", "помещение", "нежилое", "арендная плата", "пролонгация", "обеспечительный платеж", "инженерные системы"],
        "variables": 75, "variative_blocks": 7, "calculated_fields": 1,
        "tables": 3, "appendices": 3, "complexity": "Средняя",
    },
    {
        "docx": r"C:\Users\dleo2\Downloads\Шаблоны 1\Договор поставки____шаблон_2024_для конструктора.docx",
        "txt":  r"C:\Users\dleo2\Downloads\Шаблоны 1\Договор поставки____шаблон_2024_для конструктора.txt",
        "doc_name": "Договор поставки 2024 (конструктор)",
        "doc_type": "Договор поставки",
        "keywords": ["поставка", "поставщик", "покупатель", "товар", "спецификация", "стандарты", "гарантийный срок", "пени", "упаковка"],
        "variables": 82, "variative_blocks": 15, "calculated_fields": 1,
        "tables": 2, "appendices": 1, "complexity": "Средняя",
    },
    {
        "docx": r"C:\Users\dleo2\Downloads\Шаблоны_Часть_2_3шт\Спецификация_к_договору поставки_уточнение по оплатам конструктор.docx",
        "txt":  r"C:\Users\dleo2\Downloads\Шаблоны_Часть_2_3шт\Спецификация_к_договору поставки_уточнение по оплатам конструктор.txt",
        "doc_name": "Спецификация к договору поставки (уточнение оплат)",
        "doc_type": "Спецификация",
        "keywords": ["спецификация", "поставка", "товар", "условия поставки", "порядок оплаты", "грузополучатель", "гарантийный срок"],
        "variables": 35, "variative_blocks": 5, "calculated_fields": 0,
        "tables": 1, "appendices": 0, "complexity": "Высокая",
    },
    {
        "docx": r"C:\Users\dleo2\Downloads\Шаблоны_Часть_2_3шт\Ремонт_оборудования_Договор_шаблон_2024.docx",
        "txt":  r"C:\Users\dleo2\Downloads\Шаблоны_Часть_2_3шт\Ремонт_оборудования_Договор_шаблон_2024.txt",
        "doc_name": "Договор ремонта оборудования 2024",
        "doc_type": "Договор подряда",
        "keywords": ["ремонт", "оборудование", "подрядчик", "диагностика", "сервисный центр", "монтаж", "неисправность"],
        "variables": 71, "variative_blocks": 0, "calculated_fields": 0,
        "tables": 2, "appendices": 2, "complexity": "Средняя",
    },
    {
        "docx": r"C:\Users\dleo2\Downloads\Шаблоны_Часть_2_3шт\Договор_подряда_рамочный.docx",
        "txt":  r"C:\Users\dleo2\Downloads\Шаблоны_Часть_2_3шт\Договор_подряда_рамочный.txt",
        "doc_name": "Договор подряда рамочный",
        "doc_type": "Договор подряда",
        "keywords": ["подряд", "подрядчик", "заказчик", "работы", "рамочный", "техническая документация", "смета", "этапы"],
        "variables": 52, "variative_blocks": 4, "calculated_fields": 2,
        "tables": 2, "appendices": 2, "complexity": "Средняя",
    },
    {
        "docx": r"C:\Users\dleo2\Downloads\Шаблоны_Часть_3_3шт\Лицензионный договор_рамка 2024.docx",
        "txt":  r"C:\Users\dleo2\Downloads\Шаблоны_Часть_3_3шт\Лицензионный договор_рамка 2024.txt",
        "doc_name": "Лицензионный договор рамочный 2024",
        "doc_type": "Лицензионный договор",
        "keywords": ["лицензия", "лицензиар", "лицензиат", "рамочный", "программное обеспечение", "неустойка", "гарантийная поддержка"],
        "variables": 84, "variative_blocks": 8, "calculated_fields": 0,
        "tables": 1, "appendices": 1, "complexity": "Средняя",
    },
    {
        "docx": r"C:\Users\dleo2\Downloads\Шаблоны_Часть_3_3шт\ДС_шаблон_для конструктора.docx",
        "txt":  r"C:\Users\dleo2\Downloads\Шаблоны_Часть_3_3шт\ДС_шаблон_для конструктора.txt",
        "doc_name": "Дополнительное соглашение (шаблон-конструктор)",
        "doc_type": "Дополнительное соглашение",
        "keywords": ["дополнительное соглашение", "изменение договора", "редакция", "пункт договора"],
        "variables": 23, "variative_blocks": 3, "calculated_fields": 0,
        "tables": 3, "appendices": 0, "complexity": "Средняя",
    },
    {
        "docx": r"C:\Users\dleo2\Downloads\Шаблоны_Часть_3_3шт\Договор поставки+ПО (смешанный договор).docx",
        "txt":  r"C:\Users\dleo2\Downloads\Шаблоны_Часть_3_3шт\Договор поставки+ПО (смешанный договор).txt",
        "doc_name": "Договор поставки + ПО (смешанный договор)",
        "doc_type": "Смешанный договор",
        "keywords": ["поставка", "программное обеспечение", "смешанный", "лицензия", "дистрибутив", "спецификация", "товар", "покупатель", "поставщик"],
        "variables": 77, "variative_blocks": 10, "calculated_fields": 2,
        "tables": 2, "appendices": 1, "complexity": "Средняя",
    },
]

EXCERPT_CHARS = 4000

rag = []
for d in DOCS:
    # Читаем текст документа
    info = extract_docx(d["docx"])
    text = "\n".join(p for p in info.paragraphs if p.strip())
    excerpt = text[:EXCERPT_CHARS]

    # Читаем полную аннотацию из .txt файла
    annotation_raw = Path(d["txt"]).read_text(encoding="utf-8").strip()

    entry = {
        "doc_name": d["doc_name"],
        "doc_type": d["doc_type"],
        "keywords": d["keywords"],
        "variables": d["variables"],
        "variative_blocks": d["variative_blocks"],
        "calculated_fields": d["calculated_fields"],
        "tables": d["tables"],
        "appendices": d["appendices"],
        "complexity": d["complexity"],
        "annotation": annotation_raw,   # полная аннотация с детализацией по пунктам
        "text_excerpt": excerpt,
        "total_chars": len(text),
    }
    rag.append(entry)
    print(f"  OK  {d['doc_name']}: doc={len(text)} chars, annotation={len(annotation_raw)} chars")

out = Path(__file__).parent / "rag_full.json"
with open(out, "w", encoding="utf-8") as f:
    json.dump(rag, f, ensure_ascii=False, indent=2)
print(f"\nГотово: {out}  ({len(rag)} документов)")
