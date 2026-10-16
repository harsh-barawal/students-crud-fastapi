let currentPage = 1;
let editingId = null;

const tableBody = document.getElementById("studentTable");
const pageInfo = document.getElementById("pageInfo");
const message = document.getElementById("message");
const form = document.getElementById("studentForm");


function showMessage(text, type) {
    message.textContent = text;
    message.className = type;
}


function escapeHtml(text) {
    if (text === null || text === undefined) {
        return "";
    }
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}


async function loadStudents() {
    const search = document.getElementById("searchInput").value;
    const course = document.getElementById("courseInput").value;

    const params = new URLSearchParams({ page: currentPage, limit: 5 });
    if (search) params.append("search", search);
    if (course) params.append("course", course);

    const response = await fetch("/students?" + params);
    const data = await response.json();

    tableBody.innerHTML = "";

    if (data.students.length === 0) {
        tableBody.innerHTML = "<tr><td colspan='8'>No students found</td></tr>";
    }

    for (const student of data.students) {
        const row = document.createElement("tr");
        row.innerHTML = `
            <td>${escapeHtml(student.student_id)}</td>
            <td>${escapeHtml(student.name)}</td>
            <td>${student.date_of_birth}</td>
            <td>${student.age}</td>
            <td>${escapeHtml(student.email)}</td>
            <td>${escapeHtml(student.phone)}</td>
            <td>${escapeHtml(student.course)}</td>
            <td>
                <button onclick="editStudent('${student.student_id}')">Edit</button>
                <button class="delete" onclick="deleteStudent('${student.student_id}')">Delete</button>
            </td>
        `;
        tableBody.appendChild(row);
    }

    const totalPages = Math.max(1, Math.ceil(data.total / data.limit));
    pageInfo.textContent = `Page ${currentPage} of ${totalPages} (${data.total} students)`;
    document.getElementById("prevBtn").disabled = currentPage <= 1;
    document.getElementById("nextBtn").disabled = currentPage >= totalPages;
}


function getFormData() {
    const data = {
        name: document.getElementById("name").value,
        date_of_birth: document.getElementById("dob").value,
        email: document.getElementById("email").value,
        phone: document.getElementById("phone").value,
        course: document.getElementById("course").value,
        address: document.getElementById("address").value,
        enrollment_date: document.getElementById("enrollmentDate").value,
    };

    // empty fields are not sent
    for (const key in data) {
        if (data[key] === "") {
            delete data[key];
        }
    }
    return data;
}


function getErrorText(error) {
    if (Array.isArray(error.detail)) {
        return error.detail.map(e => e.msg).join(", ");
    }
    return error.detail;
}


form.addEventListener("submit", async function (event) {
    event.preventDefault();

    const url = editingId ? "/students/" + editingId : "/students";
    const method = editingId ? "PATCH" : "POST";

    const response = await fetch(url, {
        method: method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(getFormData()),
    });

    if (response.ok) {
        showMessage(editingId ? "Student updated" : "Student added", "success");
        clearForm(false);
        loadStudents();
    } else {
        showMessage(getErrorText(await response.json()), "error");
    }
});


async function editStudent(studentId) {
    const response = await fetch("/students/" + studentId);
    const student = await response.json();

    editingId = studentId;
    document.getElementById("formTitle").textContent = "Edit " + studentId;
    document.getElementById("name").value = student.name;
    document.getElementById("dob").value = student.date_of_birth;
    document.getElementById("email").value = student.email || "";
    document.getElementById("phone").value = student.phone || "";
    document.getElementById("course").value = student.course || "";
    document.getElementById("address").value = student.address || "";
    document.getElementById("enrollmentDate").value = student.enrollment_date || "";
    form.scrollIntoView({ behavior: "smooth" });
}


async function deleteStudent(studentId) {
    if (!confirm("Delete student " + studentId + "?")) {
        return;
    }
    await fetch("/students/" + studentId, { method: "DELETE" });
    loadStudents();
}


function clearForm(clearMessage = true) {
    editingId = null;
    form.reset();
    document.getElementById("formTitle").textContent = "Add Student";
    if (clearMessage) {
        showMessage("", "");
    }
}


async function askQuestion() {
    const question = document.getElementById("questionInput").value;
    const answerBox = document.getElementById("answer");

    if (!question) {
        return;
    }

    answerBox.textContent = "Thinking...";
    const response = await fetch("/ai/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: question }),
    });
    const data = await response.json();

    if (response.ok) {
        answerBox.textContent = data.answer;
    } else {
        answerBox.textContent = getErrorText(data);
    }
}


document.getElementById("searchBtn").addEventListener("click", function () {
    currentPage = 1;
    loadStudents();
});

document.getElementById("prevBtn").addEventListener("click", function () {
    currentPage--;
    loadStudents();
});

document.getElementById("nextBtn").addEventListener("click", function () {
    currentPage++;
    loadStudents();
});

document.getElementById("clearBtn").addEventListener("click", clearForm);
document.getElementById("askBtn").addEventListener("click", askQuestion);

loadStudents();
