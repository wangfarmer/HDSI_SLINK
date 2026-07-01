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

const AI_LABELS = {
  ai_native: "AI-Native",
  ai_adjacent: "AI-Adjacent",
  ai_bridge: "AI-Bridge / Domain Expert",
  discovery_candidate: "Non-AI / Discovery Candidate",
};

let profiles = [];

function schoolLabel(key) {
  return SCHOOL_LABELS[key] || key.replaceAll("_", " ");
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function renderStats(stats) {
  document.getElementById("stats").innerHTML = `
    <div class="stat-card"><strong>${stats.profiles?.toLocaleString() ?? "0"}</strong><span>Profiles scored</span></div>
    <div class="stat-card"><strong>${stats.recs_1 ?? 0}</strong><span>1 S-Link</span></div>
    <div class="stat-card"><strong>${(stats.recs_2 ?? 0) + (stats.recs_3 ?? 0)}</strong><span>2–3 S-Links</span></div>
    <div class="stat-card"><strong>${stats.ai_ai_native ?? 0}</strong><span>AI-Native</span></div>
  `;
}

function renderDomainBars(domainScores) {
  const top = [...(domainScores || [])].sort((a, b) => b.score - a.score).slice(0, 4);
  return top.map((domain) => `
    <div class="domain-row">
      <span>${escapeHtml(domain.domain_name)}</span>
      <div class="bar-track"><div class="bar-fill" style="width:${Math.round(domain.score * 100)}%"></div></div>
      <strong>${domain.score.toFixed(2)}</strong>
    </div>
  `).join("");
}

function renderTags(tags, className) {
  if (!tags?.length) {
    return `<span class="muted">—</span>`;
  }
  return tags.map((tag) => `<span class="badge ${className}">${escapeHtml(tag)}</span>`).join("");
}

function renderRecommendations(recommendations) {
  if (!recommendations?.length) {
    return `<p class="muted">No distinct S-Link recommendation met the confidence threshold.</p>`;
  }
  return recommendations.map((rec, index) => `
    <article class="rec-card">
      <h4>S-Link ${index + 1}: ${escapeHtml(rec.title)}</h4>
      <p class="muted">${escapeHtml(rec.rationale)}</p>
      <ul>
        ${rec.suggested_partners.map((partner) => `
          <li>
            <strong>${escapeHtml(partner.full_name)}</strong>
            <span class="muted">(${escapeHtml(schoolLabel(partner.school_key))}, score ${partner.score.toFixed(2)})</span>
            <div class="muted">${escapeHtml(partner.rationale)}</div>
          </li>
        `).join("")}
      </ul>
    </article>
  `).join("");
}

function renderProfiles(rows) {
  const list = document.getElementById("profile-list");
  if (!rows.length) {
    list.innerHTML = `<p class="muted panel-empty">No profiles match the current filters.</p>`;
    return;
  }

  list.innerHTML = rows.map((profile) => `
    <article class="profile-card">
      <div class="profile-head">
        <div>
          <h3>${escapeHtml(profile.full_name)}</h3>
          <p class="muted">${escapeHtml(schoolLabel(profile.school_key))}${profile.title ? ` · ${escapeHtml(profile.title)}` : ""}</p>
        </div>
        <div class="tag-row">
          <span class="badge ai">${escapeHtml(profile.ai_readiness_label || AI_LABELS[profile.ai_readiness] || profile.ai_readiness)}</span>
          <span class="badge focus">${profile.research_foci.length} focus${profile.research_foci.length === 1 ? "" : "es"}</span>
          <span class="badge rec">${profile.slink_recommendations.length} S-Link${profile.slink_recommendations.length === 1 ? "" : "s"}</span>
        </div>
      </div>

      <div class="profile-grid">
        <section>
          <h4>Domain scores</h4>
          ${renderDomainBars(profile.domain_scores)}
        </section>
        <section>
          <h4>Research foci</h4>
          <ul class="focus-list">
            ${profile.research_foci.map((focus) => `
              <li><strong>${escapeHtml(focus.label)}</strong> <span class="muted">(${focus.strength.toFixed(2)})</span></li>
            `).join("")}
          </ul>
          <h4>Method / application tags</h4>
          <div class="tag-row">${renderTags(profile.methodological_tags, "method")} ${renderTags(profile.application_tags, "app")}</div>
          ${profile.ai_readiness_rationale ? `<p class="muted readiness-note">${escapeHtml(profile.ai_readiness_rationale)}</p>` : ""}
        </section>
      </div>

      <section>
        <h4>S-Link recommendations</h4>
        ${renderRecommendations(profile.slink_recommendations)}
      </section>
    </article>
  `).join("");
}

function applyFilters() {
  const query = document.getElementById("search").value.trim().toLowerCase();
  const aiFilter = document.getElementById("ai-filter").value;
  const recFilter = document.getElementById("rec-filter").value;

  const filtered = profiles.filter((profile) => {
    const haystack = [
      profile.full_name,
      profile.title,
      profile.ai_readiness,
      ...(profile.domain_scores || []).map((d) => d.domain_name),
      ...(profile.methodological_tags || []),
      ...(profile.application_tags || []),
      ...(profile.research_foci || []).map((f) => f.label),
    ].join(" ").toLowerCase();

    if (query && !haystack.includes(query)) return false;
    if (aiFilter !== "all" && profile.ai_readiness !== aiFilter) return false;
    if (recFilter !== "all" && String(profile.slink_recommendations.length) !== recFilter) return false;
    return true;
  });

  renderProfiles(filtered.slice(0, 120));
}

async function init() {
  const [profilesResponse, statsResponse] = await Promise.all([
    fetch("./data/slink_profiles.json"),
    fetch("./data/slink_stats.json"),
  ]);
  profiles = await profilesResponse.json();
  renderStats(await statsResponse.json());
  renderProfiles(profiles.slice(0, 120));

  document.getElementById("search").addEventListener("input", applyFilters);
  document.getElementById("ai-filter").addEventListener("change", applyFilters);
  document.getElementById("rec-filter").addEventListener("change", applyFilters);
}

init().catch((error) => {
  document.getElementById("profile-list").innerHTML =
    `<p class="muted panel-empty">Failed to load S-Link profiles: ${escapeHtml(error.message)}</p>`;
});
