---
title: 自研 USB CAN 板：三路固件刷写与启动检查
navTitle: 自研 CAN 板 · 三路固件刷写
category: CAN 验证
board: 自研 USB CAN 板
date: '2026-10-30'
order: 20
result: 三路已备份、刷写、读回和重启查询
description: CAN0、CAN1、CAN2 分别进入 ROM DFU，备份完整主 Flash，刷写后读回比较并检查启动。
tags: [固件, DFU, CAN2, CANable, 刷写]
---
# 自研 USB CAN 板：三路固件刷写与启动检查

这块 USB 板的三个通道各有独立 MCU。一次刷写只更新选中的通道，需要分别执行 BOOT / RESET 流程。

## 使用的固件从哪里来

固件来自 [normaldotcom/canable2-fw](https://github.com/normaldotcom/canable2-fw/tree/b158aa7ab106bc018715cd4d5f02f544f9de1830)，固定提交 `b158aa7ab106bc018715cd4d5f02f544f9de1830`。本项目没有改写上游固件，新增的是 Linux 备份刷写工具、设备身份检查和物理收发验证工具。

| 项目 | 固定值 |
| --- | --- |
| 目标 | STM32G431CB，原版 CANable 2.0 引脚方案 |
| BIN 大小 | 26,468 字节 |
| 写入起始地址 | `0x08000000` |
| 原主 Flash 备份范围 | 完整 128 KiB |
| SHA-256 | `a24290eea6050cf6245ade91353e2f47732f9e570baf21b2a05f0f2a2c8c08f8` |

原版引脚：PB8 为 CAN_RX，PB9 为 CAN_TX；PA0 控制收发器待机，低电平进入工作；PC13 控制 CAN IO 电源，高电平有效。修改过主控或引脚的板需要先重新核对。

## 刷写后的接口变化

刷写前为 `1d50:606f / gs_usb`，主机生成 `canX`；刷写后为 `16d0:117e / USB CDC`，主机生成 `ttyACM*`，使用上游的非标准 SLCAN FD 协议。普通 Linux slcan 工具不保证支持这个 FD 扩展。

这与 [5IO 的 Linux CAN 回移驱动](/can/5io-canfd-5m)属于不同的软件路径。

## 备份和刷写步骤

先按[安装与测试说明](/can/usb-can-test)准备 Python 环境，并安装 `dfu-util`。让目标 MCU 进入 ROM DFU，确认序列号和物理 USB 路径后执行：

```sh
dfu-util -l
sudo .venv/bin/python -m ymbot_usb_canfd.cli flash \
  --serial YOUR_ROM_DFU_SERIAL \
  --usb-path YOUR_PHYSICAL_USB_PATH \
  --image firmware/bin/canable2-b158aa7.bin \
  --backup-dir backups/new-unique-backup-directory
```

备份目录必须不存在。工具先备份，再写入固定镜像，最后逐字节读回比较。设备选择同时核对 ROM 序列号和物理路径，不靠可能变化的 tty 编号。

完成后取消该通道的 BOOT 短接并复位，再执行版本查询：

```sh
.venv/bin/python -m ymbot_usb_canfd.cli inventory
sudo .venv/bin/python -m ymbot_usb_canfd.cli version --serial YOUR_USB_SERIAL
```

`version` 查询版本和错误寄存器，并关闭所选 CAN 通道；它不发送 CAN 数据帧。

## 本次完成情况与限制

CAN0、CAN1、CAN2 均完成主 Flash 备份、写入、逐字节读回和重启版本查询。CAN2 未接线，刷写成功不能替代物理收发验证。

工具没有执行 RDP 解锁、全片擦除或 BOOT0 选项字节改写。但上游启动代码本身可能将 **BOR 设为 4 级，约 2.8V**；主 Flash 备份不包含选项字节，本次没有取得其前后快照。

完整来源、版权、构建与回退范围见 [源码 README](https://github.com/lizi-learn/ymbot-usb-canfd#readme)和 [PROVENANCE](https://github.com/lizi-learn/ymbot-usb-canfd/blob/main/firmware/PROVENANCE.json)。
