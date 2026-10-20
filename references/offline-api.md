# Offline external-controller API reference

Base URL is the configured controller, normally `http://127.0.0.1:9090`. For HTTP APIs send `Authorization: Bearer <secret>`. The API helper reads `MIHOMO_SECRET`; never place secrets in command history. `GET` is read-only unless marked otherwise; mutations require user authorization when disruptive.

## Streaming and diagnostics

| Endpoint | Method | Purpose |
| --- | --- | --- |
| `/logs` | GET / WS | Log stream; optional `level=info|warning|error|debug`, `format=structured` |
| `/traffic` | GET / WS | Per-second up/down rates and cumulative byte totals |
| `/memory` | GET / WS | Per-second current memory usage |
| `/version` | GET | Core version and Meta-build status |
| `/debug/gc` | POST | Trigger garbage collection; diagnostic mutation |
| `/debug/pprof` | GET | Profiling data; restrict to trusted local diagnostics |

For browser WebSocket connections, a `token` query parameter may be used because browsers cannot set Authorization headers. Treat that URL as a secret.

## Runtime configuration, cache, and updates

| Endpoint | Method | Meaning / impact |
| --- | --- | --- |
| `/configs` | GET | Read active basic configuration |
| `/configs` | PUT `?force=true` | Reload config from path/payload; disruptive |
| `/configs` | PATCH | Update basic runtime keys such as ports/mode; mutation |
| `/configs/geo` | POST | Update Geo database from path/payload |
| `/restart` | POST | Restart core; disconnects traffic |
| `/cache/dns/flush` | POST | Clear DNS cache |
| `/cache/fakeip/flush` | POST | Clear fake-IP cache |
| `/upgrade` | POST | Upgrade core; may take `channel` and `force` |
| `/upgrade/ui` | POST | Fetch/update configured external UI |
| `/upgrade/geo` | POST | Update Geo database |

Path-based payloads outside HomeDir require the process `SAFE_PATHS` environment variable. Prefer writing a config under the skill-local `.mihomo` HomeDir, validating it, then restarting explicitly rather than using a path reload automatically.

## Groups and proxies

| Endpoint | Method | Meaning |
| --- | --- | --- |
| `/group` | GET | All policy groups |
| `/group/{name}` | GET | One policy group |
| `/group/{name}/delay` | GET | Test members; query `url`, `timeout`, optional `expected` |
| `/proxies` | GET | All proxies and policy groups |
| `/proxies/{name}` | GET | One proxy/group |
| `/proxies/{group}` | PUT | Select member with JSON `{"name":"member"}` |
| `/proxies/{name}` | DELETE | Clear fixed selection for applicable automatic group |
| `/proxies/{name}/delay` | GET | Test one proxy; query `url`, `timeout`, optional `expected` |

Names in URL paths must be URL encoded. Proxy objects report name/type/capabilities/liveness/history and provider origin; policy groups also report members and current selection.

## Providers, rules, connections, DNS, and storage

| Endpoint | Method | Meaning |
| --- | --- | --- |
| `/providers/proxies` | GET | All proxy providers |
| `/providers/proxies/{provider}` | GET | One proxy provider |
| `/providers/proxies/{provider}` | PUT | Refresh/update one provider |
| `/providers/proxies/{provider}/healthcheck` | GET | Run provider health check |
| `/providers/proxies/{provider}/{proxy}` | GET | One provider proxy |
| `/providers/proxies/{provider}/{proxy}/healthcheck` | GET | Delay-test one provider proxy |
| `/rules` | GET | Active routing rules |
| `/rules/disable` | PATCH | Temporarily disable rule indexes; reset on restart |
| `/providers/rules` | GET | All rule providers |
| `/providers/rules/{provider}` | GET / PUT | Inspect or refresh a rule provider |
| `/connections` | GET | Connections and upload/download totals |
| `/connections` | DELETE | Close all connections |
| `/connections/{id}` | DELETE | Close one connection |
| `/dns/query` | GET | Perform controller DNS query |
| `/storage/{key}` | GET / PUT / DELETE | Read/write/delete persistent storage value |

Provider refresh and health checks generate network traffic. Connection deletion, rule disabling, config reloads, upgrades, cache flushes, and restarts change live behavior; describe the consequence before invoking them.
