"""Local integration test: reach s00a through the unmodified MGS dev menu.

Requires the locally prepared emulator, discs and build. Never downloads assets.
The generated Lua only observes memory and drives emulated controller buttons.
"""
import argparse
import json
import os
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--disc', type=Path, required=True)
parser.add_argument('--emulator', type=Path, required=True)
parser.add_argument('--camera', action='store_true', help='Also verify the compiled shoulder-camera prototype')
args = parser.parse_args()
exe = ROOT / 'references/mgs_reversing/obj_dev/_mgsi.exe'
map_path = exe.with_name('asm.map')
for path in (args.disc, args.emulator, exe, map_path):
    if not path.is_file():
        parser.error(f'Missing local prerequisite: {path}')
# Take the stage address from THIS build, not from a remembered memory address.
addresses = set(re.findall(r'^\s*([0-9A-Fa-f]{8})\s+GM_CurrentStageName\s*$',
                           map_path.read_text(), re.MULTILINE))
if len(addresses) != 1:
    raise SystemExit('Expected one unambiguous GM_CurrentStageName in asm.map')
address = int(addresses.pop(), 16) & 0x1fffff
menu_addresses = set(re.findall(r'^\s*([0-9A-Fa-f]{8})\s+isStageSelectionMenu\s*$',
                                map_path.read_text(), re.MULTILINE))
assert len(menu_addresses) == 1, 'Missing/ambiguous stage menu symbol'
menu_address = int(menu_addresses.pop(), 16) & 0x1fffff
probe_addresses = []
for symbol in ('GM_PlayerPosition', 'GM_PlayerStatus'):
    matches = set(re.findall(r'^\s*([0-9A-Fa-f]{8})\s+' + symbol + r'\s*$',
                             map_path.read_text(), re.MULTILINE))
    assert len(matches) == 1, f'Missing/ambiguous {symbol}'
    probe_addresses.append(int(matches.pop(), 16) & 0x1fffff)
out = ROOT / 'local/smoke'
out.mkdir(parents=True, exist_ok=True)
replay = ROOT / 'tools/enter_dock.lua'
lua = out / 'stage_test.lua'
# This is test code, not a shipped game modification. JSON strings are Lua-safe
# for these normalized forward-slash paths.
script = r'''local ffi = require('ffi')
SMI = { stageAddress = %d, menuAddress = %d }
local ram = PCSX.getMemPtr()
local pos = ffi.cast('int16_t*', ram + %d)
local status = ffi.cast('uint32_t*', ram + %d)
local pad = PCSX.SIO0.slots[1].pads[1]
local buttons = PCSX.CONSTS.PAD.BUTTON
local samples = {}
local crawlSampled = false
local function sample(label)
    samples[#samples + 1] = string.format('%%s x=%%d z=%%d status=%%x', label, pos[0], pos[2], tonumber(status[0]))
end
function SMI.stage() return ffi.string(ram + SMI.stageAddress, 8):match('^[^%%z]*') end
local frames, stable, control = 0, 0, 0
local function report(message)
    local f = assert(io.open(SMI_RESULT_PATH, 'w'))
    f:write(message)
    f:close()
end
SMI.testListener = PCSX.Events.createEventListener('GPU::Vsync', function()
    frames = frames + 1
    if SMI.stage() == 's00a' then stable = stable + 1 else stable = 0 end
    if stable >= 300 and bit.band(tonumber(status[0]), 0x20000080) == 0 then
        control = control + 1
    elseif control == 0 then
        -- Wait for the spawn sequence to relinquish control.
    else
        report('SMI_STAGE_FAIL player control interrupted')
        PCSX.quit(2)
        return
    end
    if control == 150 then sample('before_walk'); pad.setOverride(buttons.RIGHT) end
    if control == 200 then pad.clearOverride(buttons.RIGHT); sample('after_walk') end
    if control == 220 then pad.setOverride(buttons.CROSS) end
    if control == 226 then pad.clearOverride(buttons.CROSS) end
    if control == 280 then sample('before_crawl'); pad.setOverride(buttons.LEFT) end
    -- Vsync can interrupt the same gameplay tick before or after MOVE is set.
    -- Require a bounded run of moving samples, not one phase-sensitive read.
    if control >= 320 and control <= 330 then
        sample('crawl_window_' .. tostring(control))
        if not crawlSampled and bit.band(tonumber(status[0]), 0x50) == 0x50 then
            sample('during_crawl')
            crawlSampled = true
        end
    end
    if control == 350 then sample('after_crawl'); pad.clearOverride(buttons.LEFT) end
    if control == 400 then pad.setOverride(buttons.CROSS) end
    if control == 406 then pad.clearOverride(buttons.CROSS) end
    if control >= 600 then
        sample('after_stand')
        report('SMI_STAGE_PASS s00a\n' .. table.concat(samples, '\n'))
        PCSX.quit(0)
    elseif frames >= 3600 then
        report('SMI_STAGE_FAIL stage=' .. SMI.stage())
        PCSX.quit(2)
    end
end)
''' % (address, menu_address, *probe_addresses)
if replay.exists():
    script += f'dofile({json.dumps(replay.as_posix())})\n'
