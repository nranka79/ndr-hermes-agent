// Presentation bootstrap. Keep this file thin: layout and content belong in
// index.html/styles.css, not here.

Reveal.initialize({
  hash: false,          // deck state stays out of the URL
  controls: true,
  progress: true,
  center: false,
  slideNumber: "c/t",   // "current / total"
  transition: "slide",
  width: 1280,
  height: 720,
  margin: 0.04,

  // Keyboard: reveal.js binds arrows, Page Up/Down, Home/End and F for
  // fullscreen out of the box. Nothing to configure for Phase 6's
  // navigation requirements.

  plugins: [RevealNotes, RevealZoom, RevealSearch]
});

// Chart.js and Mermaid are optional: only touched if the slide markup
// actually uses them, so a text-only deck pays nothing for either.
Reveal.on("ready", function () {
  var chartEl = document.getElementById("chart-1");
  if (chartEl && window.Chart) {
    new Chart(chartEl, {
      type: "bar",
      data: {
        labels: ["A", "B", "C"],
        datasets: [{ label: "Example", data: [3, 7, 5] }]
      },
      options: { responsive: false, plugins: { legend: { display: false } } }
    });
  }

  if (window.mermaid && document.querySelector(".mermaid")) {
    mermaid.initialize({ startOnLoad: false, securityLevel: "strict" });
    mermaid.run({ querySelector: ".mermaid" });
  }
});

if (window.DRAPresent) {
  DRAPresent.attach(Reveal);
}
