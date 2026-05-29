const api = {
  students: "/api/students",
  internships: "/api/internships",
  journal: "/api/journal-entries",
  effects: "/api/effects",
};

const state = {
  students: [],
  internships: [],
  journal: [],
  effects: [],
};

const studentForm = document.getElementById("student-form");
const internshipForm = document.getElementById("internship-form");
const journalForm = document.getElementById("journal-form");
const effectForm = document.getElementById("effect-form");

const studentList = document.getElementById("student-list");
const internshipList = document.getElementById("internship-list");
const journalList = document.getElementById("journal-list");
const effectList = document.getElementById("effect-list");

const studentSelects = document.querySelectorAll("[data-student-select]");
const internshipSelects = document.querySelectorAll("[data-internship-select]");

const messageBox = (key) => document.querySelector(`[data-message="${key}"]`);

const showMessage = (key, message, isError = false) => {
  const box = messageBox(key);
  if (!box) {
    return;
  }
  box.textContent = message;
  box.classList.remove("is-hidden");
  box.classList.toggle("error", isError);
};

const clearMessage = (key) => {
  const box = messageBox(key);
  if (!box) {
    return;
  }
  box.textContent = "";
  box.classList.add("is-hidden");
  box.classList.remove("error");
};

const requestJson = async (url, options = {}) => {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  let payload = {};
  try {
    payload = await response.json();
  } catch (error) {
    payload = {};
  }
  if (!response.ok) {
    const err = new Error(payload.error || "Blad API");
    err.payload = payload;
    throw err;
  }
  return payload;
};

const formatError = (error) => {
  if (error?.payload?.details) {
    const details = Object.values(error.payload.details).join(" ");
    return `${error.payload.error} ${details}`.trim();
  }
  if (error?.payload?.error) {
    return error.payload.error;
  }
  return "Wystapil blad podczas zapisu.";
};

const renderList = (element, items, formatter, emptyText) => {
  element.innerHTML = "";
  if (!items.length) {
    const empty = document.createElement("div");
    empty.className = "list-item";
    empty.textContent = emptyText;
    element.appendChild(empty);
    return;
  }
  items.forEach((item) => {
    element.appendChild(formatter(item));
  });
};

const createListItem = (title, meta) => {
  const item = document.createElement("div");
  item.className = "list-item";

  const titleEl = document.createElement("div");
  titleEl.className = "title";
  titleEl.textContent = title;

  const metaEl = document.createElement("div");
  metaEl.className = "meta";
  metaEl.textContent = meta;

  item.append(titleEl, metaEl);
  return item;
};

const populateSelects = (selects, items, labelFn) => {
  selects.forEach((select) => {
    const current = select.value;
    select.innerHTML = "<option value=\"\">Wybierz</option>";
    items.forEach((item) => {
      const option = document.createElement("option");
      option.value = item.id;
      option.textContent = labelFn(item);
      select.appendChild(option);
    });
    if (current) {
      select.value = current;
    }
  });
};

const loadStudents = async () => {
  const data = await requestJson(api.students);
  state.students = data.data || [];
  populateSelects(studentSelects, state.students, (item) => `${item.id} - ${item.name}`);
  renderList(
    studentList,
    state.students,
    (item) => createListItem(`${item.name}`, `ID ${item.id} | ${item.email}`),
    "Brak studentow."
  );
};

const loadInternships = async () => {
  const data = await requestJson(api.internships);
  state.internships = data.data || [];
  populateSelects(internshipSelects, state.internships, (item) => `${item.id} - ${item.company}`);
  renderList(
    internshipList,
    state.internships,
    (item) =>
      createListItem(
        `${item.company} (student ${item.student_id})`,
        `ID ${item.id} | ${item.start_date} - ${item.end_date} | ${item.status}`
      ),
    "Brak praktyk."
  );
};

