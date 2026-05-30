const palette = ["#1f6feb", "#22c55e", "#f59e0b", "#ef4444", "#8b5cf6"];

function chartColor(index) {
  return palette[index % palette.length];
}

function renderCharts(report) {
  document.querySelectorAll(".chart-canvas").forEach((container) => {
    const pageKey = container.dataset.page;
    const chartIndex = Number(container.dataset.chartIndex);
    const chart = report.pages[pageKey].charts[chartIndex];
    if (!chart) {
      container.textContent = "Chart unavailable.";
      return;
    }

    if (chart.type === "line") {
      renderLineChart(container, chart);
      return;
    }

    if (chart.type === "bar") {
      renderBarChart(container, chart);
      return;
    }

    if (chart.type === "heatmap") {
      renderHeatmap(container, chart);
      return;
    }

    container.textContent = "Unsupported chart type.";
  });
}

function createSvg(width, height) {
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
  svg.setAttribute("width", "100%");
  svg.setAttribute("height", "100%");
  svg.setAttribute("role", "img");
  return svg;
}

function addText(svg, x, y, content, extra = {}) {
  const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
  text.setAttribute("x", x);
  text.setAttribute("y", y);
  text.setAttribute("fill", extra.fill || "#5b677a");
  text.setAttribute("font-size", extra.size || "12");
  if (extra.anchor) {
    text.setAttribute("text-anchor", extra.anchor);
  }
  text.textContent = content;
  svg.appendChild(text);
}

function renderLineChart(container, chart) {
  const width = 700;
  const height = 260;
  const padding = { top: 16, right: 24, bottom: 40, left: 40 };
  const svg = createSvg(width, height);
  const labels = chart.labels || [];
  const series = chart.series || [];
  const allValues = series.flatMap((item) => item.values);
  const maxValue = Math.max(...allValues, 1);
  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;

  for (let tick = 0; tick <= 4; tick += 1) {
    const y = padding.top + (chartHeight / 4) * tick;
    const value = Math.round(maxValue * (1 - tick / 4));
    const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
    line.setAttribute("x1", padding.left);
    line.setAttribute("x2", width - padding.right);
    line.setAttribute("y1", y);
    line.setAttribute("y2", y);
    line.setAttribute("stroke", "#d8dfeb");
    line.setAttribute("stroke-width", "1");
    svg.appendChild(line);
    addText(svg, padding.left - 8, y + 4, String(value), { anchor: "end" });
  }

  series.forEach((item, index) => {
    if (!item.values.length) {
      return;
    }
    const points = item.values.map((value, pointIndex) => {
      const x = padding.left + (chartWidth * pointIndex) / Math.max(item.values.length - 1, 1);
      const y = padding.top + chartHeight - (value / maxValue) * chartHeight;
      return `${x},${y}`;
    });
    const polyline = document.createElementNS("http://www.w3.org/2000/svg", "polyline");
    polyline.setAttribute("points", points.join(" "));
    polyline.setAttribute("fill", "none");
    polyline.setAttribute("stroke", chartColor(index));
    polyline.setAttribute("stroke-width", "3");
    svg.appendChild(polyline);
  });

  const step = labels.length > 12 ? Math.ceil(labels.length / 12) : 1;
  labels.forEach((label, index) => {
    if (index % step !== 0) {
      return;
    }
    const x = padding.left + (chartWidth * index) / Math.max(labels.length - 1, 1);
    addText(svg, x, height - 12, label, { anchor: "middle" });
  });

  container.replaceChildren(svg, buildLegend(chart.series));
}

