const SCHOOL_LABELS = {
  harvard_t_h_chan_school_public_health_people: "Chan School of Public Health",
  harvard_radcliffe_institute_people: "Radcliffe Institute",
  boston_childrens_hospital_people: "Boston Children's Hospital",
  harvard_business_school_people: "Harvard Business School",
  harvard_kennedy_school_people: "Harvard Kennedy School",
  harvard_law_school_people: "Harvard Law School",
  harvard_education_school_people: "Harvard Graduate School of Education",
  harvard_graduate_school_of_design_people: "Harvard Graduate School of Design",
  harvard_school_of_dental_medicine_people: "Harvard School of Dental Medicine",
  harvard_seas_people: "Harvard SEAS",
  harvard_medical_school_people: "Harvard Medical School",
  harvard_wyss_institute_people: "Wyss Institute",
  harvard_data_science_initiative_people: "Harvard Data Science Initiative",
  harvard_gsas_staff_people: "Harvard GSAS",
  harvard_extension_school_people: "Harvard Extension School",
  harvard_college_dso_staff_people: "Harvard College",
  harvard_divinity_school_people: "Harvard Divinity School",
};

let people = [];

function schoolLabel(key) {
  return SCHOOL_LABELS[key] || key.replaceAll("_", " ");
}

function orcidUrl(orcid) {
  return `https://orcid.org/${orcid}`;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function renderStats(stats) {
  const statsNode = document.getElementById("stats");
  statsNode.innerHTML = `
    <div class="stat-card"><strong>${stats.profiles_seen?.toLocaleString() ?? "0"}</strong><span>Profiles</span></div>
    <div class="stat-card"><strong>${stats.matched?.toLocaleString() ?? "0"}</strong><span>ORCID matched</span></div>
    <div class="stat-card"><strong>${stats.match_rate_pct ?? 0}%</strong><span>Match rate</span></div>
    <div class="stat-card"><strong>${stats.orcid_records?.toLocaleString() ?? "0"}</strong><span>ORCID names loaded</span></div>
  `;
}

function renderRows(rows) {
  const body = document.getElementById("people-body");
  if (!rows.length) {
    body.innerHTML = `<tr><td colspan="5" class="muted">No people match the current filters.</td></tr>`;
    return;
  }

  body.innerHTML = rows.map((person) => {
    const profileLink = person.profile_url
      ? `<a href="${escapeHtml(person.profile_url)}" target="_blank" rel="noreferrer">${escapeHtml(person.full_name)}</a>`
      : escapeHtml(person.full_name);
    const orcidCell = person.orcid
      ? `<a class="orcid-link" href="${orcidUrl(person.orcid)}" target="_blank" rel="noreferrer">${escapeHtml(person.orcid)}</a>`
      : `<span class="muted">—</span>`;
    const matchCell = person.orcid
      ? `<span class="badge ok">${escapeHtml(person.orcid_match_method || "matched")}</span>`
      : `<span class="badge miss">unmatched</span>`;

    return `
      <tr>
        <td class="name-cell">${profileLink}</td>
        <td>${escapeHtml(schoolLabel(person.school_key))}</td>
        <td>${escapeHtml(person.title || "—")}</td>
        <td>${orcidCell}</td>
        <td>${matchCell}</td>
      </tr>
    `;
  }).join("");
}

function applyFilters() {
  const query = document.getElementById("search").value.trim().toLowerCase();
  const matchFilter = document.getElementById("match-filter").value;

  const filtered = people.filter((person) => {
    const haystack = [
      person.full_name,
      person.title,
      person.email,
      person.orcid,
      schoolLabel(person.school_key),
    ].join(" ").toLowerCase();

    if (query && !haystack.includes(query)) {
      return false;
    }
    if (matchFilter === "matched" && !person.orcid) {
      return false;
    }
    if (matchFilter === "unmatched" && person.orcid) {
      return false;
    }
    return true;
  });

  renderRows(filtered);
}

async function init() {
  const [peopleResponse, statsResponse] = await Promise.all([
    fetch("./data/people.json"),
    fetch("./data/stats.json"),
  ]);
  people = await peopleResponse.json();
  const stats = await statsResponse.json();
  renderStats(stats);
  renderRows(people);

  document.getElementById("search").addEventListener("input", applyFilters);
  document.getElementById("match-filter").addEventListener("change", applyFilters);
}

init().catch((error) => {
  document.getElementById("people-body").innerHTML =
    `<tr><td colspan="5" class="muted">Failed to load people data: ${escapeHtml(error.message)}</td></tr>`;
});
