let currentCustomer = "";

const API = {
  submit: (msg, identifier) =>
    fetch("/tasks/submit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: msg, customer_identifier: identifier }),
    }).then((r) => r.json()),

  tasks: (identifier) =>
    fetch(`/dashboard/api/tasks?customer_identifier=${encodeURIComponent(identifier)}`)
      .then((r) => r.json()),

  updateStatus: (id, status) =>
    fetch(`/tasks/${id}/status`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status }),
    }).then((r) => r.json()),
};

function toast(msg, type = "default") {
  const container = document.getElementById("toastContainer");
  const el = document.createElement("div");
  el.className = `toast ${type}`;
  el.textContent = msg;
  container.appendChild(el);
  setTimeout(() => el.remove(), 3500);
}

function formatIntent(intent) {
  const map = {
    send_money: "Send Money",
    hire_service: "Hire Service",
    verify_document: "Verify Document",
    airport_transfer: "Airport Transfer",
    check_status: "Check Status",
  };
  return map[intent] || intent;
}

function statusBadge(status) {
  const cls = {
    Pending: "badge-pending",
    "In Progress": "badge-inprogress",
    Completed: "badge-completed",
  }[status] || "badge-pending";
  return `<span class="badge ${cls}">${status}</span>`;
}

function riskBadge(label, score) {
  return `<div class="risk-score-cell">
    <div class="risk-dot risk-${label}"></div>
    <span class="risk-score-num">${score}</span>
    <span class="badge risk-badge-${label}" style="font-size:11px;padding:2px 8px;">${label}</span>
  </div>`;
}

function timeAgo(isoStr) {
  if (!isoStr) return "—";
  const diff = Date.now() - new Date(isoStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

// ── Task submission ──────────────────────────────────────────────

const textarea = document.getElementById("requestInput");
const submitBtn = document.getElementById("submitBtn");
const resultPanel = document.getElementById("resultPanel");

if (textarea) {
  textarea.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  });

  textarea.addEventListener("input", () => {
    textarea.style.height = "auto";
    textarea.style.height = Math.min(textarea.scrollHeight, 140) + "px";
  });
}

document.querySelectorAll(".example-chip").forEach((chip) => {
  chip.addEventListener("click", () => {
    if (textarea) {
      textarea.value = chip.dataset.text;
      textarea.dispatchEvent(new Event("input"));
      textarea.focus();
    }
  });
});

if (submitBtn) {
  submitBtn.addEventListener("click", handleSubmit);
}

async function handleSubmit() {
  const msg = textarea.value.trim();
  const identifier = document.getElementById("customerIdentifier")?.value.trim() || "";
  currentCustomer = identifier;

  if (!msg) {
    toast("Please describe what you need.", "error");
    return;
  }

  if (!identifier) {
    toast("Please enter your phone or email so we can track your task.", "error");
    document.getElementById("customerIdentifier")?.focus();
    return;
  }

  submitBtn.disabled = true;
  submitBtn.innerHTML = `<div class="spinner"></div> Processing…`;

  resultPanel.classList.remove("visible");

  try {
    const data = await API.submit(msg, identifier);

    if (data.error) {
      toast(data.error, "error");
      return;
    }

    renderResult(data);
    resultPanel.classList.add("visible");
    resultPanel.scrollIntoView({ behavior: "smooth", block: "start" });
    toast("Task created successfully", "success");

    if (typeof loadTasks === "function") loadTasks();
  } catch (err) {
    toast("Something went wrong. Please try again.", "error");
    console.error(err);
  } finally {
    submitBtn.disabled = false;
    submitBtn.innerHTML = `Submit Request`;
  }
}

