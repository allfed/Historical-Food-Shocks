/* Historical Food Shocks — interactive explorer
 * Loads pre-baked JSON/GeoJSON (see scripts that generate docs/data/*.json)
 * and renders a map + linked category chart. No build step required.
 */

(function () {
  "use strict";

  const state = {
    mode: "magnitude", // 'magnitude' | 'reason'
    chartGroup: "continent", // 'continent' | 'decade'
    categoryFilter: null,
    geojson: null,
    categorySummary: null,
    headlineStats: null,
  };

  const NO_DATA_COLOR = "#f0ece4";

  const tooltip = d3.select("body")
    .append("div")
    .attr("class", "tooltip");

  Promise.all([
    d3.json("data/headline_stats.json"),
    d3.json("data/countries.geojson"),
    d3.json("data/category_summary.json"),
    d3.json("data/yearly_by_country.json"),
    d3.json("data/decade_shock_counts.json"),
  ]).then(([stats, geojson, categorySummary, yearlyByCountry, decadeCounts]) => {
    state.headlineStats = stats;
    state.geojson = geojson;
    state.categorySummary = categorySummary;
    state.yearlyByCountry = yearlyByCountry;
    state.decadeCounts = decadeCounts;

    renderSpotlight(stats.spotlight);
    renderStats(stats);
    initMap(geojson);
    initToggles();
    renderChart();
    renderDecadeGrid(geojson, decadeCounts);
  }).catch((err) => {
    console.error("Failed to load data", err);
    document.getElementById("statsGrid").innerHTML =
      '<p style="color:#a33">Could not load data. If you are viewing this locally, serve the docs/ folder over HTTP (e.g. `python -m http.server`) rather than opening index.html directly.</p>';
  });

  // ---------------- Spotlight ----------------

  function renderSpotlight(spotlight) {
    const card = document.getElementById("spotlightCard");
    if (!spotlight) {
      card.hidden = true;
      return;
    }
    const absPct = Math.abs(spotlight.pct);
    card.innerHTML = `
      <p class="spotlight-eyebrow">The single worst shock on record</p>
      <p class="spotlight-headline">
        In <strong>${spotlight.year}</strong>, <strong>${spotlight.country}</strong>&rsquo;s
        food-calorie production fell <strong>${absPct}%</strong> below trend in a single year &mdash;
        roughly ${Math.round(absPct)} of every 100 calories the country would normally have grown, gone.
      </p>
      ${spotlight.reason ? `<p class="spotlight-reason">${spotlight.reason}</p>` : ""}
      <p class="spotlight-footnote">
        ${spotlight.category ? `Category: ${spotlight.category}. ` : ""}
        ${
          spotlight.source
            ? `Source: ${
                spotlight.source_link
                  ? `<a href="${spotlight.source_link}" target="_blank" rel="noopener">${spotlight.source}</a>`
                  : spotlight.source
              }.`
            : ""
        }
        This is one of ${state.headlineStats ? state.headlineStats.total_country_shock_events.toLocaleString() : "thousands of"}
        country-year shocks recorded since 1961 &mdash; explore them all below.
      </p>
    `;

    const introEl = document.getElementById("statsIntro");
    if (introEl) {
      introEl.textContent = `${spotlight.country}’s ${spotlight.year} collapse above wasn’t a one-off. This has been the pattern for six decades:`;
    }
  }

  // ---------------- Stats ----------------

  function renderStats(stats) {
    const cards = [
      {
        value: `${stats.years_with_a_shock_somewhere}/${stats.total_years_covered}`,
        label: `years since ${stats.year_min} had a national-scale food shock happening somewhere in the world`,
      },
      {
        value: `${Math.round(stats.avg_shocks_per_year)}`,
        label: "country-level food production shocks occur on average, every single year",
      },
      {
        value: `${stats.n_severe_shocks}`,
        label: `of ${stats.n_countries} countries have suffered a single-year drop of 20%+ in food-calorie production`,
      },
      {
        value: stats.total_country_shock_events.toLocaleString(),
        label: `individual country-year shock events recorded, ${stats.year_min}–${stats.year_max}`,
      },
    ];

    const grid = document.getElementById("statsGrid");
    grid.innerHTML = cards
      .map(
        (c) => `
        <div class="stat-card">
          <span class="stat-number">${c.value}</span>
          <span class="stat-label">${c.label}</span>
        </div>`
      )
      .join("");
  }

  // ---------------- Map ----------------

  let path, colorScaleMagnitude, minShock;

  function initMap(geojson) {
    const svg = d3.select("#map");
    const width = 960, height = 500;

    const projection = d3.geoNaturalEarth1().fitSize([width, height], geojson);
    path = d3.geoPath(projection);

    minShock = d3.min(geojson.features, (f) => f.properties.shock_pct);
    colorScaleMagnitude = d3.scaleSequential(d3.interpolateYlOrBr).domain([0, minShock]);

    svg
      .selectAll("path.country")
      .data(geojson.features)
      .join("path")
      .attr("class", "country")
      .attr("d", path)
      .on("mousemove", (event, d) => showTooltip(event, d))
      .on("mouseleave", hideTooltip)
      .on("click", (event, d) => selectCountry(d));

    colorMap();
    renderLegend();
  }

  function colorMap() {
    d3.selectAll("path.country")
      .classed("no-data", (d) => d.properties.shock_pct == null)
      .attr("fill", (d) => {
        if (state.mode === "magnitude") {
          return d.properties.shock_pct == null
            ? NO_DATA_COLOR
            : colorScaleMagnitude(d.properties.shock_pct);
        }
        return d.properties.category_color || NO_DATA_COLOR;
      })
      .classed("dimmed", (d) => {
        if (!state.categoryFilter) return false;
        return d.properties.category_main !== state.categoryFilter;
      });
  }

  function showTooltip(event, d) {
    const p = d.properties;
    let html = `<strong>${p.name}</strong>`;
    if (p.shock_pct != null) {
      html += `<br>${p.shock_pct}% in ${p.shock_year}`;
      if (state.mode === "reason") html += `<br>${p.category_main}`;
    } else {
      html += "<br>No shock data";
    }
    tooltip
      .html(html)
      .style("opacity", 1)
      .style("left", event.clientX + 14 + "px")
      .style("top", event.clientY + 10 + "px");
  }

  function hideTooltip() {
    tooltip.style("opacity", 0);
  }

  function selectCountry(d) {
    const p = d.properties;
    const panel = document.getElementById("detailPanel");

    if (p.shock_pct == null) {
      panel.innerHTML = `
        <p class="detail-country">${p.name}</p>
        <p class="detail-placeholder">No shock data available for this country in the underlying FAO series.</p>`;
      return;
    }

    const badgeColor = p.category_color || "#808080";
    panel.innerHTML = `
      <p class="detail-country">${p.name}</p>
      <p class="detail-year">Worst shock on record: ${p.shock_year}</p>

      <div class="detail-metric">
        <span class="label">Drop in food-calorie production</span>
        <span class="value">${p.shock_pct}%</span>
      </div>
      <div class="detail-metric">
        <span class="label">Category</span>
        <span class="value"><span class="detail-category-badge" style="background:${badgeColor}">${p.category_main || "Unknown"}</span></span>
      </div>
      ${p.reason ? `<p class="detail-reason">${p.reason}</p>` : ""}
      ${
        p.source
          ? `<p class="detail-source">Source: ${
              p.source_link
                ? `<a href="${p.source_link}" target="_blank" rel="noopener">${p.source}</a>`
                : p.source
            }</p>`
          : ""
      }
      <div class="detail-sparkline">
        <p class="detail-sparkline-label">Production vs. trend, ${state.headlineStats.year_min}–${state.headlineStats.year_max}</p>
        <div id="sparkline"></div>
      </div>
    `;

    drawSparkline(p.name_short, p.shock_year);
  }

  function drawSparkline(nameShort, shockYear) {
    const holder = document.getElementById("sparkline");
    const series = state.yearlyByCountry && state.yearlyByCountry[nameShort];
    if (!holder || !series) return;

    const data = Object.entries(series)
      .map(([year, v]) => ({ year: +year, v }))
      .filter((d) => d.v != null)
      .sort((a, b) => a.year - b.year);
    if (!data.length) return;

    const w = 260, h = 60, pad = 4;
    const x = d3.scaleLinear().domain(d3.extent(data, (d) => d.year)).range([pad, w - pad]);
    const y = d3.scaleLinear().domain(d3.extent(data, (d) => d.v)).nice().range([h - pad, pad]);

    const svg = d3.select(holder).append("svg")
      .attr("viewBox", `0 0 ${w} ${h}`)
      .attr("width", "100%")
      .attr("height", h);

    svg.append("line")
      .attr("x1", pad).attr("x2", w - pad)
      .attr("y1", y(0)).attr("y2", y(0))
      .attr("stroke", "#d8cfc0").attr("stroke-dasharray", "2,2");

    svg.append("path")
      .datum(data)
      .attr("fill", "none")
      .attr("stroke", "#b5502f")
      .attr("stroke-width", 1.5)
      .attr("d", d3.line().x((d) => x(d.year)).y((d) => y(d.v)));

    const worst = data.find((d) => d.year === shockYear) || data.reduce((a, b) => (b.v < a.v ? b : a));
    svg.append("circle")
      .attr("cx", x(worst.year)).attr("cy", y(worst.v)).attr("r", 3.5)
      .attr("fill", "#b5502f");
  }

  function renderLegend() {
    const legend = document.getElementById("legend");

    if (state.mode === "magnitude") {
      const stops = d3.range(0, 1.01, 0.1)
        .map((t) => colorScaleMagnitude(t * minShock))
        .join(",");
      legend.innerHTML = `
        <div class="legend-scale">
          <span>0%</span>
          <div class="legend-gradient" style="background:linear-gradient(90deg, ${stops})"></div>
          <span>${Math.round(minShock)}%</span>
        </div>
        <div>Drop in national food-calorie production, largest shock on record &middot; grey = no data</div>
      `;
      return;
    }

    const categories = state.categorySummary.overall.map((d) => d.category);
    const colors = state.categorySummary.colors;
    legend.innerHTML = `<div class="legend-categories">${categories
      .map(
        (cat) => `
        <span class="legend-item${state.categoryFilter && state.categoryFilter !== cat ? " legend-dimmed" : ""}" data-cat="${cat}">
          <span class="legend-swatch" style="background:${colors[cat]}"></span>${cat}
        </span>`
      )
      .join("")}</div>`;

    legend.querySelectorAll(".legend-item").forEach((el) => {
      el.addEventListener("click", () => setCategoryFilter(el.dataset.cat));
    });
  }

  // ---------------- Decade small multiples ----------------

  function renderDecadeGrid(geojson, decadeCounts) {
    const grid = document.getElementById("decadeGrid");
    if (!grid) return;

    const w = 300, h = 165;
    const projection = d3.geoNaturalEarth1().fitSize([w, h], geojson);
    const decadePath = d3.geoPath(projection);
    const color = d3.scaleSequential(d3.interpolateYlOrBr).domain([0, 1]);

    decadeCounts.decades.forEach((decade) => {
      const span = decadeCounts.decade_spans[decade];
      const yearsInDecade = span[1] - span[0] + 1;
      const isPartial = yearsInDecade < 10;

      const cell = document.createElement("div");
      cell.className = "decade-cell";
      cell.innerHTML = `
        <svg viewBox="0 0 ${w} ${h}" role="img" aria-label="Shock intensity, ${span[0]}–${span[1]}"></svg>
        <p class="decade-label">${decade}s${isPartial ? ` <span class="decade-partial">(${span[0]}–${span[1]}, partial)</span>` : ""}</p>
      `;
      grid.appendChild(cell);

      const svg = d3.select(cell.querySelector("svg"));
      svg
        .selectAll("path")
        .data(geojson.features)
        .join("path")
        .attr("d", decadePath)
        .attr("stroke", "#ffffff")
        .attr("stroke-width", 0.2)
        .attr("fill", (f) => {
          const counts = decadeCounts.counts[f.properties.name_short];
          const n = counts ? counts[decade] : undefined;
          if (n === undefined) return NO_DATA_COLOR;
          return color(n / yearsInDecade);
        });
    });

    const legend = document.createElement("div");
    legend.className = "decade-legend";
    const stops = d3.range(0, 1.01, 0.1).map((t) => color(t)).join(",");
    legend.innerHTML = `
      <span>Never in shock</span>
      <div class="legend-gradient" style="background:linear-gradient(90deg, ${stops})"></div>
      <span>In shock every year</span>
    `;
    grid.after(legend);
  }

  // ---------------- Toggles ----------------

  function initToggles() {
    document.querySelectorAll(".toggle[data-mode]").forEach((btn) => {
      btn.addEventListener("click", () => {
        state.mode = btn.dataset.mode;
        document.querySelectorAll(".toggle[data-mode]").forEach((b) => {
          b.classList.toggle("active", b === btn);
          b.setAttribute("aria-selected", b === btn ? "true" : "false");
        });
        colorMap();
        renderLegend();
      });
    });

    document.querySelectorAll(".toggle[data-group]").forEach((btn) => {
      btn.addEventListener("click", () => {
        state.chartGroup = btn.dataset.group;
        document.querySelectorAll(".toggle[data-group]").forEach((b) => {
          b.classList.toggle("active", b === btn);
          b.setAttribute("aria-selected", b === btn ? "true" : "false");
        });
        renderChart();
      });
    });

    document.getElementById("clearFilter").addEventListener("click", () => setCategoryFilter(null));
  }

  function setCategoryFilter(cat) {
    state.categoryFilter = state.categoryFilter === cat ? null : cat;

    if (state.categoryFilter && state.mode !== "reason") {
      state.mode = "reason";
      document.querySelectorAll(".toggle[data-mode]").forEach((b) => {
        b.classList.toggle("active", b.dataset.mode === "reason");
        b.setAttribute("aria-selected", b.dataset.mode === "reason" ? "true" : "false");
      });
    }

    document.getElementById("clearFilter").hidden = !state.categoryFilter;

    colorMap();
    renderLegend();
    renderChart();
  }

  // ---------------- Category chart ----------------

  function renderChart() {
    const container = document.getElementById("categoryChart");
    const summary = state.categorySummary;
    const categories = summary.overall.map((d) => d.category);
    const colors = summary.colors;

    const rows = summary[`by_${state.chartGroup}`];
    const key = state.chartGroup === "continent" ? "continent" : "decade";

    // group rows -> { groupKey: { category: count, total } }
    const grouped = new Map();
    rows.forEach((r) => {
      const k = r[key];
      if (!grouped.has(k)) grouped.set(k, { total: 0 });
      const g = grouped.get(k);
      g[r.category] = r.count;
      g.total += r.count;
    });

    let groupKeys = Array.from(grouped.keys());
    if (state.chartGroup === "decade") {
      groupKeys.sort((a, b) => a - b);
    } else {
      groupKeys.sort((a, b) => grouped.get(b).total - grouped.get(a).total);
    }

    const maxTotal = d3.max(groupKeys, (k) => grouped.get(k).total);

    container.innerHTML = groupKeys
      .map((k) => {
        const g = grouped.get(k);
        const label = state.chartGroup === "decade" ? `${k}s` : k;
        const widthPct = (g.total / maxTotal) * 100;
        const segs = categories
          .filter((cat) => g[cat])
          .map((cat) => {
            const dimmed = state.categoryFilter && state.categoryFilter !== cat;
            return `<div class="chart-bar-seg${dimmed ? " dimmed" : ""}" data-cat="${cat}" title="${cat}: ${g[cat]}" style="flex:${g[cat]} 0 auto; background:${colors[cat]}"></div>`;
          })
          .join("");
        return `
          <div class="chart-row">
            <div class="chart-row-label">${label} <span style="color:#b3a99a">(${g.total})</span></div>
            <div class="chart-bar-track" style="width:${widthPct}%">${segs}</div>
          </div>`;
      })
      .join("");

    container.querySelectorAll(".chart-bar-seg").forEach((el) => {
      el.addEventListener("click", () => setCategoryFilter(el.dataset.cat));
      el.style.cursor = "pointer";
    });
  }
})();
