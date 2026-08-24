document.querySelectorAll('[data-range]').forEach((range) => {
  const output = range.parentElement.querySelector('[data-range-output]');
  const update = () => { if (output) output.textContent = `${range.value}%`; };
  range.addEventListener('input', update); update();
});
