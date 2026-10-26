"""Internal native-plugin bridge. Authors describe their book in the host chat.

Reuse the existing installer and controller; never ask an LLM to manufacture
project records, install receipts, command recipes or execution contracts.
"""
from pathlib import Path
from contextlib import redirect_stdout
import io
import json
import re
import subprocess
import sys
from uuid import uuid4

from launcher.cli import build_parser, _run, read_project
from launcher.autonomous import controlled_command, launch_controlled
from launcher.native import find_native

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'skills/book-genesis/scripts'))
from run_host_call import run_host_call, HostCallError


def validate_creative_idea(idea):
    """Reject observed operational-context leakage; do not silently rewrite prose.

    This is a narrow input check, not a general semantic classifier. The host
    must still separate the author's creative brief from execution controls.
    """
    markers = ('# agents.md instructions', '<instructions>', '--quality-target',
               'weighted_quality_target', 'sandbox_permissions')
    score = re.search(r'\b(?:quality|score|target|rating|nota|qualidade)\b[^\n.!?]{0,120}'
                      r'\b\d+(?:\.\d+)?\s*(?:/|out of|de)\s*(?:100|10)\b', idea, re.I)
    if any(marker in idea.lower() for marker in markers) or score:
        raise ValueError('The idea file contains operational instructions or a quality-score target. '
                         'Save only the story idea and creative/length constraints, preserving their wording; '
                         'keep host instructions outside it and pass acceptance scores as quality flags. '
                         'No book was prepared and no model was called.')


def preflight(root, config):
    """One bounded authenticated call before any chapter attempt is consumed.

    The same isolated native argv and process ownership are used in production.
    This does not grant network permissions or replace the host's approval flow.
    """
    command = controlled_command(find_native('codex'), model=config['model'],
                                 effort=config['effort'],
                                 context_window=config['autonomous_contract'].get('native_context_window'))
    command['timeout_seconds'] = 60
    call_id = 'plugin-preflight-' + uuid4().hex
    folder = root / '.book-genesis/preflight'
    folder.mkdir(exist_ok=True)
    packet = folder / (call_id + '.txt')
    packet.write_text('Connectivity check. Do not use tools. Reply with exactly BOOK_GENESIS_READY.', encoding='utf-8')
    print('Checking the selected Codex connection (up to 60 seconds). No chapter is being drafted yet.', flush=True)
    try:
        receipt = run_host_call(root, call_id, packet, json.dumps(command))
    except HostCallError as exc:
        raise ValueError('Codex connection check failed. No book attempt was consumed. '
                         'Inspect the saved host-call receipt for network permission, sign-in or quota errors. '
                         'Use the host\'s normal permission/sign-in flow, then resume this folder. '
                         f'Detail: {exc}') from exc
    response = (root / receipt['paths']['response']).read_text(encoding='utf-8').strip()
    if response != 'BOOK_GENESIS_READY':
        raise ValueError('Codex did not complete the connection check as requested. '
                         'The response and receipt are saved; no book attempt was consumed.')
    print('Connection verified. Starting the saved book workflow.', flush=True)


def main(argv=None):
    try:
        args = build_parser().parse_args(argv)
        if args.command not in {'new', 'resume'}:
            return _run(args)
        root = args.project.expanduser().resolve()
        if root.is_relative_to(ROOT):
            raise ValueError('Choose a book workspace outside the installed plugin folder')
        if args.command == 'new':
            if args.host != 'codex' or not args.autonomous:
                raise ValueError('This bridge requires autonomous Codex')
            if args.author is None:
                args.author = 'Anonymous'
                print('No publishing name supplied. Using Anonymous; no account identity was inferred.', flush=True)
            idea = args.idea_file.read_text(encoding='utf-8-sig') if args.idea_file else args.idea
            if idea is None:
                raise ValueError('The host must supply the author\'s story idea before preparing the book')
            validate_creative_idea(idea)
            # Freeze exactly the bytes just validated; do not reread a changed file.
            args.idea, args.idea_file = idea, None
            requested_prepare_only = args.prepare_only
            args.prepare_only = True
            with redirect_stdout(io.StringIO()):
                code = _run(args)
            print(f'Prepared and verified your book workspace: {root}', flush=True)
            if code or requested_prepare_only:
                return code
        config = read_project(root)
        validate_creative_idea(config['idea'])
        if config['host'] != 'codex' or not config.get('autonomous_contract'):
            raise ValueError('This project is not a controlled Codex book; keep its original workflow')
        for key in ('model', 'effort', 'author'):
            supplied = getattr(args, key)
            saved = config.get('author_name' if key == 'author' else key)
            if supplied is not None and supplied != saved:
                raise ValueError('A saved autonomous book freezes model, effort and author')
        if args.command == 'resume' and args.prepare_only:
            print('Saved plugin project and skill snapshot verified. No model was called.')
            return 0
        preflight(root, config)
        return launch_controlled(root, config, model=config['model'], effort=config['effort'],
                                 author_name=config['author_name'])
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        print(f'Book Genesis: {exc}', file=sys.stderr, flush=True)
        return 2
    except (KeyboardInterrupt, EOFError):
        print('Interrupted. Saved files are preserved; resume this book folder.', file=sys.stderr, flush=True)
        return 130


if __name__ == '__main__':
    raise SystemExit(main())
