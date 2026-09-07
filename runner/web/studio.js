"use strict";
const $ = (id) => document.getElementById(id);
const token = document.querySelector('meta[name="studio-token"]').content;
const stageNames = ["Intake", "Foundation", "Architecture", "Drafting", "Audit", "Score", "Package"];
const stageLabels = ["Your idea", "Foundation", "Outline", "Chapters", "Review", "Feedback", "Your book"];
const friendlyStages = {Connecting:"Connecting your tools",Intake:"Finding the direction",Foundation:"Building the foundation",Architecture:"Shaping your outline",Drafting:"Writing and refining",Audit:"Reading the whole book",Score:"Gathering the feedback",Package:"Preparing your book"};
let state = null, pending = false, forceHome = false, selectedChapter = null, chapterText = "", lastPaper = "", lastPaperKey = "", lastBooks = "", lastChapters = "", lastLogs = "", lastRoles = "", lastQuestion = "", failures = 0, closed = false, polling = false;
let connection = "saved", writingModel = "", requestLimit = 200;
const connectionName = (name) => ({saved:"Saved connection setup",claude:"Claude Code",codex:"Codex"}[name] || name);

function node(tag, className, text) { const el = document.createElement(tag); if (className) el.className = className; if (text !== undefined) el.textContent = text; return el; }
function toast(message) { $("toast").textContent = message; $("toast").hidden = false; clearTimeout(toast.timer); toast.timer = setTimeout(() => { $("toast").hidden = true; }, 6500); }
async function api(path, data) {
  const response = await fetch("/api/" + path, {method: data === undefined ? "GET" : "POST", headers: {"X-Studio-Token":token, ...(data === undefined ? {} : {"Content-Type":"application/json"})}, ...(data === undefined ? {} : {body:JSON.stringify(data)})});
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || "The request could not be completed.");
  return result;
}
async function act(action, data = {}) {
  if (pending) return false;
  pending = true; updateControls();
  try { await api(action, data); return true; }
  catch (error) { toast(error.message); return false; }
  finally { await refresh(true); pending = false; updateControls(); }
}
function updateControls() {
  const active = Boolean(state?.active);
  $("begin").disabled = active || pending || !$("idea").value.trim();
  $("begin").textContent = pending ? "Starting…" : "Begin your book ↗";
  ["new-book","library-link","resume-button","settings-button","composer-connection","test-connection","save-connection","guidance-button","connect-api"].forEach(id => { $(id).disabled = active || pending; });
  $("pause-button").disabled = pending;
  $("export-button").disabled = active || pending || !(state?.chapters?.length || state?.has_working_drafts);
  ["answer-yes","answer-no"].forEach(id => { $(id).disabled = pending || !state?.question; });
  $("answer-note").disabled = pending || !state?.question || !$("approval-note").value.trim();
  $("save-note").disabled = pending || !$("author-note").value.trim();
}
function inline(parent, text) {
  // Text nodes and a small allowlist of formatting. Manuscripts never become HTML.
  const pieces = text.split(/(\*\*[^*\n]+\*\*|`[^`\n]+`)/g);
  for (const piece of pieces) {
    if (piece.startsWith("**") && piece.endsWith("**")) parent.append(node("strong", "", piece.slice(2,-2)));
    else if (piece.startsWith("`") && piece.endsWith("`")) parent.append(node("code", "", piece.slice(1,-1)));
    else parent.append(document.createTextNode(piece));
  }
}
function markdown(target, text) {
  target.replaceChildren(); let paragraph = [], list = null;
  const flush = () => { if (paragraph.length) { const p = node("p"); inline(p, paragraph.join(" ")); target.append(p); paragraph = []; } };
  for (const line of text.split(/\r?\n/)) {
    const heading = line.match(/^(#{1,6})\s+(.+)$/), bullet = line.match(/^\s*(?:[-*]|\d+[.)])\s+(.+)$/);
    if (!line.trim()) { flush(); list = null; continue; }
    if (heading) { flush(); list = null; const h = node("h" + Math.min(heading[1].length,3)); inline(h,heading[2]); target.append(h); }
    else if (/^\s*(?:---+|\*\*\*+)\s*$/.test(line)) { flush(); list=null; target.append(node("hr")); }
    else if (bullet) { flush(); if (!list) { list=node("ul"); target.append(list); } const li=node("li"); inline(li,bullet[1]); list.append(li); }
    else { list=null; paragraph.push(line); }
  }
  flush();
}
function placeholder(title, message) {
  const content = $("paper-content"); content.replaceChildren();
  const box=node("div","placeholder-page"); box.append(node("div","page-flower","✳"),node("h2","",title),node("p","",message)); content.append(box);
}
function paintPaper() {
  if (!state) return;
  let text = "", key = "", label = "THE WRITING ROOM", meta = "";
  if (state.question) { key="question:" + state.question.title; text=state.question.body || state.question.hint; label="READ & APPROVE"; meta="Take your time. This is your book."; }
  else if (selectedChapter !== null) { key="chapter:"+selectedChapter; text=chapterText; label="SAVED CHAPTER " + selectedChapter; meta="Saved in your project folder"; }
  else if (state.prose) { key="live:"+state.prose_task; text=state.prose; label="LIVE DRAFT"; meta=state.active ? "Preview · still being reviewed" : "Draft preview"; }
  else { key="empty:"+state.stage; meta=state.active ? "Your team is working" : "Ready when you are"; }
  $("page-label").textContent=label; $("page-meta").textContent=meta;
  $("paper-content").classList.toggle("streaming",key.startsWith("live:") && state.active);
  if (text === lastPaper && key === lastPaperKey) return;
  const paper=$("paper"), follow=paper.scrollHeight-paper.scrollTop-paper.clientHeight<90, oldTop=paper.scrollTop, changed=key!==lastPaperKey;
  if (text) markdown($("paper-content"),text);
  else placeholder(state.active ? "The first page starts here." : "A space for your next chapter.",state.active ? "Your team is shaping the direction. You’ll see the brief here before the chapters begin." : "Resume your book, or select a saved chapter to settle in and read.");
  $("paper-content").classList.toggle("streaming",key.startsWith("live:") && state.active);
  if (changed) paper.scrollTop=0; else if (follow && key.startsWith("live:")) paper.scrollTop=paper.scrollHeight; else paper.scrollTop=oldTop;
  lastPaper=text; lastPaperKey=key;
}
function paintBooks() {
  const signature=JSON.stringify([state.books,state.project?.id,state.active]); if (signature===lastBooks) return; lastBooks=signature;
  $("book-nav").replaceChildren(); $("bookshelf").replaceChildren();
  $("library-count").textContent=state.books.length; $("empty-nav").hidden=state.books.length>0; $("empty-shelf").hidden=state.books.length>0;
  $("bookshelf-caption").textContent=state.books.length ? `${state.books.length} ${state.books.length===1?"book":"books"}, each one yours.` : "Room for your next idea.";
  for (const book of state.books) {
    const open=async()=>{ if(await act("open",{id:book.id})){ forceHome=false; selectedChapter=null; lastPaperKey=""; await refresh(); } };
    const nav=node("button",book.id===state.project?.id ? "current" : "",book.title); nav.disabled=state.active; nav.addEventListener("click",open); $("book-nav").append(nav);
    const card=node("button","book-card"); card.disabled=state.active;
    const initials=book.title.split(/\s+/).filter(Boolean).slice(0,2).map(s=>s[0]).join("").toUpperCase();
    const copy=node("div"); copy.append(node("h3","",book.title),node("p","",`${book.chapters} saved ${book.chapters===1?"chapter":"chapters"} · ${book.status==="completed"?"Workflow complete":"Work in progress"}`));
    card.append(node("span","book-cover",initials),copy); card.addEventListener("click",open); $("bookshelf").append(card);
  }
}
function paintChapters() {
  const signature=JSON.stringify([state.chapters,selectedChapter,state.project?.id]); if(signature===lastChapters) return; lastChapters=signature;
  $("chapters").replaceChildren(); $("chapter-empty").hidden=state.chapters.length>0;
  $("saved-count").textContent=state.chapters.length;
  $("word-total").textContent=state.chapters.reduce((sum,ch)=>sum+ch.words,0).toLocaleString();
  $("live-button").classList.toggle("active",selectedChapter===null);
  for(const ch of state.chapters) {
    const button=node("button","chapter-link"+(selectedChapter===ch.number?" active":""));
    const label=node("span","",ch.title.replace(/^(?:chapter|capítulo)\s+\d+\s*[:—–-]?\s*/i,"")); label.append(node("small","",ch.words.toLocaleString()+" words"));
    button.append(node("span","chapter-no",String(ch.number).padStart(2,"0")),label);
    button.addEventListener("click",async()=>{ try { const result=await api("chapter?number="+ch.number); selectedChapter=ch.number; chapterText=result.text; paintChapters(); paintPaper(); } catch(error){toast(error.message);} });
    $("chapters").append(button);
  }
}
function paintJourney() {
  const index=stageNames.indexOf(state.stage), completed=state.status==="completed";
  $("journey").replaceChildren();
  stageNames.forEach((name,i)=>{ const el=node("div","journey-item"+(completed||i<index?" done":i===index?" active":"")); el.append(node("i"),node("span","",stageLabels[i])); if(i===index)el.setAttribute("aria-current","step"); $("journey").append(el); });
}
function paint() {
  $("request-count").textContent=`${state.requests_used} of ${state.request_limit} model requests this session`;
  $("close-workspace").disabled=pending || state.closing;
  if(state.probe && state.probe.status !== "idle"){
    const activity=(state.probe.logs||[]).slice(-4).join("\n");
    $("connection-feedback").textContent=activity ? state.probe.detail+"\n\n"+activity : state.probe.detail;
    $("connection-sample").textContent=state.probe.prose;$("connection-sample").hidden=!state.probe.prose;
  }
  $("recovery-panel").hidden=!state.last_error;
  if(state.last_error){$("recovery-message").textContent=state.last_error.message;$("recovery-action").textContent=state.last_error.action;$("recovery-journal").textContent="Saved history: "+state.last_error.journal;}
  $("read-warning").textContent=state.read_warning;$("read-warning").hidden=!state.read_warning;
  $("feedback-button").hidden=!state.feedback;
  const home=forceHome || !state.project; $("home").hidden=!home; $("workspace").hidden=home;
  $("breadcrumb").textContent=home ? "Your library" : state.project.title;
  $("export-button").hidden=home;
  if(!home){$("project-title").textContent=state.project.title; $("status-banner").textContent=state.detail || "Your work is saved."; $("status-banner").classList.toggle("warning",["failed","blocked","awaiting_manual","awaiting_human"].includes(state.status));}
  $("resume-button").hidden=state.active; $("pause-button").hidden=!state.active;
  $("resume-button").textContent=state.status==="completed"?"Reopen saved delivery →":"Resume writing →";
  $("activity-light").classList.toggle("running",state.active && state.status!=="awaiting_author");
  $("current-stage").textContent=state.question?"A moment for your direction":friendlyStages[state.stage] || "Ready when you are";
  $("current-detail").textContent=state.question?"Read the page, then continue or leave a note.":state.detail;
  $("elapsed").textContent=Math.floor(state.elapsed/60)+":"+String(state.elapsed%60).padStart(2,"0");
  const approval=Boolean(state.question); $("approval").hidden=!approval;
  if(approval){$("approval-title").textContent=state.question.title; $("approval-note").hidden=!state.question.allow_notes; $("answer-note").hidden=!state.question.allow_notes;
    const q=state.question.title+state.question.body; if(q!==lastQuestion){$("approval-note").value=""; lastQuestion=q; selectedChapter=null; toast("Your turn: "+state.question.title);}
  } else lastQuestion="";
  // Keep the live heartbeat and public prose preview visible. These lines are
  // deliberately emitted by activity.py without private reasoning or provider
  // tool events, so a beginner can tell that a slow request is still moving.
  const logs=state.logs.slice(-8).reverse();
  if(JSON.stringify(logs)!==lastLogs){lastLogs=JSON.stringify(logs);$("activity-feed").replaceChildren(...logs.map(line=>node("li","",line)));}
  const roles=JSON.stringify(state.roles); if(roles!==lastRoles){lastRoles=roles;$("team").replaceChildren();for(const [role,model] of Object.entries(state.roles).filter(([r])=>r!=="panel")){const row=node("div","team-row"),copy=node("div");copy.append(node("strong","",role),node("small","",model));row.append(node("span","team-avatar",role[0].toUpperCase()),copy);$("team").append(row);}}
  paintBooks(); paintChapters(); paintJourney(); paintPaper(); updateControls();
}
async function loadState(){
  if(closed)return;
  try{
    state=await api("state"); failures=0;$("connection-lost").hidden=true;
    if(!$("connection-select").options.length){ for(const c of state.connections){const option=node("option","",connectionName(c));option.value=c;$("connection-select").append(option);} connection=state.connection;writingModel=state.model;$("connection-select").value=connection;$("model-input").value=writingModel; }
    $("connection-label").textContent=connectionName(connection);
    paint();
  }catch(error){failures++;if(failures>=3){$("connection-lost").hidden=false;$("connection-lost").querySelector("span").textContent=error.message;}}
}
const refresh=createStudioRefresh(loadState);
function settings(){if(!state?.active){$("connection-select").value=connection;$("model-input").value=writingModel;$("connection-dialog").showModal();}}
$("new-book").addEventListener("click",()=>{forceHome=true;paint();$("idea").focus();});
$("library-link").addEventListener("click",()=>{forceHome=true;paint();$("bookshelf").scrollIntoView({behavior:"auto",block:"center"});});
$("brand-home").addEventListener("click",event=>{event.preventDefault();if(!state?.active){forceHome=true;paint();}});
$("idea").addEventListener("input",updateControls);
document.querySelectorAll("[data-prompt]").forEach(button=>button.addEventListener("click",()=>{$("idea").value=button.dataset.prompt;$("idea").focus();updateControls();}));
$("idea-form").addEventListener("submit",async(event)=>{event.preventDefault();const ok=await act("start",{new:true,idea:$("idea").value,language:$("language").value,connection,model:writingModel,request_limit:requestLimit});if(ok){forceHome=false;selectedChapter=null;lastPaperKey="";await refresh();}});
$("resume-button").addEventListener("click",async()=>{selectedChapter=null;await act("start",{connection,model:writingModel,request_limit:requestLimit});});
$("pause-button").addEventListener("click",async()=>{if(await act("pause"))toast("Pause requested. The current call will finish safely; saved work stays intact.");});
$("live-button").addEventListener("click",()=>{selectedChapter=null;paintChapters();paintPaper();});
$("answer-yes").addEventListener("click",()=>act("answer",{text:"yes"}));
$("answer-no").addEventListener("click",()=>act("answer",{text:"no"}));
$("answer-note").addEventListener("click",()=>act("answer",{text:$("approval-note").value}));
$("approval-note").addEventListener("input",updateControls);
$("author-note").addEventListener("input",updateControls);
$("guidance-button").addEventListener("click",()=>{$("note-dialog").showModal();$("author-note").focus();});
$("save-note").addEventListener("click",async()=>{if(await act("notes",{text:$("author-note").value})){$("note-dialog").close();$("author-note").value="";toast("Your guidance is saved. Resume when you’re ready.");}});
$("settings-button").addEventListener("click",settings);$("composer-connection").addEventListener("click",settings);
$("save-connection").addEventListener("click",()=>{const limit=Number($("request-limit").value);if(!Number.isInteger(limit)||limit<1||limit>1000){toast("Choose a request limit from 1 to 1000.");return;}requestLimit=limit;connection=$("connection-select").value;writingModel=$("model-input").value.trim();$("connection-label").textContent=connectionName(connection);$("connection-dialog").close();toast("Connection selected. Your next run will use this setup.");});
$("test-connection").addEventListener("click",async()=>{connection=$("connection-select").value;writingModel=$("model-input").value.trim();await act("probe",{connection,model:writingModel});});
$("export-button").addEventListener("click",()=>$("export-dialog").showModal());
document.querySelectorAll("[data-download]").forEach(button=>button.addEventListener("click",async()=>{button.disabled=true;try{const format=button.dataset.download;const response=await fetch("/api/download?format="+format,{headers:{"X-Studio-Token":token}});if(!response.ok)throw new Error((await response.json()).error);const url=URL.createObjectURL(await response.blob());const a=document.createElement("a");a.href=url;a.download=response.headers.get("Content-Disposition")?.match(/filename="([^"]+)"/)?.[1] || "book."+(format==="epub"?"epub":"md");a.click();setTimeout(()=>URL.revokeObjectURL(url),5000);$("export-dialog").close();toast("Your download is ready. The original remains in your project folder.");}catch(error){toast(error.message);}finally{button.disabled=false;}}));
$("reconnect").addEventListener("click",()=>{failures=0;refresh();});
$("feedback-button").addEventListener("click",()=>{$("feedback-text").textContent=state.feedback;$("feedback-dialog").showModal();});
$("close-workspace").addEventListener("click",async()=>{if(await act("close")){closed=true;$("shutdown-dialog").showModal();}});
window.addEventListener("beforeunload",()=>{if(state?.active)fetch("/api/pause",{method:"POST",headers:{"X-Studio-Token":token,"Content-Type":"application/json"},body:"{}",keepalive:true}).catch(()=>{});});
async function tick(){await refresh();if(!closed)setTimeout(tick,document.hidden?1500:450);}tick();

$("connect-api").addEventListener("click",async()=>{const data={provider:$("api-provider").value,api_key:$("api-secret").value,writer_model:$("api-writer").value.trim(),reader_model:$("api-reader").value.trim(),remember:$("api-remember").checked};if(await act("configure-api",data)){connection="saved";writingModel="";$("connection-select").value="saved";$("model-input").value="";$("api-secret").value="";}});
