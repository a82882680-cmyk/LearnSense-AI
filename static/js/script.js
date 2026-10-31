/*
  script.js - all browser-side behaviour for LearnSense AI
  ---------------------------------------------------------
  Everything lives inside one object called LS so that each page
  can call just the function it needs, e.g. LS.initStudents().
*/
const LS = (() => {
  // Project colours (same as the CSS)
  const C = { cream: "#FFF9F0", forest: "#243B32", sage: "#A8B5A0", butter: "#F4D875", coral: "#DD8978" };

  /* ---------- small helpers ---------- */
  const $ = (sel, root = document) => root.querySelector(sel);

  /** Create an element with optional class and text (textContent is safe from HTML injection). */
  function el(tag, cls, text) {
    const node = document.createElement(tag);
    if (cls) node.className = cls;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  /** Get JSON from the Flask backend. Throws a readable error if something fails. */
  async function getJSON(url) {
    const res = await fetch(url);
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.error || "Could not load data.");
    return data;
  }

  /** Send JSON to the backend with POST. */
  async function postJSON(url, body) {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.error || "Something went wrong.");
    return data;
  }

  /** Show a message inside a chart box when a chart cannot be drawn. */
  function chartMessage(canvas, text) {
    const box = canvas.parentElement;
    box.textContent = "";
    box.appendChild(el("p", "notice", text));
  }

  /** Make one Chart.js chart (with a friendly fallback if Chart.js did not load). */
  function makeChart(id, config) {
    const canvas = document.getElementById(id);
    if (!canvas) return null;
    if (typeof Chart === "undefined") {
      chartMessage(canvas, "Chart.js could not load (check your internet connection). The Python-generated charts on the Data Visualisation page still work.");
      return null;
    }
    Chart.defaults.font.family = "Inter, system-ui, sans-serif";
    Chart.defaults.color = C.forest;
    config.options = Object.assign({ responsive: true, maintainAspectRatio: false }, config.options || {});
    return new Chart(canvas, config);
  }

  /** Shortcut for axis settings. */
  function axis(title, extra = {}) {
    return Object.assign({
      title: { display: true, text: title },
      grid: { color: "#EEE8DA" },
    }, extra);
  }

  /** Load chart data once and run a callback with it. */
  async function withChartData(callback) {
    try {
      callback(await getJSON("/api/chart-data"));
    } catch (err) {
      document.querySelectorAll("canvas").forEach(c => chartMessage(c, err.message));
    }
  }

  /* ---------- navigation (mobile menu) ---------- */
  function initMenu() {
    const btn = $("#menuBtn");
    const side = $("#sidebar");
    if (!btn || !side) return;
    btn.addEventListener("click", () => {
      const open = side.classList.toggle("open");
      btn.setAttribute("aria-expanded", String(open));
    });
  }

  /* ---------- PAGE: Home ---------- */
  function initHome() {
    withChartData(d => {
      const avg = a => a.reduce((x, y) => x + y, 0) / a.length;
      const r1 = n => Math.round(n * 10) / 10;
      makeChart("homeActivityChart", {
        type: "bar",
        data: {
          labels: ["Attendance", "Assignments", "Revision", "Quiz"],
          datasets: [{
            label: "Class average (%)",
            data: [r1(avg(d.attendance)), r1(avg(d.assignment)), r1(avg(d.revision_pct)), r1(avg(d.quiz_pct))],
            backgroundColor: [C.forest, C.sage, C.sage, C.butter],
            borderColor: C.forest, borderWidth: 1,
          }],
        },
        options: { scales: { y: axis("Average (%)", { min: 0, max: 100 }), x: { grid: { display: false } } },
                   plugins: { legend: { display: false } } },
      });
      makeChart("homeCombinedChart", {
        type: "bar",
        data: {
          labels: d.ids,
          datasets: [{ label: "Combined score", data: d.combined,
                       backgroundColor: d.combined.map(v => v === Math.max(...d.combined) ? C.butter : C.sage),
                       borderColor: C.forest, borderWidth: 1 }],
        },
        options: { scales: { y: axis("Score (0-100)", { min: 0, max: 100 }), x: { grid: { display: false } } },
                   plugins: { legend: { display: false } } },
      });
    });
  }

  /* ---------- PAGE: Analytics ---------- */
  function initAnalytics() {
    withChartData(d => {
      makeChart("analyticsIndicatorChart", {
        type: "bar",
        data: {
          labels: d.ids,
          datasets: [
            { label: "Attendance (%)", data: d.attendance, backgroundColor: C.forest },
            { label: "Assignments (%)", data: d.assignment, backgroundColor: C.sage },
            { label: "Revision (%)", data: d.revision_pct, backgroundColor: "#C9D3C2" },
            { label: "Quiz (%)", data: d.quiz_pct, backgroundColor: C.coral },
          ],
        },
        options: { scales: { y: axis("Percentage (%)", { min: 0, max: 100 }), x: { grid: { display: false } } } },
      });
      makeChart("analyticsModuleChart", {
        type: "bar",
        data: {
          labels: d.modules.map(m => m.module_name),
          datasets: [
            { label: "Attendance (%)", data: d.modules.map(m => m.avg_attendance), backgroundColor: C.forest },
            { label: "Assignments (%)", data: d.modules.map(m => m.avg_assignment), backgroundColor: C.sage },
            { label: "Revision (%)", data: d.modules.map(m => m.avg_revision_pct), backgroundColor: C.butter },
            { label: "Quiz (%)", data: d.modules.map(m => m.avg_quiz_pct), backgroundColor: C.coral },
          ],
        },
        options: { scales: { y: axis("Weighted average (%)", { min: 0, max: 100 }), x: { grid: { display: false } } } },
      });
    });
  }

  /* ---------- PAGE: Charts ---------- */
  function initCharts() {
    withChartData(d => {
      makeChart("chartAttendance", {
        type: "bar",
        data: { labels: d.ids, datasets: [
          { label: "Attendance (%)", data: d.attendance, backgroundColor: C.forest },
          { label: "Assignment completion (%)", data: d.assignment, backgroundColor: C.sage },
        ] },
        options: { scales: { y: axis("Percentage (%)", { min: 0, max: 100 }), x: axis("Simulated student", { grid: { display: false } }) } },
      });

      makeChart("chartQuiz", {
        type: "bar",
        data: { labels: d.ids, datasets: [{
          label: "Quiz score (out of 10)", data: d.quiz_score,
          backgroundColor: d.quiz_score.map(q => q < 5 ? C.coral : C.forest),
        }] },
        options: { scales: { y: axis("Quiz score (out of 10)", { min: 0, max: 10 }), x: axis("Simulated student", { grid: { display: false } }) },
                   plugins: { legend: { display: false } } },
      });

      makeChart("chartRevision", {
        type: "scatter",
        data: { datasets: [{
          label: "Student",
          data: d.ids.map((id, i) => ({ x: d.revision_sessions[i], y: d.quiz_score[i], id })),
          backgroundColor: C.forest, pointRadius: 8, pointHoverRadius: 10,
        }] },
        options: {
          scales: { x: axis("Revision sessions (out of 10)", { min: 4, max: 10.5 }), y: axis("Quiz score (out of 10)", { min: 0, max: 10 }) },
          plugins: { legend: { display: false },
                     tooltip: { callbacks: { label: ctx => `${ctx.raw.id}: revision ${ctx.raw.x}/10, quiz ${ctx.raw.y}/10` } } },
        },
        plugins: [{
          // Draw the student ID next to each dot so the chart is readable without hovering
          id: "pointLabels",
          afterDatasetsDraw(chart) {
            const ctx = chart.ctx;
            ctx.save();
            ctx.fillStyle = C.forest;
            ctx.font = "600 12px Inter, sans-serif";
            chart.getDatasetMeta(0).data.forEach((pt, i) => ctx.fillText(chart.data.datasets[0].data[i].id, pt.x + 12, pt.y - 8));
            ctx.restore();
          },
        }],
      });

      const top = Math.max(...d.combined);
      makeChart("chartCombined", {
        type: "bar",
        data: { labels: d.ids, datasets: [{
          label: "Combined score", data: d.combined,
          backgroundColor: d.combined.map(v => v === top ? C.butter : C.sage),
          borderColor: C.forest, borderWidth: 1,
        }] },
        options: { scales: { y: axis("Score (0-100)", { min: 0, max: 100 }), x: axis("Simulated student", { grid: { display: false } }) },
                   plugins: { legend: { display: false } } },
      });

      const palette = [C.forest, C.coral, C.sage, "#B89B2E", "#6B7F73"];
      makeChart("chartIndicators", {
        type: "line",
        data: {
          labels: ["Attendance", "Assignments", "Revision", "Quiz"],
          datasets: d.ids.map((id, i) => ({
            label: id,
            data: [d.attendance[i], d.assignment[i], d.revision_pct[i], d.quiz_pct[i]],
            borderColor: palette[i % palette.length], backgroundColor: palette[i % palette.length],
            tension: 0.15, pointRadius: 4,
          })),
        },
        options: { scales: { y: axis("Percentage (%)", { min: 0, max: 100 }), x: { grid: { display: false } } } },
      });

      makeChart("chartDistribution", {
        type: "bar",
        data: { labels: d.distribution_labels, datasets: [{
          label: "Number of students", data: d.distribution_values,
          backgroundColor: [C.coral, C.sage, C.butter], borderColor: C.forest, borderWidth: 1,
        }] },
        options: { scales: { y: axis("Number of students", { min: 0, ticks: { stepSize: 1 } }), x: axis("Combined score band", { grid: { display: false } }) },
                   plugins: { legend: { display: false } } },
      });
    });
  }

  /* ---------- PAGE: Students (search, filter, sort, details) ---------- */
  function initStudents() {
    const dataNode = $("#studentData");
    if (!dataNode) return;
    const all = JSON.parse(dataNode.textContent);
    const tbody = $("#studentTable tbody");
    const search = $("#searchBox");
    const band = $("#bandFilter");
    const pattern = $("#patternFilter");
    let sortKey = "student_id";
    let sortDir = 1; // 1 = ascending, -1 = descending

    function passes(s) {
      const text = search.value.trim().toLowerCase();
      if (text && !s.student_id.toLowerCase().includes(text)) return false;
      if (band.value && s.band !== band.value) return false;
      if (pattern.value === "gap" && !s.gap_flag) return false;
      if (pattern.value === "lowact" && !(s.attendance < 75)) return false;
      if (pattern.value === "quizok" && !(s.quiz_score >= 7)) return false;
      return true;
    }

    function render() {
      const rows = all.filter(passes).sort((a, b) => {
        const x = a[sortKey], y = b[sortKey];
        return (typeof x === "string" ? x.localeCompare(y) : x - y) * sortDir;
      });
      tbody.textContent = "";
      rows.forEach(s => {
        const tr = el("tr", s.gap_flag ? "row-flag" : "");
        tr.appendChild(el("td", "", s.student_id));
        tr.appendChild(el("td", "", s.attendance + "%"));
        tr.appendChild(el("td", "", s.assignment_completion + "%"));
        tr.appendChild(el("td", "", s.quiz_score + "/10"));
        tr.appendChild(el("td", "", s.revision_sessions + "/10"));
        const sc = el("td"); sc.appendChild(el("strong", "hl", s.combined_score.toFixed(2))); tr.appendChild(sc);
        const act = el("td");
        const b = el("button", "btn small ghost", "View");
        b.type = "button";
        b.addEventListener("click", () => showDetail(s));
        act.appendChild(b); tr.appendChild(act);
        tbody.appendChild(tr);
      });
      if (!rows.length) {
        const tr = el("tr"); const td = el("td", "empty", "No records match your search or filters.");
        td.colSpan = 7; tr.appendChild(td); tbody.appendChild(tr);
      }
      $("#countText").textContent = `Showing ${rows.length} of ${all.length} simulated records.`;
      document.querySelectorAll("#studentTable th[data-key]").forEach(th => {
        th.classList.toggle("sorted", th.dataset.key === sortKey);
        th.dataset.dir = th.dataset.key === sortKey ? (sortDir === 1 ? "asc" : "desc") : "";
      });
    }

    function bar(label, pct, text, colour) {
      const wrap = el("div", "bar-row");
      wrap.appendChild(el("span", "bar-label", label));
      const track = el("div", "bar-track");
      const fill = el("div", "bar-fill");
      fill.style.width = Math.max(0, Math.min(100, pct)) + "%";
      fill.style.background = colour;
      track.appendChild(fill);
      wrap.appendChild(track);
      wrap.appendChild(el("span", "bar-val", text));
      return wrap;
    }

    function showDetail(s) {
      $("#detailTitle").textContent = `${s.student_id} \u2013 learning indicators (simulated)`;
      const box = $("#detailBars");
      box.textContent = "";
      box.appendChild(bar("Attendance", s.attendance, s.attendance + "%", C.forest));
      box.appendChild(bar("Assignments", s.assignment_completion, s.assignment_completion + "%", C.sage));
      box.appendChild(bar("Revision", s.revision_pct, s.revision_sessions + "/10", C.sage));
      box.appendChild(bar("Quiz", s.quiz_pct, s.quiz_score + "/10", C.coral));
      box.appendChild(bar("Combined", s.combined_score, s.combined_score.toFixed(2), C.butter));
      $("#detailNote").textContent =
        `Activity average ${s.activity_avg}% compared with quiz ${s.quiz_pct}%. ` +
        (s.gap_flag
          ? "Activity is high while the quiz result is lower, so a friendly check-in could help find out why."
          : "No large mismatch between activity and quiz result is flagged by our simple rule.") +
        " This is one small snapshot, not a judgement.";
      const panel = $("#detailPanel");
      panel.hidden = false;
      panel.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }

    [search, band, pattern].forEach(n => n.addEventListener("input", render));
    $("#resetBtn").addEventListener("click", () => {
      search.value = ""; band.value = ""; pattern.value = "";
      sortKey = "student_id"; sortDir = 1; render();
    });
    $("#closeDetail").addEventListener("click", () => { $("#detailPanel").hidden = true; });
    document.querySelectorAll("#studentTable th[data-key]").forEach(th => {
      th.addEventListener("click", () => {
        if (sortKey === th.dataset.key) sortDir *= -1; else { sortKey = th.dataset.key; sortDir = 1; }
        render();
      });
    });
    render();
  }

  /* ---------- PAGE: LearnSense AI ---------- */
  function formToNumbers(form, names, prefix = "") {
    const out = {};
    names.forEach(n => { out[n] = form.elements[prefix + n].value; });
    return out;
  }

  function showError(node, message) {
    node.textContent = message;
    node.hidden = !message;
  }

  function renderAnalysis(r) {
    $("#resultPanel").hidden = false;
    $("#indexNum").textContent = r.friction_index;
    const fill = $("#meterFill");
    fill.style.width = r.friction_index + "%";
    fill.style.background = r.friction_index >= 75 ? C.coral : r.friction_index >= 50 ? C.butter : C.sage;
    $("#bandText").textContent = r.band;
    $("#interpretText").textContent = r.interpretation;
    $("#disclaimerText").textContent = r.disclaimer;

    const tb = $("#breakdownTable tbody");
    tb.textContent = "";
    r.breakdown.forEach(b => {
      const tr = el("tr");
      tr.appendChild(el("td", "", `${b.label} (max ${b.weight})`));
      tr.appendChild(el("td", "", b.how));
      const p = el("td"); p.appendChild(el("strong", "", b.points.toFixed(1))); tr.appendChild(p);
      tb.appendChild(tr);
    });

    const sl = $("#signalList");
    sl.textContent = "";
    if (!r.signals.length) sl.appendChild(el("li", "", "No signal crossed its threshold in this session."));
    r.signals.forEach(s => {
      const li = el("li");
      li.appendChild(el("strong", "", s.title + ": "));
      li.appendChild(document.createTextNode(s.detail));
      sl.appendChild(li);
    });

    const rl = $("#recList");
    rl.textContent = "";
    r.recommendations.forEach((rec, i) => {
      const card = el("article", "rec");
      card.appendChild(el("h4", "", `${i + 1}. ${rec.suggestion}`));
      [["Signal detected", rec.signal_detected], ["Why it matters", rec.why_it_matters],
       ["Why this support", rec.why_this_support]].forEach(([k, v]) => {
        const p = el("p"); p.appendChild(el("strong", "", k + ": ")); p.appendChild(document.createTextNode(v));
        card.appendChild(p);
      });
      rl.appendChild(card);
    });
    $("#resultPanel").scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function initLearnSense() {
    const form = $("#sessionForm");
    if (!form) return;
    const fields = ["expected_time", "actual_time", "attempts", "unsuccessful", "hints"];
    const scenarios = JSON.parse($("#scenarioData").textContent);

    form.addEventListener("submit", async e => {
      e.preventDefault();
      showError($("#formError"), "");
      try {
        renderAnalysis(await postJSON("/api/analyse", formToNumbers(form, fields)));
      } catch (err) {
        $("#resultPanel").hidden = true;
        showError($("#formError"), err.message);
      }
    });

    document.querySelectorAll("#scenarioRow .chip").forEach(chip => {
      chip.addEventListener("click", () => {
        const sc = scenarios.find(s => s.id === chip.dataset.id);
        if (!sc) return;
        fields.forEach(f => { form.elements[f].value = sc.inputs[f]; });
        document.querySelectorAll("#scenarioRow .chip").forEach(c => c.classList.toggle("on", c === chip));
        $("#scenarioDesc").textContent = `${sc.name}: ${sc.description} Press ANALYSE LEARNING SESSION to see the result.`;
        showError($("#formError"), "");
      });
    });

    const rf = $("#reassessForm");
    rf.addEventListener("submit", async e => {
      e.preventDefault();
      showError($("#reassessError"), "");
      try {
        const r = await postJSON("/api/reassess", {
          before: formToNumbers(rf, fields, "b_"),
          after: formToNumbers(rf, fields, "a_"),
          quiz_before: rf.elements.quiz_before.value,
          quiz_after: rf.elements.quiz_after.value,
        });
        const tb = $("#reassessTable tbody");
        tb.textContent = "";
        r.rows.forEach(row => {
          const tr = el("tr");
          tr.appendChild(el("td", "", row.label));
          tr.appendChild(el("td", "", row.before + (row.unit ? " " + row.unit : "")));
          tr.appendChild(el("td", "", row.after + (row.unit ? " " + row.unit : "")));
          tr.appendChild(el("td", "", (row.change > 0 ? "+" : "") + row.change));
          tr.appendChild(el("td", "", row.note));
          tb.appendChild(tr);
        });
        $("#reassessSummary").textContent = r.summary;
        $("#reassessNext span").textContent = r.next_step;
        $("#reassessDisclaimer").textContent = r.disclaimer;
        $("#reassessResult").hidden = false;
      } catch (err) {
        $("#reassessResult").hidden = true;
        showError($("#reassessError"), err.message);
      }
    });
  }

  /* ---------- PAGE: About (extra team members saved in this browser only) ---------- */
  function initAbout() {
    const list = $("#teamList");
    if (!list) return;
    const KEY = "learnsense_extra_members";

    function load() {
      try { return JSON.parse(localStorage.getItem(KEY)) || []; } catch (e) { return []; }
    }
    function save(items) {
      try { localStorage.setItem(KEY, JSON.stringify(items)); return true; } catch (e) { return false; }
    }
    function draw() {
      list.querySelectorAll("li.added").forEach(li => li.remove());
      load().forEach(m => {
        const li = el("li", "added");
        li.appendChild(el("strong", "", m.name));
        li.appendChild(el("span", "", m.role));
        list.appendChild(li);
      });
    }

    $("#teamForm").addEventListener("submit", e => {
      e.preventDefault();
      const name = $("#memberName").value.trim();
      const role = $("#memberRole").value.trim();
      const err = $("#teamError");
      if (!name || !role) { showError(err, "Please enter both a name and a contribution."); return; }
      const items = load(); items.push({ name, role });
      if (!save(items)) { showError(err, "This browser blocked saving. The member was not added."); return; }
      showError(err, ""); $("#memberName").value = ""; $("#memberRole").value = ""; draw();
    });
    $("#clearTeam").addEventListener("click", () => { save([]); draw(); });
    draw();
  }

  document.addEventListener("DOMContentLoaded", initMenu);
  return { initHome, initAnalytics, initCharts, initStudents, initLearnSense, initAbout };
})();
