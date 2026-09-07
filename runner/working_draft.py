"""Recover unfinished prose without promoting it to an accepted chapter."""
import time
from pathlib import Path
from runner.history import load_manifest, sha256
from runner.export import _destination


def export_working_draft(project: Path) -> Path:
    project = project.resolve()
    selected = {}
    for path in (project / 'manuscript/chapters').glob('chapter-*.md'):
        if not path.resolve().is_relative_to(project):
            raise ValueError('A chapter path leaves the project.')
        selected[int(path.stem.split('-')[-1])] = ('Saved chapter', path)
    for manifest in (project / 'manuscript/chapters/history').glob('chapter-*/manifest.json'):
        if not manifest.resolve().is_relative_to(project):
            raise ValueError('A history path leaves the project.')
        number = int(manifest.parent.name.split('-')[-1])
        if number in selected:
            continue
        data = load_manifest(project, number)
        attempts = sorted(data['attempts'], key=lambda item: item.get('sequence', 0), reverse=True)
        for attempt in attempts:
            relative = attempt.get('draft_path')
            if not relative:
                continue
            path = (project / relative).resolve()
            if not path.is_relative_to(project) or not path.is_file():
                raise ValueError('An unfinished draft is missing or leaves the project.')
            if sha256(path) != attempt.get('sha256'):
                raise ValueError('An unfinished draft changed since it was recorded; inspect its history before exporting.')
            selected[number] = ('UNACCEPTED attempt — editorial checks unfinished', path)
            break
    if not selected:
        raise ValueError('No saved prose is available yet. Planning may still be in progress.')
    parts = ['# Working draft — unfinished', '> This recovery copy includes saved chapters and the latest recorded attempt for missing chapters. It is not an accepted or publication-ready manuscript.']
    for number, (label, path) in sorted(selected.items()):
        parts.extend([f'> Chapter {number}: {label}. Source: {path.relative_to(project).as_posix()}', path.read_text(encoding='utf-8')])
    output = _destination(project, project / 'exports' / f'working-draft-{time.time_ns()}.md')
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x', encoding='utf-8') as handle:
        handle.write('\n\n'.join(parts) + '\n')
    return output
