"""Bounded literal edits for near-boundary drafts, retaining all failed evidence."""
import json
import math
import re

from workflow_roles import (CORRECTION_SCHEMA, apply_corrections, validate_json,
                            validate_prose, validate_prose_text)
from workflow_state import WorkflowError, digest, encoded, freeze, read_json


def _record_path(workflow, key):
    if not re.fullmatch(r'draft-\d+', key):
        raise WorkflowError('Invalid draft recovery key')
    return workflow.root / 'work/draft-length-recovery' / (key + '.json')


def _edit_budget(words, low, high):
    return min(max(24, max(low - words, words - high) * 6), max(80, math.ceil(words * .06)))


def _validate(path, original, low, high, words):
    report = validate_json(path, CORRECTION_SCHEMA)
    if report['valid']:
        try:
            edits = read_json(path)['replacements']
            touched = sum(len(e['before'].split()) + len(e['after'].split()) for e in edits)
            budget = _edit_budget(words, low, high)
            if touched > budget:
                raise ValueError(f'Literal edits contain {touched} combined before/after whitespace words; maximum is {budget}. '
                                 'Use fewer edits and short unique source phrases, not whole sentences or paragraphs.')
            prose = apply_corrections(original, edits)
            if prose.splitlines()[0] != original.splitlines()[0]:
                raise ValueError('Length recovery must retain the exact heading')
            report = validate_prose_text(prose, path, low=low, high=high, report=report)
        except ValueError as exc:
            report.update(valid=False, errors=[str(exc)])
    return report


def load_recovery(workflow, key):
    path = _record_path(workflow, key)
    if not path.exists():
        return None
    record = read_json(path)
    if record.get('kind') != 'draft_length_recovery' or record.get('schema_version') != 1 or record.get('source_step') != key:
        raise WorkflowError('Unsupported draft length recovery record')
    workflow.journal.verify_files(record['evidence'])
    source_step = workflow.journal.data['steps'][key]
    if digest(encoded(source_step)) != record['source_step_sha256']:
        raise WorkflowError('Original failed draft attempts changed after recovery')
    attempts = [a for a in source_step['attempts'] if a['status'] != 'provider_wait']
    if (source_step['status'] != 'failed' or len(attempts) != 2
            or record['source_response']['path'] != f"work/host-calls/{attempts[-1]['call_id']}/response"):
        raise WorkflowError('Draft recovery source is not the final failed draft attempt')
    expected = rf"Chapter has \d+ prose words; production allowance is {record['low']}\.\.{record['high']}"
    if any(len(a.get('validation_errors', [])) != 1 or not re.fullmatch(expected, a['validation_errors'][0]) for a in attempts):
        raise WorkflowError('Draft recovery changed the original length allowance')
    repair = workflow.journal.data['steps'].get(key + '-length-repair', {})
    if (record['repair_step'] != key + '-length-repair' or repair.get('status') != 'completed'
            or digest(encoded(repair)) != record['repair_step_sha256']
            or record['repair_response']['path'] != repair.get('response')
            or record['validation']['path'] != repair.get('validation')):
        raise WorkflowError('Draft recovery differs from its completed native repair')
    source = workflow.root / record['source_response']['path']
    response = workflow.root / record['repair_response']['path']
    # Both paths must be among the verified records, not arbitrary replacement pointers.
    if any(record[k] not in record['evidence'] for k in ('source_response', 'repair_response', 'validation')):
        raise WorkflowError('Draft recovery pointers are outside frozen evidence')
    original = read_json(source)['prose']
    if validate_prose(source, low=record['low'], high=record['high'])['words'] != record['original_words']:
        raise WorkflowError('Draft recovery changed the original word count')
    validation = _validate(response, original, record['low'], record['high'], record['original_words'])
    if not validation['valid'] or validation['extracted_sha256'] != record['prose_sha256']:
        raise WorkflowError('Saved length recovery no longer validates')
    return {'prose': apply_corrections(original, read_json(response)['replacements']),
            'response': response, 'source_response': source, 'validation': validation,
            'validation_path': workflow.root / record['validation']['path'], 'record_path': path,
            'step': record['repair_step']}