result_path = out / 'stage-result.txt'
result_path.write_text('NOT_RUN', encoding='utf-8')
script = f'SMI_RESULT_PATH = {json.dumps(result_path.as_posix())}\n' + script
if args.camera:
    camera_symbols = {}
    for symbol in ('SMI_CameraActive', 'SMI_CameraEnabled', 'SMI_CameraCollision',
                   'gUnkCameraStruct2_800B7868', 'GM_Camera', 'GM_SnakeCamera', 'GM_PlayerBody'):
        matches = set(re.findall(r'^\s*([0-9A-Fa-f]{8})\s+' + symbol + r'\s*$',
                                 map_path.read_text(), re.MULTILINE))
        assert len(matches) == 1, f'Missing/ambiguous camera symbol: {symbol}'
        camera_symbols[symbol] = int(matches.pop(), 16) & 0x1fffff
    camera_probe = '''
local cameraActive = ffi.cast('int32_t*', ram + %d)
local cameraEnabled = ffi.cast('int32_t*', ram + %d)
local cameraCollision = ffi.cast('int32_t*', ram + %d)
local cameraView = ffi.cast('int16_t*', ram + %d)
local cameraSystem = ffi.cast('uint8_t*', ram + %d)
local snakeCamera = ffi.cast('int16_t*', ram + %d)
local playerBody = ffi.cast('uint32_t*', ram + %d)
local function sampleMotion(frame)
    assert(cameraActive[0] == 1, 'Shoulder camera inactive during posture motion')
    -- Pinned PS1 layout: OBJECT.objs=0; DG_OBJS.objs=0x48;
    -- DG_OBJ stride=0x5c; MATRIX.t=0x14. Observe bone6 directly:
    -- PLAYER_GROUND changes before the animation's stance/camera offset.
    local body = bit.band(tonumber(playerBody[0]), 0x1fffff)
    assert(body > 0 and body < 0x1ffffc, 'Invalid player body pointer')
    local objs = bit.band(tonumber(ffi.cast('uint32_t*', ram + body)[0]), 0x1fffff)
    assert(objs > 0 and objs + 0x48 + 6 * 0x5c + 0x20 <= 0x200000, 'Invalid player object pointer')
    assert(ffi.cast('int16_t*', ram + objs + 0x2e)[0] > 6, 'Missing head bone')
    local bone = ffi.cast('int32_t*', ram + objs + 0x48 + 6 * 0x5c + 0x14)
    samples[#samples + 1] = string.format('MOTION %%d eye=%%d,%%d,%%d target=%%d,%%d,%%d head=%%d,%%d,%%d',
        frame, cameraView[0], cameraView[1], cameraView[2], cameraView[4], cameraView[5], cameraView[6],
        bone[0], bone[1], bone[2])
end
local function sampleCamera(label)
    samples[#samples + 1] = string.format('CAM %%s active=%%d enabled=%%d collision=%%d height=%%d first=%%d',
        label, tonumber(cameraActive[0]), tonumber(cameraEnabled[0]), tonumber(cameraCollision[0]),
        cameraView[1] - pos[1], tonumber(ffi.cast('int16_t*', cameraSystem + 34)[0]))
    local headY = snakeCamera[1]
    if bit.band(tonumber(status[0]), 0x40) ~= 0 then headY = headY - 320 end
    samples[#samples + 1] = string.format('FRAME %%s eye=%%d,%%d,%%d target=%%d,%%d,%%d head=%%d,%%d,%%d',
        label, cameraView[0], cameraView[1], cameraView[2], cameraView[4], cameraView[5], cameraView[6],
        pos[0], headY, pos[2])
end
'''
    script = script.replace('function SMI.stage()', camera_probe % tuple(camera_symbols.values()) + '\nfunction SMI.stage()')
    script = script.replace("sample('before_walk');", "sampleCamera('standing'); sample('before_walk');")
    script = script.replace("    if control >= 320 and control <= 330 then",
                            "    if control == 320 then sampleCamera('crawling') end\n    if control >= 320 and control <= 330 then")
    script = script.replace('if control >= 600 then', '''
    if control >= 280 and control <= 434 and control % 2 == 0 then sampleMotion(control) end
    if control == 440 then pad.setOverride(buttons.TRIANGLE) end
    if control == 470 then sampleCamera('first_person') end
    if control == 480 then pad.clearOverride(buttons.TRIANGLE) end
    if control == 509 then
        samples[#samples + 1] = 'INPUT L3_index=' .. tostring(l3)
    end
    if control == 510 then pad.setOverride(l3) end
    if control == 514 then pad.clearOverride(l3) end
    if control == 530 then sampleCamera('disabled') end
    if control == 540 then pad.setOverride(l3) end
    if control == 544 then pad.clearOverride(l3) end
    if control == 550 then sampleCamera('restored') end
    if control >= 600 then''')
    # Redux's Lua constants omit L3/R3 in the tested release. setOverride
    # takes the serial button BIT INDEX, not MGS's byte-swapped PAD_L3 mask.
    script = script.replace('local buttons = PCSX.CONSTS.PAD.BUTTON',
                            'local buttons = PCSX.CONSTS.PAD.BUTTON\nlocal l3 = buttons.L3 or 1')
