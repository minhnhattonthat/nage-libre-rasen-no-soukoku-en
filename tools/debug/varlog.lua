-- Probe: log every change of the game-state variables (docs/re/state.md) with its frame, plus a shot.
-- emu.py ... --script tools/debug/varlog.lua [--var "VARLOG_EXTRA={0x80090B28}"]
local ffi = require("ffi")
local mem = PCSX.getMemPtr()
local function u8(a) return mem[a % 0x200000] end
local VARS = { 0x80090276, 0x80090277, 0x80090B28 }
for _, a in ipairs(VARLOG_EXTRA or {}) do VARS[#VARS + 1] = a end
local VARS32 = { 0x80090C60 }       -- fade-out callback
for _, a in ipairs(VARLOG32 or {}) do VARS32[#VARS32 + 1] = a end
local last = {}
L.on_frame(function(n)
  local changed = {}
  for _, a in ipairs(VARS) do
    local v = u8(a)
    if last[a] ~= v then changed[#changed + 1] = string.format("%08X=%02X", a, v); last[a] = v end
  end
  for _, a in ipairs(VARS32) do
    local v = ffi.cast("uint32_t*", mem + a % 0x200000)[0]
    if last[a] ~= v then changed[#changed + 1] = string.format("%08X=%08X", a, v); last[a] = v end
  end
  if #changed > 0 then
    L.log(string.format("f%d %s", n, table.concat(changed, " ")))
    if n > 1 then L.shot(string.format("v%06d.png", n)) end
  end
end)
