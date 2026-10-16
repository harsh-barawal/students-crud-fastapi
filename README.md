# Student Management API

A backend project built with **Python, FastAPI and SQLite**. It manages student records with
Create, Read, Update and Delete (CRUD) operations. As a bonus, it also has a small AI feature
that answers questions about the students using a local **Ollama** model.

## Features

- Add, view, list, update and delete students
- Search and filter students (name, email, course, date of birth) with pagination and sorting
- Input validation (name, date of birth, email, phone) and proper error responses (404, 409, 422)
- Data is stored permanently in a SQLite database
- Simple web page to use the project from the browser
- Bonus: ask questions like "How many students are there?" using Ollama

## Tech Stack

- Python 3.10+
- FastAPI
- SQLAlchemy with SQLite
- Pydantic (validation)
- Ollama (optional, for the AI feature)

## Project Structure

```
app/
    main.py          API routes
    database.py      database connection
    models.py        Student table
    schemas.py       validation rules
    crud.py          database operations
    ai_service.py    Ollama AI feature
    seed.py          adds dummy students
static/              web page (HTML, CSS, JS)
tests/               automated tests
requirements.txt
```

## Prerequisites

- Python 3.10 or higher
- Ollama (only for the AI feature) - https://ollama.com/download

## Installation

```bash
git clone <your-repository-link>
cd <repository-folder>

python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # Mac / Linux

pip install -r requirements.txt
```

## Run the project

```bash
uvicorn app.main:app --reload
```

- Web page: http://127.0.0.1:8000
- API docs (Swagger): http://127.0.0.1:8000/docs

To add some dummy students for testing:

```bash
python -m app.seed
```

## API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | /students | Create a student |
| GET | /students | List / search / filter students |
| GET | /students/{student_id} | View one student |
| PUT | /students/{student_id} | Replace all details |
| PATCH | /students/{student_id} | Update some details |
| DELETE | /students/{student_id} | Delete a student |
| POST | /ai/ask | Ask a question about the students (Ollama) |

Query options for `GET /students`: `search`, `course`, `born_after`, `born_before`,
`sort_by`, `order`, `page`, `limit`.

## Testing the API

Easiest way: open http://127.0.0.1:8000/docs and use "Try it out".

Using curl:

```bash
# create
curl -X POST http://127.0.0.1:8000/students -H "Content-Type: application/json" -d '{"name": "Aarav Sharma", "date_of_birth": "2004-08-15", "email": "aarav@example.com", "phone": "+919876543210", "course": "Python Backend"}'

# list with filter
curl "http://127.0.0.1:8000/students?course=Python Backend&born_after=2003-01-01"

# view one
curl http://127.0.0.1:8000/students/EWB20260001

# update
curl -X PATCH http://127.0.0.1:8000/students/EWB20260001 -H "Content-Type: application/json" -d '{"course": "Data Science"}'

# delete
curl -X DELETE http://127.0.0.1:8000/students/EWB20260001
```

Run the automated tests:

```bash
python -m pytest
```

## AI Feature (Ollama) - Optional

1. Install Ollama and download a model:
   ```bash
   ollama pull llama3.2:1b
   ```
2. Make sure Ollama is running, then ask a question:
   ```bash
   curl -X POST http://127.0.0.1:8000/ai/ask -H "Content-Type: application/json" -d '{"question": "List students born after 2005"}'
   ```

How it works:

1. The backend reads the question and finds what is needed (count, list, year, course or name).
2. It fetches the matching students from the database using normal queries.
3. Those records are sent to the model as context, and the model writes the answer from them.

The model never writes or runs SQL, and email / phone / address are not sent to it.
"Born after 2005" means born in 2006 or later. If Ollama is not running, the answer is
generated directly from the database.

## Notes

- All data used is dummy data. No real student information or secrets are stored in this repository.
- The database file `students.db` is created automatically when the app starts.
