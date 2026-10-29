---
title: 自研 USB CAN 板：物理收发操作
navTitle: 自研 CAN 板 · 接线与复测
category: CAN 验证
board: 自研 USB CAN 板
date: '2026-10-30'
order: 30
result: 操作说明
description: 从安装工具、识别通道、核对接线，到 Classic 1M 与 FD 5M 的独立收发验证。
tags: [CAN FD, 1M, 5M, 接线, 测试命令]
---
# 自研 USB CAN 板：物理收发操作

本文对应 STM32G431 / CANable 2.0 硬件方案、已刷入 `b158aa7` SLCAN FD 固件的 USB 板。历史测试结论见[FD 5M 实测](/can/usb-canfd-5m)。

## 安装和识别

```sh
git clone https://github.com/lizi-learn/ymbot-usb-canfd.git
cd ymbot-usb-canfd
python3 -m venv .venv
.venv/bin/pip install -e .
.venv/bin/python -m ymbot_usb_canfd.cli inventory
```

记录本机 inventory 返回的 USB 序列号。硬件命令在 root 下检查端口占用；发现其他进程读取所选端口时会拒绝执行。

## 接线和测试准备

把两个独立通道接为台架测试总线：CANH ↔ CANH、CANL ↔ CANL、GND ↔ GND，核对终端和供电。不要把未知电源脚对插。

所选接口退出业务使用，测试总线不连接执行器。确认没有电池程序、串口监控等进程抢读接口，再显式指定两个不同的 USB 序列号。

## Classic CAN 1M

```sh
sudo .venv/bin/python -m ymbot_usb_canfd.cli test \
  --tx FIRST_USB_SERIAL --rx SECOND_USB_SERIAL \
  --mode classic --length 8 --duration 10 --rate 500 \
  --output results/classic1m.json
```

## CAN FD 1M / 5M

```sh
sudo .venv/bin/python -m ymbot_usb_canfd.cli test \
  --tx FIRST_USB_SERIAL --rx SECOND_USB_SERIAL \
  --mode fd --data-bps 5000000 --length 64 \
  --duration 60 --rate 1000 --output results/fd5m.json
```

这是有限时长、指定负载的实际收发测试。`--rate` 是请求帧率，不保证程序能达到；`actual_fps` 才是该窗口的实际值。

## 怎样阅读结果

核对成功发送与对端实收是否一致，同时看缺失、重复、乱序、ID / DLC / 完整载荷错误。保留原始 JSON 和实际耗时，不只保存一个 pass 标记。

固件 E 寄存器不是完整的控制器 TEC / REC 计数。需要更高程度的验收时，应补充完整硬件计数、波形与更长运行窗口。工具结束会关闭测试通道。

## 遇到端口占用

先定位占用程序及设备选择规则。本次发现 root 电池程序会扫描 ttyACM，`TIOCEXCL` 也无法阻止 root 抢读。工具不会自动停止机器人服务或修改其访问权限。
