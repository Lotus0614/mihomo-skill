# Offline configuration reference

This is a local, task-oriented map of mihomo configuration. Read the section that matches the request, preserve unrelated keys, and use `mihomo -t -d <skill>/.mihomo -f <config>` after edits. Protocol-specific credentials are never invented: request them from the user.

## Top-level sections

| Section | Purpose | Key decisions before editing |
| --- | --- | --- |
| Global | Ports, mode, logging, controller, Geo data, profile persistence | local-only versus LAN exposure; controller secret; port conflicts |
| DNS | Resolver selection, fake-IP/redir-host, hosts, split-DNS | IPv6, bootstrap DNS, whether DNS follows rules |
| Sniffer | Reconstruct host names from HTTP/TLS/QUIC traffic | ports, override behavior, domains to skip |
| Inbounds | HTTP/SOCKS/mixed ports, redir, TProxy, TUN, listeners | whether privileged/network changes are authorized |
| Proxies | Static outbound nodes and shared TLS/transport options | exact protocol and credentials supplied by user |
| Proxy providers | HTTP/file/inline node sets | URL trust, update interval, local cache path |
| Proxy groups | Manual/automatic selection and chaining | node grouping and health-test URL |
| Rules | First-match routing, rule providers, sub-rules | intended route policy and rule-source trust |
| Rule providers | HTTP/file/inline classical/domain/IPCIDR rules | source format, path, update cadence |
| Tunnels/NTP/experimental | Fixed forwarding, time service, feature flags | explicit need and compatibility risk |

## Global settings

- Proxy listeners: `port` (HTTP), `socks-port`, `mixed-port`, `redir-port`, and `tproxy-port`. Set only the listener requested; `mixed-port` serves HTTP and SOCKS together.
- Access and routing: `allow-lan`, `bind-address`, `mode` (`rule`, `global`, or `direct`), `ipv6`, `unified-delay`, and `tcp-concurrent`.
- Logs/profile: `log-level`, `profile.store-selected`, and `profile.store-fake-ip`. Persist selection only when the user wants choices to survive restart.
- Controller/UI: `external-controller`, `secret`, `external-controller-cors`, `external-controller-tls`, `external-ui`, and `external-ui-name`. Bind controller to loopback unless remote control is explicitly authorized.
- Geo data: `geodata-mode`, `geo-auto-update`, `geo-update-interval`, and `geox-url`. Updating remote Geo assets is a network action.

## DNS and sniffer

- DNS controls include `enable`, `listen`, `ipv6`, `enhanced-mode` (`fake-ip` or `redir-host`), `fake-ip-range`, `fake-ip-filter`, `default-nameserver`, `nameserver`, `fallback`, `nameserver-policy`, `proxy-server-nameserver`, `direct-nameserver`, and `respect-rules`.
- `default-nameserver` resolves DNS-server host names. `proxy-server-nameserver` resolves proxy-server domains and prevents bootstrapping loops. Do not set `respect-rules` without considering those dependencies.
- `hosts` adds static hostname mappings. DNS nameserver values may be plain IP/UDP/TCP, TLS, DoH, DoQ, or DHCP forms; select only a form the user/network supports.
- `sniffer.enable` enables protocol sniffing. `sniff` configures HTTP/TLS/QUIC ports and destination override; `skip-domain` excludes sensitive or incompatible domains. Sniffing changes how IP traffic can match domain rules.

## Inbounds and listeners

- Legacy ports provide HTTP, SOCKS, mixed, redirect, and TProxy inbounds. They are the simplest choice for local proxy applications or router integration.
- `tun` creates a virtual interface. Important options include `enable`, `device`, `stack`, `dns-hijack`, `auto-route`, `auto-redirect`, `auto-detect-interface`, `strict-route`, `route-address`, `route-exclude-address`, and include/exclude UID/package controls. It can require administrator privileges and alter the host route table.
- `listeners` declares named inbounds. Supported families include HTTP, SOCKS, mixed, redirect, TProxy, TUN, Shadowsocks, VMess, VLESS, Trojan, AnyTLS, Mieru, Sudoku, TUIC, ShadowQUIC, Hysteria2, TrustTunnel, tunnel, and Snell. Every listener needs its type, bind/listen address and port; protocol listeners also require their authentication/transport settings.

## Outbound proxies

- Every `proxies` item has a unique `name` and `type`. Most remote protocols also require `server` and `port`; use `udp`, `ip-version`, `interface-name`, `routing-mark`, `tfo`, `mptcp`, and `dialer-proxy` only when needed.
- Built-in outbounds are `DIRECT`, `REJECT`, `REJECT-DROP`, `PASS`, `COMPATIBLE`, `dns`, and `rematch`. They do not take remote credentials.
- Supported remote families include HTTP, SOCKS, Shadowsocks, ShadowsocksR, Snell, VMess, VLESS, Trojan, AnyTLS, Mieru, Sudoku, Hysteria, Hysteria2, TUIC, ShadowQUIC, WireGuard, EasyTier, Tailscale, SSH, MASQUE, TrustTunnel, ZeroTier, and OpenVPN.
- TLS-capable protocols share choices such as `tls`, `servername`, `alpn`, `skip-cert-verify`, client fingerprint, certificate pinning, and ECH where applicable. Transport-capable protocols can use TCP, WebSocket, gRPC, HTTP/2, HTTP upgrade, XHTTP, QUIC, or protocol-specific transports. Do not combine fields from another protocol merely because names look similar.
- `dialer-proxy` makes one outbound establish its underlying connection through another proxy/group. Use it instead of deprecated relay patterns where the requested design is a chained outbound.

## Providers, groups, and rules

- A proxy provider is `http`, `file`, or `inline`. HTTP needs `url`; cache with a unique `path`; update with `interval`; optionally configure `proxy`, headers, `size-limit`, filtering, overrides, and `health-check`. A provider's content is exactly one of YAML, URI, or base64 URI forms.
- Group types are `select`, `url-test`, `fallback`, `load-balance`, and relay/compatibility forms. Use `proxies` for named items and `use` for provider names. Health-oriented groups use `url`, `interval`, `timeout`, `lazy`, and `expected-status`; filters apply to provider/included nodes.
- Rules are evaluated in order. Common rule families include domain, domain-suffix, domain-keyword, GEOIP, GEOSITE, IP-CIDR, IP-ASN, SRC-IP-CIDR, SRC-PORT, DST-PORT, process, network, inbound, rule-set, and `MATCH`. Route each rule to a proxy/group or built-in action.
- Rule providers are `http`, `file`, or `inline` with `behavior` such as `classical`, `domain`, or `ipcidr`. Their cache path must be safe under HomeDir unless the process explicitly receives `SAFE_PATHS`.

## Other sections

- `tunnels` creates fixed TCP/UDP forwarding; define network type, local address/port, target, and proxy action deliberately.
- `ntp` enables mihomo's NTP client/server behavior. Confirm the time source and listen exposure before enabling it.
- `experimental` houses features whose compatibility may change. Do not enable an experimental key without a stated user requirement and version check.
