#!/usr/bin/env python3
"""Build the static, board-specific hardware validation site from public evidence."""
import hashlib
import html
import json
import shutil
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OUT = HERE / 'dist'
URL = 'https://ymbot-hardware-test.pages.dev'
REPO = 'https://github.com/lizi-learn/ymbot-usb-canfd'
DATE = '2026-10-30'
E = html.escape
USB = json.loads((ROOT/'evidence/continuous-fd5m-20261030.json').read_text())
CHANNELS = json.loads((ROOT/'evidence/channels-20261030.json').read_text())
SMOKE = json.loads((ROOT/'evidence/published-cli-smoke-20261030.json').read_text())
FIVE = json.loads((HERE/'data/5io-snapshot.json').read_text())
FIVE_BASE = FIVE['source_repository']+'/blob/'+FIVE['source_commit']+'/'


def badge(text, color='blue'):
    return f'<span class="badge {color}">{E(text)}</span>'


def diagram(kind):
    if kind == 'usb':
        return '<div class="bus-diagram" role="img" aria-label="USB连接三颗独立STM32G431，分别驱动CAN0、CAN1和CAN2"><span class="connector">USB</span><i class="wire"></i><div class="processor">STM32G431<small>独立控制器 × 3</small></div><i class="wire"></i><div class="ports"><span>CAN0</span><span>CAN1</span><span>CAN2</span></div></div>'
    return '<div class="bus-diagram" role="img" aria-label="RK3588核心板通过5IO底板连接两路板载CAN和两路RS485"><span class="connector">核心板</span><i class="wire"></i><div class="processor">RK3588<small>5IO / 自研底板</small></div><i class="wire"></i><div class="ports"><span>CAN × 2</span><span>RS485 × 2</span></div></div>'


def section(id, number, title, body, subtitle=''):
    return f'<section class="section" id="{id}"><div class="section-head"><div><p class="section-kicker">{E(number)}</p><h2>{E(title)}</h2></div><p>{E(subtitle)}</p></div>{body}</section>'


def table(headers, rows, caption):
    return '<div class="table-scroll" tabindex="0" role="region" aria-label="'+E(caption)+'"><table class="compare"><caption class="sr-only">'+E(caption)+'</caption><thead><tr>'+''.join('<th scope="col">'+E(x)+'</th>' for x in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+x+'</td>' for x in row)+'</tr>' for row in rows)+'</tbody></table></div>'


def code(id, title, content):
    return f'<div class="code-panel"><div class="code-header"><span>{E(title)}</span><button class="copy" data-copy="{id}" type="button">复制命令</button></div><pre><code id="{id}">{E(content)}</code></pre></div>'


def metric(title, value, note):
    return f'<div class="metric"><dt>{E(title)}</dt><dd>{E(value)}</dd><p>{E(note)}</p></div>'


def links():
    return f'<a href="{REPO}">USB CAN GitHub ↗</a><a href="{FIVE["source_repository"]}">5IO GitHub ↗</a>'


def shell(path, title, body, description):
    nav = ''.join(f'<a href="{p}"'+(' aria-current="page"' if p==path else '')+f'>{name}</a>' for p,name in [('/', '验证总览'),('/usb-canfd/', '自研 USB CAN'),('/5io/', '5IO 开发板'),('/method/', '测试口径')])
    return f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{E(title)} · YMBOT 硬件验证</title><meta name="description" content="{E(description)}"><link rel="canonical" href="{URL}{path}"><meta name="theme-color" content="#2255ed"><link rel="icon" href="/assets/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="/assets/style.css"><script defer src="/assets/app.js"></script></head>
