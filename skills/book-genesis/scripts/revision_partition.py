"""Conservative repair dependencies; every selected unit still needs fresh gates."""
from group_review_schema import normalized_report
from workflow_state import WorkflowError, read_json, encoded, digest, freeze


def partition_review(manifest, catalog, report):
    """Consume a validated negative review, never turn it into an approval.

    Companion-proposal citations in a causality check are conservative hints.
    Original-source citations and shared issue IDs are not revision dependencies.
    A fresh assembled-book check remains authoritative for each selected unit.
    """
    report = normalized_report(report, catalog)
    members = {row['chapter'] for row in manifest['publications']}
    if report['verdict'] != 'block' or {row['chapter'] for row in report['chapters']} != members:
        raise WorkflowError('Partitioning requires a complete negative repair review')
    locations = {p['id']: s['source'] for s in catalog['sources'] for p in s['passages']}
    graph = {n: set() for n in members}
    blocked = {n for f in report['findings'] for n in f['chapters']}
    for row in report['chapters']:
        n = row['chapter']
        if any(c['result'] != 'pass' for c in row['checks']):
            blocked.add(n)
        for check in row['checks']:
            for identifier in check['evidence_ids']:
                if identifier not in locations:
                    raise WorkflowError('Unknown dependency evidence passage')
                source = locations[identifier]
                if check['name'] == 'Canon and causal dependencies' and source.startswith('proposed/'):
                    dep = int(source.removeprefix('proposed/chapter-').removesuffix('.md'))
                    if dep not in members:
                        raise WorkflowError('Dependency refers to an unassigned proposal')
                    if dep != n:
                        graph[n].add(dep)
    if not blocked or not blocked.issubset(members):
        raise WorkflowError('Negative review lacks bounded affected chapters')
    direct = sorted(blocked)
    reach = {n: set(deps) for n, deps in graph.items()}
    changed = True
    while changed:
        changed = False
        for n in sorted(members):
            expanded = reach[n] | {d for dep in list(reach[n]) for d in reach[dep]}
            if expanded != reach[n]:
                reach[n] = expanded
                changed = True
    blocked |= {n for n in members if reach[n] & blocked}
    remaining, units = members - blocked, []
    while remaining:
        n = min(remaining)
        component = {m for m in remaining if m == n or m in reach[n] and n in reach[m]}
        units.append(sorted(component))
        remaining -= component
    ordered, done = [], set()
    while units:
        ready = [u for u in units if all(graph[n] <= done | set(u) for n in u)]
        if not ready:
            raise WorkflowError('Repair dependency order is incomplete')
        unit = min(ready)
        units.remove(unit)
        ordered.append(unit)
        done.update(unit)
    return {'schema_version': 1, 'dependencies': {str(n): sorted(graph[n]) for n in sorted(members)},
            'directly_blocked': direct, 'blocked': sorted(blocked), 'units': ordered}


def reviewed_parent(journal, plan):
    """Reconstruct eligibility from the unchanged original negative native call."""
    import creative_groups as groups
    journal.verify_files([plan['parent_manifest']])
    manifest = read_json(journal.root / plan['parent_manifest']['path'])
    catalog = groups.catalog_for(journal, manifest)
    members = [p['chapter'] for p in manifest['publications']]
    schema = groups.schema_for(catalog, members, report_version={3: 2, 4: 3}.get(manifest['schema_version'], 1))
    response = groups.verify_step(journal, plan['parent_review_key'], groups.packet_for(manifest, catalog), schema)
    if not groups.validate_report(response, schema, catalog, members)['valid']:
        raise WorkflowError('Partition parent lacks a valid complete repair check')
    actual = partition_review(manifest, catalog, read_json(response))
    if actual != plan['partition']:
        raise WorkflowError('Partition differs from its original negative evidence')
    return manifest


def verify_unit(journal, manifest):
    journal.verify_files([manifest['partition']])
    plan = read_json(journal.root / manifest['partition']['path'])
    if plan.get('kind') != 'independent_revision_partition' or plan.get('schema_version') != 1:
        raise WorkflowError('Unsupported independent revision partition')
    parent = reviewed_parent(journal, plan)
    members = sorted(p['chapter'] for p in manifest['publications'])
    if members not in plan['partition']['units']:
        raise WorkflowError('Revision unit was not eligible in its original partition')
    old = {p['chapter']: p for p in parent['publications']}
    if manifest['tasks'] != [t for t in parent['tasks'] if t['chapter'] in members] or manifest['strategy'] != parent['strategy']:
        raise WorkflowError('Revision unit changed its assigned tickets or strategy')
    for row in manifest['publications']:
        if row != old[row['chapter']]:
            raise WorkflowError('Revision unit substituted a different proposal')


