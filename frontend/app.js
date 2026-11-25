(() => {
  const message = document.getElementById("message");
  async function loadDashboard() {
    try {
      const [meResponse, statsResponse] = await Promise.all([
        fetch("/api/me", {credentials:"same-origin"}),
        fetch("/api/dashboard", {credentials:"same-origin"})
      ]);
      if (meResponse.status === 401 || statsResponse.status === 401) {
        window.location.href = "/login.html"; return;
      }
      const me = await meResponse.json();
      const stats = await statsResponse.json();
      if (!meResponse.ok) throw new Error(me.error || "Unable to load administrator.");
      if (!statsResponse.ok) throw new Error(stats.error || "Unable to load dashboard.");
      document.getElementById("adminName").textContent = me.username;
      document.getElementById("totalStudents").textContent = stats.total_students;
      document.getElementById("totalCourses").textContent = stats.total_courses;
      document.getElementById("totalAttendance").textContent = stats.attendance_records;
      document.getElementById("totalMarks").textContent = stats.marks_records;
    } catch (error) {
      if (message) message.textContent = error.message || "Dashboard could not be loaded.";
    }
  }
  loadDashboard();
})();