function renderResult(data) {
  document.getElementById("r-task-code").textContent = data.task_code;
  document.getElementById("r-intent").textContent = formatIntent(data.intent);
  document.getElementById("r-assignment").textContent = data.employee_assignment;

  const returningEl = document.getElementById("r-returning");
  const priorCountEl = document.getElementById("r-prior-count");
  if (data.returning_customer) {
    returningEl.style.display = "block";
    priorCountEl.textContent = `${data.prior_tasks} prior task${data.prior_tasks !== 1 ? "s" : ""} on this account`;
  } else {
    returningEl.style.display = "none";
  }

  const entityWrap = document.getElementById("r-entities");
  entityWrap.innerHTML = "";
  const entities = data.entities || {};
  if (Object.keys(entities).length === 0) {
    entityWrap.innerHTML = `<span class="entity-tag" style="color:var(--text-muted)">No specific details extracted</span>`;
  } else {
    for (const [k, v] of Object.entries(entities)) {
      const tag = document.createElement("div");
      tag.className = "entity-tag";
      tag.innerHTML = `<span>${k.replace(/_/g, " ")}</span>${v}`;
      entityWrap.appendChild(tag);
    }
  }

  const risk = data.risk || {};
  const riskLabel = risk.label || "low";
  document.getElementById("r-risk-score").textContent = risk.score ?? "—";
  document.getElementById("r-risk-score").className = `risk-score-big ${riskLabel}`;
  document.getElementById("r-risk-label").innerHTML =
    `<span class="badge risk-badge-${riskLabel}">${riskLabel} risk</span>`;

  const reasonList = document.getElementById("r-risk-reasons");
  reasonList.innerHTML = "";
  (risk.reasons || []).forEach((r) => {
    const li = document.createElement("li");
    li.textContent = r;
    reasonList.appendChild(li);
  });
  if ((risk.reasons || []).length === 0) {
    const li = document.createElement("li");
    li.textContent = "No elevated risk factors identified.";
    reasonList.appendChild(li);
  }

  const stepsList = document.getElementById("r-steps");
  stepsList.innerHTML = "";
  (data.steps || []).forEach((s) => {
    const li = document.createElement("li");
    li.className = "step-item";
    li.innerHTML = `
      <div class="step-num">${s.step_number}</div>
      <div class="step-content">
        <div class="step-title">${s.title}</div>
        <div class="step-desc">${s.description}</div>
        <div class="step-owner">${s.owner}</div>
      </div>`;
    stepsList.appendChild(li);
  });

  const msgs = data.messages || {};
  document.getElementById("msg-whatsapp").textContent = msgs.whatsapp || "—";
  document.getElementById("msg-email").textContent = msgs.email || "—";
  document.getElementById("msg-sms").textContent = msgs.sms || "—";

  document.querySelectorAll(".msg-tab").forEach((t) => t.classList.remove("active"));
  document.querySelectorAll(".msg-content").forEach((c) => c.classList.remove("active"));
  document.querySelector(".msg-tab[data-tab='whatsapp']").classList.add("active");
  document.getElementById("msg-whatsapp").classList.add("active");
}

document.querySelectorAll(".msg-tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".msg-tab").forEach((t) => t.classList.remove("active"));
    document.querySelectorAll(".msg-content").forEach((c) => c.classList.remove("active"));
    tab.classList.add("active");
    document.getElementById(`msg-${tab.dataset.tab}`).classList.add("active");
  });
});

document.querySelectorAll(".msg-copy").forEach((btn) => {
  btn.addEventListener("click", () => {
    const tab = btn.dataset.for;
    const text = document.getElementById(`msg-${tab}`).textContent;
    navigator.clipboard.writeText(text).then(() => toast("Copied to clipboard"));
  });
});

// ── Dashboard table ──────────────────────────────────────────────

