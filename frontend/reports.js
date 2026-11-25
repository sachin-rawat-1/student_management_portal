(() => {
  const table=document.getElementById("reportTable");
  const message=document.getElementById("message");
  if(!table)return;
  const cell=(tr,value)=>{const td=document.createElement("td");td.textContent=value??"—";tr.appendChild(td);};
  async function load(){
    try{
      const r=await fetch("/api/reports");const data=await r.json();
      if(r.status===401){location.href="/login.html";return;}
      if(!r.ok)throw new Error(data.error||"Could not generate report.");
      table.replaceChildren();
      data.forEach(s=>{
        const tr=document.createElement("tr");
        [s.roll_no,s.name,s.course,s.semester,
         `${s.present_days} / ${s.total_days}`,
         s.attendance_percentage==null?"—":`${s.attendance_percentage}%`,
         `${Number(s.total_obtained).toFixed(2)} / ${Number(s.total_possible).toFixed(2)}`,
         s.marks_percentage==null?"—":`${s.marks_percentage}%`
        ].forEach(v=>cell(tr,v));
        table.appendChild(tr);
      });
      if(!data.length)message.textContent="No student records found.";
    }catch(e){message.textContent=e.message;}
  }
  document.getElementById("printButton")?.addEventListener("click",()=>window.print());
  load();
})();