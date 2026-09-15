import assert from 'node:assert/strict';
import { promises as fs } from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';
import {
  REPO_ROOT,
  assertSafeArtifactPath,
  computeParallelBatches,
  loadConfig,
  readJson,
  recordDecision,
  recordResult,
  renderPrompt,
  statusReport,
  syncReady,
  transitionItem,
  validateResult,
  validateRun,
  verifySystem,
  writeJsonAtomic,
} from '../src/core.mjs';

const examplePath = (...segments) => path.join(REPO_ROOT, '.orchestrator', 'examples', ...segments, 'run.json');

test('örnek run graphları semantic doğrulamadan geçer', async () => {
  const config = await loadConfig();
  for (const name of ['small-fix', 'cross-layer-feature', 'security-revision']) {
    const validation = validateRun(await readJson(examplePath(name)), config);
    assert.equal(validation.valid, true, `${name}: ${validation.errors.join(' | ')}`);
  }
});

test('dependency cycle reddedilir', async () => {
  const config = await loadConfig();
  const run = structuredClone(await readJson(examplePath('small-fix')));
  const clone = structuredClone(run.items[0]);
  clone.id = 'second-fix';
  clone.relations.dependsOn = ['fix-copy'];
  clone.status = 'draft';
  run.items[0].relations.dependsOn = ['second-fix'];
  run.items[0].status = 'draft';
  run.items.push(clone);
  const validation = validateRun(run, config);
  assert.equal(validation.valid, false);
  assert.ok(validation.errors.some((error) => error.includes('Dependency cycle')));
});

test('çakışan writer scope aynı batch içine alınmaz', async () => {
  const config = await loadConfig();
  const run = structuredClone(await readJson(examplePath('small-fix')));
  const nestedWriter = structuredClone(run.items[0]);
  nestedWriter.id = 'nested-writer';
  nestedWriter.execution.writeScopes = ['docs/example.md/child'];
  const separateWriter = structuredClone(run.items[0]);
  separateWriter.id = 'separate-writer';
  separateWriter.execution.writeScopes = ['FIRST/example'];
  const aliasedWriter = structuredClone(run.items[0]);
  aliasedWriter.id = 'aliased-writer';
  aliasedWriter.execution.writeScopes = ['docs/../docs/example.md'];
  run.items.push(nestedWriter, separateWriter, aliasedWriter);
  const batches = computeParallelBatches(run, config).map((batch) => batch.map((item) => item.id));
  assert.ok(!batches.some((batch) => batch.includes('fix-copy') && batch.includes('nested-writer')));
  assert.ok(!batches.some((batch) => batch.includes('fix-copy') && batch.includes('aliased-writer')));
  assert.ok(batches.some((batch) => batch.includes('fix-copy') && batch.includes('separate-writer')));
});

test('korumalı ve repo dışı write scope reddedilir', async () => {
  const config = await loadConfig();
  const protectedRun = structuredClone(await readJson(examplePath('small-fix')));
  protectedRun.items[0].execution.writeScopes = ['.git/config'];
  assert.equal(validateRun(protectedRun, config).valid, false);
  const escapingRun = structuredClone(await readJson(examplePath('small-fix')));
  escapingRun.items[0].execution.writeScopes = ['../../outside'];
  assert.equal(validateRun(escapingRun, config).valid, false);
  await assert.rejects(() => assertSafeArtifactPath(path.join(REPO_ROOT, '.git', 'probe.txt')), /korumalı/);
});

