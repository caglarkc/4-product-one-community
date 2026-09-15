#!/usr/bin/env node

import path from 'node:path';
import {
  REPO_ROOT,
  assertSafeArtifactPath,
  createRun,
  discoverRepository,
  loadConfig,
  readJson,
  recordDecision,
  recordResult,
  renderPrompt,
  statusReport,
  syncReady,
  transitionItem,
  validateEventHistory,
  validateRun,
  verifySystem,
  writeMapManifest,
  writeTextAtomic,
} from '../src/core.mjs';

function parseArguments(values) {
  const positionals = [];
  const options = {};
  for (let index = 0; index < values.length; index += 1) {
    const value = values[index];
    if (!value.startsWith('--')) {
      positionals.push(value);
      continue;
    }
    const key = value.slice(2);
    const next = values[index + 1];
    if (!next || next.startsWith('--')) options[key] = true;
    else {
      options[key] = next;
      index += 1;
    }
  }
  return { positionals, options };
}

function required(value, name) {
  if (typeof value !== 'string' || value.trim() === '') throw new Error(`Eksik parametre: ${name}`);
  return value;
}

function resolveInput(value) {
  return path.isAbsolute(value) ? value : path.resolve(REPO_ROOT, value);
}

function printJson(value) {
  process.stdout.write(`${JSON.stringify(value, null, 2)}\n`);
}

function help() {
  process.stdout.write(`Project Orchestrator\n\n` +
    `Kullanım:\n` +
    `  discover [--out <catalog.json>]\n` +
    `  map-manifest\n` +
    `  new --id <id> --title <title> --goal <goal> [--out <run-dir>]\n` +
    `  validate <run.json>\n` +
    `  status <run.json>\n` +
    `  sync <run.json> [--actor <name>] [--expected-revision <n>]\n` +
    `  decision <run.json> --id <id> --summary <text> --reason <text> [--item <id> --boundary <name> --outcome approved|denied --provenance user-confirmed|platform-approved] [--actor <name>]\n` +
    `  transition <run.json> <item-id> <status> --reason <text> [--actor <name>] [--expected-revision <n>]\n` +
    `  render <run.json> <item-id> --platform codex|cursor|claude-code [--out <prompt.md>]\n` +
    `  record <run.json> <result.json> [--actor <name>] [--expected-revision <n>]\n` +
    `  verify-system\n`);
}

async function main() {
  const [command, ...rest] = process.argv.slice(2);
  const { positionals, options } = parseArguments(rest);
  if (!command || ['help', '--help', '-h'].includes(command)) {
    help();
    return;
  }

  if (command === 'discover') {
    const result = await discoverRepository(REPO_ROOT, typeof options.out === 'string' ? options.out : null);
    printJson({
      destination: result.destination,
      snapshot: result.catalog.snapshot,
      skills: result.catalog.skills.length,
      maps: result.catalog.maps.semantic.length,
      mapHealth: result.catalog.mapHealth,
      adapters: result.catalog.adapters.map((adapter) => adapter.id),
    });
    return;
  }

  if (command === 'map-manifest') {
    printJson(await writeMapManifest());
    return;
  }

  if (command === 'new') {
    const result = await createRun({
      id: required(options.id, '--id'),
      title: required(options.title, '--title'),
      goal: required(options.goal, '--goal'),
      outputDirectory: typeof options.out === 'string' ? options.out : null,
      actor: typeof options.actor === 'string' ? options.actor : 'manager',
    });
    printJson({ runPath: result.runPath, runId: result.run.runId });
    return;
  }

  if (command === 'validate') {
    const runPath = resolveInput(required(positionals[0], '<run.json>'));
    const run = await readJson(runPath);
    const config = await loadConfig();
    let catalog = null;
    try {
      catalog = await readJson(path.join(REPO_ROOT, config.paths.catalog));
    } catch {
      catalog = null;
    }
    const validation = validateRun(run, config, catalog);
    const history = await validateEventHistory(runPath, run);
    const report = { ...validation, valid: validation.valid && history.valid, history };
    printJson(report);
    if (!report.valid) process.exitCode = 1;
    return;
  }

  if (command === 'status') {
    const run = await readJson(resolveInput(required(positionals[0], '<run.json>')));
    printJson(statusReport(run, await loadConfig()));
    return;
  }

  if (command === 'sync') {
    const runPath = resolveInput(required(positionals[0], '<run.json>'));
    printJson(await syncReady(runPath, typeof options.actor === 'string' ? options.actor : 'manager', REPO_ROOT, { expectedRevision: options['expected-revision'] }));
    return;
  }

  if (command === 'decision') {
    const runPath = resolveInput(required(positionals[0], '<run.json>'));
    const hasApprovalFields = options.item || options.boundary || options.outcome;
    let extensions;
    if (hasApprovalFields) {
      const outcome = required(options.outcome, '--outcome');
      if (!['approved', 'denied'].includes(outcome)) throw new Error('--outcome approved veya denied olmalı.');
      extensions = {
        type: 'approval',
        itemId: required(options.item, '--item'),
        boundary: required(options.boundary, '--boundary'),
        outcome,
        provenance: required(options.provenance, '--provenance'),
      };
    }
    const decision = await recordDecision(runPath, {
      id: required(options.id, '--id'),
      summary: required(options.summary, '--summary'),
      reason: required(options.reason, '--reason'),
      ...(extensions ? { extensions } : {}),
    }, typeof options.actor === 'string' ? options.actor : 'manager', REPO_ROOT, { expectedRevision: options['expected-revision'] });
    printJson(decision);
    return;
  }

  if (command === 'transition') {
    const runPath = resolveInput(required(positionals[0], '<run.json>'));
    const itemId = required(positionals[1], '<item-id>');
    const status = required(positionals[2], '<status>');
    const reason = required(options.reason, '--reason');
    const result = await transitionItem(runPath, itemId, status, reason, typeof options.actor === 'string' ? options.actor : 'manager', { expectedRevision: options['expected-revision'] });
    printJson({ itemId, status: result.item.status, attempt: result.item.attempt });
    return;
  }

  if (command === 'render') {
    const runPath = resolveInput(required(positionals[0], '<run.json>'));
    const itemId = required(positionals[1], '<item-id>');
    const platform = required(options.platform, '--platform');
    if (!['codex', 'cursor', 'claude-code'].includes(platform)) throw new Error(`Desteklenmeyen platform: ${platform}`);
    const prompt = await renderPrompt(await readJson(runPath), itemId, platform);
    if (typeof options.out === 'string') {
      const outputPath = resolveInput(options.out);
      await assertSafeArtifactPath(outputPath);
      await writeTextAtomic(outputPath, prompt);
      printJson({ outputPath });
    } else {
      process.stdout.write(prompt);
    }
    return;
  }

  if (command === 'record') {
    const runPath = resolveInput(required(positionals[0], '<run.json>'));
    const resultPath = resolveInput(required(positionals[1], '<result.json>'));
    printJson(await recordResult(runPath, resultPath, typeof options.actor === 'string' ? options.actor : 'manager', REPO_ROOT, { expectedRevision: options['expected-revision'] }));
    return;
  }

  if (command === 'verify-system') {
    const report = await verifySystem();
    printJson(report);
    if (!report.valid) process.exitCode = 1;
    return;
  }

  throw new Error(`Bilinmeyen komut: ${command}`);
}

main().catch((error) => {
  process.stderr.write(`HATA: ${error.message}\n`);
  process.exitCode = 1;
});
