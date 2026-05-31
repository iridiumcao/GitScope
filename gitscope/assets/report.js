const report = JSON.parse(document.getElementById("report-data").textContent || "{}");

function el(tag, options = {}, children = []) {
  const node = document.createElement(tag);
  if (options.className) {
    node.className = options.className;
  }
  if (options.text) {
    node.textContent = options.text;
  }
  if (options.html) {
    node.innerHTML = options.html;
  }
  if (options.attrs) {
    Object.entries(options.attrs).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        node.setAttribute(key, value);
      }
    });
  }
  children.forEach((child) => {
    if (child) {
      node.appendChild(child);
    }
  });
  return node;
}

function renderHeader() {
  const header = document.getElementById("report-header");
  const filterChips = [
    chip("Analyzed ref", report.metadata.analyzed_ref),
    chip("Current branch", report.metadata.current_branch || "N/A"),
    chip("Default branch", report.metadata.default_branch || "N/A"),
    chip("Generated", report.metadata.generated_at),
  ];

  Object.entries(report.metadata.filters || {}).forEach(([key, value]) => {
    if (value) {
      filterChips.push(chip(key, value));
    }
  });

  header.appendChild(el("div", { className: "eyebrow", text: "Repository report" }));
  header.appendChild(
    el("div", { className: "title-row" }, [
      el("div", {}, [
        el("h1", { text: report.metadata.repository_name }),
        el("p", { className: "subtitle", text: report.metadata.repository_path }),
      ]),
    ]),
  );
  header.appendChild(
    el("p", {
      className: "subtitle",
      text: "GitScope analyzes local Git data, stores normalized entities in SQLite, and renders this static report from a single report payload.",
    }),
  );
  header.appendChild(el("div", { className: "header-meta" }, filterChips));
}

function chip(label, value) {
  return el("span", { className: "chip", text: `${label}: ${value}` });
}

function renderOverview() {
  const shell = document.getElementById("overview-shell");
  if (report.summary?.length) {
    shell.appendChild(renderSummaryGrid(report.summary));
  }
}

function renderNavigation() {
  const nav = document.getElementById("sidebar-nav");
  report.sections.forEach((section, index) => {
    const link = el("a", {
      className: `sidebar-link${index === 0 ? " active" : ""}`,
      text: section.title,
      attrs: { href: `#${section.id}` },
    });
    link.addEventListener("click", () => {
      document.querySelectorAll(".sidebar-link").forEach((item) => item.classList.remove("active"));
      link.classList.add("active");
    });
    nav.appendChild(link);
  });
}

function renderSections() {
  const root = document.getElementById("sections-root");
  report.sections.forEach((section) => {
    const sectionNode = el("section", { className: "section-card", attrs: { id: section.id } });
    sectionNode.appendChild(
      el("div", { className: "section-heading" }, [
        el("h2", { text: section.title }),
        el("p", { className: "section-description", text: section.description }),
      ]),
    );

    if (section.summary?.length) {
      sectionNode.appendChild(renderSummaryGrid(section.summary));
    }

    if (section.charts?.length) {
      const chartGrid = el("div", { className: "card-grid" });
      section.charts.forEach((chart) => chartGrid.appendChild(renderChartCard(chart)));
      sectionNode.appendChild(chartGrid);
    }

    if (section.tables?.length) {
      const tableGrid = el("div", { className: "card-grid" });
      section.tables.forEach((table) => tableGrid.appendChild(renderTableCard(table)));
      sectionNode.appendChild(tableGrid);
    }

    if (section.notes?.length) {
      const list = el("ul", { className: "notes-list" });
      section.notes.forEach((note) => list.appendChild(el("li", { text: note })));
      sectionNode.appendChild(list);
    }

    root.appendChild(sectionNode);
  });
}

function renderSummaryGrid(metrics) {
  const grid = el("div", { className: "summary-grid" });
  metrics.forEach((item) => {
    const card = el("article", { className: `summary-card ${item.tone || "default"}`.trim() });
    card.appendChild(el("div", { className: "summary-label", text: item.label }));
    card.appendChild(el("div", { className: "summary-value", text: String(item.value) }));
    if (item.hint) {
      card.appendChild(el("div", { className: "summary-hint", text: item.hint }));
    }
    grid.appendChild(card);
  });
  return grid;
}