lua.write_text(script, encoding='utf-8')
command = [str(args.emulator.resolve()), '-portable', '-noupdate',
           '-no-ui', '-no-webserver', '-no-gdb', '-no-pcdrv',
           '-bios', str(args.emulator.resolve().parent / 'openbios.bin'),
           '-iso', str(args.disc.resolve()), '-exe', str(exe),
           '-memcard1', str(out / 'test-slot1.mcd'),
           '-memcard2', str(out / 'test-slot2.mcd'),
           '-logfile', str(out / 'stage-emulator.log'),
           '-dofile', str(lua), '-run']
process = subprocess.Popen(command, cwd=args.emulator.resolve().parent,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                           text=True, errors='replace')
try:
    stdout, stderr = process.communicate(timeout=150)
except (subprocess.TimeoutExpired, KeyboardInterrupt):
    # The Windows launcher starts pcsx-redux.main: stop our own tree, not all
    # emulator processes on the machine. Never leave a timed-out test running.
    if os.name == 'nt':
        subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'],
                       capture_output=True, check=False)
    else:
        process.kill()
    process.communicate(timeout=10)
    raise
(out / 'stage-console.log').write_text(stdout + stderr, encoding='utf-8')
evidence = result_path.read_text()
print(evidence)
print(stderr[-1000:])
assert process.returncode == 0, f'Emulator/test exited {process.returncode}; see local/smoke logs'
assert evidence.startswith('SMI_STAGE_PASS s00a\n'), 'No positive stage completion evidence'
game_log = (out / 'stage-emulator.log').read_text(errors='replace')
assert 'load s00a' in game_log, 'No dock loading request'
assert 'end scenario' in game_log.split('load s00a', 1)[1], 'Dock scenario did not finish loading'
samples = {}
for label, x, z, status in re.findall(r'(\w+) x=(-?\d+) z=(-?\d+) status=([0-9a-f]+)', evidence):
    samples[label] = (int(x), int(z), int(status, 16))
