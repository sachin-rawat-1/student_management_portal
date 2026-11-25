(() => {
  const form = document.getElementById("loginForm");
  if (!form) return;
  const message = document.getElementById("message");
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    message.textContent = "Signing in...";
    const payload = {
      username: document.getElementById("username").value.trim(),
      password: document.getElementById("password").value
    };
    try {
      const response = await fetch("/api/login", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        credentials: "same-origin",
        body: JSON.stringify(payload)
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || "Login failed.");
      window.location.href = "/dashboard.html";
    } catch (error) {
      message.textContent = error.message || "Unable to connect to the server.";
    }
  });
})();