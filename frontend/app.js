const fallbackResponse = {
  summary:
    'Navagator recommends a short stack for researching, planning, and shipping your first result without paying for too many overlapping tools.',
  recommendations: [
    {
      tool: {
        name: 'ChatGPT',
        description: 'General-purpose AI assistant for drafting, research, and structured thinking.',
        best_for: 'Best when you need a flexible first tool to reduce blank-page friction fast.'
      },
      score: 8,
      reasons: ['Fits a broad set of beginner-to-advanced workflows.', 'Strong first tool for planning and writing.'],
      cautions: [],
      comparison_note: null
    },
    {
      tool: {
        name: 'Perplexity',
        description: 'Research-first AI search tool with fast source-backed exploration.',
        best_for: 'Best when current information matters.'
      },
      score: 7,
      reasons: ['Useful when you need source-backed research.', 'Pairs well with planning and comparison work.'],
      cautions: [],
      comparison_note: null
    },
    {
      tool: {
        name: 'Notion',
        description: 'Workspace tool for organizing notes, workflows, and repeatable operating systems.',
        best_for: 'Best when you need a simple operating layer.'
      },
      score: 6,
      reasons: ['Good for keeping the workflow organized.', 'Works well for low-friction execution.'],
      cautions: ['You may not need this if you already have a workspace tool.'],
      comparison_note: null
    }
  ],
  workflow: [
    {
      step: 1,
      title: 'Clarify the job',
      detail: 'Use ChatGPT to tighten the exact outcome before touching extra tools or subscriptions.'
    },
    {
      step: 2,
      title: 'Research the landscape',
      detail: 'Use Perplexity to compare options, collect sources, and avoid relying on stale tool lists.'
    },
    {
      step: 3,
      title: 'Turn research into execution',
      detail: 'Use Notion or your workspace layer to track the first workflow and the result it should produce.'
    }
  ],
  session_id: null,
  engine_mode: 'heuristic',
  model_name: null,
  engine_note: null
};

const QUESTIONNAIRE_FALLBACK = [
  {
    id: 'goal',
    label: 'What are you trying to get done?',
    kind: 'text',
    required: true,
    options: [],
    help_text: 'Example: launch a landing page, automate outreach, build a content system.',
    placeholder: 'Example: research competitors and ship a landing page this week.',
    show_when: {}
  },
  {
    id: 'skill_level',
    label: 'How comfortable are you with AI tools right now?',
    kind: 'select',
    required: true,
    options: ['beginner', 'intermediate', 'advanced'],
    show_when: {}
  },
  {
    id: 'budget',
    label: 'What budget range fits your current stack?',
    kind: 'select',
    required: true,
    options: ['free', 'low', 'mid', 'high'],
    show_when: {}
  },
  {
    id: 'workflow_style',
    label: 'What kind of workflow do you want?',
    kind: 'select',
    required: true,
    options: ['fast execution', 'deep research', 'content production', 'automation'],
    show_when: {}
  },
  {
    id: 'timeline',
    label: 'How fast does this need to move?',
    kind: 'select',
    required: true,
    options: ['today', 'this week', 'this month'],
    help_text: 'Urgency changes which tools are worth the setup cost.',
    show_when: {}
  },
  {
    id: 'primary_outcome',
    label: 'What should this workflow produce first?',
    kind: 'select',
    required: true,
    options: ['research insights', 'content asset', 'working prototype', 'automation system'],
    show_when: {}
  },
  {
    id: 'team_context',
    label: 'Who needs to work with the output?',
    kind: 'select',
    required: true,
    options: ['solo', 'small team', 'client work', 'internal team'],
    show_when: {
      workflow_style: ['content production', 'automation', 'fast execution']
    }
  },
  {
    id: 'install_preference',
    label: 'Where should the stack lean?',
    kind: 'select',
    required: true,
    options: ['local-first', 'cloud-ok', 'no preference'],
    help_text:
      'This helps Navagator favor installable and privacy-sensitive workflows when needed.',
    show_when: {
      workflow_style: ['automation', 'fast execution', 'deep research']
    }
  },
  {
    id: 'pain_points',
    label: 'What is slowing you down most?',
    kind: 'multiselect',
    required: false,
    options: [
      'tool overload',
      'blank page',
      'too much manual work',
      'handoff friction',
      'cost confusion'
    ],
    show_when: {
      skill_level: ['intermediate', 'advanced']
    }
  },
  {
    id: 'constraints',
    label: 'What constraint matters most right now?',
    kind: 'text',
    required: false,
    options: [],
    help_text: 'Example: no coding, low budget, team handoff, speed.',
    placeholder: 'Example: no coding, very little time, small budget.',
    show_when: {}
  }
];

