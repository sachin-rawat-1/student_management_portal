(() => {
  const form = document.getElementById("studentForm");
  if (!form) return;
  const message = document.getElementById("message");
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const payload = {
      roll: document.getElementById("roll").value.trim(),
      name: document.getElementById("name").value.trim(),
      email: document.getElementById("email").value.trim(),
      phone: document.getElementById("phone").value.trim(),
      course: document.getElementById("course").value,
      semester: Number(document.getElementById("semester").value)
    };
    try {
      const response = await fetch("/api/students", {
        method:"POST", credentials:"same-origin",
        headers:{"Content-Type":"application/json"}, body:JSON.stringify(payload)
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || "Could not save student.");
      message.textContent = "Student saved successfully.";
      form.reset();
    } catch (error) {
      message.textContent = error.message || "Server connection failed.";
    }
  });
})();