assert samples['before_walk'][2] & 0x20000080 == 0, 'Player not controllable'
assert samples['before_walk'][:2] != samples['after_walk'][:2], 'Walking did not change position'
assert samples['after_walk'][2] & 0x10, 'Walking flag absent'
window = [samples[f'crawl_window_{frame}'] for frame in range(320,331)]
moving = [s for s in window if s[2] & 0x50 == 0x50]
assert len(moving) >= 8, f'Insufficient sustained crawl samples: {len(moving)}/11'
assert abs(moving[-1][0]-moving[0][0])+abs(moving[-1][1]-moving[0][1]) >= 50, 'No sustained crawl window displacement'
assert 'during_crawl' in samples, 'No moving crawl observation in the bounded window'
assert samples['after_crawl'][2] & 0x50 == 0x50, 'Ground + moving flags absent'
assert samples['during_crawl'][2] & 0x50 == 0x50, 'Sustained crawl flags absent'
assert samples['during_crawl'][:2] != samples['after_crawl'][:2], 'Sustained crawling did not change position'
assert samples['after_stand'][2] & 0x60 == 0, 'Player did not stand back up'
assert all(sample[2] & 0x2300 == 0 for sample in samples.values()), 'Damage/downed/death confounds movement'
print('PASS: dock loaded; walking, crawling displacement and standing verified in live game memory.')
if args.camera:
    camera_samples = {label: tuple(map(int, (active, enabled, collision, height, first)))
                      for label, active, enabled, collision, height, first in re.findall(
                          r'CAM (\w+) active=(\d+) enabled=(\d+) collision=(\d+) height=(-?\d+) first=(\d+)', evidence)}
    # Necessary geometric guard, NOT proof that the renderer draws Snake.
    # The head-height landmark must lie in the PS1 vertical/horizontal viewport.
    import math
    framing = re.findall(r'FRAME (\w+) eye=([-\d,]+) target=([-\d,]+) head=([-\d,]+)', evidence)
    assert {row[0] for row in framing} == {'standing', 'crawling', 'first_person', 'disabled', 'restored'}, 'Missing framing samples'
    motion = re.findall(r'MOTION (\d+) eye=([-\d,]+) target=([-\d,]+) head=([-\d,]+)', evidence)
    assert [int(row[0]) for row in motion] == list(range(280, 435, 2)), 'Missing/duplicate motion frames'
    framing += [('motion_' + frame, eye, target, head) for frame, eye, target, head in motion]
    for label, eye, target, head in framing:
        if label not in ('standing', 'crawling', 'restored') and not label.startswith('motion_'):
            continue
        eye, target, head = [tuple(map(int, v.split(','))) for v in (eye, target, head)]
        forward = [t - e for t, e in zip(target, eye)]
        length = math.sqrt(sum(v*v for v in forward))
        forward = [v / length for v in forward]
        right = [forward[2], 0, -forward[0]]
        length = math.sqrt(sum(v*v for v in right))
        right = [v / length for v in right]
        up = [forward[1]*right[2], forward[2]*right[0]-forward[0]*right[2], -forward[1]*right[0]]
        relative = [h-e for h, e in zip(head, eye)]
        depth = sum(a*b for a,b in zip(relative, forward))
        assert depth > 0, f'{label}: Snake landmark behind camera'
        # Dock wall replay: avoid the excessive body close-up at control 320.
        # This depth guard is paired with same-pose rendered inspection.
        if label == 'crawling':
            print(f'WALL crawling: landmark depth={depth:.1f}')
            assert depth >= 950, f'{label}: excessive wall close-up (depth={depth:.1f} < 950)'
        x = 320 * sum(a*b for a,b in zip(relative, right)) / depth
        y = 320 * sum(a*b for a,b in zip(relative, up)) / depth * 58 / 64
        print(f'FRAMING {label}: head landmark x={x:.1f} y={y:.1f}')
        assert abs(x) < 160 and abs(y) < 112, f'{label}: Snake head landmark outside viewport'
    assert camera_samples['standing'][0] == 1, 'Shoulder camera not active while standing'
    assert camera_samples['crawling'][0] == 1, 'Shoulder camera not active while crawling'
    assert camera_samples['crawling'][3] < camera_samples['standing'][3], 'Camera did not lower for crawl'
    assert camera_samples['first_person'][0] == 0, 'Camera failed to yield to first-person'
    assert camera_samples['first_person'][4] == 1, 'First-person test never entered its target mode'
    assert camera_samples['disabled'][:2] == (0, 0), 'L3 did not restore original camera'
    assert camera_samples['crawling'][2] == 1, 'Hazard shortening branch was not exercised'
    assert camera_samples['restored'][0] == 1, 'Shoulder camera did not resume'
    print('PASS: shoulder camera lowered for crawl, exercised hazard shortening, yielded to first-person and toggled off/on.')