async function loadTasks() {
  const tbody = document.getElementById("tasksBody");
  const statsEl = {
    total: document.getElementById("stat-total"),
    pending: document.getElementById("stat-pending"),
    inprogress: document.getElementById("stat-inprogress"),
    completed: document.getElementById("stat-completed"),
  };

  if (!tbody) return;

  try {
    const tasks = await API.tasks(currentCustomer || "");

    if (!Array.isArray(tasks)) {
      console.error("Invalid tasks response:", tasks);

      tbody.innerHTML = `
        <tr>
          <td colspan="8" style="text-align:center;padding:40px;color:var(--red);">
            Failed to load tasks (server error or invalid response)
          </td>
        </tr>`;

      return;
    }

    if (statsEl.total) {
      statsEl.total.textContent = tasks.length;
      statsEl.pending.textContent = tasks.filter((t) => t.status === "Pending").length;
      statsEl.inprogress.textContent = tasks.filter((t) => t.status === "In Progress").length;
      statsEl.completed.textContent = tasks.filter((t) => t.status === "Completed").length;
    }

    if (tasks.length === 0) {
      tbody.innerHTML = `<tr><td colspan="8" style="text-align:center;padding:40px;color:var(--text-muted);">No tasks yet. Submit a request above to get started.</td></tr>`;
      return;
    }

    tbody.innerHTML = tasks.map((task) => `
      <tr data-id="${task.id}">
        <td><span class="task-code">${task.task_code}</span></td>
        <td><span class="intent-label">${formatIntent(task.intent)}</span></td>
        <td>${riskBadge(task.risk_label || "low", task.risk_score ?? 0)}</td>
        <td>
          <select class="status-select" onchange="changeStatus('${task.id}', this.value)">
            <option ${task.status === "Pending" ? "selected" : ""}>Pending</option>
            <option ${task.status === "In Progress" ? "selected" : ""}>In Progress</option>
            <option ${task.status === "Completed" ? "selected" : ""}>Completed</option>
          </select>
        </td>
        <td><span class="assignment-pill">${task.employee_assignment || "—"}</span></td>
        <td class="ts">${timeAgo(task.created_at)}</td>
        <td><button class="view-btn" onclick="openModal('${task.task_code}')">View</button></td>
      </tr>`).join("");
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="8" style="text-align:center;padding:40px;color:var(--red);">Failed to load tasks. Check your connection.</td></tr>`;
    console.error(err);
  }
}

async function changeStatus(taskId, newStatus) {
  try {
    const result = await API.updateStatus(taskId, newStatus);
    if (result.error) {
      toast(result.error, "error");
    } else {
      toast(`Status updated to ${newStatus}`, "success");
      loadTasks();
    }
  } catch (err) {
    toast("Failed to update status", "error");
  }
}

// ── Task detail modal ─────────────────────────────────────────────

async function openModal(taskCode) {
  const overlay = document.getElementById("taskModal");
  const modalBody = document.getElementById("modalBody");
  overlay.classList.remove("hidden");
  modalBody.innerHTML = `<div style="text-align:center;padding:40px;color:var(--text-muted);">Loading…</div>`;

  try {
    const res = await fetch(`/tasks/${taskCode}/detail`);
    const task = await res.json();

    if (task.error) {
      modalBody.innerHTML = `<p style="color:var(--red)">${task.error}</p>`;
      return;
    }

    const entities = typeof task.entities === "string"
      ? JSON.parse(task.entities) : (task.entities || {});
    const steps = typeof task.steps === "string"
      ? JSON.parse(task.steps) : (task.steps || []);
    const msgs = task.messages || {};

    const entitiesHtml = Object.keys(entities).length
      ? Object.entries(entities).map(([k, v]) =>
        `<div class="entity-tag"><span>${k.replace(/_/g, " ")}</span>${v}</div>`).join("")
      : `<span style="color:var(--text-muted);font-size:13px">No entities extracted</span>`;

    const stepsHtml = steps.length
      ? steps.map((s) => `
          <li class="step-item">
            <div class="step-num">${s.step_number}</div>
            <div class="step-content">
              <div class="step-title">${s.title}</div>
              <div class="step-desc">${s.description}</div>
              <div class="step-owner">${s.owner}</div>
            </div>
          </li>`).join("")
      : `<li style="color:var(--text-muted);font-size:13px;padding:8px 0">No steps available</li>`;

    modalBody.innerHTML = `
      <div class="modal-section">
        <div class="modal-section-title">Request</div>
        <p style="font-size:14px;color:var(--text-secondary);line-height:1.6">${task.original_message || "—"}</p>
      </div>
      <div class="modal-section">
        <div class="modal-section-title">Details</div>
        <div class="entity-list">${entitiesHtml}</div>
      </div>
      <div class="modal-section">
        <div class="modal-section-title">Risk</div>
        <div class="risk-summary">
          <span class="risk-score-big ${task.risk_label}">${task.risk_score}</span>
          <span class="badge risk-badge-${task.risk_label}">${task.risk_label} risk</span>
        </div>
      </div>
      <div class="modal-section">
        <div class="modal-section-title">Fulfilment Steps</div>
        <ul class="steps-list">${stepsHtml}</ul>
      </div>
      <div class="modal-section">
        <div class="modal-section-title">Confirmation Messages</div>
        <div class="msg-tabs" id="modalMsgTabs">
          <button class="msg-tab active" data-tab="m-whatsapp">WhatsApp</button>
          <button class="msg-tab" data-tab="m-email">Email</button>
          <button class="msg-tab" data-tab="m-sms">SMS</button>
        </div>
        <div class="msg-content active" id="msg-m-whatsapp">
          <div class="msg-bubble">${msgs.whatsapp_message || "—"}</div>
        </div>
        <div class="msg-content" id="msg-m-email">
          <div class="msg-bubble">${msgs.email_message || "—"}</div>
        </div>
        <div class="msg-content" id="msg-m-sms">
          <div class="msg-bubble">${msgs.sms_message || "—"}</div>
        </div>
      </div>`;

    document.querySelectorAll("#modalMsgTabs .msg-tab").forEach((tab) => {
      tab.addEventListener("click", () => {
        document.querySelectorAll("#modalMsgTabs .msg-tab").forEach((t) => t.classList.remove("active"));
        document.querySelectorAll("#modalBody .msg-content").forEach((c) => c.classList.remove("active"));
        tab.classList.add("active");
        document.getElementById(`msg-${tab.dataset.tab}`).classList.add("active");
      });
    });
  } catch (err) {
    modalBody.innerHTML = `<p style="color:var(--red)">Failed to load task details.</p>`;
    console.error(err);
  }
}

document.getElementById("modalClose")?.addEventListener("click", () => {
  document.getElementById("taskModal").classList.add("hidden");
});

document.getElementById("taskModal")?.addEventListener("click", (e) => {
  if (e.target === e.currentTarget) e.currentTarget.classList.add("hidden");
});

if (document.getElementById("tasksBody")) {
  loadTasks();
}