test('pending approval dispatchi engeller, approved decision kapıyı açar', async () => {
  const config = await loadConfig();
  const run = structuredClone(await readJson(examplePath('cross-layer-feature')));
  run.items.find((item) => item.id === 'scope-analysis').status = 'done';
  run.items.find((item) => item.id === 'define-api-contract').status = 'ready';
  let validation = validateRun(run, config);
  assert.equal(validation.valid, false);
  assert.ok(validation.errors.some((error) => error.includes('approval boundary')));
  assert.equal(computeParallelBatches(run, config).flat().some((item) => item.id === 'define-api-contract'), false);

  run.decisions.push({
    id: 'approve-contract-policy',
    summary: 'Contract policy değişikliği onaylandı.',
    reason: 'Ürün sahibi retention ve response shape kararını kabul etti.',
    decidedAt: '2026-07-16T09:30:00.000Z',
    actor: 'manager',
    extensions: {
      type: 'approval',
      itemId: 'define-api-contract',
      boundary: 'schema-policy-change',
      outcome: 'approved',
      provenance: 'user-confirmed',
    },
  });
  validation = validateRun(run, config);
  assert.equal(validation.valid, false);
  run.decisions.at(-1).actor = 'product-owner';
  validation = validateRun(run, config);
  assert.equal(validation.valid, true, validation.errors.join(' | '));
  assert.equal(computeParallelBatches(run, config).flat().some((item) => item.id === 'define-api-contract'), true);
});

test('failed artifact yalnız review veya revision ilişkisi için dependency olabilir', async () => {
  const config = await loadConfig();
  const run = structuredClone(await readJson(examplePath('security-revision')));
  const review = run.items.find((item) => item.id === 'security-review-v1');
  review.status = 'ready';
  review.resultRef = null;
  assert.ok(computeParallelBatches(run, config).flat().some((item) => item.id === review.id));
  review.relations.reviews = [];
  assert.equal(computeParallelBatches(run, config).flat().some((item) => item.id === review.id), false);
});

test('approval decision event olarak kaydolur ve sync itemı ready yapar', async (context) => {
  const temporaryRoot = await fs.mkdtemp(path.join(os.tmpdir(), 'orchestrator-approval-'));
  context.after(async () => {
    if (path.resolve(temporaryRoot).startsWith(path.resolve(os.tmpdir()))) {
      await fs.rm(temporaryRoot, { recursive: true, force: true });
    }
  });
  const runPath = path.join(temporaryRoot, 'run.json');
  const run = structuredClone(await readJson(examplePath('cross-layer-feature')));
  run.items.find((item) => item.id === 'scope-analysis').status = 'done';
  await writeJsonAtomic(runPath, run);
  await recordDecision(runPath, {
    id: 'approve-contract-policy',
    summary: 'Contract policy değişikliği onaylandı.',
    reason: 'Ürün sahibi saklama ve response kararını kabul etti.',
    extensions: {
      type: 'approval',
      itemId: 'define-api-contract',
      boundary: 'schema-policy-change',
      outcome: 'approved',
      provenance: 'user-confirmed',
    },
  }, 'product-owner');
  const synced = await syncReady(runPath, 'test-manager');
  assert.ok(synced.changed.includes('define-api-contract'));
  const events = (await fs.readFile(path.join(temporaryRoot, 'events.jsonl'), 'utf8')).trim().split(/\r?\n/).map(JSON.parse);
  assert.deepEqual(events.map((event) => event.type), ['decision-recorded', 'item-ready']);
});

test('render çıktısı acceptance ve platform fallback bilgisini taşır', async () => {
  const run = await readJson(examplePath('small-fix'));
  const rendered = await renderPrompt(run, 'fix-copy', 'codex');
  assert.match(rendered, /Yanlış metin düzeltilmiş olmalı/);
  assert.match(rendered, /native subagents/i);
  assert.match(rendered, /result\.schema\.json/);
});