def execute_partitioned(workflow, number, tasks, strategy, *, staged=None):
    """One bounded evidence-based split, with fresh gates for each eligible unit."""
    import creative_groups as groups
    from correction_groups import group_key
    journal, root = workflow.journal, workflow.root
    key = group_key('creative', number, tasks)
    final_path = root / f'evaluations/decisions/{key}-partition-outcomes.json'
    journal.check_canonical()
    if final_path.exists():
        saved = read_json(final_path)
        journal.verify_files(saved['evidence'])
        return saved['outcomes']
    original = groups.execute(workflow, number, tasks, strategy, staged=staged)
    manifest_path = root / f'work/creative-groups/{key}/manifest.json'
    check_key = key + '-check'
    step = journal.data['steps'].get(check_key, {})
    if step.get('status') != 'completed' or not manifest_path.exists():
        return original
    parent = read_json(manifest_path)
    catalog = groups.catalog_for(journal, parent)
    members = [p['chapter'] for p in parent['publications']]
    schema = groups.schema_for(catalog, members, report_version={3: 2, 4: 3}.get(parent['schema_version'], 1))
    response = groups.verify_step(journal, check_key, groups.packet_for(parent, catalog), schema)
    if not groups.validate_report(response, schema, catalog, members)['valid']:
        raise WorkflowError('Partition parent check is invalid')
    report = read_json(response)
    # A rejected preference is not permission to poll the same proposal again.
    if report['verdict'] != 'block':
        return original
    plan = {'schema_version': 1, 'kind': 'independent_revision_partition',
            'parent_manifest': journal.record_file(manifest_path), 'parent_review_key': check_key,
            'partition': partition_review(parent, catalog, report)}
    plan_path = root / f'work/creative-groups/{key}/partition.json'
    freeze(plan_path, encoded(plan))
    parent = reviewed_parent(journal, plan)
    evidence = [journal.record_file(plan_path), journal.record_file(response)]
    parent_result = read_json(root / f'evaluations/decisions/{key}-outcomes.json')
    evidence += parent_result['evidence']
    results = {r['chapter']: dict(r) for r in original}
    accepted, failed = set(), set(plan['partition']['blocked'])
    for unit in plan['partition']['units']:
        prerequisites = {d for n in unit for d in plan['partition']['dependencies'][str(n)]} - set(unit)
        if not prerequisites <= accepted:
            failed.update(unit)
            for n in unit:
                results[n]['reason'] = 'A required companion revision was not accepted; original retained.'
            continue
        unit_key = f'revision-{number}-unit-{min(unit)}-{max(unit)}-' + digest(encoded([key, unit]))[:16]
        unit_manifest = root / f'work/creative-groups/{unit_key}/manifest.json'
        if unit_manifest.exists():
            stored = read_json(unit_manifest)
            journal.verify_files(list(stored['sources'].values()))
            current = [root / row['path'] for name, row in sorted(stored['sources'].items()) if name.startswith('original/')]
        else:
            current = workflow.snapshot(unit_key + '-source-book')
        by_name = {p.name: p for p in current}
        prepared = []
        unit_tasks = [t for t in parent['tasks'] if t['chapter'] in unit]
        for task in unit_tasks:
            n, name = task['chapter'], f"chapter-{task['chapter']:02d}.md"
            publication = next(p for p in parent['publications'] if p['chapter'] == n)
            prepared.append({'task': task, 'accepted': by_name[name],
                'candidate': root / publication['candidate']['path'], 'target': root / publication['target'],
                'manuscript': current})
        outcomes = groups.execute(workflow, number, unit_tasks, parent['strategy'], staged=prepared,
                                  key=unit_key, partition=journal.record_file(plan_path))
        results.update({r['chapter']: r for r in outcomes})
        unit_result_path = root / f'evaluations/decisions/{unit_key}-outcomes.json'
        evidence += [journal.record_file(unit_result_path)] + read_json(unit_result_path)['evidence']
        if all(r['decision'] == 'promote' for r in outcomes):
            accepted.update(unit)
        else:
            failed.update(unit)
    outcomes = [results[t['chapter']] for t in tasks]
    journal.verify_files(evidence)
    freeze(final_path, encoded({'outcomes': outcomes, 'evidence': evidence}))
    workflow.log('Independent revisions | accepted ' + ', '.join(map(str, sorted(accepted)))
                 + ' | retained ' + ', '.join(map(str, sorted(failed))))
    return outcomes