const FIELD_DEFAULTS = {
  skill_level: 'beginner',
  budget: 'low',
  workflow_style: 'fast execution',
  timeline: 'this week',
  primary_outcome: 'working prototype',
  team_context: 'solo',
  install_preference: 'local-first'
};

const apiBase = window.navagatorDesktop?.apiBase || 'http://127.0.0.1:8000';

function apiUrl(pathname) {
  return `${apiBase}${pathname}`;
}

const form = document.getElementById('questionnaireForm');
const statusNode = document.getElementById('apiStatus');
const summaryHeading = document.getElementById('summaryHeading');
const summaryText = document.getElementById('summaryText');
const recommendationList = document.getElementById('recommendationList');
const workflowList = document.getElementById('workflowList');
const sessionList = document.getElementById('sessionList');
const savePreferencesButton = document.getElementById('savePreferencesButton');
const previewSubmitButton = document.getElementById('previewSubmitButton');
const runtimeBackendNode = document.getElementById('runtimeBackend');
const runtimeEngineNode = document.getElementById('runtimeEngine');
const runtimeProfileNode = document.getElementById('runtimeProfile');
const runtimeDatabaseNode = document.getElementById('runtimeDatabase');
const runtimeNoteNode = document.getElementById('runtimeNote');
const engineMetaNode = document.getElementById('engineMeta');
const sessionBannerNode = document.getElementById('sessionBanner');
const sessionIdDisplayNode = document.getElementById('sessionIdDisplay');
const copySessionIdButton = document.getElementById('copySessionId');
const exportBackupButton = document.getElementById('exportBackupButton');

let questionnaireShowWhen = {};

function fieldIdToDomId(fieldId) {
  return fieldId.replace(/_([a-z])/g, (_, ch) => ch.toUpperCase());
}

