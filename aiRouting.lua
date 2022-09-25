-- call in STD jsbFuncs
  local _log, _time = jsb.callSTD()[1], jsb.callSTD()[6]
--

local SOC = require "socket"
local JSON = require "JSON"

local jmr = aiMed.fun.getJMR()
local has_attribute = aiMed.cache()
local _ = aiMed.fun

local debug_route = false
local mark_idx = 45462
local shallowCopy = jsbFM.shallowCopy

-- data
  local module_data = {
    config = {
      local_host = "localhost",
      allow_picture_cooldown = 1050,
      manager_timer = 1.734,
    },
    ports = {
      aiRouteServer = 3025,
      aiRouteClient = 3015,
    },
    requests = {},
    req_idx = -1,
    rec_idx = 0,
    routes = {},
  }
--

-- server socket class
  local aiRouteServer, server_methods = {}, {}
  local server_buffer = {}
  local server, errtry

  -- methods
    function server_methods:connect()
      server, errtry = SOC.bind(module_data.config.local_host, module_data.ports.aiRouteServer)
      if not server then
        -- error
        _log("ASTAR Server bind error (%s)", errtry)
      else
        _log("ASTAR Server re-bind OK.")
        server:settimeout(0.0144)
      end
    end
    
    -- local ins = require"inspect"

    function server_methods:recv()
      if not server then self:connect() end
      local line, err, msg
      local py_client = server:accept()
      if py_client then
        line, err, msg = py_client:receive()
        if msg then
          local data = JSON:decode(msg)
          server_buffer[#server_buffer+1]  = {
            idx = data.idx,
            msg = JSON:decode(data.msg),
          }; -- stp()
          -- ins.inspect(server_buffer[#server_buffer])
          module_data.rec_idx = module_data.rec_idx + 1
          _log("ASTAR Recv data from Python for proc")
          return true
        else
          _log("ASTAR No Client msg recv (INFO)")
        end
        -- jsb.debug_print("ASTAR", "server rcv", {line, err, msg})
      -- else
      --   _log("ASTAR No Client to get from (INFO)")
      end
    end

    function server_methods:proc()
      if #server_buffer < 1 then return end
      local xy = {}
      local ret = server_buffer[1]
      if ret then
        local idx = ret.idx
        local msg = ret.msg
        -- stp()
        if not msg then
          _log("ASTAR ERROR: No msg in return")
          if #server_buffer > 1 then table.remove(server_buffer, 1) else server_buffer = {} end
          return true
        end
        local cx, cy = msg[2], msg[1]
        if #cx < 1 or #cy < 1 then
          -- failed route
          _log("ASTAR ERROR: No route in return")
          if #server_buffer > 1 then table.remove(server_buffer, 1) else server_buffer = {} end
          return true
        end
        for i = 1, #cx do
          if _.getDist({x = module_data.requests[idx].goal[1], y = 0, z = module_data.requests[idx].goal[2]}, {x = 245600 - cx[i] * 680, y = 0, z = (744878 - cy[i] * 677) * -1}) > 31000 then
            xy[#xy+1] = {245600 - cx[i] * 680, (744878 - cy[i] * 677) * -1}
          end
          if debug_route then
            mark_idx = mark_idx + 1
            trigger.action.markToAll(mark_idx, "route"..i , {
              y = 0,
              z = (744878 - cy[i] * 677) * -1,
              x = 245600 - cx[i] * 680,
            },
            true, tostring(i))
          end
        end
        if #xy > 0 then
          module_data.routes[idx] = xy
          _log("ASTAR Added Skynet%s to the route data %d points", idx, #xy)
          if #server_buffer > 1 then table.remove(server_buffer, 1) else server_buffer = {} end
          return true
        else
          if #server_buffer > 1 then table.remove(server_buffer, 1) else server_buffer = {} end
          return _log("ASTAR Skynet%s ERROR in proc no new route data", idx)
        end
      else
        _log("ASTAR ERROR: No return data to proc!")
        if #server_buffer > 1 then table.remove(server_buffer, 1) else server_buffer = {} end
      end
    end
  --

  local function getServer()
    if not server then
      server, errtry = SOC.bind(module_data.config.local_host, module_data.ports.aiRouteServer)
      if not server then
        -- error
        _log("ASTAR Server bind error (%s)", errtry)
      else
        _log("ASTAR Server bind OK.")
        server:settimeout(0.0135)
      end
    end
    return setmetatable({
      socket = server or {},
    }, {__index = server_methods})
  end; setmetatable(aiRouteServer, {__call = function(self) return getServer() end})
--

-- client socket class
  local aiRouteClient, client_methods = {}, {}
  local client_buffer = {}
  local client, c_errtry

  -- methods
    function client_methods:send()
      local result, sock_err, bytes = client:send( self.buff )
      client:close()
      self.buff = nil
      module_data.req_idx = module_data.req_idx + 1
      return result, sock_err, bytes
    end

    function client_methods:connect()
      client, c_errtry = SOC.tcp()
      if not client then
        _log("ASTAR client instance error (%s)", c_errtry)
      else
        _log("ASTAR client created OK.")
      end
      local result, sock_err, bytes = client:connect(module_data.config.local_host, module_data.ports.aiRouteClient)
      if not result then
        return _log("Error in aiRouting socket connect (%s)", sock_err)
      else
        client:settimeout(0.005)
        return true
      end
    end
    
    function client_methods:build_picture()
      local blue_units = jmr.findUnits(nil, nil, 2)
      local seen = {}
      if #blue_units > 0 then
        for i = 1,#blue_units do
          if blue_units[i]:isActive() then
            local grp_name = blue_units[i]:getGroup():getName()
            if not seen[grp_name] and has_attribute(blue_units[i],"SAM") or (has_attribute(blue_units[i],"Planes") or has_attribute(blue_units[i],"Helicopters")) or has_attribute(blue_units[i],"Armed Air Defence") or has_attribute(blue_units[i],"Naval") then
              local pos = blue_units[i]:getPosition().p
              seen[grp_name] = {
                x = pos.x, y = pos.z,
                size = (has_attribute(blue_units[i],"SAM") or has_attribute(blue_units[i],"Armed Air Defence")) and 40000 or has_attribute(blue_units[i],"Planes") and 70000 or has_attribute(blue_units[i],"Helicopters") and 20000 or 80000,
              }
            end
          end
        end
        return seen
      end
    end

    function client_methods:picture()
      if self.pic_cool and ((_time() - self.pic_cool) < module_data.config.allow_picture_cooldown) then
        return
      end
      self.pic_cool = _time()
      client_buffer[1].msg.threats = self:build_picture()
    end

    function client_methods:proc()
      if #client_buffer < 1 then return false end
      self:picture()
      self.buff = JSON:encode(client_buffer[1])
      module_data.requests[tostring(client_buffer[1].idx)] = {goal = shallowCopy(client_buffer[1].msg.to), from = shallowCopy(client_buffer[1].msg.from)}
      if #client_buffer > 1 then table.remove(client_buffer, 1) else client_buffer = {} end
      return true
    end
  --

  local function getClient()
    if not client then
      client, c_errtry = SOC.tcp()
      if not client then
        _log("ASTAR client instance error (%s)", c_errtry)
      -- else
      --   _log("ASTAR client created OK.")
      end
    end
    return setmetatable({
      socket = client or {},
    }, {__index = client_methods})
  end; setmetatable(aiRouteClient, {__call = function(self) return getClient() end})
--

-- SEND
local function send_request(args)
  local from = args.point1 or args.base1 and Airbase.getByName(args.base1):getPoint()
  local goal = args.point2 or args.base2 and Airbase.getByName(args.base2):getPoint()
  if not from or not goal then return _log("ERROR ASTAR no routing details") end
  client_buffer[#client_buffer+1] = {
    idx = args.idx,
    msg = {
      to = {goal.x, goal.z},
      from = {from.x, from.z},
    },
  }
end -- send{ point1 = {}, base2 = {}, idx = 0 }

-- RECV
local function get_route(idx)
  if module_data.routes[idx] then
    return module_data.routes[idx]
  end
  _log("Could not find route!! Error in ASTAR, Skynet%s", idx)
end

aiRoute = {}

-- class manager
  local routine
  
  local route_co = function()
    local Client, Server
    local result, sock_err, bytes
    while true do
      -- socket objects
      if #client_buffer > 0 and not Client then Client = getClient() end
      if not Server then
        Server = getServer()
        Server.socket:setoption("tcp-nodelay", true)
        Server.socket:setoption("keepalive", true)
      end
      -- Server.socket:close()
      -- proc route requests
        if #client_buffer > 0 and Client:connect() and Client:proc() then
          result, sock_err, bytes = Client:send()
          if not result then
            _log("ASTAR Client send ERROR :: %s", sock_err)
          else
            _log("ASTAR sent through new request to Python")
          end
      -- get back results
        elseif #server_buffer > 0 or (module_data.rec_idx ~= module_data.req_idx) then
          if Server:recv() and Server:proc() then
            _log("ASTAR completed new route")
          end
          -- Server.socket:close()
        end
      --
      coroutine.yield()
    end
  end

  local function route_manager()
    timer.scheduleFunction( route_manager, nil, _time(module_data.config.manager_timer) )
    if not routine then
      routine = coroutine.create(route_co)
    end
    --
    if module_data.rec_idx ~= module_data.req_idx or #client_buffer > 0 or #server_buffer > 0 then
      if module_data.req_idx < 0 then
        module_data.rec_idx = 0
        module_data.req_idx = 0
      end
      local run, err =  coroutine.resume(routine)
      if not run then
        _log("ASTAR CO ERROR %s", err)
        routine = coroutine.create(route_co)
      end
    end
  end

  timer.scheduleFunction( route_manager, nil, _time(90) )
--

-- API
aiRoute.getAPI = function()
  return {
    get_route = get_route,
    send = send_request,
    data = function ()
      return module_data, client_buffer, server_buffer
    end,
    client = aiRouteClient,
    server = aiRouteServer,
  }
end