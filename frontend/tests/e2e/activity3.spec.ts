import { test, expect } from '@playwright/test';
import type { Page } from '@playwright/test';
import { mkdir } from 'node:fs/promises';
const PASSWORD = 'Activity3-test-password-123!';
const api = 'http://127.0.0.1:8001/api/v1';
async function login(page: Page, role = 'admin') {
  await page.goto('/login');
  await page.getByLabel('Email address').fill(`${role}@example.com`);
  await page.getByLabel('Password', { exact: true }).fill(PASSWORD);
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();
  await expect(page.locator('#main')).toBeVisible();
  await page.goto('/');
  await expect(page.getByRole('heading', { name: /Welcome back/ })).toBeVisible();
}
async function screenshot(page: Page, name: string) {
  await expect(page.locator('.state-panel[role="status"]')).toHaveCount(0);
  await page.evaluate(() => document.fonts.ready);
  await mkdir('docs/evidence', { recursive: true });
  await page.screenshot({
    path: `docs/evidence/${name}.png`,
    fullPage: true,
    animations: 'disabled',
  });
}
async function fillStudent(page: Page, number: string) {
  await page.locator('#field-student_number').fill(number);
  await page.locator('#field-first_name').fill('Amelia');
  await page.locator('#field-last_name').fill('Santos');
  await expect(page.locator('#field-program_id option[value="1"]')).toBeAttached();
  await page.locator('#field-program_id').selectOption('1');
  await page.locator('#field-email').fill('amelia@example.com');
}

test('authentication, protected navigation, expired sessions and logout', async ({ page }) => {
  await page.goto('/students');
  await expect(page).toHaveURL(/\/login/);
  await screenshot(page, '01-login');
  await page.getByLabel('Email address').fill('admin@example.com');
  await page.getByLabel('Password', { exact: true }).fill('incorrect');
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();
  await expect(page.getByRole('alert')).toHaveText('Invalid email or password.');
  await screenshot(page, '02-invalid-login');
  await page.getByLabel('Password', { exact: true }).fill(PASSWORD);
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();
  await expect(page).toHaveURL(/\/students$/);
  await expect(page.locator('tbody tr')).toHaveCount(20);
  await page.getByRole('link', { name: 'Overview', exact: true }).click();
  await expect(page.getByRole('heading', { name: /Welcome back/ })).toBeVisible();
  await screenshot(page, '03-dashboard');
  await page.goto('/students/1');
  await page.reload();
  await expect(page.getByRole('heading', { name: 'Student001 Family001' })).toBeVisible();
  await page.evaluate(() => sessionStorage.setItem('campus.session', 'expired-token'));
  await page.reload();
  await expect(page).toHaveURL(/\/login/);
  await expect(page.getByText('Your session has expired.')).toBeVisible();
  await login(page);
  await page.getByRole('button', { name: 'Sign out', exact: true }).click();
  await expect(page).toHaveURL(/\/login/);
  expect(await page.evaluate(() => sessionStorage.getItem('campus.session'))).toBeNull();
});