<body><a href="#main" class="skip">跳到正文</a><header><div class="wrap header-inner"><a class="brand" href="/" aria-label="YMBOT 硬件验证首页"><span class="brand-icon">Y</span><span><b>YMBOT</b><small>HARDWARE VALIDATION</small></span></a><nav class="site-nav" id="site-nav" aria-label="主导航">{nav}</nav><a class="header-github" href="{REPO}">GitHub ↗</a><button class="menu-toggle" type="button" aria-label="展开导航" aria-controls="site-nav" aria-expanded="false">☰</button></div></header>
<main class="wrap" id="main">{body}</main><div class="wrap"><footer class="footer"><div>YMBOT 硬件验证 / 两块板，独立记录<br>实测快照更新于 {DATE} · 静态证据站点</div><div>{links()}<br><a href="https://ymbot-5io-wiki.pages.dev/">5IO 系统优化 Wiki ↗</a> · <a href="/method/">结果与测量口径</a></div></footer></div><div class="sr-only" role="status" id="copy-status"></div></body></html>'''


def home():
    hero = '''<section class="hero"><div><div class="eyebrow">HARDWARE VALIDATION / 硬件验证</div><h1>选对板卡，<br>再看<em>验证结果。</em></h1><p class="hero-copy">自研 USB CAN 板与 5IO 开发板，分别记录驱动、固件、测试条件和收发结果。<br>同样写着 CAN FD 5M，验证对象与结论各有归属。</p><div class="hero-meta"><span>02 块板卡</span><span>物理收发记录</span><span>更新 2026.10.30</span></div></div><aside class="hero-side"><strong>1M / 5M</strong><b>仲裁段 / FD 数据段</b><p>配置位速率、应用吞吐、稳定性<br>分别衡量，分别给出证据。</p><a class="small" href="/method/">先读懂测试口径 →</a></aside></section>'''
    cards = f'''<div class="board-grid"><article class="board-card featured"><div class="board-top"><span class="board-index">BOARD 01 / USB-CAN</span>{badge('最新 · 2026.10.30')}</div><h3>自研 USB CAN 板</h3><p class="board-sub">CANable 2.0 硬件方案 · STM32G431 × 3<br>独立外接板 / SLCAN FD 固件与测试工具</p><div class="board-visual">{diagram('usb')}</div><div class="board-result"><p class="result-heading">CAN0 ↔ CAN1：FD 5M 本轮收发通过</p><p class="result-copy">64 字节连续收发，143,076 帧全部收到。CAN2 已刷写并启动，尚未接线验证。</p></div><dl class="card-facts"><div><dt>数据段配置</dt><dd>5 Mbit/s</dd></div><div><dt>最长同时双向窗口</dt><dd>60 秒</dd></div></dl><div class="card-bottom"><a href="/usb-canfd/">查看自研 CAN 板验证 →</a><span>满载 / 长时稳定性待测</span></div></article>
