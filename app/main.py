from datetime import date
from pathlib import Path
from typing import Literal

from fastapi import Depends, FastAPI, Query, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from . import ai_service, crud
from .database import Base, engine, get_db
from .schemas import Question, StudentCreate, StudentList, StudentResponse, StudentUpdate

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Student Management API", version="1.0")


@app.post("/students", response_model=StudentResponse, status_code=201)
def create_student(data: StudentCreate, db: Session = Depends(get_db)):
    return crud.create_student(db, data)


@app.get("/students", response_model=StudentList)
def list_students(
    search: str | None = None,
    course: str | None = None,
    born_after: date | None = None,
    born_before: date | None = None,
    sort_by: Literal["id", "name", "date_of_birth", "enrollment_date"] = "id",
    order: Literal["asc", "desc"] = "asc",
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    students, total = crud.get_students(db, search, course, born_after, born_before, sort_by, order, page, limit)
    return {"total": total, "page": page, "limit": limit, "students": students}


@app.get("/students/{student_id}", response_model=StudentResponse)
def get_student(student_id: str, db: Session = Depends(get_db)):
    return crud.get_student(db, student_id)


@app.put("/students/{student_id}", response_model=StudentResponse)
def replace_student(student_id: str, data: StudentCreate, db: Session = Depends(get_db)):
    return crud.update_student(db, student_id, data.model_dump())


@app.patch("/students/{student_id}", response_model=StudentResponse)
def update_student(student_id: str, data: StudentUpdate, db: Session = Depends(get_db)):
    return crud.update_student(db, student_id, data.model_dump(exclude_unset=True))


@app.delete("/students/{student_id}", status_code=204)
def delete_student(student_id: str, db: Session = Depends(get_db)):
    crud.delete_student(db, student_id)
    return Response(status_code=204)


@app.post("/ai/ask")
def ask_ai(body: Question, db: Session = Depends(get_db)):
    return ai_service.answer_question(db, body.question)


STATIC_FOLDER = Path(__file__).resolve().parent.parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_FOLDER), name="static")


@app.get("/", include_in_schema=False)
def home():
    return FileResponse(STATIC_FOLDER / "index.html")
