# Mihomo external-controller API

Use this reference only after mihomo is running with an `external-controller` and a non-empty `secret`. The bundled `offline-api.md` is the complete local endpoint inventory.

In the commands below, set `MIHOMO_SKILL_DIR` to the absolute directory containing the installed mihomo skill.

## Enable securely

```yaml
external-controller: 127.0.0.1:9090
secret: "a-unique-secret-kept-out-of-source-control"
```

Keep the controller bound to loopback by default. Binding it to `0.0.0.0` exposes a control plane; only do so after the user has explicitly approved the network exposure, firewall policy, TLS/reverse proxy design, CORS origins, and strong secret handling. Unix sockets and Windows named pipes do not verify `secret`, so they are not a shortcut around local access controls.

HTTP requests authenticate with `Authorization: Bearer <secret>`. Store the secret in a shell environment variable or a protected secret store; never pass it as a positional argument, commit it, or echo it.

```sh
export MIHOMO_CONTROLLER='http://127.0.0.1:9090'
export MIHOMO_SECRET='…'
python "$MIHOMO_SKILL_DIR/scripts/mihomo_api.py" /version
```

## Common REST operations

The bundled helper prints the JSON response and accepts `--method` plus `--json` for mutation requests. Endpoint path components must be URL encoded; the helper does that with `--path-part` where necessary.

```sh
# Core version, effective configuration, policies, and current rules
python "$MIHOMO_SKILL_DIR/scripts/mihomo_api.py" /version
python "$MIHOMO_SKILL_DIR/scripts/mihomo_api.py" /configs
python "$MIHOMO_SKILL_DIR/scripts/mihomo_api.py" /proxies
python "$MIHOMO_SKILL_DIR/scripts/mihomo_api.py" /rules

# Refresh a provider and trigger its health checks
python "$MIHOMO_SKILL_DIR/scripts/mihomo_api.py" --method PUT --path-part subscription /providers/proxies
python "$MIHOMO_SKILL_DIR/scripts/mihomo_api.py" --path-part subscription /providers/proxies --suffix /healthcheck

# Test one proxy: URL and timeout are query parameters
python "$MIHOMO_SKILL_DIR/scripts/mihomo_api.py" --path-part 'node name' --query 'url=https://www.gstatic.com/generate_204' --query timeout=5000 /proxies --suffix /delay

# Change a Selector group's active member; this is a runtime mutation.
python "$MIHOMO_SKILL_DIR/scripts/mihomo_api.py" --method PUT --path-part PROXY --json '{"name":"node name"}' /proxies
```

`GET /proxies` reports proxies and policy groups; `PUT /proxies/{group}` selects a member. `GET /proxies/{name}/delay` measures latency. `GET|PUT /providers/proxies/{name}` gets or refreshes a proxy provider. `GET /rules` returns active rules.

## Operations requiring extra caution

- `PATCH /configs` changes selected basic runtime configuration; `PUT /configs?force=true` reloads configuration. Prefer an edited file plus `mihomo -t` and an explicit restart unless the user specifically wants a live API update.
- `mihomo_ctl.py tun on|off` applies `PATCH /configs` with `{"tun":{"enable":true|false}}`. It changes only the running core; use a deliberate `tun:` configuration edit when the setting must survive restart.
- `POST /cache/dns/flush` and `/cache/fakeip/flush` clear runtime caches. `DELETE /connections` terminates all current connections. `POST /restart`, `/upgrade`, and `/upgrade/geo` are disruptive or change installed/runtime state; state the impact and obtain user authorization first.
- `/logs`, `/traffic`, and `/memory` are WebSocket endpoints for streaming diagnostics. A browser WebSocket may authenticate using `?token=<secret>` because it cannot set HTTP headers; do not put that URL in logs, screenshots, history, or shared output.

For any endpoint absent above, look it up in the official API documentation instead of assuming Clash-compatible variants are implemented identically.
