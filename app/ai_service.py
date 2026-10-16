import re
from datetime import date

import httpx
from sqlalchemy.orm import Session

from . import crud
from .models import Student

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "llama3.2:1b"
MAX_RECORDS = 50

SYSTEM_PROMPT = (
    "You answer questions about student records. "
    "Use ONLY the data given in the message. Do not make up students, numbers or dates. "
    "If the answer is not in the data, say you could not find it. "
    "Use total_matched for counts. Keep the answer short. "
    "When listing students, put each student on a new line as: number. name - date of birth - course."
)


def find_filters(question: str, db: Session):
    q = question.lower()
    filters = {}

    match = re.search(r"born\s+(after|before|in)\s+(\d{4})", q)
    if match:
        word, year = match.group(1), int(match.group(2))
        if word == "after":
            filters["born_after"] = date(year + 1, 1, 1)
        elif word == "before":
            filters["born_before"] = date(year - 1, 12, 31)
        else:
            filters["born_after"] = date(year, 1, 1)
            filters["born_before"] = date(year, 12, 31)

    courses = [row[0] for row in db.query(Student.course).distinct() if row[0]]
    for course in courses:
        if course.lower() in q:
            filters["course"] = course

    match = re.search(r"(?:named|called|name is)\s+([a-z .'-]+)", q)
    if match:
        filters["search"] = match.group(1).strip(" ?.")

    return filters


def find_action(question: str):
    q = question.lower()
    if re.search(r"how many|count|number of|total", q):
        return "count"
    if re.search(r"average age|avg age", q):
        return "average_age"
    if "oldest" in q:
        return "oldest"
    if "youngest" in q:
        return "youngest"
    return "list"


def get_context(db: Session, question: str):
    filters = find_filters(question, db)
    action = find_action(question)

    order = "desc" if action == "youngest" else "asc"
    students, total = crud.get_students(db, sort_by="date_of_birth", order=order, limit=10000, **filters)

    context = {"total_matched": total}
    if students:
        context["average_age"] = round(sum(s.age for s in students) / len(students), 1)

    if action in ("oldest", "youngest"):
        students = students[:1]
    students = students[:MAX_RECORDS]

    # email, phone and address are not sent to the model
    context["students"] = [
        {
            "student_id": s.student_id,
            "name": s.name,
            "date_of_birth": str(s.date_of_birth),
            "age": s.age,
            "course": s.course,
        }
        for s in students
    ]
    return action, context


def ask_ollama(question: str, context: dict):
    message = f"DATA: {context}\n\nQUESTION: {question}"
    response = httpx.post(
        OLLAMA_URL,
        json={
            "model": MODEL_NAME,
            "stream": False,
            "options": {"temperature": 0},
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": message},
            ],
        },
        timeout=60,
    )
    response.raise_for_status()
    return response.json()["message"]["content"].strip()


def simple_answer(action: str, context: dict):
    students = context["students"]

    if action == "count":
        return f"Total matching students: {context['total_matched']}"
    if action == "average_age":
        return f"Average age: {context.get('average_age')} years"
    if not students:
        return "No matching students found."
    if action in ("oldest", "youngest"):
        s = students[0]
        return f"The {action} student is {s['name']} (born {s['date_of_birth']}, age {s['age']})."

    lines = [f"{context['total_matched']} matching student(s) found:", ""]
    for number, s in enumerate(students, start=1):
        lines.append(f"{number}. {s['name']}")
        lines.append(f"      ID      : {s['student_id']}")
        lines.append(f"      DOB     : {s['date_of_birth']} (age {s['age']})")
        lines.append(f"      Course  : {s['course'] or '-'}")
        lines.append("")
    return "\n".join(lines).strip()


def answer_question(db: Session, question: str):
    action, context = get_context(db, question)
    try:
        answer = ask_ollama(question, context)
        source = "ollama"
    except (httpx.HTTPError, KeyError, ValueError):
        answer = simple_answer(action, context) + "\n\n(Ollama is not running, answered directly from the database)"
        source = "database"
    return {
        "question": question,
        "answer": answer,
        "source": source,
        "records_used": len(context["students"]),
    }