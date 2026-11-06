"""Explicit recovery of a stopped Codex book, with an immutable full backup.

This never dispatches inference, changes prose, refunds budgets or changes the
quality policy. Normal resume still refuses a silently changed installation.
"""
import ast
import copy
from hashlib import sha256
import json
from pathlib import Path
import shutil
import stat
import sys
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'skills/book-genesis/scripts'


def _scripts():
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))


def verify_recovery(root, data):
    _scripts()
    from recovery_evidence import verify_recoveries
    return verify_recoveries(root, data)


def _hash(path):
    return sha256(path.read_bytes()).hexdigest()


def _inventory(root):
    from launcher.cli import _install_path
    root = _install_path(root)
    result = {}
    for path in sorted(root.rglob('*')):
        if path.is_symlink() or getattr(path.lstat(), 'st_file_attributes', 0) & getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0):
            raise ValueError('Runtime recovery refuses linked files or directories')
        if path.is_file() and path.relative_to(root).as_posix() != '.book-genesis/launcher.lock':
            result[path.relative_to(root).as_posix()] = _hash(path)
    return result


def _method(path, cls, method):
    tree = ast.parse(path.read_text(encoding='utf-8-sig'))
    parent = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == cls)
    node = next(n for n in parent.body if isinstance(n, ast.FunctionDef) and n.name == method)
    return ast.dump(node, include_attributes=False)


def _quality_policy(old_skill):
    new_skill = ROOT / 'skills/book-genesis'
    fixed = ['references/scoring/evaluator-protocol.md', 'references/scoring/genesis-score.md',
             'references/scoring/rubric-criteria.md', 'scripts/decide_comparison.py',
             'scripts/validate_rubric.py']
    for name in fixed:
        if (old_skill / name).read_bytes() != (new_skill / name).read_bytes():
            raise ValueError('Runtime recovery cannot change the scoring policy: ' + name)
    for file, cls, methods in [('autonomous_book.py', 'BookWorkflow', ('rubric', 'panel', 'measure')),
                               ('workflow_state.py', 'Journal', ('reserve_pass',))]:
        for method in methods:
            if _method(old_skill / 'scripts' / file, cls, method) != _method(new_skill / 'scripts' / file, cls, method):
                raise ValueError('Runtime recovery cannot change scoring, votes or revision budgets: ' + method)