test('result kaydı itemı done yapar ve append-only event üretir', async (context) => {
  const temporaryRoot = await fs.mkdtemp(path.join(os.tmpdir(), 'orchestrator-test-'));
  context.after(async () => {
    if (path.resolve(temporaryRoot).startsWith(path.resolve(os.tmpdir()))) {
      await fs.rm(temporaryRoot, { recursive: true, force: true });
    }
  });
  const runPath = path.join(temporaryRoot, 'run.json');
  const resultPath = path.join(temporaryRoot, 'incoming-result.json');
  const run = structuredClone(await readJson(examplePath('small-fix')));
  await writeJsonAtomic(runPath, run);
  await transitionItem(runPath, 'fix-copy', 'active', 'Test dispatch', 'test-agent');
  const result = {
    schemaVersion: '1.0.0',
    runId: run.runId,
    itemId: 'fix-copy',
    agent: { platform: 'manual', identity: 'test-agent', sessionRef: null },
    outcome: 'pass',
    summary: 'Acceptance maddeleri doğrulandı.',
    artifacts: [{ type: 'diff', path: 'docs/example.md', change: 'modified', description: 'Metin düzeltildi.' }],
    acceptance: run.items[0].acceptanceCriteria.map((criterion) => ({ criterion, status: 'passed', evidence: 'Test kanıtı.' })),
    checks: [{ name: 'manual-diff-check', status: 'passed', evidence: 'Hedef dışı değişiklik yok.' }],
    risks: [],
    followUps: [],
    completedAt: '2026-07-16T12:00:00.000Z',
  };
  await writeJsonAtomic(resultPath, result);
  const recorded = await recordResult(runPath, resultPath, 'test-manager');
  assert.equal(recorded.status, 'done');
  assert.equal((await readJson(runPath)).items[0].status, 'done');
  const events = (await fs.readFile(path.join(temporaryRoot, 'events.jsonl'), 'utf8')).trim().split(/\r?\n/).map(JSON.parse);
  assert.deepEqual(events.map((event) => event.type), ['status-transition', 'result-recorded', 'status-transition']);
});

test('geçersiz result tarihi path üretmeden reddedilir', async () => {
  const run = await readJson(examplePath('small-fix'));
  const item = run.items[0];
  const result = {
    schemaVersion: '1.0.0',
    runId: run.runId,
    itemId: item.id,
    agent: { platform: 'manual', identity: 'test-agent', sessionRef: null },
    outcome: 'pass',
    summary: 'Geçersiz tarih testi.',
    artifacts: [],
    acceptance: item.acceptanceCriteria.map((criterion) => ({ criterion, status: 'passed', evidence: 'Kanıt.' })),
    checks: [],
    risks: [],
    followUps: [],
    completedAt: '../../outside',
  };
  const validation = validateResult(result, run, item);
  assert.equal(validation.valid, false);
  assert.ok(validation.errors.some((error) => error.includes('completedAt')));
});

test('eksik agent, boş evidence, geçersiz check ve secret value resultı reddedilir', async () => {
  const run = await readJson(examplePath('small-fix'));
  const item = run.items[0];
  const result = {
    schemaVersion: '1.0.0',
    runId: run.runId,
    itemId: item.id,
    outcome: 'pass',
    summary: 'Bearer super-secret result içine sızdı.',
    artifacts: [],
    acceptance: item.acceptanceCriteria.map((criterion) => ({ criterion, status: 'passed', evidence: '' })),
    checks: [{ name: 'bad-check', status: 'unknown', evidence: '' }],
    risks: [],
    followUps: [],
    completedAt: '2026-07-16T12:00:00.000Z',
  };
  const validation = validateResult(result, run, item);
  assert.equal(validation.valid, false);
  assert.ok(validation.errors.some((error) => error.includes('result.agent')));
  assert.ok(validation.errors.some((error) => error.includes('evidence')));
  assert.ok(validation.errors.some((error) => error.includes('check')));
  assert.ok(validation.errors.some((error) => error.includes('secret')));
});

