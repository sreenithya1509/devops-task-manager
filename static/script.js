const $ = (id) => document.getElementById(id);
let busy = false;
async function api(path, options = {}) {
  const response = await fetch(path, { ...options, headers: { 'Content-Type': 'application/json', ...options.headers } });
  if (response.status === 204) return null;
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || 'Unable to save your changes.');
  return data;
}
function showError(error) { $('error').textContent = error.message || 'Unable to connect. Please try again.'; $('error').hidden = false; }
function render(tasks) {
  $('total').textContent = tasks.length;
  const completed = tasks.filter(t => t.completed).length;
  $('completed').textContent = completed;
  $('pending').textContent = tasks.length - completed;
  $('empty').hidden = tasks.length > 0;
  $('tasks').replaceChildren();
  for (const task of tasks) {
    const card = document.createElement('article'); card.className = `task-card${task.completed ? ' done' : ''}`;
    const check = document.createElement('input'); check.type = 'checkbox'; check.checked = task.completed;
    check.setAttribute('aria-label', `Mark ${task.title} ${task.completed ? 'pending' : 'completed'}`);
    check.addEventListener('change', () => mutate(() => api(`/api/tasks/${task.id}`, { method: 'PATCH', body: JSON.stringify({ completed: check.checked }) }), 'Task updated.', check));
    const copy = document.createElement('div'); copy.className = 'task-copy';
    const title = document.createElement('span'); title.className = 'task-title'; title.textContent = task.title;
    const status = document.createElement('span'); status.className = 'status'; status.textContent = task.completed ? 'Completed' : 'In progress';
    copy.append(title, status);
    const remove = document.createElement('button'); remove.className = 'delete'; remove.textContent = 'Delete'; remove.setAttribute('aria-label', `Delete ${task.title}`);
    remove.addEventListener('click', () => mutate(() => api(`/api/tasks/${task.id}`, { method: 'DELETE' }), 'Task deleted.', remove));
    card.append(check, copy, remove); $('tasks').append(card);
  }
}
async function refresh() { render((await api('/api/tasks')).tasks); }
async function mutate(action, message, control) {
  if (busy) { if (control?.type === 'checkbox') control.checked = !control.checked; return; }
  busy = true; $('add-button').disabled = true; $('error').hidden = true;
  document.querySelectorAll('.task-card input, .task-card button').forEach(el => el.disabled = true);
  try { await action(); $('announcement').textContent = message; await refresh(); }
  catch (error) { if (control?.type === 'checkbox') control.checked = !control.checked; showError(error); }
  finally { busy = false; $('add-button').disabled = false; document.querySelectorAll('.task-card input, .task-card button').forEach(el => el.disabled = false); }
}
$('task-form').addEventListener('submit', event => {
  event.preventDefault(); const title = $('title').value.trim();
  if (!title) { showError(new Error('Please enter a task title.')); return; }
  mutate(async () => { await api('/api/tasks', { method: 'POST', body: JSON.stringify({ title }) }); $('title').value = ''; $('title').focus(); }, 'Task added.');
});
$('refresh').addEventListener('click', () => { if (!busy) { $('error').hidden = true; refresh().catch(showError); } });
refresh().catch(showError);
api('/version').then(data => $('version').textContent = `v${data.version}`).catch(() => $('version').textContent = 'offline');
