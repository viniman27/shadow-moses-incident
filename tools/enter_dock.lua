-- Original controller replay for the pinned MGS dev stage selector.
-- Host supplies SMI.stage() and SMI.menuAddress from the current linker map.
-- No RAM writes, no game code patch, no window focus or network required.
local ram = PCSX.getMemPtr()
local pad = PCSX.SIO0.slots[1].pads[1]
local buttons = PCSX.CONSTS.PAD.BUTTON
local elapsed = 0
local started = false
local done = false
SMI.dockListener = PCSX.Events.createEventListener('GPU::Vsync', function()
    if done then return end
    if not started then
        if SMI.stage() ~= 'title' or ram[SMI.menuAddress] == 0 then return end
        started = true
    end
    elapsed = elapsed + 1
    -- Fresh dev boot: TITLE -> D00A (cutscene) -> S00A (playable dock).
    -- Short presses with release gaps avoid the menu's key-repeat behavior.
    if elapsed == 90 or elapsed == 110 then pad.setOverride(buttons.DOWN) end
    if elapsed == 94 or elapsed == 114 then pad.clearOverride(buttons.DOWN) end
    if elapsed == 140 then pad.setOverride(buttons.CIRCLE) end
    if elapsed == 144 then
        pad.clearOverride(buttons.CIRCLE)
        done = true
    end
end)