test('cancelled quality gate high-risk runı complete yapamaz', async () => {
  const config = await loadConfig();
  const run = structuredClone(await readJson(examplePath('small-fix')));
  const target = run.items[0];
  target.risk.level = 'high';
  target.status = 'done';
  target.resultRef = 'results/fake.json';
  const review = structuredClone(target);
  review.id = 'cancelled-review';
  review.kind = 'review';
  review.risk.level = 'low';
  review.relations = { dependsOn: [target.id], reviews: [target.id], verifies: [], revises: [], integrates: [] };
  review.execution = { ...review.execution, readOnly: true, independent: true, writeScopes: [], owner: 'reviewer' };
  review.status = 'cancelled';
  review.resultRef = null;
  const verify = structuredClone(review);
  verify.id = 'cancelled-verify';
  verify.kind = 'verify';
  verify.relations = { dependsOn: [review.id], reviews: [], verifies: [target.id], revises: [], integrates: [] };
  run.items.push(review, verify);
  const validation = validateRun(run, config);
  assert.equal(validation.valid, false);
  assert.equal(statusReport(run, config).status, 'blocked');
});

test('resume örneğindeki resultRef dosyaları fiziksel olarak vardır', async () => {
  const runPath = examplePath('security-revision');
  const run = await readJson(runPath);
  for (const item of run.items.filter((candidate) => candidate.resultRef)) {
    await fs.access(path.join(path.dirname(runPath), item.resultRef));
  }
});

test('verify-system bütün örnek ve JSON artifactlerini doğrular', async () => {
  const report = await verifySystem();
  assert.equal(report.valid, true, report.errors.join(' | '));
  assert.equal(report.examples.length, 3);
});

test('delegated manager approval human boundary kapısını açar', async () => {
  const config = await loadConfig();
  const run = structuredClone(await readJson(examplePath('cross-layer-feature')));
  run.items.find((item) => item.id === 'scope-analysis').status = 'done';
  run.items.find((item) => item.id === 'define-api-contract').status = 'ready';
  run.decisions.push({
    id: 'manager-contract-approval', summary: 'Yönetici karar verdi.', reason: 'Devredilmiş proje yetkisi.',
    decidedAt: '2026-07-17T10:00:00.000Z', actor: 'manager',
    extensions: { type: 'approval', itemId: 'define-api-contract', boundary: 'schema-policy-change', outcome: 'approved', provenance: 'manager-delegated' },
  });
  assert.equal(validateRun(run, config).valid, true);
  assert.ok(computeParallelBatches(run, config).flat().some((item) => item.id === 'define-api-contract'));
});

test('high risk custom kind ile cross-layer iş quality gate atlayamaz', async () => {
  const config = await loadConfig();
  const run = structuredClone(await readJson(examplePath('small-fix')));
  run.items[0].kind = 'feature';
  run.items[0].risk.level = 'high';
  run.items[0].execution.writeScopes = ['INTO/modules/example', 'FIRST/example'];
  const validation = validateRun(run, config);
  assert.equal(validation.valid, false);
  assert.ok(validation.errors.some((error) => error.includes('review item')));
  assert.ok(validation.errors.some((error) => error.includes('verify item')));
  assert.ok(validation.errors.some((error) => error.includes('integration')));
});

test('artifact path item write scope dışındaysa result reddedilir', async () => {
  const run = await readJson(examplePath('small-fix'));
  const item = run.items[0];
  const result = {
    schemaVersion: '1.0.0', runId: run.runId, itemId: item.id,
    agent: { platform: 'manual', identity: 'test-agent', sessionRef: null }, outcome: 'pass', summary: 'Scope testi.',
    artifacts: [{ type: 'diff', path: 'FIRST/.env', change: 'modified', description: 'Geçersiz hedef.' }],
    acceptance: item.acceptanceCriteria.map((criterion) => ({ criterion, status: 'passed', evidence: 'Kanıt.' })),
    checks: [], risks: [], followUps: [], completedAt: '2026-07-17T10:00:00.000Z',
  };
  const validation = validateResult(result, run, item);
  assert.equal(validation.valid, false);
  assert.ok(validation.errors.some((error) => error.includes('writeScopes dışında')));
});
