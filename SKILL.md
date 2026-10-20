---
name: mihomo
description: Install, configure, run, validate, and troubleshoot the mihomo proxy core. Use for mihomo/Clash.Meta configuration, proxy providers or subscriptions, local proxy operation, and core diagnostics; not for unrelated VPN clients.
---

# Mihomo

Treat mihomo as one system: configuration defines traffic behavior, the core realizes it, and the controller observes or changes the running state. Start from the user's intent—not from a fixed document or command sequence—and use the local references only to resolve the relevant details.

Keep all local state inside this skill at `.mihomo/`: the default `config.yaml`, provider caches, logs, PID/runtime files, and the per-platform core in `.mihomo/bin/<os>-<arch>/`. Do not add the core to `PATH` or download it just because this skill was invoked.

In shell examples, `MIHOMO_SKILL_DIR` means the absolute directory containing this `SKILL.md`. Resolve it from the installed skill location; do not assume a particular Codex home directory. For manual terminal use, set it once with `export MIHOMO_SKILL_DIR="/absolute/path/to/mihomo"`.

## Daily commands first

For ordinary lifecycle and subscription work, use `scripts/mihomo_ctl.py` instead of editing YAML or composing controller requests. It obtains the configured controller secret from `MIHOMO_SECRET` or the local `config.yaml` without printing it.

```sh
# Validate, start, inspect, then stop
python "$MIHOMO_SKILL_DIR/scripts/mihomo_ctl.py" init
python "$MIHOMO_SKILL_DIR/scripts/mihomo_ctl.py" validate
python "$MIHOMO_SKILL_DIR/scripts/mihomo_ctl.py" start
python "$MIHOMO_SKILL_DIR/scripts/mihomo_ctl.py" status
python "$MIHOMO_SKILL_DIR/scripts/mihomo_ctl.py" stop

# Providers and nodes; refresh and latency-test one provider
python "$MIHOMO_SKILL_DIR/scripts/mihomo_ctl.py" providers
python "$MIHOMO_SKILL_DIR/scripts/mihomo_ctl.py" nodes subscription
python "$MIHOMO_SKILL_DIR/scripts/mihomo_ctl.py" speedtest subscription

# Switch a selectable group deliberately
python "$MIHOMO_SKILL_DIR/scripts/mihomo_ctl.py" select PROXY 'node name'

# Temporarily toggle TUN on the running core
python "$MIHOMO_SKILL_DIR/scripts/mihomo_ctl.py" tun on
python "$MIHOMO_SKILL_DIR/scripts/mihomo_ctl.py" tun off
```

`init` creates a configuration only when none exists; `start` invokes it automatically on first use, then validates before launching and records a PID/log under the skill's `.mihomo/` directory. The first-use configuration enables local HTTP on `127.0.0.1:7890` and SOCKS on `127.0.0.1:7891`, keeps LAN disabled, and creates a random local controller secret. Existing configuration is never overwritten. If no `proxy-providers` or static `proxies` exist, `start` stops before launch; ask the user for a subscription URL or node configuration rather than silently running `DIRECT`. `stop` only targets that PID. `status` queries the live controller's read-only `/version` and `/configs` endpoints, returning JSON with `running`, core version, and the active effective configuration; it does not use the PID file as a health signal. It needs controller address and secret, obtained from `--controller`/`MIHOMO_SECRET` when supplied or otherwise from the local config. `speedtest` refreshes the named provider and triggers its health checks, so it is a network-affecting action. `tun on|off` uses the local controller to change the running instance only; it can alter routes and DNS, may need elevated privileges, and resets after restart. Obtain explicit user authorization before `tun on`. `ensure_mihomo.py` defaults to the configured GitHub mirror for release-asset transfer, falls back to the official asset only when transport fails, and always verifies GitHub's release SHA-256. Use `--direct` only when explicitly requested or when diagnosing mirror transport.

## Choose the working path

- **New setup or a new subscription:** establish the requested listener style (local HTTP/SOCKS, mixed port, TUN, or a server inbound), routing behavior, DNS behavior, and provider/node source. If the core/config exists but no proxy source is configured, explicitly ask the user for a subscription URL or static node configuration before starting it. Build the smallest configuration that meets those choices.
- **Existing configuration change:** inspect the actual YAML first; identify which traffic stage changes (listener, DNS, proxy/provider, group, rule, or controller), then preserve all unrelated settings.
- **Run, test, or diagnose:** first determine whether the configuration already validates; then run foreground, inspect logs/listeners, and only use the controller after it is healthy.
- **Controller/API request:** inspect the configured controller binding and authentication, then select the least invasive endpoint. Read-only inspection does not justify live mutations such as reload, restart, switching a group, provider refresh, cache flush, or connection termination.

