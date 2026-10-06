"""Real dock wall replay: fixed-yaw crawl away/backward/away, then framing.

Runs the complete original regression first to regenerate current-build symbols.
The projected-scale bound is a visual acceptance guard, not a minimum eye depth.
Only controller inputs and read-only RAM observations; proprietary evidence stays local.
"""
import argparse
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--disc', type=Path, required=True)
p.add_argument('--emulator', type=Path, required=True)
p.add_argument('--pause', type=int, default=0, help='Visual checkpoint 140..1279; not a passing smoke')
a = p.parse_args()
if a.pause and not 140 <= a.pause < 1280:
    p.error('--pause must be in 140..1279, before the final quit callback')
out = ROOT / 'local/smoke'
out.mkdir(parents=True, exist_ok=True)
result_path = out/'wall-result.txt'
paused_path = out/'wall-checkpoint.txt'
# Clear before the preceding regression, not after it: a same-frame marker
# from an earlier inspection must never identify this run as ready.
paused_path.unlink(missing_ok=True)
result_path.write_text('NOT_RUN')
with (out/'wall-regression.log').open('w') as log:
    subprocess.run([sys.executable, str(ROOT/'tests/run_stage_smoke.py'), '--camera',
                    '--disc', str(a.disc), '--emulator', str(a.emulator)],
                   stdout=log, stderr=subprocess.STDOUT, check=True)
print('PASS: original camera/gameplay regression (local/smoke/wall-regression.log)', flush=True)
script = (out/'stage_test.lua').read_text()
map_text = (ROOT/'references/mgs_reversing/obj_dev/asm.map').read_text()
addresses = set(re.findall(r'^\s*([0-9A-Fa-f]{8})\s+GM_PlayerControl\s*$', map_text, re.M))
assert len(addresses) == 1, 'Missing/ambiguous player control symbol'
control_address = int(addresses.pop(), 16) & 0x1fffff
setup = '''
local routeControl = ffi.cast('uint32_t*', ram + %d)
local function sampleRoute(frame)
    sampleMotion(frame)
    local cp = bit.band(tonumber(routeControl[0]), 0x1fffff)
    assert(cp > 0 and cp + 16 < 0x200000, 'Invalid control pointer')
    local yaw = ffi.cast('int16_t*', ram + cp + 8)[1]
    local zoom = ffi.cast('int32_t*', cameraView)[7]
    samples[#samples + 1] = string.format('ROUTE %%d x=%%d z=%%d status=%%d yaw=%%d zoom=%%d collision=%%d',
        frame,pos[0],pos[2],tonumber(status[0]),yaw,zoom,tonumber(cameraCollision[0]))
end
''' % control_address
script = script.replace('function SMI.stage()', setup+'\nfunction SMI.stage()')
start = script.index('    if control == 150 then')
end = script.index('    elseif frames >= 3600 then', start)
replay = '''    if control >= 140 and control <= 1280 then sampleRoute(control) end
    if control == %d then
        report('SMI_WALL_PAUSED\\n' .. table.concat(samples, '\\n'))
        local pf = assert(io.open(%s, 'w')); pf:write(tostring(control)); pf:close()
        PCSX.pauseEmulator()
        return
    end
    if control == 150 then pad.setOverride(buttons.RIGHT) end
    if control == 200 then pad.clearOverride(buttons.RIGHT) end
    if control == 220 then pad.setOverride(buttons.CROSS) end
    if control == 226 then pad.clearOverride(buttons.CROSS) end
    if control == 280 then pad.setOverride(buttons.LEFT) end
    if control == 500 then pad.clearOverride(buttons.LEFT) end
    if control == 600 then pad.setOverride(buttons.RIGHT) end
    if control == 880 then pad.clearOverride(buttons.RIGHT) end
    if control == 980 then pad.setOverride(buttons.LEFT) end
    if control == 1180 then pad.clearOverride(buttons.LEFT) end
    if control >= 1280 then
        report('SMI_WALL_PASS s00a\\n' .. table.concat(samples, '\\n'))
        PCSX.quit(0)
''' % (a.pause or -1, json.dumps(paused_path.as_posix()))
script = script[:start]+replay+script[end:]
script = script.replace('stage-result.txt', 'wall-result.txt')
lua = out/'wall-test.lua'
lua.write_text(script)
emulator = a.emulator.resolve()
cmd = [str(emulator), '-portable', '-noupdate', '-no-webserver', '-no-gdb', '-no-pcdrv',
       '-bios', str(emulator.parent/'openbios.bin'), '-iso', str(a.disc.resolve()),
       '-exe', str(ROOT/'references/mgs_reversing/obj_dev/_mgsi.exe'),
       '-memcard1', str(out/'test-slot1.mcd'), '-memcard2', str(out/'test-slot2.mcd'),
       '-logfile', str(out/'wall-emulator.log'), '-dofile', str(lua), '-run']
if not a.pause:
    cmd.append('-no-ui')
proc = subprocess.Popen(cmd, cwd=emulator.parent, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                        text=True, errors='replace')
print('EMULATOR_PID', proc.pid, flush=True)
try:
    stdout, stderr = proc.communicate(timeout=180)
except (subprocess.TimeoutExpired, KeyboardInterrupt):
    if os.name == 'nt':
        subprocess.run(['taskkill', '/PID', str(proc.pid), '/T', '/F'], capture_output=True, check=False)
    else:
        proc.kill()
    proc.communicate(timeout=10)
    raise
