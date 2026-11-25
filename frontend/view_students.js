(() => {
  const table = document.getElementById("studentTable");
  if (!table) return;

  const search = document.getElementById("searchStudent");
  const message = document.getElementById("message");
  const count = document.getElementById("recordCount");
  let students = [];

  // Edit form styling
  const style = document.createElement("style");
  style.textContent = `
    .edit-modal {
      display:none;
      position:fixed;
      inset:0;
      background:rgba(0,0,0,0.65);
      z-index:9999;
      justify-content:center;
      align-items:center;
      padding:15px;
    }
    .edit-box {
      background:white;
      color:#222;
      padding:25px;
      border-radius:10px;
      width:100%;
      max-width:450px;
      max-height:90vh;
      overflow-y:auto;
    }
    .edit-box h2 { margin-top:0; }
    .edit-box label {
      display:block;
      margin-top:12px;
      font-weight:bold;
    }
    .edit-box input, .edit-box select {
      width:100%;
      padding:10px;
      margin-top:5px;
      box-sizing:border-box;
    }
    .edit-actions {
      display:flex;
      gap:10px;
      margin-top:20px;
    }
  `;
  document.head.appendChild(style);

  // Create edit modal
  const modal = document.createElement("div");
  modal.className = "edit-modal";
  modal.innerHTML = `
    <form class="edit-box" id="editForm">
      <h2>Edit Student Details</h2>

      <label>Roll Number</label>
      <input name="roll" maxlength="20" required>

      <label>Student Name</label>
      <input name="name" maxlength="100" required>

      <label>Email</label>
      <input name="email" type="email" maxlength="100" required>

      <label>Phone</label>
      <input name="phone" maxlength="15" required>

      <label>Course</label>
      <select name="course" required>
        <option>B.Sc Computer Science</option>
        <option>BCA</option>
        <option>B.Tech</option>
        <option>Other</option>
      </select>

      <label>Semester</label>
      <select name="semester" required>
        <option value="1">1st Semester</option>
        <option value="2">2nd Semester</option>
        <option value="3">3rd Semester</option>
        <option value="4">4th Semester</option>
        <option value="5">5th Semester</option>
        <option value="6">6th Semester</option>
        <option value="7">7th Semester</option>
        <option value="8">8th Semester</option>
      </select>

      <div class="edit-actions">
        <button type="submit">Update Student</button>
        <button type="button" id="cancelEdit">Cancel</button>
      </div>
    </form>
  `;
  document.body.appendChild(modal);

  const form = document.getElementById("editForm");
  let editingStudent = null;

  document.getElementById("cancelEdit").addEventListener("click", () => {
    modal.style.display = "none";
  });

  function cell(value) {
    const td = document.createElement("td");
    td.textContent = value == null ? "" : value;
    return td;
  }

  function render() {
    const term = (search.value || "").toLowerCase();

    const filtered = students.filter(s =>
      [s.roll_no, s.name, s.email, s.phone, s.course, s.semester]
        .some(v => String(v ?? "").toLowerCase().includes(term))
    );

    table.replaceChildren();

    filtered.forEach(s => {
      const tr = document.createElement("tr");

      [s.roll_no, s.name, s.email, s.phone, s.course, s.semester]
        .forEach(v => tr.appendChild(cell(v)));

      const actions = document.createElement("td");

      const edit = document.createElement("button");
      edit.type = "button";
      edit.textContent = "Edit";
      edit.className = "action-button edit-button";
      edit.addEventListener("click", () => editStudent(s));

      const del = document.createElement("button");
      del.type = "button";
      del.textContent = "Delete";
      del.className = "action-button delete-button";
      del.addEventListener("click", () => deleteStudent(s));

      actions.append(edit, del);
      tr.appendChild(actions);
      table.appendChild(tr);
    });

    count.textContent =
      `Showing ${filtered.length} of ${students.length} student(s).`;
  }

  async function load() {
    try {
      const response = await fetch("/api/students", {
        credentials: "same-origin"
      });

      if (response.status === 401) {
        location.href = "/login.html";
        return;
      }

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.error || "Unable to load students.");
      }

      students = result;
      render();

    } catch (error) {
      message.textContent = error.message;
    }
  }

  function editStudent(s) {
    editingStudent = s;

    form.elements.roll.value = s.roll_no;
    form.elements.name.value = s.name;
    form.elements.email.value = s.email;
    form.elements.phone.value = s.phone;
    form.elements.course.value = s.course;
    form.elements.semester.value = String(s.semester);

    modal.style.display = "flex";
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();

    if (!editingStudent) return;

    const payload = {
      roll: form.elements.roll.value.trim(),
      name: form.elements.name.value.trim(),
      email: form.elements.email.value.trim(),
      phone: form.elements.phone.value.trim(),
      course: form.elements.course.value,
      semester: Number(form.elements.semester.value)
    };

    try {
      const response = await fetch(
        `/api/students/${editingStudent.id}`,
        {
          method: "PUT",
          credentials: "same-origin",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify(payload)
        }
      );

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.error || "Update failed.");
      }

      modal.style.display = "none";
      editingStudent = null;
      message.textContent = "Student updated successfully!";

      await load();

    } catch (error) {
      message.textContent = error.message;
    }
  });

  async function deleteStudent(s) {
    if (!confirm(`Delete ${s.name} (${s.roll_no})?`)) return;

    try {
      const response = await fetch(`/api/students/${s.id}`, {
        method: "DELETE",
        credentials: "same-origin"
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.error || "Delete failed.");
      }

      message.textContent = "Student deleted successfully!";
      await load();

    } catch (error) {
      message.textContent = error.message;
    }
  }

  search.addEventListener("input", render);
  load();
})();