When a core is genuinely required, `mihomo_ctl.py start` or `validate` will ensure it automatically. Use `scripts/ensure_mihomo.py --print-path` to inspect without downloading, and use `--force` only for an explicitly requested refresh.

## Configuration and subscriptions

Work offline-first. The core configuration relationship is: inbound listener → rules → proxy group → proxy or provider node. Keep it explicit in the generated YAML so a later API inspection has meaningful group names to operate on.

For a new subscription configuration, [configuration.md](references/configuration.md) provides a coherent baseline where the provider cache, a selectable `PROXY` group, DNS, controller, and final `MATCH` rule agree with the skill-local `.mihomo` HomeDir. Adapt that baseline rather than assembling unrelated snippets. Before enabling TUN, LAN listening, external controller exposure, redirect/TProxy ports, or remote UI, explain the system/network impact and obtain authorization.

Use [offline-config.md](references/offline-config.md) as a field map when the task needs a different listener, a particular outbound protocol, a health strategy, rule provider, DNS mode, tunnel, NTP, or experimental option. It is lookup material, not a checklist: read only the relevant section and do not add optional features the user did not request.

For remote subscriptions, prefer an HTTP `proxy-provider` with a unique cache path below the skill's `.mihomo`, then reference it through a named group. A bare subscription URL does not establish its format, whether conversion is allowed, or the intended rule policy. Preserve sensitive URLs and provider contents.

After a material configuration change, validate before running:

```sh
MIHOMO_BIN="$(python "$MIHOMO_SKILL_DIR/scripts/ensure_mihomo.py" --ensure)"
"$MIHOMO_BIN" -t -d "$MIHOMO_SKILL_DIR/.mihomo" -f "$MIHOMO_SKILL_DIR/.mihomo/config.yaml"
```

If the user chose a non-default configuration path, substitute it in the validation command.

## Running and diagnosing

Default to foreground operation. The normal evidence chain is: validate the file, start the core with the same HomeDir and config path, confirm the requested listener/controller is bound, then inspect the smallest relevant signal (log, provider state, group selection, rule list, or delay). Use a log file only when requested, preserve the process ID, and stop it gracefully before replacing a running instance. Do not register launchd, systemd, or Windows services unless explicitly asked.

```sh
MIHOMO_BIN="$(python "$MIHOMO_SKILL_DIR/scripts/ensure_mihomo.py" --ensure)"
"$MIHOMO_BIN" -d "$MIHOMO_SKILL_DIR/.mihomo" -f "$MIHOMO_SKILL_DIR/.mihomo/config.yaml"
```

For failures, start with `-t`. A parse failure means fix YAML/schema; a provider failure means inspect provider reachability and format; a listener failure means inspect port/bind conflicts; a traffic failure means inspect group selection, rule order, DNS, then node delay. Treat TUN mode, transparent proxying, firewall changes, and privileged ports as privileged host changes: explain the impact and obtain authorization before using elevated privileges or changing system networking.

## Advanced configuration and controller operations

Use direct YAML changes or `scripts/mihomo_api.py` only for work that `mihomo_ctl.py` does not cover: TUN/listeners, DNS, protocols, routing rules, unusual provider options, live config patching, streams, connection management, cache control, and upgrades. Confirm the live impact before mutating configuration or traffic.

Use the external controller only after confirming it is loopback-bound or otherwise deliberately secured, and that a secret is configured. Never expose its secret in commands, logs, or user-facing output. `mihomo_api.py` URL-encodes proxy/group names and does not accept a secret CLI argument.

Use [api.md](references/api.md) for normal controller tasks: inspect version/config/proxies, refresh a provider, test delay, and intentionally switch a group. Use [offline-api.md](references/offline-api.md) only when selecting a less-common endpoint or a streaming diagnostic. Interpret endpoint choice in context: `/proxies` diagnoses selection, `/providers/proxies` diagnoses subscriptions, `/rules` diagnoses routing, and `/connections` diagnoses live traffic.

Never use reload/restart/upgrade, configuration patching, cache flush, connection deletion, rule disabling, or provider refresh as a speculative fix. State the live impact and obtain authorization first. Treat undocumented or version-dependent behavior as unknown rather than browsing automatically.