function renderChartCard(chart) {
  const card = el("article", { className: "chart-card" });
  card.appendChild(el("h3", { className: "card-title", text: chart.title }));
  card.appendChild(el("p", { className: "card-description", text: chart.description }));
  if (chart.type === "heatmap") {
    card.appendChild(renderHeatmap(chart));
    return card;
  }

  const variantKeys = Object.keys(chart.variants || {});
  if (!variantKeys.length) {
    card.appendChild(emptyState(chart.empty_state || "No data available."));
    return card;
  }

  const tabs = el("div", { className: "variant-tabs" });
  const stage = el("div", { className: "chart-stage" });
  const activeKey = chart.default_variant && chart.variants[chart.default_variant] ? chart.default_variant : variantKeys[0];

  const renderVariant = (variantKey) => {
    stage.replaceChildren();
    const variant = chart.variants[variantKey];
    if (!variant || !variant.labels.length || !variant.series.some((series) => series.values.some((value) => value > 0))) {
      stage.appendChild(emptyState(chart.empty_state || "No data available."));
      return;
    }
    if (chart.type === "line") {
      stage.appendChild(renderLineChart(variant));
    } else {
      stage.appendChild(renderBarChart(variant));
    }
  };

  variantKeys.forEach((variantKey) => {
    const button = el("button", {
      className: `variant-button${variantKey === activeKey ? " active" : ""}`,
      text: variantKey,
      attrs: { type: "button" },
    });
    button.addEventListener("click", () => {
      tabs.querySelectorAll(".variant-button").forEach((node) => node.classList.remove("active"));
      button.classList.add("active");
      renderVariant(variantKey);
    });
    tabs.appendChild(button);
  });

  if (variantKeys.length > 1) {
    card.appendChild(tabs);
  }
  renderVariant(activeKey);
  card.appendChild(stage);
  return card;
}

function renderLineChart(variant) {
  const width = 720;
  const height = 260;
  const padding = 36;
  const values = variant.series.flatMap((series) => series.values);
  const maxValue = Math.max(...values, 1);
  const plotWidth = width - padding * 2;
  const plotHeight = height - padding * 2;
  const svg = svgNode("svg", { viewBox: `0 0 ${width} ${height}`, class: "chart-svg" });

  [0, 0.25, 0.5, 0.75, 1].forEach((step) => {
    const y = padding + plotHeight * step;
    svg.appendChild(
      svgNode("line", {
        x1: padding,
        y1: y,
        x2: width - padding,
        y2: y,
        class: "grid-line",
      }),
    );
  });

  const pointX = (index, total) => padding + (plotWidth * index) / Math.max(total - 1, 1);
  const pointY = (value) => height - padding - (plotHeight * value) / maxValue;

  variant.series.forEach((series, seriesIndex) => {
    const points = series.values.map((value, index) => `${pointX(index, series.values.length)},${pointY(value)}`).join(" ");
    if (!points) {
      return;
    }
    svg.appendChild(
      svgNode("polyline", {
        points,
        class: "line-path",
        stroke: series.color || defaultColor(seriesIndex),
      }),
    );
  });

  const tickIndexes = uniqueTickIndexes(variant.labels.length);
  tickIndexes.forEach((index) => {
    svg.appendChild(
      svgNode("text", {
        x: pointX(index, variant.labels.length),
        y: height - 10,
        "text-anchor": "middle",
        class: "axis-label",
      }, variant.labels[index]),
    );
  });

  const wrapper = el("div");
  wrapper.appendChild(svg);
  wrapper.appendChild(renderLegend(variant.series));
  return wrapper;
}

function renderBarChart(variant) {
  const width = 720;
  const height = 260;
  const padding = 36;
  const labels = variant.labels;
  const series = variant.series[0];
  const maxValue = Math.max(...series.values, 1);
  const plotWidth = width - padding * 2;
  const plotHeight = height - padding * 2;
  const svg = svgNode("svg", { viewBox: `0 0 ${width} ${height}`, class: "chart-svg" });
  const barWidth = plotWidth / Math.max(labels.length, 1);

  series.values.forEach((value, index) => {
    const heightValue = (plotHeight * value) / maxValue;
    svg.appendChild(
      svgNode("rect", {
        x: padding + index * barWidth + 6,
        y: height - padding - heightValue,
        width: Math.max(barWidth - 12, 8),
        height: heightValue,
        rx: 6,
        fill: series.color || "#2563eb",
      }),
    );
  });

  uniqueTickIndexes(labels.length).forEach((index) => {
    svg.appendChild(
      svgNode("text", {
        x: padding + index * barWidth + barWidth / 2,
        y: height - 10,
        "text-anchor": "middle",
        class: "axis-label",
      }, labels[index]),
    );
  });

  const wrapper = el("div");
  wrapper.appendChild(svg);
  wrapper.appendChild(renderLegend([series]));
  return wrapper;
}