(out/'wall-console.log').write_text(stdout+stderr)
if a.pause:
    assert paused_path.is_file() and paused_path.read_text().strip() == str(a.pause), 'Requested visual checkpoint was not reached'
    assert result_path.read_text().startswith('SMI_WALL_PAUSED\n'), 'Missing paused replay evidence'
    print('Visual inspection ended; NOT a smoke PASS. Child exit:', proc.returncode)
    raise SystemExit(proc.returncode)
assert proc.returncode == 0, f'Wall emulator exit {proc.returncode}'
evidence = result_path.read_text()
assert evidence.startswith('SMI_WALL_PASS s00a\n'), 'Missing wall completion'
game_log = (out/'wall-emulator.log').read_text(errors='replace')
assert 'load s00a' in game_log and 'end scenario' in game_log.split('load s00a',1)[1]
route = re.findall(r'ROUTE (\d+) x=(-?\d+) z=(-?\d+) status=(\d+) yaw=(\d+) zoom=(\d+) collision=(\d+)', evidence)
motion = re.findall(r'MOTION (\d+) eye=([-\d,]+) target=([-\d,]+) head=([-\d,]+)', evidence)
expected = list(range(140,1281))
assert [int(r[0]) for r in route] == expected, 'Missing/duplicate route samples'
assert [int(r[0]) for r in motion] == expected, 'Missing/duplicate bone samples'
rows = {}
for r, m in zip(route,motion):
    frame,x,z,status,yaw,zoom,collision = map(int,r)
    eye,target,head = [tuple(map(int,v.split(','))) for v in m[1:]]
    f = [t-e for t,e in zip(target,eye)]
    norm = math.sqrt(sum(v*v for v in f)); f = [v/norm for v in f]
    right = [f[2],0,-f[0]]
    norm = math.sqrt(sum(v*v for v in right)); right = [v/norm for v in right]
    up = [f[1]*right[2],f[2]*right[0]-f[0]*right[2],-f[1]*right[0]]
    rel = [h-e for h,e in zip(head,eye)]
    depth = sum(x*y for x,y in zip(rel,f))
    assert depth > 0, ('head behind eye',frame)
    assert status & 0x2300 == 0, ('damage/downed/death',frame)
    assert 192 <= zoom <= 320, ('unbounded projection',frame,zoom)
    assert collision or zoom == 320, ('free-space zoom changed',frame)
    sx = zoom*sum(x*y for x,y in zip(rel,right))/depth
    sy = zoom*sum(x*y for x,y in zip(rel,up))/depth*58/64
    assert abs(sx)<160 and abs(sy)<112, ('head outside viewport',frame,sx,sy)
    rows[frame] = dict(frame=frame,x=x,z=z,status=status,yaw=yaw,zoom=zoom,collision=collision,
                       eye=eye,target=target,head=head,depth=depth,scale=zoom/depth,screen_x=sx,screen_y=sy)
for lo,hi,sign in [(360,480,-1),(650,800,1),(1020,1160,-1)]:
    part = [rows[i] for i in range(lo,hi+1)]
    assert all(r['status'] & 0x50 == 0x50 and r['yaw']==3072 for r in part), ('crawl/yaw',lo,hi)
    assert sign*(part[-1]['x']-part[0]['x'])>1000, ('crawl displacement',lo,hi)
assert rows[599]['status']==rows[979]['status']==0x40, 'Not settled prone at comparison poses'
assert rows[599]['zoom']==rows[1100]['zoom']==320, 'Zoom failed to return after retreat'
near = rows[979]
# The rear wall limit must not be crossed. Lateral adaptation may move the eye
# toward the pivot, but not beyond the previous same-side clearance at contact.
assert abs(near['eye'][0]+3848)<=5, ('rear wall clearance changed',near)
assert 0 <= near['eye'][2]-near['target'][2] <= 105, ('unsafe contact lateral offset',near)
for frame in (400,1100):
    row = rows[frame]
    assert row['yaw']==3072, ('corridor yaw',frame)
    rear = row['eye'][0]-(row['target'][0]+1600)
    # Here the side wall, not the rear wall, wasted usable boom length.
    # This is a scene-specific recovery guard, never a runtime minimum.
    print(f'CORRIDOR {frame}: rear={rear}')
    assert rear >= 1500, f'Unnecessary side-wall retreat at {frame}: rear={rear} < 1500'
summary = {'sample_count':len(rows),'checkpoints':[rows[i] for i in (400,599,800,840,979,1100,1279)],
           'max_near_scale':max(rows[i]['scale'] for i in range(800,980)),
           'limit_scale':320/1200,
           'limits':'Geometric projected-size bound paired with real window captures; not volume collision, temporal smoothness or campaign acceptance.'}
(out/'wall-analysis.json').write_text(json.dumps(summary,indent=2))
print(json.dumps(summary,indent=2))
# Measure magnification, not physical distance: zoom compensation can pass without
# moving the eye. This must fail on the old fixed-320 build before implementation.
assert summary['max_near_scale'] <= 320/1200, (
    f"Wall body magnification too high: {summary['max_near_scale']:.4f} > {320/1200:.4f}; inspect near image")
print('PASS: 1141 wall samples; fixed-yaw crawl away/back/away; bounded near magnification; far zoom restored.')
