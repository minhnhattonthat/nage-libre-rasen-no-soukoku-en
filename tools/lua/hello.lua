-- Setup check: proves --script Lua runs and L.log reaches log.txt.
L.on_frame(function(n)
  if n == 60 then L.log("hello from lua, frame " .. n) end
end)
