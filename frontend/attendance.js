(() => {
  const form = document.getElementById("attendanceForm");
  const select = document.getElementById("student");
  const table = document.getElementById("attendanceTable");
  const message = document.getElementById("message");
  const dateInput = document.getElementById("attendanceDate");
  if (!form) return;
  dateInput.max = new Date().toISOString().slice(0,10);
  const addCell = (tr, value) => { const td=document.createElement("td"); td.textContent=value ?? ""; tr.appendChild(td); };
  async function loadStudents() {
    const r=await fetch("/api/students"); const data=await r.json();
    if (!r.ok) throw new Error(data.error || "Could not load students.");
    select.replaceChildren(new Option("Select student",""));
    data.forEach(s=>select.add(new Option(`${s.roll_no} - ${s.name}`,s.id)));
  }
  async function loadAttendance() {
    const r=await fetch("/api/attendance"); const data=await r.json();
    if (!r.ok) throw new Error(data.error || "Could not load attendance.");
    table.replaceChildren();
    data.forEach(a=>{const tr=document.createElement("tr");[a.roll_no,a.name,a.attendance_date,a.status].forEach(v=>addCell(tr,v));table.appendChild(tr);});
  }
  form.addEventListener("submit",async e=>{
    e.preventDefault();
    try {
      const r=await fetch("/api/attendance",{method:"POST",headers:{"Content-Type":"application/json"},
        body:JSON.stringify({student_id:Number(select.value),attendance_date:dateInput.value,status:document.getElementById("status").value})});
      const data=await r.json(); if(!r.ok) throw new Error(data.error || "Save failed.");
      message.textContent=data.message; await loadAttendance();
    } catch(err){message.textContent=err.message;}
  });
  Promise.all([loadStudents(),loadAttendance()]).catch(e=>message.textContent=e.message);
})();