import { execFileSync } from 'node:child_process';
import { createHash, randomUUID } from 'node:crypto';
import { promises as fs } from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

export const REPO_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..');

const RELATION_KEYS = ['dependsOn', 'reviews', 'verifies', 'revises', 'integrates'];
const ID_PATTERN = /^[a-z0-9][a-z0-9-]{1,62}$/;
const SKIPPED_DIRECTORY_NAMES = new Set([
  '.git',
  'node_modules',
  'build',
  'dist',
  'logs',
  'Pods',
  'ephemeral',
]);

function nowIso() {
  return new Date().toISOString();
}

function asArray(value) {
  return Array.isArray(value) ? value : [];
}

function cleanScalar(value) {
  if (typeof value !== 'string') return value;
  const trimmed = value.trim();
  if ((trimmed.startsWith('"') && trimmed.endsWith('"')) || (trimmed.startsWith("'") && trimmed.endsWith("'"))) {
    return trimmed.slice(1, -1);
  }
  if (trimmed === 'true') return true;
  if (trimmed === 'false') return false;
  return trimmed;
}

function normalizeRepoPath(value) {
  return path.posix.normalize(value.replaceAll('\\', '/').replace(/^\.\//, '')).replace(/\/$/, '');
}

function isPathWithin(root, candidate) {
  const relative = path.relative(path.resolve(root), path.resolve(candidate));
  return relative === '' || (!relative.startsWith('..') && !path.isAbsolute(relative));
}

function isControlledWritePath(relativePath, config) {
  return asArray(config?.repoGuardrails?.controlledWritePaths).map(normalizeRepoPath).includes(normalizeRepoPath(relativePath));
}

async function nearestExistingPath(targetPath) {
  let current = path.resolve(targetPath);
  while (true) {
    try {
      return await fs.realpath(current);
    } catch (error) {
      if (error.code !== 'ENOENT') throw error;
      const parent = path.dirname(current);
      if (parent === current) throw error;
      current = parent;
    }
  }
}

export async function assertSafeArtifactPath(targetPath, repoRoot = REPO_ROOT, config = null) {
  const resolvedTarget = path.resolve(targetPath);
  const effectiveConfig = config ?? await loadConfig(repoRoot);
  const allowedRoots = [repoRoot, os.tmpdir(), path.join(path.parse(repoRoot).root, 'tmp')];
  const existingTargetParent = await nearestExistingPath(path.dirname(resolvedTarget));
  const allowedRealRoots = [];
  for (const root of allowedRoots) {
    try {
      allowedRealRoots.push(await fs.realpath(root));
    } catch {
      // Mevcut olmayan opsiyonel temp root güven sınırı olamaz.
    }
  }
  if (!allowedRealRoots.some((root) => isPathWithin(root, existingTargetParent))) {
    throw new Error(`Artifact hedefi repo veya güvenli temp kökü dışında: ${resolvedTarget}`);
  }
  if (isPathWithin(repoRoot, resolvedTarget)) {
    const relative = normalizeRepoPath(path.relative(repoRoot, resolvedTarget));
    const protectedPrefixes = [
      ...asArray(effectiveConfig.repoGuardrails?.protectedPrefixes),
      ...asArray(effectiveConfig.repoGuardrails?.doNotTouch),
    ].map(normalizeRepoPath);
    if (!isControlledWritePath(relative, effectiveConfig) && protectedPrefixes.some((prefix) => relative === prefix || relative.startsWith(`${prefix}/`))) {
      throw new Error(`Artifact hedefi korumalı repo scope'unda: ${relative}`);
    }
  }
  return resolvedTarget;
}

function validateWriteScope(scope, config) {
  if (scope === '*') return null;
  if (typeof scope !== 'string' || scope.trim() === '') return 'boş veya string değil';
  const slashPath = scope.replaceAll('\\', '/');
  if (path.posix.isAbsolute(slashPath) || /^[A-Za-z]:\//.test(slashPath)) return 'absolute path kullanılamaz';
  const normalized = normalizeRepoPath(slashPath);
  if (normalized === '..' || normalized.startsWith('../')) return 'repo dışına çıkan path kullanılamaz';
  const protectedPrefixes = [
    ...asArray(config.repoGuardrails?.protectedPrefixes),
    ...asArray(config.repoGuardrails?.doNotTouch),
  ].map(normalizeRepoPath);
  if (!isControlledWritePath(normalized, config) && protectedPrefixes.some((prefix) => normalized === prefix || normalized.startsWith(`${prefix}/`))) return 'korumalı repo scope';
  return null;
}

function hashContent(value) {
  return createHash('sha256').update(value).digest('hex');
}

function itemNeedsQualityGates(item, config) {
  if (new Set(['analysis', 'review', 'verify', 'integration', 'comparison', 'specification']).has(item?.kind)) return false;
  const forcedKinds = new Set(asArray(config.riskPolicy?.forceQualityGateKinds));
  const gatedKinds = new Set(asArray(config.riskPolicy?.independentGateKinds));
  const highRisk = new Set([
    ...asArray(config.riskPolicy?.requireIndependentReviewAt),
    ...asArray(config.riskPolicy?.requireVerificationAt),
  ]).has(item?.risk?.level);
  return highRisk || forcedKinds.has(item?.kind) || gatedKinds.has(item?.kind);
}

function productLayer(scope) {
  const normalized = normalizeRepoPath(scope || '');
  for (const layer of ['FIRST', 'STEP', 'INTO', 'PATH']) {
    if (normalized === layer || normalized.startsWith(`${layer}/`)) return layer;
  }
  return null;
}

function isCrossLayerRun(run) {
  const layers = new Set();
  for (const item of asArray(run?.items)) {
    for (const scope of asArray(item?.execution?.writeScopes)) {
      const layer = productLayer(scope);
      if (layer) layers.add(layer);
    }
  }
  return layers.size > 1;
}

function artifactPathError(artifactPath, item) {
  if (artifactPath === null) return null;
  if (typeof artifactPath !== 'string' || artifactPath.trim() === '') return 'artifact path string veya null olmalı';
  const normalized = normalizeRepoPath(artifactPath);
  if (path.posix.isAbsolute(artifactPath) || normalized === '..' || normalized.startsWith('../')) return 'artifact path repo-relative olmalı';
  const scopes = asArray(item?.execution?.writeScopes).map(normalizeRepoPath);
  if (scopes.includes('*')) return null;
  if (!scopes.some((scope) => normalized === scope || normalized.startsWith(`${scope}/`))) return 'artifact path item writeScopes dışında';
  return null;
}

function runDirectory(runPath) {
  return path.dirname(path.resolve(runPath));
}

function eventsPath(runPath) {
  return path.join(runDirectory(runPath), 'events.jsonl');
}

function lockPath(runPath) {
  return `${path.resolve(runPath)}.lock`;
}

async function withRunLock(runPath, action) {
  const target = lockPath(runPath);
  for (let attempt = 0; attempt < 100; attempt += 1) {
    try {
      await fs.mkdir(target);
    } catch (error) {
      if (error.code !== 'EEXIST') throw error;
      await new Promise((resolve) => setTimeout(resolve, 20));
      continue;
    }
    try {
      return await action();
    } finally {
      await fs.rm(target, { recursive: true, force: true });
    }
  }
  throw new Error(`Run mutasyon kilidi zaman aşımına uğradı: ${runPath}`);
}

function assertExpectedRevision(run, expectedRevision) {
  if (expectedRevision === undefined || expectedRevision === null) return;
  if (Number(run.revision ?? 0) !== Number(expectedRevision)) {
    throw new Error(`Run revision çakışması: beklenen ${expectedRevision}, mevcut ${run.revision ?? 0}`);
  }
}

function advanceRevision(run) {
  run.revision = Number(run.revision ?? 0) + 1;
  run.updatedAt = nowIso();
}

function eventRecord(runId, itemId, type, actor, payload) {
  return {
    schemaVersion: '1.0.0',
    eventId: randomUUID(),
    timestamp: nowIso(),
    type,
    actor,
    runId,
    itemId,
    payload,
  };
}

export async function readJson(filePath) {
  return JSON.parse(await fs.readFile(filePath, 'utf8'));
}

export async function writeJsonAtomic(filePath, value) {
  await fs.mkdir(path.dirname(filePath), { recursive: true });
  const temporaryPath = `${filePath}.${process.pid}.${Date.now()}.tmp`;
  await fs.writeFile(temporaryPath, `${JSON.stringify(value, null, 2)}\n`, 'utf8');
  try {
    await fs.rename(temporaryPath, filePath);
  } catch (error) {
    if (!['EEXIST', 'EPERM'].includes(error.code)) throw error;
    await fs.copyFile(temporaryPath, filePath);
    await fs.unlink(temporaryPath);
  }
}

export async function writeTextAtomic(filePath, value) {
  await fs.mkdir(path.dirname(filePath), { recursive: true });
  const temporaryPath = `${filePath}.${process.pid}.${Date.now()}.tmp`;
  await fs.writeFile(temporaryPath, value, 'utf8');
  try {
    await fs.rename(temporaryPath, filePath);
  } catch (error) {
    if (!['EEXIST', 'EPERM'].includes(error.code)) throw error;
    await fs.copyFile(temporaryPath, filePath);
    await fs.unlink(temporaryPath);
  }
}

async function appendEvents(filePath, records) {
  await fs.mkdir(path.dirname(filePath), { recursive: true });
  const lines = records.map((record) => JSON.stringify(record)).join('\n');
  await fs.appendFile(filePath, `${lines}\n`, 'utf8');
}

export async function validateEventHistory(runPath, run) {
  const historyPath = eventsPath(runPath);
  let content;
  try {
    content = await fs.readFile(historyPath, 'utf8');
  } catch (error) {
    if (error.code === 'ENOENT') return { valid: true, errors: [], warnings: ['events.jsonl yok; snapshot başlangıç durumu olarak kabul edildi.'] };
    throw error;
  }
  const errors = [];
  const warnings = [];
  const records = [];
  const eventIds = new Set();
  const allowedTypes = new Set(['run-created', 'item-ready', 'status-transition', 'result-recorded', 'decision-recorded']);
  let previousTimestamp = Number.NEGATIVE_INFINITY;
  for (const [index, line] of content.split(/\r?\n/).filter(Boolean).entries()) {
    let record;
    try {
      record = JSON.parse(line);
    } catch (error) {
      errors.push(`events.jsonl satır ${index + 1} geçersiz JSON: ${error.message}`);
      continue;
    }
    records.push(record);
    if (record.schemaVersion !== '1.0.0') errors.push(`Event ${index + 1} schemaVersion geçersiz.`);
    validateString(record.eventId, `event[${index}].eventId`, errors);
    if (eventIds.has(record.eventId)) errors.push(`Tekrarlanan eventId: ${record.eventId}`);
    eventIds.add(record.eventId);
    if (!allowedTypes.has(record.type)) errors.push(`Event type geçersiz: ${record.type}`);
    if (record.runId !== run.runId) errors.push(`Event runId eşleşmiyor: ${record.eventId}`);
    if (record.itemId !== null && !asArray(run.items).some((item) => item.id === record.itemId)) errors.push(`Event itemId bilinmiyor: ${record.itemId}`);
    validateString(record.actor, `event[${index}].actor`, errors);
    const timestamp = Date.parse(record.timestamp);
    if (!Number.isFinite(timestamp)) errors.push(`Event timestamp geçersiz: ${record.eventId}`);
    else if (timestamp < previousTimestamp) errors.push(`Event timestamp sırası bozuk: ${record.eventId}`);
    else previousTimestamp = timestamp;
    if (!record.payload || typeof record.payload !== 'object' || Array.isArray(record.payload)) errors.push(`Event payload object olmalı: ${record.eventId}`);
  }

  for (const item of asArray(run.items).filter((candidate) => candidate.resultRef)) {
    const matching = records.some((record) =>
      record.type === 'result-recorded' && record.itemId === item.id && record.payload?.resultRef === item.resultRef,
    );
    if (!matching) errors.push(`${item.id}: resultRef için result-recorded event eksik.`);
  }
  for (const item of asArray(run.items).filter((candidate) => ['done', 'failed', 'cancelled'].includes(candidate.status))) {
    const transitions = records.filter((record) => record.type === 'status-transition' && record.itemId === item.id);
    if (transitions.length === 0) errors.push(`${item.id}: terminal status için transition event eksik.`);
    else if (transitions.at(-1).payload?.to !== item.status) errors.push(`${item.id}: son transition snapshot status ile eşleşmiyor.`);
  }
  return { valid: errors.length === 0, errors, warnings, records: records.length };
}

export async function loadConfig(repoRoot = REPO_ROOT) {
  return readJson(path.join(repoRoot, '.orchestrator', 'config.json'));
}

function validateString(value, label, errors) {
  if (typeof value !== 'string' || value.trim() === '') errors.push(`${label} boş olmayan string olmalı.`);
}

function findSensitiveKeys(value, fragments, currentPath = '$') {
  if (!value || typeof value !== 'object') return [];
  const findings = [];
  for (const [key, nested] of Object.entries(value)) {
    const nestedPath = `${currentPath}.${key}`;
    if (fragments.some((fragment) => key.toLowerCase().includes(fragment.toLowerCase()))) findings.push(nestedPath);
    findings.push(...findSensitiveKeys(nested, fragments, nestedPath));
  }
  return findings;
}

function findSensitiveStringValues(value, currentPath = '$') {
  const patterns = [
    /\bbearer\s+[A-Za-z0-9._~+/=-]{8,}/i,
    /\b(?:sk|rk|pk)-[A-Za-z0-9_-]{8,}\b/i,
    /-----BEGIN [A-Z ]*PRIVATE KEY-----/,
    /\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b/,
    /\b(?:password|secret|api[_-]?key|access[_-]?token|refresh[_-]?token)\s*[:=]\s*["']?[^\s,"']{4,}/i,
  ];
  if (typeof value === 'string') return patterns.some((pattern) => pattern.test(value)) ? [currentPath] : [];
  if (!value || typeof value !== 'object') return [];
  const findings = [];
  for (const [key, nested] of Object.entries(value)) findings.push(...findSensitiveStringValues(nested, `${currentPath}.${key}`));
  return findings;
}

function relationValues(item, relation) {
  return asArray(item?.relations?.[relation]);
}

function findDependencyCycle(items) {
  const graph = new Map(items.map((item) => [item.id, relationValues(item, 'dependsOn')]));
  const visiting = new Set();
  const visited = new Set();
  const stack = [];

  function visit(id) {
    if (visiting.has(id)) {
      const start = stack.indexOf(id);
      return [...stack.slice(start), id];
    }
    if (visited.has(id)) return null;
    visiting.add(id);
    stack.push(id);
    for (const dependency of graph.get(id) ?? []) {
      const cycle = visit(dependency);
      if (cycle) return cycle;
    }
    stack.pop();
    visiting.delete(id);
    visited.add(id);
    return null;
  }

  for (const id of graph.keys()) {
    const cycle = visit(id);
    if (cycle) return cycle;
  }
  return null;
}

function dependsTransitively(item, targetId, itemById, visited = new Set()) {
  if (!item || visited.has(item.id)) return false;
  visited.add(item.id);
  const dependencies = relationValues(item, 'dependsOn');
  if (dependencies.includes(targetId)) return true;
  return dependencies.some((dependencyId) => dependsTransitively(itemById.get(dependencyId), targetId, itemById, visited));
}

export function validateRun(run, config, catalog = null) {
  const errors = [];
  const warnings = [];
  const statuses = new Set(config.lifecycle.statuses);
  const riskLevels = new Set(config.riskPolicy.levels);
  const items = asArray(run?.items);

  if (run?.schemaVersion !== '1.0.0') errors.push('schemaVersion 1.0.0 olmalı.');
  validateString(run?.runId, 'runId', errors);
  if (typeof run?.runId === 'string' && !ID_PATTERN.test(run.runId)) errors.push('runId formatı geçersiz.');
  validateString(run?.title, 'title', errors);
  validateString(run?.goal, 'goal', errors);
  if (!run?.context || !Array.isArray(run.context.requiredPaths)) errors.push('context.requiredPaths array olmalı.');
  if (!Array.isArray(run?.constraints)) errors.push('constraints array olmalı.');
  if (!Array.isArray(run?.decisions)) errors.push('decisions array olmalı.');
  if (!Array.isArray(run?.items)) errors.push('items array olmalı.');
  if (items.length === 0) warnings.push('Run henüz work item içermiyor.');

  const ids = new Set();
  const itemById = new Map();
  for (const [index, item] of items.entries()) {
    const prefix = `items[${index}]`;
    validateString(item?.id, `${prefix}.id`, errors);
    if (typeof item?.id === 'string' && !ID_PATTERN.test(item.id)) errors.push(`${prefix}.id formatı geçersiz.`);
    if (ids.has(item?.id)) errors.push(`${prefix}.id tekrar ediyor: ${item.id}`);
    ids.add(item?.id);
    itemById.set(item?.id, item);
    validateString(item?.title, `${prefix}.title`, errors);
    validateString(item?.kind, `${prefix}.kind`, errors);
    if (typeof item?.kind === 'string' && !/^[a-z][a-z0-9-]*$/.test(item.kind)) errors.push(`${prefix}.kind formatı geçersiz.`);
    validateString(item?.objective, `${prefix}.objective`, errors);
    validateString(item?.responsibility, `${prefix}.responsibility`, errors);
    if (!Array.isArray(item?.domains) || item.domains.length === 0) errors.push(`${prefix}.domains en az bir değer içermeli.`);
    if (asArray(item?.domains).some((domain) => typeof domain !== 'string' || !/^[a-z][a-z0-9-]*$/.test(domain))) {
      errors.push(`${prefix}.domains yalnız küçük harf, rakam ve tire kullanmalı.`);
    }
    if (!Array.isArray(item?.inputs)) errors.push(`${prefix}.inputs array olmalı.`);
    if (!Array.isArray(item?.outputs) || item.outputs.length === 0) errors.push(`${prefix}.outputs en az bir değer içermeli.`);
    if (!Array.isArray(item?.acceptanceCriteria) || item.acceptanceCriteria.length === 0) errors.push(`${prefix}.acceptanceCriteria en az bir değer içermeli.`);
    if (!Array.isArray(item?.capabilities)) errors.push(`${prefix}.capabilities array olmalı.`);
    if (!statuses.has(item?.status)) errors.push(`${prefix}.status geçersiz: ${item?.status}`);
    if (!riskLevels.has(item?.risk?.level)) errors.push(`${prefix}.risk.level geçersiz: ${item?.risk?.level}`);
    if (!item?.execution || !['inline', 'delegate'].includes(item.execution.mode)) errors.push(`${prefix}.execution.mode geçersiz.`);
    if (!Array.isArray(item?.execution?.writeScopes)) errors.push(`${prefix}.execution.writeScopes array olmalı.`);
    for (const scope of asArray(item?.execution?.writeScopes)) {
      const scopeError = validateWriteScope(scope, config);
      if (scopeError) errors.push(`${prefix}.execution.writeScopes geçersiz (${scope}): ${scopeError}.`);
    }
    if (item?.execution?.readOnly === true && asArray(item.execution.writeScopes).length > 0) {
      errors.push(`${prefix} readOnly iken writeScopes boş olmalı.`);
    }
    if (!item?.relations) errors.push(`${prefix}.relations zorunlu.`);
    for (const relation of RELATION_KEYS) {
      if (!Array.isArray(item?.relations?.[relation])) errors.push(`${prefix}.relations.${relation} array olmalı.`);
    }
    const acceptance = asArray(item?.acceptanceCriteria);
    if (new Set(acceptance).size !== acceptance.length) warnings.push(`${item?.id}: acceptance criterion tekrarı var.`);
  }

  for (const item of items) {
    for (const relation of RELATION_KEYS) {
      for (const target of relationValues(item, relation)) {
        if (!ids.has(target)) errors.push(`${item.id}.relations.${relation} bilinmeyen item'a işaret ediyor: ${target}`);
        if (target === item.id) errors.push(`${item.id}.relations.${relation} kendisine işaret edemez.`);
        if (relation !== 'dependsOn' && ids.has(target) && !dependsTransitively(item, target, itemById)) {
          errors.push(`${item.id}.relations.${relation} hedefi dependsOn zincirinde değil: ${target}`);
        }
      }
    }
    const unresolved = relationValues(item, 'dependsOn').filter((id) => itemById.get(id)?.status !== 'done');
    if (item.status === 'ready' && unresolved.length > 0) {
      errors.push(`${item.id} ready fakat tamamlanmamış bağımlılıkları var: ${unresolved.join(', ')}`);
    }
    const pendingApprovals = pendingApprovalBoundaries(run, item, config);
    if (item.status === 'ready' && pendingApprovals.length > 0) {
      errors.push(`${item.id} ready fakat approval boundary bekliyor: ${pendingApprovals.join(', ')}`);
    }
    for (const revisedId of relationValues(item, 'revises')) {
      const revised = itemById.get(revisedId);
      if (revised && Number(item.attempt ?? 0) <= Number(revised.attempt ?? 0)) {
        errors.push(`${item.id} revision attempt değeri ${revisedId} değerinden büyük olmalı.`);
      }
    }
  }

  const cycle = findDependencyCycle(items);
  if (cycle) errors.push(`Dependency cycle bulundu: ${cycle.join(' -> ')}`);

  const reviewLevels = new Set(config.riskPolicy.requireIndependentReviewAt);
  const verifyLevels = new Set(config.riskPolicy.requireVerificationAt);
  for (const item of items) {
    if (!itemNeedsQualityGates(item, config)) continue;
    if (item.status === 'cancelled') continue;
    const forceGate = asArray(config.riskPolicy.forceQualityGateKinds).includes(item.kind);
    if (forceGate || reviewLevels.has(item.risk?.level)) {
      const reviewers = items.filter((candidate) =>
        relationValues(candidate, 'reviews').includes(item.id) &&
        candidate.execution?.independent === true &&
        !['failed', 'cancelled'].includes(candidate.status),
      );
      if (reviewers.length === 0) errors.push(`${item.id} için bağımsız review item'ı zorunlu.`);
      for (const reviewer of reviewers) {
        if (reviewer.execution?.owner && item.execution?.owner && reviewer.execution.owner === item.execution.owner) {
          errors.push(`${reviewer.id} bağımsız review için implementer owner'dan farklı olmalı.`);
        }
      }
    }
    if ((forceGate || verifyLevels.has(item.risk?.level)) && item.status !== 'failed') {
      const verifiers = items.filter((candidate) =>
        relationValues(candidate, 'verifies').includes(item.id) && candidate.execution?.independent === true && !['failed', 'cancelled'].includes(candidate.status),
      );
      if (verifiers.length === 0) errors.push(`${item.id} için verify item'ı zorunlu.`);
      for (const verifier of verifiers) {
        if (verifier.execution?.owner && item.execution?.owner && verifier.execution.owner === item.execution.owner) {
          errors.push(`${verifier.id} bağımsız verify için implementer owner'dan farklı olmalı.`);
        }
      }
    }
  }

  if (run?.policy?.requiresIntegration === true || isCrossLayerRun(run)) {
    const integrationItems = items.filter((item) =>
      item.kind === 'integration' && relationValues(item, 'integrates').length >= 2 && !['failed', 'cancelled'].includes(item.status),
    );
    if (integrationItems.length === 0) errors.push('Cross-layer policy için en az iki item bağlayan integration düğümü zorunlu.');
  }

  if (catalog) {
    const knownCapabilities = new Set(asArray(catalog.capabilities));
    for (const item of items) {
      const unknown = asArray(item.capabilities).filter((capability) => !knownCapabilities.has(capability));
      if (unknown.length > 0) warnings.push(`${item.id}: catalog'da bulunmayan capability: ${unknown.join(', ')}`);
    }
  }

  return { valid: errors.length === 0, errors, warnings };
}

export function validateResult(result, run, item, config = null) {
  const errors = [];
  if (result?.schemaVersion !== '1.0.0') errors.push('Result schemaVersion 1.0.0 olmalı.');
  if (result?.runId !== run.runId) errors.push(`Result runId eşleşmiyor: ${result?.runId}`);
  if (result?.itemId !== item.id) errors.push(`Result itemId eşleşmiyor: ${result?.itemId}`);
  if (!['pass', 'revise', 'blocked', 'fail'].includes(result?.outcome)) errors.push('Result outcome geçersiz.');
  validateString(result?.summary, 'result.summary', errors);
  if (!result?.agent || typeof result.agent !== 'object' || Array.isArray(result.agent)) errors.push('result.agent object olmalı.');
  if (!['codex', 'cursor', 'claude-code', 'manual'].includes(result?.agent?.platform)) errors.push('result.agent.platform geçersiz.');
  validateString(result?.agent?.identity, 'result.agent.identity', errors);
  if (result?.agent?.sessionRef !== null && typeof result?.agent?.sessionRef !== 'string') errors.push('result.agent.sessionRef string veya null olmalı.');
  if (!Array.isArray(result?.artifacts)) errors.push('result.artifacts array olmalı.');
  if (!Array.isArray(result?.acceptance)) errors.push('result.acceptance array olmalı.');
  if (!Array.isArray(result?.checks)) errors.push('result.checks array olmalı.');
  if (!Array.isArray(result?.risks)) errors.push('result.risks array olmalı.');
  if (!Array.isArray(result?.followUps)) errors.push('result.followUps array olmalı.');
  for (const [index, artifact] of asArray(result?.artifacts).entries()) {
    validateString(artifact?.type, `result.artifacts[${index}].type`, errors);
    if (typeof artifact?.type === 'string' && !/^[a-z][a-z0-9-]*$/.test(artifact.type)) errors.push(`result.artifacts[${index}].type formatı geçersiz.`);
    if (artifact?.path !== null && typeof artifact?.path !== 'string') errors.push(`result.artifacts[${index}].path string veya null olmalı.`);
    if (!['none', 'created', 'modified', 'deleted', 'reported'].includes(artifact?.change)) errors.push(`result.artifacts[${index}].change geçersiz.`);
    validateString(artifact?.description, `result.artifacts[${index}].description`, errors);
    const pathError = artifactPathError(artifact?.path, item);
    if (pathError) errors.push(`result.artifacts[${index}].path ${pathError}.`);
  }
  for (const [index, entry] of asArray(result?.acceptance).entries()) {
    validateString(entry?.criterion, `result.acceptance[${index}].criterion`, errors);
    if (!['passed', 'failed', 'not_verified'].includes(entry?.status)) errors.push(`result.acceptance[${index}].status geçersiz.`);
    validateString(entry?.evidence, `result.acceptance[${index}].evidence`, errors);
  }
  for (const [index, check] of asArray(result?.checks).entries()) {
    validateString(check?.name, `result.checks[${index}].name`, errors);
    if (!['passed', 'failed', 'not_run'].includes(check?.status)) errors.push(`result.checks[${index}].status geçersiz.`);
    validateString(check?.evidence, `result.checks[${index}].evidence`, errors);
  }
  if (asArray(result?.risks).some((risk) => typeof risk !== 'string')) errors.push('result.risks yalnız string içermeli.');
  if (asArray(result?.followUps).some((followUp) => typeof followUp !== 'string')) errors.push('result.followUps yalnız string içermeli.');
  if (typeof result?.completedAt !== 'string' || !Number.isFinite(Date.parse(result.completedAt))) {
    errors.push('result.completedAt geçerli ISO date-time olmalı.');
  }

  const expected = new Set(asArray(item.acceptanceCriteria));
  const reported = new Map(asArray(result?.acceptance).map((entry) => [entry.criterion, entry]));
  for (const criterion of expected) {
    if (!reported.has(criterion)) errors.push(`Acceptance sonucu eksik: ${criterion}`);
  }
  for (const criterion of reported.keys()) {
    if (!expected.has(criterion)) errors.push(`Bilinmeyen acceptance criterion raporlandı: ${criterion}`);
  }
  if (result?.outcome === 'pass') {
    const incomplete = [...reported.values()].filter((entry) => entry.status !== 'passed');
    if (incomplete.length > 0) errors.push('pass sonucu için tüm acceptance maddeleri passed olmalı.');
    if (asArray(result?.checks).some((check) => check.status === 'failed')) errors.push('pass sonucu failed check içeremez.');
  }
  const sensitiveKeys = findSensitiveKeys(
    result,
    config?.historyPolicy?.redactKeyFragments ?? ['authorization', 'cookie', 'password', 'secret', 'token', 'apiKey', 'privateKey'],
  );
  if (sensitiveKeys.length > 0) errors.push(`Result hassas anahtar içeremez: ${sensitiveKeys.join(', ')}`);
  const sensitiveValues = findSensitiveStringValues(result);
  if (sensitiveValues.length > 0) errors.push(`Result olası secret değeri içeremez: ${sensitiveValues.join(', ')}`);
  return { valid: errors.length === 0, errors, warnings: [] };
}

function dependencySatisfied(item, dependencyId, itemById) {
  const dependency = itemById.get(dependencyId);
  if (dependency?.status === 'done') return true;
  if (dependency?.status !== 'failed') return false;
  return relationValues(item, 'reviews').includes(dependencyId) || relationValues(item, 'revises').includes(dependencyId);
}

function dependenciesDone(item, itemById) {
  return relationValues(item, 'dependsOn').every((id) => dependencySatisfied(item, id, itemById));
}

function approvalDecision(run, itemId, boundary) {
  const decisions = asArray(run.decisions);
  for (let index = decisions.length - 1; index >= 0; index -= 1) {
    const decision = decisions[index];
    if (
      decision?.extensions?.type === 'approval' &&
      decision.extensions.itemId === itemId &&
      decision.extensions.boundary === boundary
    ) return decision;
  }
  return null;
}

function approvalIsValid(decision, boundary, config) {
  if (decision?.extensions?.outcome !== 'approved') return false;
  if (!asArray(config?.riskPolicy?.requireHumanDecisionFor).includes(boundary)) return true;
  if (config?.authorityPolicy?.managerMayApproveBoundaries === true &&
      String(decision.actor).toLowerCase() === 'manager' &&
      decision.extensions?.provenance === config.authorityPolicy.managerApprovalProvenance) return true;
  const reservedActors = new Set(['manager', 'agent', 'model', 'orchestrator']);
  return !reservedActors.has(String(decision.actor).toLowerCase()) &&
    ['user-confirmed', 'platform-approved'].includes(decision.extensions?.provenance);
}

export function pendingApprovalBoundaries(run, item, config = null) {
  return asArray(item?.risk?.approvalBoundaries).filter((boundary) => !approvalIsValid(approvalDecision(run, item.id, boundary), boundary, config));
}

export function qualityGateBlockers(run, config) {
  const items = asArray(run.items);
  const blockers = [];
  const reviewLevels = new Set(config.riskPolicy.requireIndependentReviewAt);
  const verifyLevels = new Set(config.riskPolicy.requireVerificationAt);
  for (const item of items.filter((candidate) => candidate.status === 'done' && itemNeedsQualityGates(candidate, config))) {
    const forceGate = asArray(config.riskPolicy.forceQualityGateKinds).includes(item.kind);
    if (forceGate || reviewLevels.has(item.risk?.level)) {
      const passedReview = items.some((candidate) =>
        candidate.status === 'done' && candidate.execution?.independent === true && relationValues(candidate, 'reviews').includes(item.id),
      );
      if (!passedReview) blockers.push({ itemId: item.id, gate: 'independent-review' });
    }
    if (forceGate || verifyLevels.has(item.risk?.level)) {
      const passedVerify = items.some((candidate) => candidate.status === 'done' && relationValues(candidate, 'verifies').includes(item.id));
      if (!passedVerify) blockers.push({ itemId: item.id, gate: 'verification' });
    }
  }
  if (run?.policy?.requiresIntegration === true || isCrossLayerRun(run)) {
    const integrationDone = items.some((item) => item.kind === 'integration' && item.status === 'done' && relationValues(item, 'integrates').length >= 2);
    const integratedTargetsDone = items.filter((item) => item.kind === 'integration').some((item) =>
      relationValues(item, 'integrates').length >= 2 && relationValues(item, 'integrates').every((id) => items.find((candidate) => candidate.id === id)?.status === 'done'),
    );
    if (integratedTargetsDone && !integrationDone) blockers.push({ itemId: null, gate: 'integration' });
  }
  return blockers;
}

export function deriveRunStatus(run, config) {
  const items = asArray(run.items);
  if (items.length === 0) return 'draft';
  const itemById = new Map(items.map((item) => [item.id, item]));
  const runnable = items.some((item) => item.status === 'ready' && dependenciesDone(item, itemById) && pendingApprovalBoundaries(run, item, config).length === 0);
  if (items.some((item) => item.status === 'active')) return 'active';
  if (runnable) return 'ready';
  const qualityBlockers = qualityGateBlockers(run, config);
  if (items.every((item) => ['done', 'cancelled'].includes(item.status))) return qualityBlockers.length === 0 ? 'complete' : 'blocked';
  if (qualityBlockers.length > 0) return 'blocked';
  if (items.some((item) => pendingApprovalBoundaries(run, item, config).length > 0 && ['draft', 'ready', 'blocked'].includes(item.status))) return 'blocked';
  if (items.some((item) => ['blocked', 'failed'].includes(item.status))) return 'blocked';
  return 'waiting';
}

function scopesConflict(left, right) {
  if (left.execution?.readOnly || right.execution?.readOnly) return false;
  const leftScopes = asArray(left.execution?.writeScopes).map(normalizeRepoPath).map((scope) => scope.toLowerCase()).filter(Boolean);
  const rightScopes = asArray(right.execution?.writeScopes).map(normalizeRepoPath).map((scope) => scope.toLowerCase()).filter(Boolean);
  if (leftScopes.length === 0 || rightScopes.length === 0) return true;
  if (leftScopes.includes('*') || rightScopes.includes('*')) return true;
  return leftScopes.some((leftScope) =>
    rightScopes.some((rightScope) =>
      leftScope === rightScope || leftScope.startsWith(`${rightScope}/`) || rightScope.startsWith(`${leftScope}/`),
    ),
  );
}

export function computeParallelBatches(run, config) {
  const items = asArray(run.items);
  const itemById = new Map(items.map((item) => [item.id, item]));
  const runnable = items.filter((item) =>
    item.status === 'ready' && dependenciesDone(item, itemById) && pendingApprovalBoundaries(run, item, config).length === 0,
  );
  const batches = [];
  const maxWriters = config.parallelPolicy.defaultMaxWriters;

  for (const item of runnable) {
    let placed = false;
    for (const batch of batches) {
      const writers = batch.filter((candidate) => !candidate.execution?.readOnly).length;
      const writerLimitReached = !item.execution?.readOnly && writers >= maxWriters;
      const conflict = batch.some((candidate) => scopesConflict(candidate, item));
      if (!writerLimitReached && !conflict) {
        batch.push(item);
        placed = true;
        break;
      }
    }
    if (!placed) batches.push([item]);
  }
  return batches;
}

export function statusReport(run, config) {
  const batches = computeParallelBatches(run, config);
  return {
    runId: run.runId,
    revision: Number(run.revision ?? 0),
    status: deriveRunStatus(run, config),
    counts: Object.fromEntries(config.lifecycle.statuses.map((status) => [status, asArray(run.items).filter((item) => item.status === status).length])),
    readyBatches: batches.map((batch, index) => ({
      batch: index + 1,
      items: batch.map((item) => ({
        id: item.id,
        kind: item.kind,
        mode: item.execution.mode,
        readOnly: item.execution.readOnly,
        writeScopes: item.execution.writeScopes,
      })),
    })),
    blockers: asArray(run.items)
      .filter((item) => ['blocked', 'failed'].includes(item.status))
      .map((item) => ({ id: item.id, status: item.status, resultRef: item.resultRef })),
    approvalBlockers: asArray(run.items)
      .map((item) => ({ id: item.id, boundaries: pendingApprovalBoundaries(run, item, config) }))
      .filter((item) => item.boundaries.length > 0),
    qualityGateBlockers: qualityGateBlockers(run, config),
  };
}

export async function createRun({ id, title, goal, outputDirectory, repoRoot = REPO_ROOT, actor = 'manager' }) {
  if (!ID_PATTERN.test(id)) throw new Error('Run id küçük harf, rakam ve tire içermeli (2-63 karakter).');
  const config = await loadConfig(repoRoot);
  const directory = outputDirectory ? path.resolve(repoRoot, outputDirectory) : path.join(repoRoot, config.paths.runs, id);
  const runPath = path.join(directory, 'run.json');
  await assertSafeArtifactPath(runPath, repoRoot, config);
  try {
    await fs.access(runPath);
    throw new Error(`Run zaten var: ${runPath}`);
  } catch (error) {
    if (error.code !== 'ENOENT') throw error;
  }
  const timestamp = nowIso();
  let catalogSnapshot = null;
  try {
    const catalog = await readJson(path.join(repoRoot, config.paths.catalog));
    catalogSnapshot = catalog.snapshot ?? null;
  } catch {
    catalogSnapshot = null;
  }
  const run = {
    schemaVersion: '1.0.0',
    runId: id,
    title,
    goal,
    createdAt: timestamp,
    updatedAt: timestamp,
    revision: 0,
    context: {
      requiredPaths: config.paths.requiredContext,
      optionalPaths: [],
      catalogSnapshot,
      assumptions: [],
    },
    constraints: [
      'Kullanıcı aksini söylemediyse accepted entegrasyon mantıksal commitlerle main branch\'e push edilir; alt writerlar bağımsız push yapmaz ve force-push yasaktır.',
      'Backend servisleri ve lokal Docker agent makinesinde başlatılmaz.',
    ],
    policy: { requiresIntegration: false },
    decisions: [],
    items: [],
  };
  await writeJsonAtomic(runPath, run);
  await appendEvents(eventsPath(runPath), [eventRecord(id, null, 'run-created', actor, { title, goal })]);
  await fs.mkdir(path.join(directory, 'results'), { recursive: true });
  return { runPath, run };
}

function assertTransitionAllowed(item, toStatus, config, itemById, allowDoneWithoutResult) {
  const allowed = config.lifecycle.transitions[item.status] ?? [];
  if (!allowed.includes(toStatus)) throw new Error(`Geçersiz transition: ${item.status} -> ${toStatus}`);
  if (['ready', 'active'].includes(toStatus) && !dependenciesDone(item, itemById)) {
    throw new Error(`${item.id} bağımlılıkları tamamlanmadan ${toStatus} olamaz.`);
  }
  if (toStatus === 'done' && !allowDoneWithoutResult && !item.resultRef) {
    throw new Error('done transition için result contract kaydı zorunlu; record komutunu kullanın.');
  }
}

async function transitionItemUnsafe(runPath, itemId, toStatus, reason, actor = 'manager', options = {}) {
  const config = await loadConfig(options.repoRoot ?? REPO_ROOT);
  await assertSafeArtifactPath(runPath, options.repoRoot ?? REPO_ROOT, config);
  const run = await readJson(runPath);
  assertExpectedRevision(run, options.expectedRevision);
  const itemById = new Map(asArray(run.items).map((item) => [item.id, item]));
  const item = itemById.get(itemId);
  if (!item) throw new Error(`Work item bulunamadı: ${itemId}`);
  if (['ready', 'active'].includes(toStatus) && pendingApprovalBoundaries(run, item, config).length > 0) {
    throw new Error(`${item.id} approval boundary bekliyor: ${pendingApprovalBoundaries(run, item, config).join(', ')}`);
  }
  assertTransitionAllowed(item, toStatus, config, itemById, options.allowDoneWithoutResult === true);
  const fromStatus = item.status;
  item.status = toStatus;
  if (toStatus === 'active') item.attempt = Math.max(1, Number(item.attempt ?? 0));
  advanceRevision(run);
  await writeJsonAtomic(runPath, run);
  await appendEvents(eventsPath(runPath), [
    eventRecord(run.runId, itemId, 'status-transition', actor, { from: fromStatus, to: toStatus, reason }),
  ]);
  return { run, item };
}

export async function transitionItem(runPath, itemId, toStatus, reason, actor = 'manager', options = {}) {
  return withRunLock(runPath, () => transitionItemUnsafe(runPath, itemId, toStatus, reason, actor, options));
}

async function syncReadyUnsafe(runPath, actor = 'manager', repoRoot = REPO_ROOT, options = {}) {
  const config = await loadConfig(repoRoot);
  await assertSafeArtifactPath(runPath, repoRoot, config);
  const run = await readJson(runPath);
  assertExpectedRevision(run, options.expectedRevision);
  const itemById = new Map(asArray(run.items).map((item) => [item.id, item]));
  const records = [];
  const changed = [];
  for (const item of asArray(run.items)) {
    if (item.status !== 'draft' || !dependenciesDone(item, itemById) || pendingApprovalBoundaries(run, item, config).length > 0) continue;
    item.status = 'ready';
    changed.push(item.id);
    records.push(eventRecord(run.runId, item.id, 'item-ready', actor, { reason: 'Tüm dependsOn düğümleri done.' }));
  }
  if (changed.length > 0) {
    advanceRevision(run);
    await writeJsonAtomic(runPath, run);
    await appendEvents(eventsPath(runPath), records);
  }
  return { changed, status: statusReport(run, config) };
}

export async function syncReady(runPath, actor = 'manager', repoRoot = REPO_ROOT, options = {}) {
  return withRunLock(runPath, () => syncReadyUnsafe(runPath, actor, repoRoot, options));
}

function safeTimestampForFile(value) {
  return new Date(value).toISOString().replaceAll(':', '-').replaceAll('.', '-');
}

function agentIdentityKey(agent) {
  if (!agent) return null;
  return `${agent.platform}:${agent.sessionRef || agent.identity}`;
}

async function recordResultUnsafe(runPath, resultPath, actor = 'manager', repoRoot = REPO_ROOT, options = {}) {
  const config = await loadConfig(repoRoot);
  await assertSafeArtifactPath(runPath, repoRoot, config);
  const run = await readJson(runPath);
  assertExpectedRevision(run, options.expectedRevision);
  const result = await readJson(resultPath);
  const runValidation = validateRun(run, config);
  if (!runValidation.valid) throw new Error(`Run geçersiz:\n- ${runValidation.errors.join('\n- ')}`);
  const item = asArray(run.items).find((candidate) => candidate.id === result.itemId);
  if (!item) throw new Error(`Result bilinmeyen item'a ait: ${result.itemId}`);
  if (item.status !== 'active') throw new Error(`Result kaydı için item active olmalı; mevcut: ${item.status}`);
  const validation = validateResult(result, run, item, config);
  if (!validation.valid) throw new Error(`Result geçersiz:\n- ${validation.errors.join('\n- ')}`);
  if (item.execution?.independent === true) {
    const targets = [...new Set([...relationValues(item, 'reviews'), ...relationValues(item, 'verifies')])];
    for (const targetId of targets) {
      const target = asArray(run.items).find((candidate) => candidate.id === targetId);
      if (!target?.resultRef) throw new Error(`Bağımsız gate için hedef resultRef eksik: ${targetId}`);
      const targetResultPath = path.resolve(runDirectory(runPath), target.resultRef);
      if (!isPathWithin(runDirectory(runPath), targetResultPath)) throw new Error(`Hedef resultRef run dizini dışında: ${targetId}`);
      const targetResult = await readJson(targetResultPath);
      if (agentIdentityKey(targetResult.agent) === agentIdentityKey(result.agent)) {
        throw new Error(`Bağımsız gate aynı agent/session tarafından tamamlanamaz: ${targetId}`);
      }
    }
  }

  const storedName = `${item.id}-${safeTimestampForFile(result.completedAt)}.json`;
  const storedPath = path.join(runDirectory(runPath), 'results', storedName);
  await assertSafeArtifactPath(storedPath, repoRoot, config);
  await writeJsonAtomic(storedPath, result);
  const relativeStoredPath = normalizeRepoPath(path.relative(runDirectory(runPath), storedPath));
  item.resultRef = relativeStoredPath;

  const outcomeToStatus = { pass: 'done', revise: 'failed', blocked: 'blocked', fail: 'failed' };
  const targetStatus = outcomeToStatus[result.outcome];
  const itemById = new Map(asArray(run.items).map((candidate) => [candidate.id, candidate]));
  assertTransitionAllowed(item, targetStatus, config, itemById, true);
  const fromStatus = item.status;
  item.status = targetStatus;
  advanceRevision(run);
  await writeJsonAtomic(runPath, run);
  await appendEvents(eventsPath(runPath), [
    eventRecord(run.runId, item.id, 'result-recorded', actor, { outcome: result.outcome, resultRef: relativeStoredPath }),
    eventRecord(run.runId, item.id, 'status-transition', actor, {
      from: fromStatus,
      to: targetStatus,
      reason: `Result outcome: ${result.outcome}`,
    }),
  ]);
  return { itemId: item.id, status: targetStatus, resultRef: relativeStoredPath };
}

export async function recordResult(runPath, resultPath, actor = 'manager', repoRoot = REPO_ROOT, options = {}) {
  return withRunLock(runPath, () => recordResultUnsafe(runPath, resultPath, actor, repoRoot, options));
}

async function recordDecisionUnsafe(runPath, decision, actor = 'manager', repoRoot = REPO_ROOT, options = {}) {
  const config = await loadConfig(repoRoot);
  await assertSafeArtifactPath(runPath, repoRoot, config);
  const run = await readJson(runPath);
  assertExpectedRevision(run, options.expectedRevision);
  if (!ID_PATTERN.test(decision.id)) throw new Error('Decision id formatı geçersiz.');
  if (asArray(run.decisions).some((current) => current.id === decision.id)) throw new Error(`Decision id zaten var: ${decision.id}`);
  if (typeof decision.summary !== 'string' || decision.summary.trim() === '') throw new Error('Decision summary zorunlu.');
  if (typeof decision.reason !== 'string' || decision.reason.trim() === '') throw new Error('Decision reason zorunlu.');
  if (typeof actor !== 'string' || actor.trim() === '') throw new Error('Decision actor zorunlu.');
  if (decision.extensions?.type === 'approval') {
    const item = asArray(run.items).find((candidate) => candidate.id === decision.extensions.itemId);
    if (!item) throw new Error(`Approval decision bilinmeyen item'a ait: ${decision.extensions.itemId}`);
    if (!asArray(item.risk?.approvalBoundaries).includes(decision.extensions.boundary)) {
      throw new Error(`Approval boundary item'da tanımlı değil: ${decision.extensions.boundary}`);
    }
    if (!['approved', 'denied'].includes(decision.extensions.outcome)) throw new Error('Approval outcome approved veya denied olmalı.');
    if (asArray(config.riskPolicy.requireHumanDecisionFor).includes(decision.extensions.boundary)) {
      const managerDelegation = config.authorityPolicy?.managerMayApproveBoundaries === true &&
        actor.toLowerCase() === 'manager' &&
        decision.extensions.provenance === config.authorityPolicy.managerApprovalProvenance;
      if (!managerDelegation && ['manager', 'agent', 'model', 'orchestrator'].includes(actor.toLowerCase())) {
        throw new Error('Human approval boundary manager/model tarafından onaylanamaz; gerçek actor zorunlu.');
      }
      if (!['user-confirmed', 'platform-approved', config.authorityPolicy?.managerApprovalProvenance].includes(decision.extensions.provenance)) {
        throw new Error('Human approval boundary için provenance user-confirmed, platform-approved veya manager-delegated olmalı.');
      }
    }
  }
  const normalized = {
    id: decision.id,
    summary: decision.summary,
    reason: decision.reason,
    decidedAt: nowIso(),
    actor,
    ...(decision.extensions ? { extensions: decision.extensions } : {}),
  };
  run.decisions.push(normalized);
  advanceRevision(run);
  await writeJsonAtomic(runPath, run);
  await appendEvents(eventsPath(runPath), [
    eventRecord(run.runId, decision.extensions?.itemId ?? null, 'decision-recorded', actor, {
      decisionId: decision.id,
      summary: decision.summary,
      extensions: decision.extensions ?? null,
    }),
  ]);
  return normalized;
}

export async function recordDecision(runPath, decision, actor = 'manager', repoRoot = REPO_ROOT, options = {}) {
  return withRunLock(runPath, () => recordDecisionUnsafe(runPath, decision, actor, repoRoot, options));
}

function parseFrontmatter(markdown) {
  const match = markdown.match(/^---\s*\r?\n([\s\S]*?)\r?\n---/);
  if (!match) return {};
  const lines = match[1].split(/\r?\n/);
  const output = {};
  for (let index = 0; index < lines.length; index += 1) {
    const keyMatch = lines[index].match(/^([A-Za-z0-9_-]+):\s*(.*)$/);
    if (!keyMatch) continue;
    const [, key, rawValue] = keyMatch;
    if (['>-', '>', '|', '|-'].includes(rawValue.trim())) {
      const folded = [];
      while (index + 1 < lines.length && /^\s+/.test(lines[index + 1])) {
        index += 1;
        folded.push(lines[index].trim());
      }
      output[key] = folded.join(' ');
    } else {
      output[key] = cleanScalar(rawValue);
    }
  }
  return output;
}

async function pathExists(targetPath) {
  try {
    await fs.access(targetPath);
    return true;
  } catch {
    return false;
  }
}

async function walkFiles(root, predicate = () => true) {
  if (!(await pathExists(root))) return [];
  const output = [];
  const entries = await fs.readdir(root, { withFileTypes: true });
  for (const entry of entries) {
    if (SKIPPED_DIRECTORY_NAMES.has(entry.name)) continue;
    const fullPath = path.join(root, entry.name);
    if (entry.isDirectory()) output.push(...await walkFiles(fullPath, predicate));
    else if (entry.isFile() && predicate(fullPath)) output.push(fullPath);
  }
  return output;
}

async function newestFile(paths) {
  let newest = null;
  for (const root of paths) {
    for (const filePath of await walkFiles(root)) {
      const stat = await fs.stat(filePath);
      if (!newest || stat.mtimeMs > newest.mtimeMs) newest = { filePath, mtimeMs: stat.mtimeMs };
    }
  }
  return newest;
}

async function deterministicTreeFingerprint(roots, repoRoot = REPO_ROOT) {
  const entries = [];
  for (const root of roots) {
    for (const filePath of await walkFiles(root)) {
      const relative = normalizeRepoPath(path.relative(repoRoot, filePath));
      entries.push(`${relative}:${hashContent(await fs.readFile(filePath))}`);
    }
  }
  return hashContent(entries.sort().join('\n'));
}

function gitCommit(repoRoot) {
  try {
    return execFileSync('git', ['rev-parse', 'HEAD'], { cwd: repoRoot, encoding: 'utf8' }).trim();
  } catch {
    return null;
  }
}

export async function discoverRepository(repoRoot = REPO_ROOT, outputPath = null) {
  const config = await loadConfig(repoRoot);
  const skills = [];
  for (const root of config.paths.skillRoots) {
    const absoluteRoot = path.join(repoRoot, root);
    for (const skillPath of await walkFiles(absoluteRoot, (candidate) => path.basename(candidate) === 'SKILL.md')) {
      const content = await fs.readFile(skillPath, 'utf8');
      const frontmatter = parseFrontmatter(content);
      skills.push({
        name: frontmatter.name || path.basename(path.dirname(skillPath)),
        description: frontmatter.description || '',
        path: normalizeRepoPath(path.relative(repoRoot, skillPath)),
        root,
        disableModelInvocation: frontmatter['disable-model-invocation'] === true,
        fingerprint: hashContent(content),
      });
    }
  }
  skills.sort((left, right) => left.path.localeCompare(right.path));

  const mapDirectory = path.join(repoRoot, '.cursor', 'maps', 'stack-shared-ai');
  const mapFiles = await walkFiles(mapDirectory, (candidate) => candidate.endsWith('.md'));
  const maps = [];
  for (const mapPath of mapFiles) {
    const content = await fs.readFile(mapPath, 'utf8');
    maps.push({ path: normalizeRepoPath(path.relative(repoRoot, mapPath)), fingerprint: hashContent(content) });
  }
  maps.sort((left, right) => left.path.localeCompare(right.path));

  let stacklit = null;
  const stacklitPath = path.join(repoRoot, '.cursor', 'maps', 'stacklit.json');
  if (await pathExists(stacklitPath)) {
    const value = await readJson(stacklitPath);
    stacklit = {
      path: normalizeRepoPath(path.relative(repoRoot, stacklitPath)),
      generatedAt: value.generated_at ?? null,
      primaryLanguage: value.tech?.primary_language ?? null,
      moduleCount: value.modules && typeof value.modules === 'object' ? Object.keys(value.modules).length : 0,
      fingerprint: hashContent(await fs.readFile(stacklitPath, 'utf8')),
    };
  }

  const sourceRoots = config.paths.sourceRoots.map((root) => path.join(repoRoot, root));
  const sourceFingerprint = await deterministicTreeFingerprint(sourceRoots, repoRoot);
  let mapManifest = null;
  try { mapManifest = await readJson(path.join(repoRoot, '.orchestrator', 'catalog', 'map-manifest.json')); } catch { mapManifest = null; }
  const adapters = [];
  for (const adapterPath of await walkFiles(path.join(repoRoot, config.paths.adapters), (candidate) => candidate.endsWith('.json'))) {
    const value = await readJson(adapterPath);
    adapters.push({ id: value.id, path: normalizeRepoPath(path.relative(repoRoot, adapterPath)), capabilities: value.nativeCapabilities });
  }
  adapters.sort((left, right) => left.id.localeCompare(right.id));

  const layers = {};
  for (const layer of ['FIRST', 'STEP', 'INTO', 'PATH']) layers[layer] = await pathExists(path.join(repoRoot, layer));
  const catalog = {
    schemaVersion: '1.0.0',
    generatedAt: nowIso(),
    repository: { root: '.', name: path.basename(repoRoot), commit: gitCommit(repoRoot), layers },
    skills,
    capabilities: [...new Set(skills.map((skill) => skill.name))].sort(),
    maps: { semantic: maps, dependency: stacklit },
    mapHealth: {
      stale: mapManifest?.sourceFingerprint !== sourceFingerprint,
      sourceFingerprint,
      mapSourceFingerprint: mapManifest?.sourceFingerprint ?? null,
      dependencyMapGeneratedAt: stacklit?.generatedAt ?? null,
      note: 'Tazelik, checkout mtime yerine deterministik kaynak ağacı fingerprint’i ile ölçülür.',
    },
    adapters,
  };
  const stableCatalog = structuredClone(catalog);
  delete stableCatalog.generatedAt;
  catalog.snapshot = hashContent(JSON.stringify(stableCatalog));
  const destination = outputPath ? path.resolve(repoRoot, outputPath) : path.join(repoRoot, config.paths.catalog);
  await assertSafeArtifactPath(destination, repoRoot, config);
  await writeJsonAtomic(destination, catalog);
  return { destination, catalog };
}

export async function writeMapManifest(repoRoot = REPO_ROOT) {
  const config = await loadConfig(repoRoot);
  const sourceFingerprint = await deterministicTreeFingerprint(config.paths.sourceRoots.map((root) => path.join(repoRoot, root)), repoRoot);
  const manifest = { schemaVersion: '1.0.0', sourceFingerprint, generatedAt: nowIso(), generator: 'manual-product-context' };
  const destination = path.join(repoRoot, '.orchestrator', 'catalog', 'map-manifest.json');
  await writeJsonAtomic(destination, manifest);
  return { destination, manifest };
}

function bulletList(values, empty = '- Yok') {
  return values.length > 0 ? values.map((value) => `- ${value}`).join('\n') : empty;
}

export async function renderPrompt(run, itemId, platform, repoRoot = REPO_ROOT) {
  const item = asArray(run.items).find((candidate) => candidate.id === itemId);
  if (!item) throw new Error(`Work item bulunamadı: ${itemId}`);
  const adapter = await readJson(path.join(repoRoot, '.orchestrator', 'adapters', `${platform}.json`));
  const resultAcceptance = asArray(item.acceptanceCriteria).map((criterion) => ({ criterion, status: 'not_verified', evidence: '' }));
  const inputLines = asArray(item.inputs).map((input) => `${input.type}: ${input.value}${input.description ? ` — ${input.description}` : ''}`);

  return `# Orchestrator Handoff\n\n` +
    `Run: ${run.runId} — ${run.title}\n` +
    `Item: ${item.id} — ${item.title}\n` +
    `Platform: ${adapter.displayName}\n\n` +
    `## Amaç\n\n${item.objective}\n\n` +
    `## Sorumluluk sınırı\n\n${item.responsibility}\n\n` +
    `## Tür ve domainler\n\n- Kind: ${item.kind}\n- Domains: ${asArray(item.domains).join(', ')}\n- Risk: ${item.risk.level}\n- Mode: ${item.execution.mode}\n- Isolation: ${item.execution.isolation}\n\n` +
    `## Girdiler\n\n${bulletList(inputLines)}\n\n` +
    `## Zorunlu bağlam\n\n${bulletList(asArray(run.context.requiredPaths))}\n\n` +
    `## Beklenen çıktılar\n\n${bulletList(asArray(item.outputs))}\n\n` +
    `## Kabul kriterleri\n\n${bulletList(asArray(item.acceptanceCriteria))}\n\n` +
    `## İlişkiler\n\n- Depends on: ${relationValues(item, 'dependsOn').join(', ') || 'Yok'}\n` +
    `- Reviews: ${relationValues(item, 'reviews').join(', ') || 'Yok'}\n` +
    `- Verifies: ${relationValues(item, 'verifies').join(', ') || 'Yok'}\n` +
    `- Revises: ${relationValues(item, 'revises').join(', ') || 'Yok'}\n` +
    `- Integrates: ${relationValues(item, 'integrates').join(', ') || 'Yok'}\n\n` +
    `## Kapsam ve kurallar\n\n- Read-only: ${item.execution.readOnly}\n` +
    `- Write scopes: ${asArray(item.execution.writeScopes).join(', ') || 'Yok'}\n` +
    `- Gerekli capabilities: ${asArray(item.capabilities).join(', ') || 'Yok'}\n` +
    `${bulletList(asArray(run.constraints))}\n- Path'leri map'ten aldıktan sonra gerçek dosyadan doğrula.\n` +
    `- Kapsam dışı refactor yapma. Bu work item içinde commit/push yapma; accepted final entegrasyonun Git teslimini üst agent yönetir.\n- Kritik belirsizlikte dur ve blocker olarak raporla.\n\n` +
    `## ${adapter.displayName} dispatch notları\n\n${bulletList(adapter.dispatchGuidance)}\n\n` +
    `## Teslim sözleşmesi\n\nSonucu \`.orchestrator/contracts/result.schema.json\` biçiminde döndür. Başlangıç acceptance gövdesi:\n\n` +
    `\`\`\`json\n${JSON.stringify(resultAcceptance, null, 2)}\n\`\`\`\n\n` +
    `Ayrıca repo tesliminde \`.agent/skills/meta/code-implementation-mode/SKILL.md\` içindeki beş başlığı koru.\n`;
}

export async function verifySystem(repoRoot = REPO_ROOT) {
  const report = { valid: true, checkedJson: [], examples: [], errors: [] };
  const jsonRoots = [
    path.join(repoRoot, '.orchestrator', 'config.json'),
    ...await walkFiles(path.join(repoRoot, '.orchestrator', 'contracts'), (candidate) => candidate.endsWith('.json')),
    ...await walkFiles(path.join(repoRoot, '.orchestrator', 'adapters'), (candidate) => candidate.endsWith('.json')),
    ...await walkFiles(path.join(repoRoot, '.orchestrator', 'templates'), (candidate) => candidate.endsWith('.json')),
    ...await walkFiles(path.join(repoRoot, '.orchestrator', 'catalog'), (candidate) => candidate.endsWith('.json')),
  ];
  for (const filePath of jsonRoots) {
    try {
      await readJson(filePath);
      report.checkedJson.push(normalizeRepoPath(path.relative(repoRoot, filePath)));
    } catch (error) {
      report.errors.push(`${normalizeRepoPath(path.relative(repoRoot, filePath))}: ${error.message}`);
    }
  }
  const config = await loadConfig(repoRoot);
  const examplePaths = await walkFiles(path.join(repoRoot, '.orchestrator', 'examples'), (candidate) => path.basename(candidate) === 'run.json');
  for (const examplePath of examplePaths) {
    try {
      const run = await readJson(examplePath);
      const validation = validateRun(run, config);
      if (!validation.valid) report.errors.push(`${normalizeRepoPath(path.relative(repoRoot, examplePath))}: ${validation.errors.join(' | ')}`);
      const historyValidation = await validateEventHistory(examplePath, run);
      if (!historyValidation.valid) report.errors.push(`${normalizeRepoPath(path.relative(repoRoot, examplePath))}: ${historyValidation.errors.join(' | ')}`);
      for (const item of asArray(run.items).filter((candidate) => candidate.resultRef)) {
        const resultPath = path.resolve(path.dirname(examplePath), item.resultRef);
        const expectedRoot = path.resolve(path.dirname(examplePath));
        if (!resultPath.startsWith(expectedRoot + path.sep)) {
          report.errors.push(`${item.id}: resultRef örnek dizini dışına çıkıyor.`);
          continue;
        }
        try {
          const result = await readJson(resultPath);
          const resultValidation = validateResult(result, run, item, config);
          if (!resultValidation.valid) report.errors.push(`${item.id}: ${resultValidation.errors.join(' | ')}`);
          const expectedStatus = { pass: 'done', revise: 'failed', blocked: 'blocked', fail: 'failed' }[result.outcome];
          if (item.status !== expectedStatus) report.errors.push(`${item.id}: result outcome ${result.outcome} ile status ${item.status} uyumsuz.`);
          if (item.execution?.independent === true) {
            for (const targetId of [...relationValues(item, 'reviews'), ...relationValues(item, 'verifies')]) {
              const target = asArray(run.items).find((candidate) => candidate.id === targetId);
              if (!target?.resultRef) {
                report.errors.push(`${item.id}: bağımsız gate hedef resultRef eksik: ${targetId}`);
                continue;
              }
              const targetResult = await readJson(path.resolve(path.dirname(examplePath), target.resultRef));
              if (agentIdentityKey(targetResult.agent) === agentIdentityKey(result.agent)) {
                report.errors.push(`${item.id}: bağımsız gate hedefle aynı agent/session kullanıyor: ${targetId}`);
              }
            }
          }
        } catch (error) {
          report.errors.push(`${item.id}: resultRef okunamadı: ${error.message}`);
        }
      }
      const firstItem = asArray(run.items)[0];
      if (firstItem) {
        for (const platform of ['codex', 'cursor', 'claude-code']) await renderPrompt(run, firstItem.id, platform, repoRoot);
      }
      report.examples.push({ path: normalizeRepoPath(path.relative(repoRoot, examplePath)), ...validation, history: historyValidation });
    } catch (error) {
      report.errors.push(`${normalizeRepoPath(path.relative(repoRoot, examplePath))}: ${error.message}`);
    }
  }
  report.valid = report.errors.length === 0;
  return report;
}
