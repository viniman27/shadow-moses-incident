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
    if control == 320 then sample('during_crawl') end
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
assert samples['after_crawl'][2] & 0x50 == 0x50, 'Ground + moving flags absent'
assert samples['during_crawl'][2] & 0x50 == 0x50, 'Sustained crawl flags absent'
assert samples['during_crawl'][:2] != samples['after_crawl'][:2], 'Sustained crawling did not change position'
assert samples['after_stand'][2] & 0x60 == 0, 'Player did not stand back up'
assert all(sample[2] & 0x2300 == 0 for sample in samples.values()), 'Damage/downed/death confounds movement'
print('PASS: dock loaded; walking, crawling displacement and standing verified in live game memory.')