function titleCaseWords(value) {
  return value
    .split(/\s+/)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

function escapeHtml(raw) {
  if (raw == null) {
    return '';
  }
  return String(raw)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function loadQuestionnaireMeta(questions) {
  questionnaireShowWhen = {};
  questions.forEach((q) => {
    questionnaireShowWhen[q.id] = q.show_when && Object.keys(q.show_when).length ? q.show_when : {};
  });
}

function evaluateShowWhen(showWhen) {
  if (!showWhen || Object.keys(showWhen).length === 0) {
    return true;
  }
  return Object.entries(showWhen).every(([fieldId, allowed]) => {
    const domId = fieldIdToDomId(fieldId);
    const el = document.getElementById(domId);
    if (!el) {
      return false;
    }
    return allowed.includes(el.value);
  });
}

function updateConditionalFields() {
  document.querySelectorAll('[data-conditional-for]').forEach((node) => {
    const fieldId = node.getAttribute('data-conditional-for');
    const showWhen = questionnaireShowWhen[fieldId] || {};
    const visible = evaluateShowWhen(showWhen);
    node.hidden = !visible;
  });
}

function appendHelpText(label, text) {
  if (!text) {
    return;
  }
  const help = document.createElement('p');
  help.className = 'field-help';
  help.textContent = text;
  label.appendChild(help);
}

function renderQuestionnaireFields(questions) {
  const container = document.getElementById('questionnaireFields');
  if (!container) {
    return;
  }
  container.replaceChildren();
  loadQuestionnaireMeta(questions);

  const fullWidthIds = new Set(['goal', 'pain_points', 'constraints']);

  for (const q of questions) {
    const domId = fieldIdToDomId(q.id);
    const showWhen = q.show_when && Object.keys(q.show_when).length ? q.show_when : null;

    if (q.kind === 'text') {
      const label = document.createElement('label');
      if (fullWidthIds.has(q.id)) {
        label.classList.add('full-width');
      }
      const span = document.createElement('span');
      span.textContent = q.label;
      label.appendChild(span);
      appendHelpText(label, q.help_text);

      if (q.id === 'constraints') {
        const input = document.createElement('input');
        input.type = 'text';
        input.name = q.id;
        input.id = domId;
        input.placeholder = q.placeholder || '';
        label.appendChild(input);
      } else {
        const ta = document.createElement('textarea');
        ta.name = q.id;
        ta.id = domId;
        ta.rows = q.id === 'goal' ? 4 : 3;
        ta.placeholder = q.placeholder || '';
        label.appendChild(ta);
      }

      const wrapped = showWhen ? wrapConditional(label, q.id) : label;
      container.appendChild(wrapped);
      continue;
    }

    if (q.kind === 'select') {
      const label = document.createElement('label');
      if (fullWidthIds.has(q.id)) {
        label.classList.add('full-width');
      }
      const span = document.createElement('span');
      span.textContent = q.label;
      label.appendChild(span);
      appendHelpText(label, q.help_text);

      const select = document.createElement('select');
      select.name = q.id;
      select.id = domId;
      for (const opt of q.options || []) {
        const o = document.createElement('option');
        o.value = opt;
        o.textContent = titleCaseWords(opt);
        const def = FIELD_DEFAULTS[q.id];
        if (def !== undefined && def === opt) {
          o.selected = true;
        }
        select.appendChild(o);
      }
      label.appendChild(select);

      const wrapped = showWhen ? wrapConditional(label, q.id) : label;
      container.appendChild(wrapped);
      continue;
    }

    if (q.kind === 'multiselect') {
      const fs = document.createElement('fieldset');
      fs.className = 'pain-points full-width';
      fs.setAttribute('data-conditional-for', q.id);
      const legend = document.createElement('legend');
      legend.textContent = q.label;
      fs.appendChild(legend);
      const grid = document.createElement('div');
      grid.className = 'pain-points__grid';
      for (const opt of q.options || []) {
        const lab = document.createElement('label');
        const cb = document.createElement('input');
        cb.type = 'checkbox';
        cb.name = 'pain_points';
        cb.value = opt;
        lab.appendChild(cb);
        lab.appendChild(document.createTextNode(` ${titleCaseWords(opt)}`));
        grid.appendChild(lab);
      }
      fs.appendChild(grid);
      container.appendChild(fs);
    }
  }
}

function wrapConditional(inner, fieldId) {
  const wrapper = document.createElement('div');
  wrapper.setAttribute('data-conditional-for', fieldId);
  wrapper.appendChild(inner);
  return wrapper;
}

async function loadQuestionnaire() {
  const container = document.getElementById('questionnaireFields');
  if (!container) {
    return;
  }
  container.setAttribute('aria-busy', 'true');
  try {
    const res = await fetch(apiUrl('/api/questionnaire'));
    if (!res.ok) {
      throw new Error(String(res.status));
    }
    const questions = await res.json();
    renderQuestionnaireFields(questions);
  } catch {
    renderQuestionnaireFields(QUESTIONNAIRE_FALLBACK);
  } finally {
    container.setAttribute('aria-busy', 'false');
  }
}

function bindFieldChangeListeners() {
  const skill = document.getElementById('skillLevel');
  const wf = document.getElementById('workflowStyle');
  if (skill) {
    skill.addEventListener('change', updateConditionalFields);
  }
  if (wf) {
    wf.addEventListener('change', updateConditionalFields);
  }
}

function renderRecommendations(items) {
  recommendationList.innerHTML = items
    .map(
      (item, index) => `
        <article class="stack-item${index === 0 ? ' stack-item--featured' : ''}">
          ${index === 0 ? '<span class="stack-badge">Top pick</span>' : ''}
          <div class="stack-top">
            <div>
              <h3>${escapeHtml(item.tool.name)}</h3>
              <p class="stack-meta">${escapeHtml(item.tool.description)}</p>
            </div>
            <div class="stack-score">${escapeHtml(String(item.score))}</div>
          </div>
          <p class="stack-meta">${escapeHtml(item.tool.best_for || '')}</p>
          ${
            item.comparison_note
              ? `<p class="stack-compare">${escapeHtml(item.comparison_note)}</p>`
              : ''
          }
          <div class="stack-reasons">${item.reasons.map((reason) => `<span>${escapeHtml(reason)}</span>`).join('')}</div>
          ${item.cautions?.length ? `<div class="stack-cautions">${item.cautions.map((caution) => `<span>${escapeHtml(caution)}</span>`).join('')}</div>` : ''}
        </article>
      `
    )
    .join('');
}

function renderWorkflow(items) {
  workflowList.innerHTML = items
    .map(
      (item) => `
        <li>
          <div class="workflow-step">${escapeHtml(String(item.step))}</div>
          <div>
            <h3>${escapeHtml(item.title)}</h3>
            <p>${escapeHtml(item.detail)}</p>
          </div>
        </li>
      `
    )
    .join('');
}

function updateEngineMeta(payload) {
  if (!engineMetaNode) {
    return;
  }
  const mode = payload.engine_mode || 'heuristic';
  if (mode === 'openai') {
    const model = payload.model_name ? ` (${payload.model_name})` : '';
    engineMetaNode.textContent = `Engine: OpenAI${model}`;
    engineMetaNode.hidden = false;
    return;
  }
  engineMetaNode.textContent = 'Engine: Local heuristic ranking';
  engineMetaNode.hidden = false;
}

function updateSessionBanner(sessionId) {
  if (!sessionBannerNode || !sessionIdDisplayNode) {
    return;
  }
  if (!sessionId) {
    sessionBannerNode.hidden = true;
    sessionIdDisplayNode.textContent = '';
    return;
  }
  sessionIdDisplayNode.textContent = sessionId;
  sessionBannerNode.hidden = false;
}

function renderResponse(payload) {
  summaryHeading.textContent = 'Your stack preview is ready.';
  summaryText.textContent = payload.summary;
  renderRecommendations(payload.recommendations || []);
  renderWorkflow(payload.workflow || []);
  updateEngineMeta(payload);
  updateSessionBanner(payload.session_id || null);
}

function setStatusMessage(message) {
  if (statusNode) {
    statusNode.textContent = message;
  }
}

function renderRuntimeStatus(payload) {
  runtimeBackendNode.textContent = payload.backend_status || 'offline';
  runtimeEngineNode.textContent =
    payload.engine_mode === 'openai'
      ? `${payload.model_name || 'OpenAI'}`
      : 'Local heuristic';
  runtimeProfileNode.textContent = payload.profile_id || 'default';
  runtimeDatabaseNode.textContent = payload.database_path || 'Unavailable';
  runtimeNoteNode.textContent =
    payload.engine_note || 'Runtime status is available.';
}

function renderOfflineRuntimeStatus() {
  renderRuntimeStatus({
    backend_status: 'offline',
    engine_mode: 'heuristic',
    profile_id: 'default',
    database_path: 'Backend unavailable',
    engine_note:
      'Backend is offline. Start the local API or launch through the desktop shell.'
  });
}

function fillFormFromRequest(request) {
  const goalEl = document.getElementById('goal');
  if (goalEl && request.goal !== undefined) {
    goalEl.value = request.goal ?? '';
  }
  const setVal = (id, key, fallback) => {
    const el = document.getElementById(id);
    if (!el || request[key] === undefined) {
      return;
    }
    el.value = request[key] ?? fallback;
  };
  setVal('skillLevel', 'skill_level', 'beginner');
  setVal('budget', 'budget', 'low');
  setVal('workflowStyle', 'workflow_style', 'fast execution');
  setVal('timeline', 'timeline', 'this week');
  setVal('primaryOutcome', 'primary_outcome', 'working prototype');
  setVal('teamContext', 'team_context', 'solo');
  setVal('installPreference', 'install_preference', 'local-first');
  setVal('constraints', 'constraints', '');
  document.querySelectorAll('input[name="pain_points"]').forEach((input) => {
    input.checked = (request.pain_points || []).includes(input.value);
  });
  updateConditionalFields();
}

function renderSessions(items) {
  if (!sessionList) {
    return;
  }

  if (!items?.length) {
    sessionList.innerHTML =
      '<p class="session-empty">No saved sessions yet. Generate a preview to create the first one.</p>';
    return;
  }

  sessionList.innerHTML = items
    .map(
      (item) => `
        <button class="session-card" type="button" data-session-id="${escapeHtml(item.id)}">
          <div class="session-card__top">
            <p class="session-card__meta">${escapeHtml(item.workflow_style)} | ${escapeHtml(item.budget)} | ${escapeHtml(item.skill_level)}</p>
            <span class="stack-score">${escapeHtml(item.top_tool_name || 'Preview')}</span>
          </div>
          <h3 class="session-card__title">${escapeHtml(item.goal)}</h3>
          <p class="session-card__summary">${escapeHtml(item.summary)}</p>
        </button>
      `
    )
    .join('');

  sessionList.querySelectorAll('[data-session-id]').forEach((button) => {
    button.addEventListener('click', async () => {
      const sessionId = button.getAttribute('data-session-id');
      try {
        const response = await fetch(apiUrl(`/api/sessions/${sessionId}`));
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }
        const payload = await response.json();
        fillFormFromRequest(payload.request);
        renderResponse(payload.response);
        setStatusMessage('Loaded a saved local session.');
        await loadRuntimeStatus();
      } catch (error) {
        setStatusMessage('Could not load that saved session from the backend.');
      }
    });
  });
}

async function loadSessions() {
  if (!sessionList) {
    return;
  }

  try {
    const response = await fetch(apiUrl('/api/sessions'));
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    const payload = await response.json();
    renderSessions(payload);
  } catch (error) {
    renderSessions([]);
  }
}

async function loadRuntimeStatus() {
  try {
    const response = await fetch(apiUrl('/api/runtime-status'));
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    const payload = await response.json();
    renderRuntimeStatus(payload);
  } catch (error) {
    renderOfflineRuntimeStatus();
  }
}

function buildPayload(formData) {
  return {
    goal:
      formData.get('goal') ||
      'Choose the right AI tools for my first practical workflow.',
    skill_level: formData.get('skill_level') || 'beginner',
    budget: formData.get('budget') || 'low',
    workflow_style: formData.get('workflow_style') || 'fast execution',
    timeline: formData.get('timeline') || 'this week',
    primary_outcome: formData.get('primary_outcome') || 'working prototype',
    team_context: formData.get('team_context') || 'solo',
    install_preference: formData.get('install_preference') || 'local-first',
    pain_points: formData.getAll('pain_points'),
    constraints: formData.get('constraints') || ''
  };
}

function setPreviewLoading(loading) {
  if (!previewSubmitButton) {
    return;
  }
  previewSubmitButton.disabled = loading;
  previewSubmitButton.setAttribute('aria-busy', loading ? 'true' : 'false');
  previewSubmitButton.classList.toggle('is-loading', loading);
}

async function savePreferences() {
  const formData = new FormData(form);
  const payload = { profile_id: 'default', ...buildPayload(formData) };

  try {
    const response = await fetch(apiUrl('/api/preferences'), {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    setStatusMessage('Saved local defaults for future runs.');
    await loadRuntimeStatus();
  } catch (error) {
    setStatusMessage('Could not save defaults. Backend may be unavailable.');
  }
}

async function loadPreferences() {
  try {
    const response = await fetch(apiUrl('/api/preferences'));
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    const payload = await response.json();
    fillFormFromRequest(payload);
    setStatusMessage('Loaded local defaults from backend.');
    await loadRuntimeStatus();
  } catch (error) {
    updateConditionalFields();
  }
}

async function requestPreview(formData) {
  const body = buildPayload(formData);
  setPreviewLoading(true);
  try {
    const response = await fetch(apiUrl('/api/recommendations/preview'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const payload = await response.json();
    setStatusMessage('Connected to backend preview API.');
    renderResponse(payload);
    await loadSessions();
    await loadRuntimeStatus();
  } catch (error) {
    setStatusMessage('Backend unavailable, showing local fallback preview.');
    renderResponse(fallbackResponse);
    renderOfflineRuntimeStatus();
  } finally {
    setPreviewLoading(false);
  }
}

form.addEventListener('submit', (event) => {
  event.preventDefault();
  const formData = new FormData(form);
  requestPreview(formData);
});

savePreferencesButton?.addEventListener('click', () => {
  savePreferences();
});

async function exportBackup() {
  try {
    const response = await fetch(apiUrl('/api/backup/export'));
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    let filename = 'navagator-backup.json';
    const disposition = response.headers.get('Content-Disposition');
    if (disposition) {
      const match = disposition.match(/filename="([^"]+)"/);
      if (match) {
        filename = match[1];
      }
    }
    anchor.href = url;
    anchor.download = filename;
    anchor.rel = 'noopener';
    anchor.click();
    URL.revokeObjectURL(url);
    setStatusMessage('Backup file downloaded.');
  } catch (error) {
    setStatusMessage('Could not export backup. Is the backend running?');
  }
}

exportBackupButton?.addEventListener('click', () => {
  exportBackup();
});

if (copySessionIdButton && sessionIdDisplayNode) {
  copySessionIdButton.addEventListener('click', async () => {
    const id = sessionIdDisplayNode.textContent;
    if (!id) {
      return;
    }
    try {
      await navigator.clipboard.writeText(id);
      setStatusMessage('Session id copied to clipboard.');
    } catch {
      setStatusMessage('Could not copy session id.');
    }
  });
}

async function init() {
  await loadQuestionnaire();
  bindFieldChangeListeners();
  updateConditionalFields();
  renderResponse(fallbackResponse);
  renderOfflineRuntimeStatus();
  await loadPreferences();
  loadSessions();
  loadRuntimeStatus();
}

init();