function renderBarChart(container, chart) {
  const width = 700;
  const height = 280;
  const padding = { top: 16, right: 24, bottom: 60, left: 40 };
  const svg = createSvg(width, height);
  const labels = chart.labels || [];
  const series = chart.series || [];
  const allValues = series.flatMap((item) => item.values);
  const maxValue = Math.max(...allValues, 1);
  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;
  const groupWidth = chartWidth / Math.max(labels.length, 1);
  const barWidth = Math.max((groupWidth - 8) / Math.max(series.length, 1), 8);

  for (let tick = 0; tick <= 4; tick += 1) {
    const y = padding.top + (chartHeight / 4) * tick;
    const value = Math.round(maxValue * (1 - tick / 4));
    const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
    line.setAttribute("x1", padding.left);
    line.setAttribute("x2", width - padding.right);
    line.setAttribute("y1", y);
    line.setAttribute("y2", y);
    line.setAttribute("stroke", "#d8dfeb");
    line.setAttribute("stroke-width", "1");
    svg.appendChild(line);
    addText(svg, padding.left - 8, y + 4, String(value), { anchor: "end" });
  }

  labels.forEach((label, labelIndex) => {
    series.forEach((serie, seriesIndex) => {
      const value = serie.values[labelIndex] || 0;
      const x = padding.left + labelIndex * groupWidth + 4 + seriesIndex * barWidth;
      const barHeight = (value / maxValue) * chartHeight;
      const y = padding.top + chartHeight - barHeight;
      const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
      rect.setAttribute("x", x);
      rect.setAttribute("y", y);
      rect.setAttribute("width", barWidth - 2);
      rect.setAttribute("height", barHeight);
      rect.setAttribute("rx", "4");
      rect.setAttribute("fill", chartColor(seriesIndex));
      svg.appendChild(rect);
    });

    const x = padding.left + labelIndex * groupWidth + groupWidth / 2;
    addText(svg, x, height - 18, label, { anchor: "middle" });
  });

  container.replaceChildren(svg, buildLegend(chart.series));
}

function renderHeatmap(container, chart) {
  const width = 700;
  const height = 180;
  const svg = createSvg(width, height);
  const cells = chart.cells || [];
  const maxValue = Math.max(...cells.map((cell) => cell.value), 1);
  const size = 11;
  const offsetX = 40;
  const offsetY = 22;

  ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"].forEach((label, index) => {
    addText(svg, 8, offsetY + index * (size + 3) + 9, label, { size: "11" });
  });

  cells.forEach((cell) => {
    const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
    rect.setAttribute("x", offsetX + cell.week * (size + 3));
    rect.setAttribute("y", offsetY + cell.weekday * (size + 3));
    rect.setAttribute("width", size);
    rect.setAttribute("height", size);
    rect.setAttribute("rx", "2");
    rect.setAttribute("fill", heatmapColor(cell.value, maxValue));
    svg.appendChild(rect);
  });

  container.replaceChildren(svg);
}

function heatmapColor(value, maxValue) {
  if (value === 0) {
    return "#e2e8f0";
  }
  const alpha = Math.min(0.25 + value / maxValue, 1);
  return `rgba(31, 111, 235, ${alpha.toFixed(2)})`;
}

function buildLegend(series) {
  const legend = document.createElement("div");
  legend.className = "chart-legend";
  series.forEach((item, index) => {
    const label = document.createElement("span");
    const dot = document.createElement("span");
    dot.className = "legend-dot";
    dot.style.backgroundColor = chartColor(index);
    label.append(dot, item.name);
    legend.appendChild(label);
  });
  return legend;
}

function activateSidebar() {
  const links = Array.from(document.querySelectorAll(".nav-list a"));
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) {
          return;
        }
        links.forEach((link) => {
          link.classList.toggle("active", link.getAttribute("href") === `#${entry.target.id}`);
        });
      });
    },
    { rootMargin: "-20% 0px -60% 0px", threshold: 0.1 },
  );

  document.querySelectorAll(".page").forEach((section) => observer.observe(section));
}

document.addEventListener("DOMContentLoaded", () => {
  const report = window.GITSCOPE_REPORT;
  if (!report) {
    return;
  }
  renderCharts(report);
  activateSidebar();
});