test('students use backend search, filters, pagination, CRUD and validation', async ({ page }) => {
  await login(page);
  await page.getByRole('link', { name: 'Students', exact: true }).click();
  await expect(page.locator('tbody tr')).toHaveCount(20);
  await screenshot(page, '04-students');
  await page.getByRole('button', { name: 'Next page', exact: true }).click();
  await expect(page.getByText('Page 2 of 5')).toBeVisible();
  await page.getByRole('searchbox').count();
  await page.getByRole('textbox', { name: 'Search students', exact: true }).fill('Student001');
  await page.getByRole('button', { name: 'Search', exact: true }).click();
  await expect(page.locator('tbody tr')).toHaveCount(1);
  await expect(page.locator('tbody')).toContainText('2026-00001');
  await page.getByLabel('Year level', { exact: true }).selectOption('2');
  await expect(page.getByRole('heading', { name: 'No students found' })).toBeVisible();
  await screenshot(page, '05-empty-state');
  await page.getByRole('button', { name: 'Reset', exact: true }).click();
  await expect(page).toHaveURL(/\/students$/);
  await page.getByLabel('Program', { exact: true }).selectOption('1');
  await page.getByLabel('Year level', { exact: true }).selectOption('1');
  await page.getByLabel('Sort by').selectOption('-last_name');
  await expect(page.locator('tbody tr')).toHaveCount(9);
  await expect(page).toHaveURL(/program_id=1/);
  await page.getByRole('link', { name: 'Add student', exact: true }).click();
  await page.getByRole('button', { name: 'Create student', exact: true }).click();
  await expect(page.getByRole('alert')).toContainText('review the highlighted fields');
  await fillStudent(page, '2026-00001');
  await page.getByRole('button', { name: 'Create student', exact: true }).click();
  await expect(page.getByRole('alert')).toContainText('Duplicate record');
  await screenshot(page, '06-conflict-feedback');
  await page.locator('#field-student_number').fill('ACT3-STUDENT');
  await page.locator('#field-user_id').fill('999999');
  await page.getByRole('button', { name: 'Create student', exact: true }).click();
  await expect(page.getByText('Referenced record does not exist.')).toBeVisible();
  await screenshot(page, '07-field-validation');
  await page.locator('#field-user_id').fill('');
  await page.getByRole('button', { name: 'Create student', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Amelia Santos' })).toBeVisible();
  const path = new URL(page.url()).pathname;
  await page.getByRole('link', { name: 'Edit student', exact: true }).click();
  await expect(page.locator('#field-first_name')).toHaveValue('Amelia');
  await page.locator('#field-first_name').fill('Amelia Updated');
  await page.getByRole('button', { name: 'Save changes', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Amelia Updated Santos' })).toBeVisible();
  await screenshot(page, '08-student-detail');
  await page.getByRole('link', { name: 'Edit student', exact: true }).click();
  await page.locator('#field-status').selectOption('INACTIVE');
  await page.getByRole('button', { name: 'Save changes', exact: true }).click();
  await expect(page.getByRole('dialog')).toBeVisible();
  await screenshot(page, '09-deactivate-confirmation');
  await page.getByRole('button', { name: 'Confirm change' }).click();
  await expect(page).toHaveURL(new RegExp(path + '$'));
  await expect(page.locator('.panel-heading .badge')).toHaveText('inactive');
  await page.goto('/students');
  const id = path.split('/').pop();
  await page.getByRole('textbox', { name: 'Search students', exact: true }).fill('ACT3-STUDENT');
  await page.getByRole('button', { name: 'Search', exact: true }).click();
  await page.getByRole('button', { name: `Delete student ${id}`, exact: true }).click();
  await page.getByRole('button', { name: 'Delete record', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'No students found' })).toBeVisible();
});

test('reference data, offerings, enrollment and grades complete a real academic flow', async ({
  page,
}) => {
  await login(page);
  await page.goto('/programs/new');
  await page.locator('#field-code').fill('ACT3');
  await page.locator('#field-name').fill('Activity Three Program');
  await page.getByRole('button', { name: 'Create program', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Activity Three Program' })).toBeVisible();
  await page.goto('/courses/new');
  await expect(page.locator('#field-program_id option[value="1"]')).toBeAttached();
  await page.locator('#field-program_id').selectOption('1');
  await page.locator('#field-course_code').fill('ACT301');
  await page.locator('#field-course_title').fill('Frontend Integration');
  await page.getByRole('button', { name: 'Create subject', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Frontend Integration' })).toBeVisible();
  const courseId = new URL(page.url()).pathname.split('/').pop()!;
  await page.goto('/programs/1');
  await expect(page.getByRole('heading', { name: 'Subjects' })).toBeVisible();
  await expect(page.getByRole('cell', { name: 'ACT301' })).toBeVisible();
  await page.goto('/academic-terms/new');
  await page.locator('#field-academic_year').fill('2028-2029');
  await page.locator('#field-semester').selectOption('FIRST');
  await page.locator('#field-start_date').fill('2028-08-01');
  await page.locator('#field-end_date').fill('2028-12-20');
  await page.getByRole('button', { name: 'Create academic term', exact: true }).click();
  await expect(page.getByRole('heading', { name: /Academic term #/ })).toBeVisible();
  const termId = new URL(page.url()).pathname.split('/').pop()!;
  await page.goto('/course-offerings/new');
  await page.getByRole('textbox', { name: 'Search subject options', exact: true }).fill('ACT301');
  await page.getByRole('button', { name: 'Search subject', exact: true }).click();
  await expect(page.locator(`#field-course_id option[value="${courseId}"]`)).toBeAttached();
  await page.locator('#field-course_id').selectOption(courseId);
  await expect(page.locator(`#field-academic_term_id option[value="${termId}"]`)).toBeAttached();
  await page.locator('#field-academic_term_id').selectOption(termId);
  await expect(page.locator('#field-instructor_id option[value="3"]')).toBeAttached();
  await page.locator('#field-instructor_id').selectOption('3');
  await page.locator('#field-section').fill('ACT3');
  await page.locator('#field-schedule').fill('Monday 10:00–11:30');
  await screenshot(page, '10-offering-form');
  await page.getByRole('button', { name: 'Create subject offering', exact: true }).click();
  await expect(page.getByRole('heading', { name: /Subject offering #/ })).toBeVisible();
  const offeringId = new URL(page.url()).pathname.split('/').pop()!;
  await page.goto('/enrollments/new');
  await expect(page.locator('#field-student_id option[value="1"]')).toBeAttached();
  await page.locator('#field-student_id').selectOption('1');
  await page
    .getByRole('textbox', { name: 'Search subject offering options', exact: true })
    .fill('ACT3');
  await page.getByRole('button', { name: 'Search subject offering', exact: true }).click();
  await expect(
    page.locator(`#field-course_offering_id option[value="${offeringId}"]`)
  ).toBeAttached();
  await page.locator('#field-course_offering_id').selectOption(offeringId);
  await page.getByRole('button', { name: 'Create enrollment', exact: true }).click();
  await expect(page.getByRole('heading', { name: /Enrollment #/ })).toBeVisible();
  const enrollmentId = new URL(page.url()).pathname.split('/').pop()!;
  await page.goto('/enrollments/new');
  await expect(page.locator('#field-student_id option[value="1"]')).toBeAttached();
  await page.locator('#field-student_id').selectOption('1');
  await page
    .getByRole('textbox', { name: 'Search subject offering options', exact: true })
    .fill('ACT3');
  await page.getByRole('button', { name: 'Search subject offering', exact: true }).click();
  await expect(
    page.locator(`#field-course_offering_id option[value="${offeringId}"]`)
  ).toBeAttached();
  await page.locator('#field-course_offering_id').selectOption(offeringId);
  await page.getByRole('button', { name: 'Create enrollment', exact: true }).click();
  await expect(page.getByRole('alert')).toContainText('Duplicate');
  // The paginated selector can reach records beyond its first page.
  await page.goto('/grades/new');
  for (let i = 0; i < 10; i++) {
    await page.getByRole('button', { name: 'Next enrollment options', exact: true }).click();
    await expect(page.getByText(`Options page ${i + 2} of 11`)).toBeVisible();
  }
  await expect(page.locator(`#field-enrollment_id option[value="${enrollmentId}"]`)).toBeAttached();
  await page.locator('#field-enrollment_id').selectOption(enrollmentId);
  await page.locator('#field-midterm_grade').fill('85');
  await page.locator('#field-final_grade').fill('92');
  await page.getByRole('button', { name: 'Create grade', exact: true }).click();
  await expect(page.getByRole('heading', { name: /Grade #/ })).toBeVisible();
  await page.goto('/academic-record?student=1');
  await expect(page.getByRole('heading', { name: '2028-2029', exact: true })).toBeVisible();
  await expect(page.locator('tbody').filter({ hasText: 'ACT301' })).toBeVisible();
  await screenshot(page, '11-academic-record');
  await page.goto(`/enrollments/${enrollmentId}/edit`);
  await page.locator('#field-status').selectOption('COMPLETED');
  await page.getByRole('button', { name: 'Save changes', exact: true }).click();
  await expect(page.locator('.panel-heading .badge')).toHaveText('completed');
});

test('restricted roles keep backend authorization authoritative', async ({ page, request }) => {
  await login(page, 'instructor');
  await expect(page.getByRole('link', { name: 'Students', exact: true })).toHaveCount(0);
  await page.goto('/grades/1/edit');
  await page.locator('#field-final_grade').fill('93');
  await page.getByRole('button', { name: 'Save changes', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Grade #1', exact: true })).toBeVisible();
  await page.goto('/grades/1/edit');
  await page.locator('#field-final_grade').fill('101');
  await page.getByRole('button', { name: 'Save changes', exact: true }).click();
  await expect(page.getByText('Enter a number from 0 to 100.')).toBeVisible();
  await page.goto('/course-offerings/2/students');
  await expect(page.getByRole('heading', { name: 'Access denied' })).toBeVisible();
  await screenshot(page, '12-forbidden');
  const instructorToken = await page.evaluate(() => sessionStorage.getItem('campus.session'));
  const denied = await request.patch(`${api}/grades/3`, {
    headers: { Authorization: `Bearer ${instructorToken}` },
    data: { final_grade: 99 },
  });
  expect(denied.status()).toBe(403);
  await page.getByRole('button', { name: 'Sign out', exact: true }).click();
  await login(page, 'student');
  await expect(page.getByRole('link', { name: 'Students', exact: true })).toHaveCount(0);
  await page.getByRole('link', { name: 'Academic record', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'My academic record' })).toBeVisible();
  await expect(page.getByRole('heading', { name: '2026-2027', exact: true }).first()).toBeVisible();
  await expect(page.getByText('General weighted average')).toBeVisible();
  await expect(page.getByTestId('gwa-value')).toHaveText(/^\d+\.\d{2}$/);
  await screenshot(page, '13-student-portal');
  await page.goto('/profile');
  await expect(page.getByTestId('profile-gwa')).toHaveText(/^\d+\.\d{2}$/);
  await page.goto('/students/2');
  await expect(page.getByRole('heading', { name: 'Access denied' })).toBeVisible();
  await page.goto('/grades/1/edit');
  await expect(page.getByRole('heading', { name: 'Access denied' })).toBeVisible();
  await page.getByRole('button', { name: 'Sign out', exact: true }).click();
  await login(page, 'registrar');
  await expect(page.getByRole('link', { name: 'Grades', exact: true })).toHaveCount(0);
  await page.goto('/grades');
  await expect(page.getByRole('heading', { name: 'Access denied' })).toBeVisible();
  const registrarToken = await page.evaluate(() => sessionStorage.getItem('campus.session'));
  const registrarHeaders = { Authorization: `Bearer ${registrarToken}` };
  expect((await request.get(`${api}/grades`, { headers: registrarHeaders })).status()).toBe(403);
  const transcript = await request.get(`${api}/students/1/academic-record`, {
    headers: registrarHeaders,
  });
  expect(transcript.status()).toBe(200);
  expect(typeof (await transcript.json()).data.gwa).toBe('number');
  await page.goto('/course-offerings/new');
  await expect(page.locator('#field-instructor_id option[value="3"]')).toBeAttached();
  await expect(page.getByRole('link', { name: 'User accounts', exact: true })).toHaveCount(0);
});

test('controlled loading, offline, server error, missing record and route states', async ({
  page,
}) => {
  await login(page);
  await page.route('**/api/v1/students?**', async (route) => {
    await new Promise((resolve) => setTimeout(resolve, 700));
    await route.continue();
  });
  await page.goto('/students');
  await expect(page.getByRole('status')).toContainText('Loading records');
  await expect(page.locator('tbody tr')).toHaveCount(20);
  await page.unroute('**/api/v1/students?**');
  await page.route('**/api/v1/students?**', (route) => route.abort('failed'));
  await page.reload();
  await expect(page.getByRole('heading', { name: 'Connection unavailable' })).toBeVisible();
  await screenshot(page, '14-network-error');
  await page.unroute('**/api/v1/students?**');
  await page.getByRole('button', { name: 'Try again', exact: true }).click();
  await expect(page.locator('tbody tr')).toHaveCount(20);
  await page.route('**/api/v1/students?**', (route) =>
    route.fulfill({
      status: 500,
      contentType: 'application/json',
      body: JSON.stringify({ message: 'private stack trace' }),
    })
  );
  await page.reload();
  await expect(page.getByRole('alert')).toContainText('The server could not complete');
  await expect(page.getByText('private stack trace')).toHaveCount(0);
  await screenshot(page, '15-server-error');
  await page.unroute('**/api/v1/students?**');
  await page.goto('/students/9999999');
  await expect(page.getByRole('heading', { name: 'Record not found' })).toBeVisible();
  await page.goto('/missing-route');
  await expect(page.getByRole('heading', { name: 'Record not found' })).toBeVisible();
  await screenshot(page, '16-not-found');
});

test('major modules and narrow layout are usable', async ({ page }) => {
  await login(page);
  for (const [path, name] of [
    ['programs', 'programs'],
    ['courses', 'courses'],
    ['academic-terms', 'terms'],
    ['course-offerings', 'offerings'],
    ['enrollments', 'enrollments'],
    ['grades', 'grades'],
    ['profile', 'profile'],
  ]) {
    await page.goto('/' + path);
    await expect(page.locator('.state-panel[role="status"]')).toHaveCount(0);
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
    await screenshot(page, `module-${name}`);
  }
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/students');
  await expect(page.locator('tbody tr')).toHaveCount(20);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(
    true
  );
  await screenshot(page, '17-mobile-students');
  await page.getByRole('button', { name: 'Open menu' }).click();
  await expect(page.getByRole('navigation', { name: 'Main navigation' })).toBeVisible();
  await page.getByRole('link', { name: 'Overview', exact: true }).click();
  await expect(page.getByRole('heading', { name: /Welcome back/ })).toBeVisible();
  await screenshot(page, '18-mobile-dashboard');
  await page.goto('/students/new');
  await page.locator('#field-first_name').fill('Mobile');
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(
    true
  );
  await screenshot(page, '19-mobile-form');
});

test('stale enrollment reference is rejected by the real backend and shown inline', async ({
  page,
  request,
}) => {
  await login(page);
  const token = await page.evaluate(() => sessionStorage.getItem('campus.session'));
  const headers = { Authorization: `Bearer ${token}` };
  const created = await request.post(`${api}/students`, {
    headers,
    data: {
      student_number: 'ACT3-STALE',
      first_name: 'Temporary',
      last_name: 'Student',
      program_id: 1,
      year_level: 1,
    },
  });
  expect(created.status()).toBe(201);
  const student = (await created.json()).data;
  await page.goto('/enrollments/new');
  await page
    .getByRole('textbox', { name: 'Search student options', exact: true })
    .fill('ACT3-STALE');
  await page.getByRole('button', { name: 'Search student', exact: true }).click();
  await expect(page.locator(`#field-student_id option[value="${student.id}"]`)).toBeAttached();
  await page.locator('#field-student_id').selectOption(String(student.id));
  await expect(page.locator('#field-course_offering_id option[value="1"]')).toBeAttached();
  await page.locator('#field-course_offering_id').selectOption('1');
  expect((await request.delete(`${api}/students/${student.id}`, { headers })).status()).toBe(204);
  await page.getByRole('button', { name: 'Create enrollment', exact: true }).click();
  await expect(page.getByText('Referenced record does not exist.')).toBeVisible();
  await screenshot(page, '20-stale-enrollment-reference');
  const invalidGrade = await request.patch(`${api}/grades/1`, {
    headers,
    data: { final_grade: 101 },
  });
  expect(invalidGrade.status()).toBe(422);
});
