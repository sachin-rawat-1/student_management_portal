(() => {
  const form=document.getElementById("marksForm");
  const select=document.getElementById("student");
  const table=document.getElementById("marksTable");
  const message=document.getElementById("message");
  if(!form) return;
  const addCell=(tr,v)=>{const td=document.createElement("td");td.textContent=v??"";tr.appendChild(td);};
  async function loadStudents(){
    const r=await fetch("/api/students");const data=await r.json();
    if(!r.ok)throw new Error(data.error||"Could not load students.");
    select.replaceChildren(new Option("Select student",""));
    data.forEach(s=>select.add(new Option(`${s.roll_no} - ${s.name}`,s.id)));
  }
  async function loadMarks(){
    const r=await fetch("/api/marks");const data=await r.json();
    if(!r.ok)throw new Error(data.error||"Could not load marks.");
    table.replaceChildren();
    data.forEach(m=>{const tr=document.createElement("tr");
      [m.roll_no,m.name,m.subject,m.marks_obtained,m.total_marks,
       `${(Number(m.marks_obtained)*100/Number(m.total_marks)).toFixed(2)}%`].forEach(v=>addCell(tr,v));
      table.appendChild(tr);
    });
  }
  form.addEventListener("submit",async e=>{
    e.preventDefault();
    const obtained=Number(document.getElementById("obtained").value);
    const total=Number(document.getElementById("total").value);
    if(obtained>total){message.textContent="Obtained marks cannot exceed maximum marks.";return;}
    try{
      const r=await fetch("/api/marks",{method:"POST",headers:{"Content-Type":"application/json"},
        body:JSON.stringify({student_id:Number(select.value),subject:document.getElementById("subject").value.trim(),
          marks_obtained:obtained,total_marks:total})});
      const data=await r.json();if(!r.ok)throw new Error(data.error||"Save failed.");
      message.textContent=data.message;form.reset();await loadMarks();
    }catch(err){message.textContent=err.message;}
  });
  Promise.all([loadStudents(),loadMarks()]).catch(e=>message.textContent=e.message);
})();