<article class="board-card"><div class="board-top"><span class="board-index">BOARD 02 / 5IO</span>{badge('历史 · 2026.10.25','gray')}</div><h3>5IO 开发板</h3><p class="board-sub">RK3588 · LBM5-DIBAN-V01A 自研底板<br>板载 CAN / Linux 6.1 回移驱动</p><div class="board-visual">{diagram('5io')}</div><div class="board-result"><p class="result-heading">FD 5M：30 分钟严格验收未通过</p><p class="result-copy">30 分钟压测及 30 秒基线共收齐 12,386,944 帧；仍有总线与 RX FIFO 异常。</p></div><dl class="card-facts"><div><dt>默认运行配置</dt><dd>Classic 1M</dd></div><div><dt>FD 持续测试</dt><dd>30 分钟</dd></div></dl><div class="card-bottom"><a href="/5io/">查看 5IO 独立记录 →</a><span>不套用 USB CAN 结果</span></div></article></div>'''
    compare = table(['比较项','自研 USB CAN 板','5IO 开发板'],[
        ('硬件与连接','STM32G431 × 3，经 USB 外接','RK3588 核心板 + LBM5-DIBAN-V01A 底板'),
        ('驱动 / 固件','CANable 上游固件 <code>b158aa7</code><br>本项目提供 Linux 刷写与验证工具','Linux 上游 CAN 驱动回移到 6.1<br>本项目提供 BSP / 板级适配'),
        ('主机接口','USB CDC / <code>ttyACM*</code> / SLCAN FD','SocketCAN / <code>can0</code>、<code>can1</code>'),
        ('FD 5M 结论',badge('本轮物理收发通过','green')+'<br>未达满载，未完成长时验收',badge('30 分钟严格验收失败','amber')+'<br>收齐帧仍有总线 / FIFO 错误'),
        ('待补验证','CAN2 对端收发；总线满载；更长时间测试','总线 / FIFO 异常定位；长线与多节点验证')
    ],'两块不同板卡的配置与验证对比')
    method = '''<div class="method-grid"><div class="panel"><h3>5M 具体发生在哪一段？</h3><p>开启 BRS 后，FD 帧的数据阶段切换到 5M；应用有效载荷还受帧开销、USB 协议与程序调度影响。</p><div class="phase" aria-label="仲裁阶段1M，FD数据阶段5M，随后结束和应答"><span>仲裁<small>1 Mbit/s</small></span><span class="fast">FD 数据 · 最多 64 B<small>5 Mbit/s / BRS</small></span><span>结束 / 应答<small>帧开销</small></span></div><a class="inline-link" href="/method/">理解位速率与实际吞吐 →</a></div><div class="panel"><h3>从结果回到证据</h3><p>每块板分别保留测试日期、参数、帧数、异常和验证范围。原始 JSON、PDF 与源码可以交叉查阅。</p><p>静态记录呈现历史实测，不连接设备、不开启发送，也不把构建成功当作硬件验收。</p><div class="pill-links"><a href="/usb-canfd/#downloads">自研板报告与固件 ↗</a><a href="/5io/#evidence">5IO 失败记录 ↗</a></div></div></div>'''
    return hero+section('boards','01 / 选择硬件','两块板，独立验证',cards,'先确认硬件与软件栈，再阅读结论。')+section('compare','02 / 快速对比','相同速率，不同测试对象',compare)+section('reading','03 / 读懂结果','参数、吞吐与稳定性',method)


def detail_intro(name,eyebrow,title,copy,tags,nav):
    return f'<div class="breadcrumb"><a href="/">验证总览</a><span>/</span><span>{E(name)}</span></div><section class="detail-hero"><div class="eyebrow">{E(eyebrow)}</div><h1>{title}</h1><p class="hero-copy">{copy}</p><div class="detail-tags">{tags}</div></section><nav class="detail-nav" aria-label="本页内容">'+''.join(f'<a href="#{id}">{E(label)}</a>' for id,label in nav)+'</nav>'


def usb_page():
    intro=detail_intro('自研 USB CAN 板','BOARD 01 / STM32G431 × 3','自研 CAN 板<br><em>CAN FD 5M 驱动与固件验证</em>','采用 CANable 2.0 硬件方案的三通道 USB 板。当前记录验证刷写、启动与 CAN0 / CAN1 物理收发；CAN2 已启动，尚未接线。',badge('CAN0 ↔ CAN1 本轮通过','green')+badge('CAN2 收发待测','gray')+badge('实测 2026.10.30'),[('results','实测结果'),('channels','三路状态'),('software','驱动与固件'),('reproduce','复现操作'),('downloads','证据与下载')])
    metrics='<dl class="metrics">'+metric('仲裁 / 数据段','1M / 5M','FD + BRS，64 字节负载')+metric('连续测试实收','143,076','三阶段合计，缺失 / 重复 / 内容错误均为 0')+metric('最长同时双向','60 秒','每方向各 54,929 帧')+metric('单向有效载荷','约 0.85 Mb/s','约 1,660 帧/秒，未跑满总线')+'</dl>'
    rows=[]
    for stage in USB['stages']:
        flows=stage['flows'];direction='CAN0 → CAN1' if stage['sources']==[0] else 'CAN1 → CAN0' if stage['sources']==[1] else '同时双向'
        counts=' / '.join(f'{flow["received"]:,}' for flow in flows.values())
        fps=' / '.join(f'{flow["received_fps_per_send_window"]:,.2f}' for flow in flows.values())
        rows.append((direction,str(stage['seconds'])+' 秒',counts,fps,'缺失 / 重复 / 内容错误 0'))
    result=table(['方向','发送窗口','实收帧数','各方向帧/秒','完整性'],rows,'USB CAN FD 5M连续测试三阶段结果')
    result+='<p class="source-line">另外完成 Classic 1M、FD 2M / 5M 功能测试共 164 帧，覆盖标准 / 扩展 ID 和全部合法 FD 长度。发布版 CLI 再测双向 5 秒，4,565 帧全部收到；与上表分别计数。</p>'
    result+='<div class="note amber"><strong>验证边界：</strong>5M 是配置的数据段位速率。最长双向窗口为 60 秒，未完成总线满载、示波器位宽测量或数小时 / 数天稳定性测试。固件 E 寄存器为 0，不等于已取得完整 TEC / REC 硬件错误计数。</div>'
    channels=table(['物理通道','主 Flash 备份','逐字节读回','重启版本查询','对端物理收发'],[(c['channel'],'已完成','通过','通过',badge('Classic 1M / FD 2M、5M 通过','green') if c['channel']!='CAN2' else badge('未接线，未运行','gray')) for c in CHANNELS['channels']],'三路USB CAN的刷写和物理收发状态')
    channels+='<p class="source-line">每路是独立 MCU，分别进入 ROM DFU、分别刷写。选择设备使用 USB 序列号及物理路径，不能依赖可能变化的 ttyACM 编号。</p>'
    software=f'''<div class="two-columns"><div class="panel"><h3>这次“驱动验证”验证了什么</h3><p>主机通过 USB CDC 驱动访问 <code>ttyACM*</code>，Linux 工具使用非标准 SLCAN FD 协议。MCU 固件控制板上的 FDCAN 外设，完成实际总线收发。</p><p>刷写后设备由原来的 <code>gs_usb / canX</code> 切换为 <code>CDC / SLCAN FD</code>；普通 slcan 工具不保证支持这个 FD 扩展。</p></div><div class="panel"><h3>开源来源与本项目工作</h3><p>固件来自 <a href="https://github.com/normaldotcom/canable2-fw/tree/b158aa7ab106bc018715cd4d5f02f544f9de1830">normaldotcom/canable2-fw · b158aa7 ↗</a>，未修改上游固件。</p><p>本项目新增设备身份校验、备份刷写、有限时长物理收发测试、完整载荷校验和验证记录。与 5IO 的 Linux 6.1 CAN 回移驱动分别维护。</p></div></div><div class="note"><strong>已定位的干扰：</strong>实测中已有 root 电池进程扫描并抢读 ttyACM，造成串口回复被截取。原测试临时排除所选端口访问，测试后恢复；发布工具遇占用会拒绝运行。正式集成应修正业务程序的设备选择。</div>'''
    reproduce='''<div class="step-grid"><div class="panel"><span class="step-no">01 / 识别</span><h3>先核对目标通道</h3><p>inventory 获取本机 USB 序列号；version 查询启动。固件备份与刷写按 README 单独执行。</p></div><div class="panel"><span class="step-no">02 / 接线</span><h3>准备独立测试总线</h3><p>两路 CANH、CANL、GND 对应连接，核对终端与供电。业务设备退出测试总线，停止占用端口的程序。</p></div><div class="panel"><span class="step-no">03 / 验证</span><h3>保存原始收发结果</h3><p>明确选择两个不同 USB 序列号；比较对端序号、ID、DLC 和完整载荷，记录实际帧率与缺失。</p></div></div>'''
    reproduce+=code('install','Linux / Python 3.10+','git clone https://github.com/lizi-learn/ymbot-usb-canfd.git\ncd ymbot-usb-canfd\npython3 -m venv .venv\n.venv/bin/pip install -e .\n.venv/bin/python -m ymbot_usb_canfd.cli inventory')
    reproduce+=code('test','使用本机 inventory 得到的两个序列号','sudo .venv/bin/python -m ymbot_usb_canfd.cli test \\\n  --tx FIRST_USB_SERIAL --rx SECOND_USB_SERIAL \\\n  --mode fd --data-bps 5000000 --length 64 \\\n  --duration 60 --rate 1000 --output results/fd5m.json')
    reproduce+=f'<p class="source-line">脚本实际帧率受调度与 ASCII 传输限制，--rate 为请求值。完整刷写步骤、引脚、BOR 启动行为和回退说明见 <a href="{REPO}#readme">README ↗</a>。</p>'
    downloads='<div class="download-list">'+''.join(f'<a href="{url}"><span>↗</span><b>{name}</b><small>{desc}</small></a>' for url,name,desc in [
        ('/downloads/CAN0-CAN1-FD5M-20261030.pdf','真实验证报告 · PDF','CAN0 / CAN1 固件刷写与 FD 5M 实测'),
        (REPO+'/releases/tag/v0.1.0','v0.1.0 完整发布包','固件、对应源码、Linux 工具、原始统计与 SHA-256'),
        ('/data/continuous-fd5m-20261030.json','FD 5M 连续测试 · JSON','三个阶段逐方向统计、错误寄存器和验证边界'),
        ('/data/published-cli-smoke-20261030.json','发布工具真机复测 · JSON','双向 5 秒、4,565 帧；独立于历史连续测试'),
        ('/data/channels-20261030.json','三路通道状态 · JSON','CAN0 / CAN1 已接线；CAN2 未接线'),
        (REPO,'GitHub 源码','固件来源、构建、刷写与验证分别执行')
    ])+'</div>'
    downloads+='<details><summary>固件 SHA-256 与可复核来源</summary><p>BIN：26,468 字节 · Flash 起始 0x08000000<br><code>a24290eea6050cf6245ade91353e2f47732f9e570baf21b2a05f0f2a2c8c08f8</code></p><p>三路写入同版固件，并完成逐字节读回。上游启动代码可能将 BOR 设为 4 级（约 2.8V）；本次没有选项字节前后快照。详见源码 README 和 PROVENANCE。</p></details>'
    return intro+metrics+section('results','01 / 结果','FD 5M 实际收发',result)+section('channels','02 / 通道','三路状态，分别核验',channels)+section('software','03 / 软件栈','固件、主机驱动与工具的分工',software)+section('reproduce','04 / 复现','从识别到独立收发',reproduce)+section('downloads','05 / 证据','报告、固件与原始记录',downloads)


def five_page():
    intro=detail_intro('5IO 开发板','BOARD 02 / RK3588 · LBM5-DIBAN-V01A','5IO 板载 CAN<br><em>Linux 6.1 回移驱动验证</em>','历史实测记录：RK3588 核心板安装在 LBM5-DIBAN-V01A 自研底板，两路板载 CAN 通过 SocketCAN 收发。当前页仅展示该板的结论。',badge('FD 5M 严格验收未通过','amber')+badge('默认 Classic 1M','gray')+badge('实测 2026.10.25','gray'),[('results','FD 5M 结果'),('software','软件与范围'),('evidence','独立证据')])
    metrics='<dl class="metrics">'+metric('仲裁 / FD 数据段','1M / 5M','FD 实验配置，默认恢复普通 1M')+metric('压测窗口','30 分钟','另有 30 秒基线；总活动窗口 1,830 秒')+metric('含基线合计实收','12,386,944','压测 12,326,944 + 基线 60,000 帧')+metric('总线错误增量','每口 +6','另有一个 RX FIFO 异常')+'</dl>'
    rows=[(s['name'],str(s['seconds'])+' 秒',f'{s["frames"]:,}',badge(s['result'],'green' if s['result']=='该阶段通过' else 'amber')) for s in FIVE['stages']]
    result=table(['阶段','时长','实收帧数','阶段结论'],rows,'5IO板载CAN FD 5M的历史30分钟测试')
    result+='<div class="note amber"><strong>严格结论：失败。</strong>所有帧最终收到，不代表总线没有错误或恢复 / 重试。标准 ID 两阶段通过；扩展与混合负载出现异常，短测通过不能覆盖后续失败。</div><p class="source-line">标准 ID 阶段有效载荷约 3.41 Mbit/s，软件估算线占用约 99.33%；缺少独立分析仪测量，不能宣称物理线速 100%。</p>'
    software='''<div class="two-columns"><div class="panel"><h3>Linux 驱动回移与 BSP 适配</h3><p>驱动主体来自 Linux 上游，本项目完成 6.1 API 回移、RK3588 / BSP 与板级适配、位时序调优和实机验证。模块须用目标 BSP 配套构建信息编译。</p><p>主机接口是 SocketCAN 的 <code>can0</code> / <code>can1</code>，与 USB CAN 板的 CDC / SLCAN FD 固件路径不同。</p></div><div class="panel"><h3>当前配置和后续定位</h3><p>默认普通 CAN 1M，FD 保留实验入口。普通 CAN 1M 已实收实发，但有丢失 / 重复及勘误恢复失败记录，尚未完成零错误验收。</p><p>下一步需结合收发器实装、终端、线束、差分波形与驱动勘误恢复继续定位。不能直接套用另一块 USB 板的通过结论。</p></div></div>'''
    evidence='<div class="download-list">'+''.join(f'<a href="{url}"><span>↗</span><b>{name}</b><small>{desc}</small></a>' for url,name,desc in [
        (FIVE_BASE+FIVE['source_path'],'CAN 速率与验收说明','固定源码提交的结论与统计依据'),
        (FIVE_BASE+FIVE['evidence_path'],'30 分钟原始测试 · JSON','包括错误计数、完整性与各阶段'),
        ('https://ymbot-5io-wiki.pages.dev/can','5IO CAN 教学 Wiki','原有系统优化与排查手册'),
        ('https://ymbot-5io-wiki.pages.dev/','5IO 系统优化完整手册','CAN / RS485、启动、桌面、网络和新机配置')
    ])+'</div>'
    evidence+=f'<p class="source-line">引用快照：<code>{FIVE["source_commit"]}</code><br>原始测试日期 {FIVE["test_date"]}；本页汇编于 {DATE}，本次未对 5IO 重新发送测试帧。</p>'
    return intro+metrics+section('results','01 / 历史实测','收齐帧，仍未通过严格验收',result)+section('software','02 / 软件与范围','单独维护 5IO 的结论',software)+section('evidence','03 / 来源','回到这块板的原始证据',evidence)


def method_page():
    intro=detail_intro('测试口径','READ THE EVIDENCE / 测量口径','同样是 5M，<br><em>看清测量的层次。</em>','板卡身份、软件栈、配置、实际数据与异常计数共同构成结论。复用操作时先确认硬件，比较结果时同时看负载和时长。',badge('配置 → 收发 → 压力与稳定性'),[('speed','速率与吞吐'),('stack','两类软件栈'),('criteria','结果如何判定')])
    speed=table(['指标','实际含义','本次 USB CAN 板'],[
        ('仲裁段 1M','仲裁相关阶段的配置位速率','1,000,000 bit/s'),
        ('FD 数据段 5M','BRS 开启后数据阶段的配置位速率','5,000,000 bit/s；未用示波器独立测位宽'),
        ('应用吞吐','接收有效载荷 ÷ 发送窗口时间','单向约 0.85 Mbit/s，约 1,660 帧/秒'),
        ('总线利用率','线上帧与填充等占用时间的比例','本次未独立测量，也未完成满载'),
        ('长期稳定性','给定线束、负载、时长下的数据与错误记录','最长同时双向 60 秒；数小时 / 天待验证')
    ],'配置位速率、吞吐、占用和稳定性的区别')
    stack='''<div class="two-columns"><div class="panel"><h3>自研 USB CAN 板</h3><p>Linux 测试工具 → USB CDC / ttyACM → SLCAN FD 协议 → STM32G431 固件 → FDCAN 控制器与收发器。</p><p>使用 CANable 原版固件，并为本项目补充备份、读回与实际收发工具。三颗 MCU 各自刷写。</p></div><div class="panel"><h3>5IO 开发板</h3><p>Linux 测试工具 → SocketCAN → Linux 6.1 回移 CAN 驱动 → RK3588 板载控制器与底板收发器。</p><p>Linux 上游驱动回移到厂商 BSP，结合设备树与位时序配置。两路板载接口。</p></div></div>'''
    criteria='''<div class="step-grid"><div class="panel"><span class="step-no">01 / 身份与条件</span><h3>先确定测的是谁</h3><p>记录板卡、固件 / 驱动版本、通道、接线、终端、位时序、载荷和时长。另一块板的通过结论不能代用。</p></div><div class="panel"><span class="step-no">02 / 对端实收</span><h3>比较完整数据</h3><p>通过物理总线由对端接收。核对成功入队帧的序号、ID、长度、方向与完整载荷，统计缺失、重复和乱序。</p></div><div class="panel"><span class="step-no">03 / 异常与边界</span><h3>同时查看错误</h3><p>应用收齐不代表无总线错误。保留错误计数和失败阶段；缺少硬件计数或波形时明确标注测量范围。</p></div></div><div class="note">本网站是静态验证档案，不提供远程控制或实时设备状态。阅读、下载和复制示例不会向 CAN 总线发送数据；脚本收发需要在本机明确选择通道并执行。</div>'''
    return intro+section('speed','01 / 速率','配置值与实测值，分别记录',speed)+section('stack','02 / 软件栈','“驱动”和“固件”分别在哪',stack)+section('criteria','03 / 判定','结论随证据与条件成立',criteria)


def validate_evidence():
    assert USB['status']=='pass' and USB['data_bps']==5000000 and USB['nominal_bps']==1000000
    total=0
    for stage in USB['stages']:
        assert stage['pass_integrity'] and stage['malformed']==0 and stage['unexpected']==0
        for f in stage['flows'].values():
            assert f['sent']==f['received'] and all(f[k]==0 for k in ['missing','duplicates','payload_errors','out_of_order'])
            total+=f['received']
    assert total==143076==CHANNELS['continuous_frames']
    assert CHANNELS['channels'][2]['physical_peer_test']=='not_connected_not_run'
    assert SMOKE['status']=='pass' and sum(f['received'] for f in SMOKE['flows'].values())==4565
    assert sum(s['frames'] for s in FIVE['stages'])==FIVE['received_frames']==12386944
    assert sum(s['seconds'] for s in FIVE['stages'])==FIVE['seconds_including_baseline']==1830
    assert FIVE['pressure_received_frames']+FIVE['baseline_received_frames']==FIVE['received_frames']
    assert FIVE['seconds']==1800 and FIVE['strict_acceptance']=='failed'


def main():
    validate_evidence()
    if OUT.exists():shutil.rmtree(OUT)
    OUT.mkdir()
    shutil.copytree(HERE/'assets',OUT/'assets')
    (OUT/'data').mkdir();(OUT/'downloads').mkdir()
    for name in ['continuous-fd5m-20261030.json','published-cli-smoke-20261030.json','channels-20261030.json']:
        shutil.copyfile(ROOT/'evidence'/name,OUT/'data'/name)
    shutil.copyfile(HERE/'data/5io-snapshot.json',OUT/'data/5io-snapshot.json')
    shutil.copyfile(ROOT/'docs/CAN0-CAN1-FD5M-20261030.pdf',OUT/'downloads/CAN0-CAN1-FD5M-20261030.pdf')
    pages=[('/', '板卡验证总览',home(),'自研 USB CAN 板与 5IO 开发板的独立验证记录、CAN FD 5M 实测、原始证据与报告。'),('/usb-canfd/', '自研 CAN 板 FD 5M 验证',usb_page(),'CANable 2.0 方案自研 USB CAN 板三通道刷写与 CAN0/CAN1 FD 5M 物理收发验证。'),('/5io/', '5IO 板载 CAN 驱动验证',five_page(),'RK3588 / 5IO 板载 CAN 回移驱动的独立历史测试，保留 30 分钟 FD 5M 严格验收失败记录。'),('/method/', '测试口径与结果判定',method_page(),'区分 CAN FD 配置位速率、应用吞吐、总线满载与长期稳定性，按板卡确认软件栈和证据。')]
    for path,title,body,description in pages:
        dest=OUT/path.strip('/')/'index.html';dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(shell(path,title,body,description))
    (OUT/'404.html').write_text(shell('/404','页面未找到','<section class="detail-hero"><h1>这条记录暂时找不到。</h1><p class="hero-copy">从板卡总览继续查看独立的硬件验证记录。</p><div class="pill-links"><a href="/">返回验证总览 →</a></div></section>','页面未找到'))
    (OUT/'robots.txt').write_text('User-agent: *\nAllow: /\nSitemap: '+URL+'/sitemap.xml\n')
    (OUT/'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join('<url><loc>'+URL+p[0]+'</loc><lastmod>'+DATE+'</lastmod></url>' for p in pages)+'</urlset>')
    (OUT/'_redirects').write_text('/usb-canfd /usb-canfd/ 301\n/5io /5io/ 301\n/method /method/ 301\n')
    (OUT/'_headers').write_text("/*\n  Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; base-uri 'none'; frame-ancestors 'none'; form-action 'none'\n  X-Content-Type-Options: nosniff\n  Referrer-Policy: strict-origin-when-cross-origin\n  Permissions-Policy: camera=(), microphone=(), geolocation=()\n  Cache-Control: public, max-age=0, must-revalidate\n/assets/*\n  Cache-Control: public, max-age=300\n/data/*\n  Cache-Control: public, max-age=300\n")
    sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    manifest={p.relative_to(OUT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.rglob('*') if p.is_file()}
    info={'source_commit':sha,'updated':DATE,'boards':['usb-can-stm32g431','5io-rk3588-lbm5-diban-v01a'],'site':URL,'mode':'static historical evidence','artifacts_sha256':manifest}
    (OUT/'build-info.json').write_text(json.dumps(info,indent=2)+'\n')
    print(f'Built {len(pages)} pages, {len(manifest)} files; independent board evidence validated')

if __name__=='__main__':main()
