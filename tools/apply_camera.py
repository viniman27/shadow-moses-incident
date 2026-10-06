"""Install/remove an original DEV_EXE-only camera hook in the pinned local checkout.

Refuses to overwrite unrelated camera.c edits. No game assets are distributed.
"""
import argparse
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'references/mgs_reversing'
RELATIVE = 'source/game/camera.c'
HEADER = SOURCE / 'source/game/smi_shoulder_camera.h'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--remove', action='store_true')
    args = parser.parse_args()
    pinned = json.loads((ROOT / 'upstreams.lock.json').read_text())['mgs_reversing']['commit']
    actual = subprocess.check_output(['git', '-C', str(SOURCE), 'rev-parse', 'HEAD'], text=True).strip()
    if actual != pinned:
        raise RuntimeError('Upstream revision differs from the reviewed pin')
    original = subprocess.check_output(['git', '-C', str(SOURCE), 'show', f'{pinned}:{RELATIVE}'])
    newline = b'\r\n' if b'\r\n' in original else b'\n'
    include_anchor = b'static void Act(GV_ACT *work)'
    call_anchor = b'            camera_act_helper4_8002F78C();'
    assert original.count(include_anchor) == original.count(call_anchor) == 1
    include = newline.join([b'#ifdef DEV_EXE', b'#include "smi_shoulder_camera.h"', b'#endif', b'', b''])
    call = newline.join([call_anchor, b'#ifdef DEV_EXE', b'            SMI_ApplyShoulderCamera();', b'#endif'])
    modified = original.replace(include_anchor, include + include_anchor).replace(call_anchor, call)
    target = SOURCE / RELATIVE
    current = target.read_bytes().replace(b'\r\n', b'\n')
    allowed = [version.replace(b'\r\n', b'\n') for version in (original, modified)]
    if current not in allowed:
        raise RuntimeError('camera.c has unrelated edits; refusing to overwrite')
    if args.remove:
        target.write_bytes(original)
        HEADER.unlink(missing_ok=True)
        print('Removed camera hook; rebuild DEV_EXE to restore its executable.')
    else:
        HEADER.write_bytes((ROOT / 'src/shoulder_camera.h').read_bytes())
        target.write_bytes(modified)
        print('Installed DEV_EXE-only camera hook; rebuild before testing.')


if __name__ == '__main__':
    main()