const loadJournalEntries = async () => {
  const data = await requestJson(api.journal);
  state.journal = data.data || [];
  renderList(
    journalList,
    state.journal,
    (item) =>
      createListItem(
        `${item.activity} (${item.hours}h)`,
        `ID ${item.id} | praktyka ${item.internship_id} | ${item.date}`
      ),
    "Brak wpisow dziennika."
  );
};

const loadEffects = async () => {
  const data = await requestJson(api.effects);
  state.effects = data.data || [];
  renderList(
    effectList,
    state.effects,
    (item) =>
      createListItem(
        `${item.code} - ${item.description}`,
        `ID ${item.id} | praktyka ${item.internship_id} | osiagniety: ${item.achieved ? "tak" : "nie"}`
      ),
    "Brak efektow."
  );
};

const refreshAll = async () => {
  await loadStudents();
  await loadInternships();
  await loadJournalEntries();
  await loadEffects();
};

const parseId = (value) => {
  const parsed = Number.parseInt(value, 10);
  return Number.isNaN(parsed) ? null : parsed;
};

const isEmailValid = (value) => /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(value);

studentForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  clearMessage("student");

  const name = studentForm.name.value.trim();
  const email = studentForm.email.value.trim();

  if (!name || !email) {
    showMessage("student", "Uzupelnij wymagane pola.", true);
    return;
  }
  if (!isEmailValid(email)) {
    showMessage("student", "Nieprawidlowy format email.", true);
    return;
  }

  try {
    await requestJson(api.students, {
      method: "POST",
      body: JSON.stringify({ name, email }),
    });
    studentForm.reset();
    showMessage("student", "Student zostal dodany.");
    await refreshAll();
  } catch (error) {
    showMessage("student", formatError(error), true);
  }
});

internshipForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  clearMessage("internship");

  const studentId = parseId(internshipForm.student_id.value);
  const company = internshipForm.company.value.trim();
  const startDate = internshipForm.start_date.value;
  const endDate = internshipForm.end_date.value;
  const status = internshipForm.status.value;

  if (!studentId || !company || !startDate || !endDate || !status) {
    showMessage("internship", "Uzupelnij wymagane pola.", true);
    return;
  }

  try {
    await requestJson(api.internships, {
      method: "POST",
      body: JSON.stringify({
        student_id: studentId,
        company,
        start_date: startDate,
        end_date: endDate,
        status,
      }),
    });
    internshipForm.reset();
    showMessage("internship", "Praktyka zostala dodana.");
    await refreshAll();
  } catch (error) {
    showMessage("internship", formatError(error), true);
  }
});

journalForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  clearMessage("journal");

  const internshipId = parseId(journalForm.internship_id.value);
  const date = journalForm.date.value;
  const activity = journalForm.activity.value.trim();
  const hours = parseId(journalForm.hours.value);

  if (!internshipId || !date || !activity || !hours) {
    showMessage("journal", "Uzupelnij wymagane pola.", true);
    return;
  }

  try {
    await requestJson(api.journal, {
      method: "POST",
      body: JSON.stringify({
        internship_id: internshipId,
        date,
        activity,
        hours,
      }),
    });
    journalForm.reset();
    showMessage("journal", "Wpis dziennika zostal dodany.");
    await refreshAll();
  } catch (error) {
    showMessage("journal", formatError(error), true);
  }
});

effectForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  clearMessage("effect");

  const internshipId = parseId(effectForm.internship_id.value);
  const code = effectForm.code.value.trim();
  const description = effectForm.description.value.trim();
  const achieved = effectForm.achieved.checked;

  if (!internshipId || !code || !description) {
    showMessage("effect", "Uzupelnij wymagane pola.", true);
    return;
  }

  try {
    await requestJson(api.effects, {
      method: "POST",
      body: JSON.stringify({
        internship_id: internshipId,
        code,
        description,
        achieved,
      }),
    });
    effectForm.reset();
    showMessage("effect", "Efekt zostal dodany.");
    await refreshAll();
  } catch (error) {
    showMessage("effect", formatError(error), true);
  }
});

refreshAll();
