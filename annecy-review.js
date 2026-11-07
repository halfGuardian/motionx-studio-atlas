/* Read-only research dashboard. Evidence assessment never grants approval. */
(function () {
  'use strict';
  function matches(text, state, group, query, selectedState, selectedGroup) {
    return text.toLocaleLowerCase().includes(query.toLocaleLowerCase().trim()) && (!selectedState || selectedState === state) && (!selectedGroup || selectedGroup === group);
  }
  if (typeof module !== 'undefined') module.exports = { matches };
  if (typeof document === 'undefined') return;
  const search = document.getElementById('search'), state = document.getElementById('state'), group = document.getElementById('group');
  if (!search || !state || !group) return;
  const rows = [...document.querySelectorAll('tbody tr')];
  function update() {
    let visible = 0;
    for (const row of rows) {
      row.hidden = !matches(row.textContent, row.dataset.state, row.dataset.group, search.value, state.value, group.value);
      if (!row.hidden) visible++;
    }
    document.getElementById('count').textContent = visible.toLocaleString() + ' of ' + rows.length.toLocaleString() + ' exhibitor rows';
  }
  search.addEventListener('input', update); state.addEventListener('change', update); group.addEventListener('change', update);
}());
