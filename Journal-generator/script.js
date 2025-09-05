// Handles auto-fitting the page to the browser window
function fitPageToWindow() {
  const page = document.querySelector('.page');
  const container = document.querySelector('.page-wrapper');

  const windowWidth = window.innerWidth;
  const windowHeight = window.innerHeight;

  const scaleX = windowWidth / page.offsetWidth;
  const scaleY = windowHeight / page.offsetHeight;

  const scale = Math.min(scaleX, scaleY, 1); // never upscale

  page.style.transform = `scale(${scale})`;
  page.dataset.scale = scale; // store initial scale
}

// Handles manual zoom control
function setupZoomControl() {
  const scaleInput = document.getElementById("scale-range");
  const page = document.querySelector(".page");

  scaleInput.addEventListener("input", () => {
    const factor = scaleInput.value;
    const base = parseFloat(page.dataset.scale || 1);
    const newScale = base * factor;
    page.style.transform = `scale(${newScale})`;
  });
}

// Handles page number and identifier update
function setupControls() {
  const pageNumberInput = document.getElementById("page-number");
  const identifierInput = document.getElementById("identifier");

  const pageNumElement = document.querySelector(".page-number");
  const identifierElement = document.querySelector(".identifier");

  document.getElementById("update-btn").addEventListener("click", () => {
    const newId = identifierInput.value.trim();
    const newPage = pageNumberInput.value.trim();

    if (newId) identifierElement.textContent = newId;
    if (newPage) pageNumElement.textContent = newPage;
  });
}

// Initialize on load and resize
window.addEventListener('load', () => {
  fitPageToWindow();
  setupZoomControl();
  setupControls();
});

window.addEventListener('resize', fitPageToWindow);