function renderHeatmap(chart) {
  if (!chart.heatmap?.length) {
    return emptyState(chart.empty_state || "No heatmap data available.");
  }

  const weeks = [...new Set(chart.heatmap.map((cell) => cell.week))];
  const weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
  const maxValue = Math.max(...chart.heatmap.map((cell) => cell.value), 1);
  const lookup = new Map(chart.heatmap.map((cell) => [`${cell.week}:${cell.weekday}`, cell]));

  const container = el("div", { className: "heatmap" });
  const body = el("div", { className: "heatmap-body" });

  weekdays.forEach((weekday) => {
    const row = el("div", {
      className: "heatmap-row",
      attrs: { style: `grid-template-columns: 34px repeat(${weeks.length}, 14px);` },
    });
    row.appendChild(el("div", { className: "heatmap-weekday", text: weekday }));
    weeks.forEach((week) => {
      const cell = lookup.get(`${week}:${weekday}`);
      const intensity = cell ? cell.value / maxValue : 0;
      row.appendChild(
        el("div", {
          className: "heatmap-cell",
          attrs: {
            title: cell ? cell.tooltip : `${week} ${weekday}: 0 commits`,
            style: `background: ${heatColor(intensity)};`,
          },
        }),
      );
    });
    body.appendChild(row);
  });

  container.appendChild(body);
  return container;
}

function renderLegend(seriesList) {
  const legend = el("div", { className: "legend" });
  seriesList.forEach((series, index) => {
    legend.appendChild(
      el("div", { className: "legend-item" }, [
        el("span", {
          className: "legend-swatch",
          attrs: { style: `background: ${series.color || defaultColor(index)};` },
        }),
        el("span", { text: series.name }),
      ]),
    );
  });
  return legend;
}

function renderTableCard(table) {
  const card = el("article", { className: "table-card" });
  card.appendChild(el("h3", { className: "card-title", text: table.title }));
  card.appendChild(el("p", { className: "card-description", text: table.description }));
  if (!table.rows?.length) {
    card.appendChild(emptyState(table.empty_state || "No rows available."));
    return card;
  }

  const wrap = el("div", { className: "table-wrap" });
  const tableNode = el("table");
  const headRow = el("tr");
  table.columns.forEach((column) => {
    headRow.appendChild(el("th", { text: column.label, className: column.align === "right" ? "align-right" : column.align === "center" ? "align-center" : "" }));
  });
  tableNode.appendChild(el("thead", {}, [headRow]));

  const body = el("tbody");
  table.rows.forEach((row) => {
    const rowNode = el("tr");
    table.columns.forEach((column) => {
      rowNode.appendChild(renderCell(row[column.key], column.align));
    });
    body.appendChild(rowNode);
  });
  tableNode.appendChild(body);
  wrap.appendChild(tableNode);
  card.appendChild(wrap);
  return card;
}

function renderCell(value, align) {
  const cell = el("td", { className: align === "right" ? "align-right" : align === "center" ? "align-center" : "" });
  if (Array.isArray(value)) {
    const group = el("div", { className: "badge-group" });
    value.forEach((item) => group.appendChild(renderBadge(item)));
    cell.appendChild(group);
    return cell;
  }
  cell.textContent = value === null || value === undefined ? "-" : String(value);
  return cell;
}

function renderBadge(label) {
  return el("span", {
    className: `badge badge-${String(label).toLowerCase()}`,
    text: String(label),
  });
}

function emptyState(message) {
  return el("div", { className: "empty-state", text: message });
}

function svgNode(tag, attrs = {}, text) {
  const node = document.createElementNS("http://www.w3.org/2000/svg", tag);
  Object.entries(attrs).forEach(([key, value]) => node.setAttribute(key, String(value)));
  if (text) {
    node.textContent = text;
  }
  return node;
}

function uniqueTickIndexes(length) {
  if (length <= 4) {
    return Array.from({ length }, (_, index) => index);
  }
  return [...new Set([0, Math.floor(length / 3), Math.floor((length * 2) / 3), length - 1])];
}

function defaultColor(index) {
  return ["#2563eb", "#16a34a", "#dc2626", "#7c3aed"][index % 4];
}

function heatColor(intensity) {
  if (intensity <= 0) {
    return "#e2e8f0";
  }
  const alpha = Math.min(0.15 + intensity * 0.75, 0.9);
  return `rgba(37, 99, 235, ${alpha})`;
}

renderHeader();
renderOverview();
renderNavigation();
renderSections();