def recover_runtime(root, archive):
    from launcher.cli import read_project, _ownership, _install_path
    from runner.distribution import install_suite, verify_install, _tree_digest
    _scripts()
    from workflow_state import Journal, atomic, encoded, read_json, freeze

    root, archive = Path(root).absolute(), Path(archive).absolute()
    if root.resolve() != root or archive.resolve() != archive:
        raise ValueError('Use real, unlinked book and archive paths')
    if archive.exists() or archive.is_relative_to(root) or root.is_relative_to(archive):
        raise ValueError('Choose a new archive outside the book')
    if not archive.parent.is_dir():
        raise ValueError('The archive parent must already exist')
    config = read_project(root, verify_snapshot=False)
    if config['host'] != 'codex' or config['collaboration'] != 'autonomous':
        raise ValueError('Runtime recovery currently supports stopped autonomous Codex books')
    with _ownership(root):
        if (root / 'work/host-calls/.active.lock').exists():
            raise ValueError('A native call still has an active lock; preserve its owner')
        state_path = root / '.book-genesis/workflow.json'
        before = read_json(state_path)
        if before.get('status') != 'blocked' or before.get('phase') != 5 or before.get('pending_mutation'):
            raise ValueError('Runtime recovery requires a stopped, blocked revision without pending publication')
        if not any(s.get('status') == 'blocked_input_size' for s in before['steps'].values()):
            raise ValueError('No preserved oversized request establishes this runtime recovery')
        journal = Journal(root, before['contract'])
        old_skills = root / '.book-genesis/skills'
        install = old_skills / '.book-genesis-install.json'
        recorded = read_json(install)
        if recorded.get('target') != 'codex' or not recorded.get('skills'):
            raise ValueError('Missing original Codex installation evidence')
        for name, expected in recorded['skills'].items():
            if Path(name).name != name or _tree_digest(old_skills / name) != expected:
                raise ValueError('Original installed snapshot changed: ' + name)
        contract = before['contract']
        if (contract['project_sha256'] != _hash(root / '.book-genesis/project.json')
                or contract['install_sha256'] != _hash(install)
                or contract['runner_sha256'] != _hash(old_skills / 'book-genesis/scripts/autonomous_book.py')
                or contract['command'] != read_json(root / '.book-genesis/native-command.json')):
            raise ValueError('Original execution contract changed')
        for field in ('chapters', 'min_words', 'max_words', 'quality_target', 'weighted_quality_target'):
            if config['autonomous_contract'].get(field) != contract.get(field):
                raise ValueError('Project differs from its frozen quality or production contract')
        for field in ('model', 'effort'):
            if config.get(field) != contract.get(field):
                raise ValueError('Project differs from its frozen native model')

        def verify_records(value):
            if isinstance(value, dict):
                if isinstance(value.get('path'), str) and isinstance(value.get('sha256'), str):
                    journal.verify_files([value])
                for child in value.values():
                    verify_records(child)
            elif isinstance(value, list):
                for child in value:
                    verify_records(child)
        verify_records(before)
        _quality_policy(old_skills / 'book-genesis')
        original_inventory = _inventory(root)
        shutil.copytree(_install_path(root), _install_path(archive))
        if _inventory(archive) != original_inventory or _inventory(root) != original_inventory:
            raise ValueError('Book changed during archival; original runtime retained')
        recovery_dir = root / '.book-genesis/runtime-recoveries' / uuid4().hex
        recovery_dir.mkdir(parents=True)
        freeze(recovery_dir / 'original-workflow.json', state_path.read_bytes())
        freeze(recovery_dir / 'archive-inventory.json', encoded(original_inventory))
        staged = recovery_dir / 'new-skills'
        installed = install_suite('codex', destination=_install_path(staged))
        if not installed['ok'] or not verify_install('codex', destination=_install_path(staged))['ok']:
            raise ValueError('New runtime installation failed; original retained')
        after = copy.deepcopy(before)
        after['contract']['install_sha256'] = _hash(staged / '.book-genesis-install.json')
        after['contract']['runner_sha256'] = _hash(staged / 'book-genesis/scripts/autonomous_book.py')
        record = {'schema_version': 1, 'kind': 'explicit_runtime_recovery', 'created_at': Journal.now(),
                  'archive': str(archive), 'archive_inventory': journal.record_file(recovery_dir / 'archive-inventory.json'),
                  'original_journal': journal.record_file(recovery_dir / 'original-workflow.json'),
                  'old_contract': before['contract'], 'new_contract': after['contract'],
                  'reason': 'Repair undispatched oversized revision verification; preserve scores, prose and budgets.'}
        receipt = recovery_dir / 'recovery.json'
        freeze(receipt, encoded(record))
        after.setdefault('runtime_recoveries', []).append(journal.record_file(receipt))
        verify_recovery(root, after)
        previous = recovery_dir / 'previous-skills'
        # All rename targets are resolved children of this book's metadata.
        for path in (old_skills, staged, previous):
            if not path.resolve().is_relative_to(root / '.book-genesis'):
                raise ValueError('Runtime recovery path escapes book metadata')
        old_skills.rename(previous)
        try:
            staged.rename(old_skills)
            atomic(state_path, encoded(after))
        except BaseException:
            if old_skills.exists():
                old_skills.rename(staged)
            previous.rename(old_skills)
            raise
        return {'status': 'recovered', 'book': str(root), 'archive': str(archive),
                'receipt': str(receipt), 'model_calls': 0, 'literary_result': 'unchanged_not_passed'}
