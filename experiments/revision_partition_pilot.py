"""Review four existing Luna candidates in an isolated evaluation copy.

No book-generation, final scoring, export, main-book mutation or automation.
Imported candidates retain their original native receipts; all acceptance roles
run fresh through the official selected Codex command.
"""
import argparse
import json
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / 'skills/book-genesis/scripts'))
from launcher.cli import prepare_project, read_project, _ownership
from launcher.recovery import _quality_policy
from autonomous_book import BookWorkflow
from revision_partition import execute_partitioned
from workflow_state import encoded, read_json, digest, freeze, atomic
from export_book import discover_chapters, word_count_receipt


MEMBERS = (4, 8, 18, 22)


def source_hashes(source):
    paths = list((source / 'manuscript/chapters').glob('*.md'))
    paths += [source / '.book-genesis/workflow.json']
    paths += list((source / 'evaluations').glob('measure-*.json'))
    return {p.relative_to(source).as_posix(): digest(p.read_bytes()) for p in paths}


def run(source, output):
    source, output = source.resolve(), output.resolve()
    if output.is_relative_to(source) or source.is_relative_to(output) or output.is_relative_to(REPO):
        raise ValueError('Evaluation must be separate from the source book and checkout')
    before = source_hashes(source)
    original = read_json(source / '.book-genesis/workflow.json')
    contract = original['contract']
    if (contract['model'], contract['effort']) != ('gpt-5.6-luna', 'high'):
        raise ValueError('The selected original native model must be Luna high')
    _quality_policy(source / '.book-genesis/skills/book-genesis')
    command = read_json(source / '.book-genesis/native-command.json')
    fresh = not (output / '.book-genesis/project.json').exists()
    if fresh:
        prepare_project(output, host='codex', model=contract['model'], effort=contract['effort'],
            author_name='Felipe Lobo', language='English', autonomous=True,
            idea='Targeted evaluation of four existing revisions of The Hidden Groove.',
            autonomous_contract={k: contract[k] for k in ('chapters','min_words','max_words','quality_target','weighted_quality_target')})
    else:
        read_project(output)
    with _ownership(output):
        workflow = BookWorkflow(output, command, **{k: contract[k] for k in
            ('chapters','min_words','max_words','quality_target','weighted_quality_target')})
        if fresh:
            for path in (source / 'artifacts').glob('*.md'):
                freeze(output / 'artifacts' / path.name, path.read_bytes())
            for path in sorted((source / 'manuscript/chapters').glob('chapter-*.md')):
                copied = output / 'inputs/original' / path.name
                freeze(copied, path.read_bytes())
                workflow.journal.publish(copied, output / 'manuscript/chapters' / path.name)
            freeze(output / 'inputs/main-hashes.json', encoded(before))
        elif read_json(output / 'inputs/main-hashes.json') != before:
            raise ValueError('Main book changed since the evaluation was prepared')
        plan = original['strategies'][0]
        tasks = [t for t in plan['tasks'] if t['mode'] == 'creative' and t['chapter'] in MEMBERS]
        snapshot = workflow.snapshot('pilot-original')
        by_name = {p.name: p for p in snapshot}
        stages, provenance = [], []
        for task in tasks:
            n = task['chapter']
            step = original['steps'][f'revision-1-c{n:02d}']
            raw = source / step['response']
            folder = raw.parent
            receipt = read_json(folder / 'receipt.json')
            if receipt['status'] != 'completed' or receipt['exit_code'] != 0:
                raise ValueError('Imported producer did not complete')
            for name in ('packet','response','stdout','stderr'):
                if digest((folder / name).read_bytes()) != receipt[name + '_sha256']:
                    raise ValueError('Original native producer evidence changed')
                freeze(output / f'inputs/native-c{n:02d}' / name, (folder / name).read_bytes())
            stderr = (folder / 'stderr').read_text(encoding='utf-8')
            if 'model: gpt-5.6-luna' not in stderr or 'reasoning effort: high' not in stderr:
                raise ValueError('Imported producer was not verified Luna high')
            freeze(output / f'inputs/native-c{n:02d}/receipt.json', (folder / 'receipt.json').read_bytes())
            imported = output / f'inputs/native-c{n:02d}/response'
            candidate = workflow.stage_response(f'import-c{n:02d}', imported)
            prior_stage = source / f'work/attempts/revision-1-c{n:02d}/stage/chapter.md'
            if candidate.read_bytes() != prior_stage.read_bytes():
                raise ValueError('Imported proposal differs from the original staged prose')
            name = f'chapter-{n:02d}.md'
            stages.append({'task': task, 'accepted': by_name[name], 'candidate': candidate,
                           'target': output / 'manuscript/chapters' / name, 'manuscript': snapshot})
            provenance.append({'chapter': n, 'original_response': str(raw),
                'response_sha256': digest(raw.read_bytes()), 'candidate': workflow.journal.record_file(candidate)})
        freeze(output / 'inputs/provenance.json', encoded(provenance))
        atomic(output / 'pilot-status.json', encoded({'status':'running','scope':'four imported revisions only',
            'model':contract['model'],'effort':contract['effort'],'whole_book_generation':False}))
        result = {'scope':'four imported revisions; unchanged book supplies canon',
            'whole_book_generation':False,'whole_book_rescored':False,'export_attempted':False}
        try:
            result['outcomes'] = execute_partitioned(workflow, 1, tasks, plan['strategy'], staged=stages)
            result['status'] = 'completed_targeted_evaluation'
            result['evaluation_word_count'] = word_count_receipt(discover_chapters(output / 'manuscript/chapters'))['total']
            result['quality_policy_unchanged'] = True
        except BaseException as exc:
            result.update(status='stopped', error=str(exc), error_type=type(exc).__name__)
            raise
        finally:
            result['main_book_unchanged'] = source_hashes(source) == before
            result['native_roles'] = {key:step['status'] for key,step in workflow.journal.data['steps'].items()}
            atomic(output / 'pilot-status.json', encoded(result))
            if not result['main_book_unchanged']:
                raise ValueError('Main book changed during the isolated evaluation')
        print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    run(args.source, args.output)
