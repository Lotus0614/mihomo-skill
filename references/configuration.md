# Mihomo configuration guide

Consult this reference when creating, reviewing, or changing a `config.yaml`. For configuration areas not covered by this practical guide, read the bundled `offline-config.md`; do not assume network access.

## Configuration model

`mihomo -d <skill>/.mihomo -f <skill>/.mihomo/config.yaml` makes the skill-local `.mihomo` directory the HomeDir. Relative paths, including a provider's `path`, resolve below it.

The normal traffic flow is:

`listener (port / socks-port / mixed-port / redir-port / TUN) → rules → proxy group → direct proxy or proxy-provider node`.

Ask whether the user wants ordinary local HTTP/SOCKS proxying or TUN before creating a configuration. Do not enable `tun`, `allow-lan`, `external-controller: 0.0.0.0:…`, redirection ports, or firewall changes by default: each changes host/network exposure or needs elevated privileges.

## Baseline: local proxy with one subscription provider

Use this as a starting shape only after the user supplies a provider URL and desired secret. It listens locally, sends matched traffic through a selectable group, and falls back to `DIRECT` when selected.

```yaml
port: 7890
socks-port: 7891
allow-lan: false
mode: rule
log-level: info

external-controller: 127.0.0.1:9090
secret: "replace-with-a-unique-local-secret"

profile:
  store-selected: true
  store-fake-ip: true

dns:
  enable: true
  ipv6: false
  enhanced-mode: fake-ip
  fake-ip-range: 198.18.0.1/16
  default-nameserver:
    - 223.5.5.5
    - 1.1.1.1
  nameserver:
    - https://dns.alidns.com/dns-query
    - https://cloudflare-dns.com/dns-query

proxy-providers:
  subscription:
    type: http
    url: "https://provider.example/subscription"
    path: ./providers/subscription.yaml
    interval: 86400
    health-check:
      enable: true
      url: https://www.gstatic.com/generate_204
      interval: 300

proxy-groups:
  - name: PROXY
    type: select
    proxies:
      - DIRECT
    use:
      - subscription

rules:
  - MATCH,PROXY
```

The provider `path` must be unique. For HTTP providers, `url` and `type` are required; `interval` is seconds. Provider content may be YAML, URI, or base64 URI content, but one provider file must not mix those formats.

Do not copy the placeholder URL or secret into a live configuration. Keep URLs carrying credentials and the downloaded provider file private.

## Routing, groups, nodes, and DNS

- Add policy groups for a user-facing routing choice. `select` is manual selection; `url-test`, `fallback`, and `load-balance` perform different health-based selection strategies. A group may reference explicit names in `proxies` and provider node sets in `use`.
- Add rules in first-match order and end with one `MATCH,<group-or-proxy>` rule. Create rule providers only when the user selects a particular maintained rule source; do not silently add third-party rule URLs.
- Put a user-supplied static node in top-level `proxies`; every node needs a unique `name`, `type`, `server`, and `port`, plus protocol-specific fields. Confirm the protocol before creating it.
- DNS choice affects routing correctness. For local-only usage, begin with explicit `default-nameserver` and encrypted `nameserver` values. Discuss `fake-ip` versus `redir-host`, IPv6, `respect-rules`, split-DNS, and any DNS bootstrap restrictions before changing defaults.

## Safe edit and validation workflow

1. Back up an existing config before a material change and preserve secrets verbatim.
2. Make the smallest requested change; never log sensitive fields.
3. Validate with `mihomo -t -d <skill>/.mihomo -f <skill>/.mihomo/config.yaml` before restarting.
4. Start in the foreground first, check the configured listener and controller locally, then update providers or use the controller API only after the core is healthy.

`-t` validates configuration; it does not prove that a remote provider URL, node credential, or routing policy will work. Report those separately.
