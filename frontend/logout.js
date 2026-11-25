async function logout() {
  try {
    await fetch("/api/logout", {
      method: "POST", credentials: "same-origin",
      headers: {"Content-Type":"application/json"}, body: "{}"
    });
  } finally {
    window.location.href = "/login.html";
  }
}