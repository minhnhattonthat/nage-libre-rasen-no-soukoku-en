-- Probe for tools/debug/tour.py (after warp.lua): shoots the scene the warp landed on, then presses circle every 40
-- frames and shoots one frame per
-- new text screen, named like emu.py's own f<frame>.png so sheet.py orders them in. Windows draw their text into
-- 4bpp VRAM textures at (640,256)+ (docs/re/vwf.md), so a hash of that area is the text on screen: shoot when it
-- differs from the last shot, has stopped changing for 20 frames (typing done) and wasn't seen before (loops).
local ffi = require("ffi")
local bit = require("bit")
local function text_hash()
  local v = PCSX.GPU.getVRAM()
  local p = ffi.cast("const uint32_t*", v.data)   -- a Support.Slice: .data is the pointer
  local h = 0
  for y = 256, 511 do
    local row = y * 512 + 320   -- 1024 16-bit pixels per row = 512 words; x 640 = word 320
    for x = 0, 191 do h = bit.bxor(bit.rol(h, 5), p[row + x]) end
  end
  return h
end
local h20, last, seen = nil, nil, {}
local started = false
L.on_frame(function(n)
  if not WARP_DONE then return end
  if not started then started = true; L.shot(string.format("f%06d.png", n)) end
  if not L.route_done() or n % 20 ~= 0 then return end
  local h = text_hash()
  if n % 40 == 0 then
    if h == h20 and h ~= last and not seen[h] then
      L.shot(string.format("f%06d.png", n))
      last, seen[h] = h, true
    end
    L.press("circle", 6)
  end
  h20 = h
end)
