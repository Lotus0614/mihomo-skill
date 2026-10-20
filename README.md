# mihomo skill

用 mihomo（Clash.Meta）内核跑本地代理的 Agent 技能包：自动下载内核、生成配置、启动代理，并提供节点测速、切换和诊断工具。纯 Python 标准库，无第三方依赖。

[简体中文](#简体中文) · [English](#english)

---

## 简体中文

### 快速开始

```sh
export MIHOMO_SKILL_DIR="/absolute/path/to/mihomo-skill"

python "$MIHOMO_SKILL_DIR/scripts/mihomo_ctl.py" init      # 生成配置：HTTP 7890 / SOCKS 7891
python "$MIHOMO_SKILL_DIR/scripts/mihomo_ctl.py" start     # 首次自动下载内核并启动
python "$MIHOMO_SKILL_DIR/scripts/mihomo_ctl.py" status    # 查看内核版本与生效配置
```

启动后验证代理是否可用：

```sh
curl -x http://127.0.0.1:7890 https://www.gstatic.com/generate_204
```

环境要求：Python 3.9+；首次运行需要能访问 GitHub 下载内核。

### 配置订阅

默认配置里没有节点，所以 `start` 会提示需要先配置订阅，不会静默走直连。把订阅地址填进 `.mihomo/config.yaml`：

```yaml
proxy-providers:
  subscription:
    type: http
    url: "https://your-subscription-url"
    path: ./providers/subscription.yaml
    interval: 86400
```

再执行 `start`，代理即可用。

### 日常命令

```sh
python "$MIHOMO_SKILL_DIR/scripts/mihomo_ctl.py" validate              # 检查配置有没有写错
python "$MIHOMO_SKILL_DIR/scripts/mihomo_ctl.py" providers             # 列出订阅
python "$MIHOMO_SKILL_DIR/scripts/mihomo_ctl.py" nodes subscription    # 列出节点
python "$MIHOMO_SKILL_DIR/scripts/mihomo_ctl.py" speedtest subscription  # 刷新订阅并测延迟
python "$MIHOMO_SKILL_DIR/scripts/mihomo_ctl.py" select PROXY 'node name'
python "$MIHOMO_SKILL_DIR/scripts/mihomo_ctl.py" logs --tail 80
python "$MIHOMO_SKILL_DIR/scripts/mihomo_ctl.py" stop
```

### 更细的配置

TUN、DNS、分流规则、各类协议、rule-provider 这些，`SKILL.md` 之外还有 `references/` 里的配置与 controller API 手册可以查；也可以直接用 `scripts/mihomo_api.py` 调内核的 REST 接口。

社区维护，非官方项目。

---

## English

An agent skill for running a local proxy with the mihomo (Clash.Meta) core: it downloads the core, writes a config, starts the proxy, and gives you node latency tests, group switching, and diagnostics. Python standard library only.

### Quick start

```sh
export MIHOMO_SKILL_DIR="/absolute/path/to/mihomo-skill"

python "$MIHOMO_SKILL_DIR/scripts/mihomo_ctl.py" init      # HTTP 7890 / SOCKS 7891
python "$MIHOMO_SKILL_DIR/scripts/mihomo_ctl.py" start     # downloads the core on first run
python "$MIHOMO_SKILL_DIR/scripts/mihomo_ctl.py" status    # core version and effective config
```

Check that the proxy works:

```sh
curl -x http://127.0.0.1:7890 https://www.gstatic.com/generate_204
```

Requires Python 3.9+ and GitHub access on the first run.

### Add your subscription

The default config has no nodes, so `start` tells you to configure a subscription instead of silently proxying nothing. Put your URL into `.mihomo/config.yaml`:

```yaml
proxy-providers:
  subscription:
    type: http
    url: "https://your-subscription-url"
    path: ./providers/subscription.yaml
    interval: 86400
```

Then run `start` again.

### Daily commands

```sh
python "$MIHOMO_SKILL_DIR/scripts/mihomo_ctl.py" validate              # check the config
python "$MIHOMO_SKILL_DIR/scripts/mihomo_ctl.py" providers             # list providers
python "$MIHOMO_SKILL_DIR/scripts/mihomo_ctl.py" nodes subscription    # list nodes
python "$MIHOMO_SKILL_DIR/scripts/mihomo_ctl.py" speedtest subscription  # refresh and measure latency
python "$MIHOMO_SKILL_DIR/scripts/mihomo_ctl.py" select PROXY 'node name'
python "$MIHOMO_SKILL_DIR/scripts/mihomo_ctl.py" logs --tail 80
python "$MIHOMO_SKILL_DIR/scripts/mihomo_ctl.py" stop
```

### Going further

For TUN, DNS, routing rules, protocols, and rule-providers, `references/` holds the configuration and controller API manuals; `scripts/mihomo_api.py` talks to the core's REST API directly.

Community-maintained, unofficial.