def recover(workflow, key, *, low, high):
    saved = load_recovery(workflow, key)
    if saved is not None:
        record = read_json(saved['record_path'])
        if (record['low'], record['high']) != (low, high):
            raise WorkflowError('Draft recovery allowance changed')
        return saved
    step = workflow.journal.data['steps'].get(key, {})
    attempts = [a for a in step.get('attempts', []) if a['status'] != 'provider_wait']
    expected = rf'Chapter has \d+ prose words; production allowance is {low}\.\.{high}'
    if (step.get('status') != 'failed' or len(attempts) != 2
            or any(len(a.get('validation_errors', [])) != 1 or not re.fullmatch(expected, a['validation_errors'][0]) for a in attempts)):
        return None
    evidence = workflow.rejected_validation_evidence(key)
    if evidence is None:
        return None
    for index, attempt in enumerate(step['attempts'], 1):
        if attempt['status'] == 'provider_wait':
            continue
        folder = workflow.root / 'work/host-calls' / attempt['call_id']
        receipt = read_json(folder / 'receipt.json')
        if receipt['status'] != 'completed' or receipt['exit_code'] != 0 or receipt.get('error') is not None:
            return None
        check = validate_prose(folder / 'response', low=low, high=high)
        if check['valid'] or check['errors'] != attempt['validation_errors']:
            raise WorkflowError('Saved draft length failure differs from its original response')
        evidence.append(workflow.journal.record_file(workflow.root / f'work/workflow/{key}/validation-{index}.json'))
    source = workflow.root / 'work/host-calls' / attempts[-1]['call_id'] / 'response'
    original = read_json(source)['prose']
    words = validate_prose(source, low=low, high=high)['words']
    if max(low - words, words - high) > max(20, math.ceil(words * .03)):
        return None  # Large editorial restructuring is not a tiny length repair.
    repair_key = key + '-length-repair'
    packet = ('Make a small length repair to this unaccepted draft. Use only this packet; no tools. '
              'Return exact, unambiguous before/after literal replacements, not the complete chapter. '
              'Preserve every story event, fact, name, chronology, speaker, meaning and the exact heading. '
              'Do not summarize or cut off the ending. Remove redundant wording for an overlong draft; '
              'for a short draft, clarify existing on-page action without adding events or facts. '
              'The program counts actual prose words and applies only exact nonoverlapping edits. '
              f'The TOTAL whitespace word count of ALL before and after strings combined must not exceed {_edit_budget(words, low, high)}. '
              'Use the smallest unique source phrase needed, not the whole sentence. One short edit is enough for a one-word excess. '
              'Prefer modest headroom inside the interval when it permits this; avoid the boundary.\n\n'
              + json.dumps({'prose': original, 'actual_words': words, 'minimum': low, 'maximum': high}, ensure_ascii=False))
    response, validation = workflow.call(repair_key, packet, CORRECTION_SCHEMA,
        lambda p: _validate(p, original, low, high, words), feedback=True, feedback_response=True)
    evidence += workflow.journal.data['steps'][repair_key]['evidence']
    record = {'schema_version': 1, 'kind': 'draft_length_recovery', 'source_step': key,
        'source_step_sha256': digest(encoded(step)), 'repair_step': repair_key,
        'repair_step_sha256': digest(encoded(workflow.journal.data['steps'][repair_key])),
        'source_response': workflow.journal.record_file(source),
        'repair_response': workflow.journal.record_file(response),
        'validation': workflow.journal.record_file(workflow.root / workflow.journal.data['steps'][repair_key]['validation']),
        'low': low, 'high': high, 'original_words': words, 'prose_sha256': validation['extracted_sha256'],
        'evidence': evidence}
    workflow.journal.verify_files(evidence)
    freeze(_record_path(workflow, key), encoded(record))
    return load_recovery(workflow, key)
