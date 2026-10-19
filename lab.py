"""Captura evidencia y aplica una propuesta solo con confirmacion humana."""
import argparse
import difflib
import json
import re
import subprocess
import sys
from agent import ROOT, OUT, digest, validate_expression


def run(command):
    return subprocess.run(command, cwd=ROOT, capture_output=True, text=True,
                          encoding='utf-8', errors='replace', timeout=90)


def checked(command):
    p = run(command)
    if p.returncode:
        raise ValueError(p.stderr or p.stdout)
    return p.stdout.strip()


def tests():
    return run([sys.executable, '-B', '-m', 'unittest', 'discover', '-s', 'tests', '-v'])


def record(run_id):
    OUT.mkdir(exist_ok=True)
    code = (ROOT / 'costs.py').read_text(encoding='utf-8')
    meta = {'source_sha256': digest(code), 'origin': 'local'}
    if run_id:
        if not run_id.isdigit():
            raise ValueError('El ID de ejecucion debe ser numerico')
        if checked(['git', 'status', '--porcelain']):
            raise ValueError('Necesitas un arbol Git limpio para asociar el fallo al commit')
        info = json.loads(checked(['gh', 'run', 'view', run_id, '--json', 'headSha,status,conclusion,url']))
        if info['status'] != 'completed' or info['conclusion'] != 'failure':
            raise ValueError('Selecciona una ejecucion terminada con fallo')
        if info['headSha'] != checked(['git', 'rev-parse', 'HEAD']):
            raise ValueError('El commit local no coincide con la ejecucion')
        log = checked(['gh', 'run', 'view', run_id, '--log-failed'])
        meta.update(origin='github', run_url=info['url'], commit=info['headSha'])
    else:
        p = tests()
        log = p.stdout + p.stderr
        if p.returncode == 0:
            raise ValueError('Las pruebas pasan; no hay fallo que investigar')
    (OUT / 'failure.txt').write_text(log, encoding='utf-8')
    (OUT / 'evidence.json').write_text(json.dumps(meta, indent=2), encoding='utf-8')
    print(log)
    print('Evidencia guardada. Siguiente: py agent.py')


def apply():
    proposal = json.loads((OUT / 'proposal.json').read_text(encoding='utf-8'))
    expression = validate_expression(proposal['expression'])
    path = ROOT / 'costs.py'
    original_bytes = path.read_bytes()
    before = path.read_text(encoding='utf-8')
    if digest(before) != proposal['source_sha256']:
        raise ValueError('La propuesta esta desactualizada. Captura y analiza de nuevo')
    after, count = re.subn(r'^    return .+$', '    return ' + expression, before, flags=re.M)
    if count != 1 or after == before:
        raise ValueError('No hay un cambio unico aplicable')
    print(''.join(difflib.unified_diff(before.splitlines(True), after.splitlines(True), fromfile='antes/costs.py', tofile='despues/costs.py')))
    if input('Escribe APLICAR para modificar costs.py y ejecutar las pruebas: ').strip() != 'APLICAR':
        print('Cancelado. No se modifico el archivo.')
        return
    success = False
    try:
        path.write_text(after, encoding='utf-8')
        p = tests()
        log = p.stdout + p.stderr
        (OUT / 'validation.txt').write_text(log, encoding='utf-8')
        print(log)
        success = p.returncode == 0
        if not success:
            raise ValueError('La propuesta fallo las pruebas; se restaura el archivo original')
    finally:
        if not success:
            path.write_bytes(original_bytes)
    print('Cambio aplicado y pruebas correctas. Sigue la guia para abrir el PR; no se publica automaticamente.')


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest='action', required=True)
    rec = sub.add_parser('record')
    rec.add_argument('--run', help='ID de una ejecucion fallida de GitHub Actions')
    sub.add_parser('apply')
    args = p.parse_args()
    try:
        record(args.run) if args.action == 'record' else apply()
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        raise SystemExit(str(exc))


if __name__ == '__main__':
    main()
