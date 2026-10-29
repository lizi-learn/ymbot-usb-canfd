# YMBOT USB CAN FD

硬件验证入口：**[YMBOT 硬件验证](https://ymbot-hardware-test.pages.dev/)** · [本板 FD 5M 实测](https://ymbot-hardware-test.pages.dev/usb-canfd/)。自研 USB CAN 板与 5IO 板分开记录，原 [5IO Wiki](https://ymbot-5io-wiki.pages.dev/) 保留。静态站点源码与发布说明见 [site/README.md](site/README.md)。

CANable 2.0 固件、备份刷写和物理收发测试工具。适用于采用原版 STM32G431CB / CANable 2.0 引脚方案的 USB CAN 板；与 RK3588 板载 CAN 回移驱动是两个项目。

**固件来自 [normaldotcom/canable2-fw](https://github.com/normaldotcom/canable2-fw/tree/b158aa7ab106bc018715cd4d5f02f544f9de1830)，提交 `b158aa7`，没有改写上游固件。** 本项目新增 Linux 工具、验证记录和复现构建流程。保留 GPL 与 ST 等第三方版权说明。

## 2026-10-30 实测

| 项目 | 结果 |
|---|---|
| 三路独立 MCU | CAN0、CAN1、CAN2 均已备份、烧录、逐字节读回和重启查询通过 |
| CAN0 ↔ CAN1 | Classic 1M、FD 1M/2M、FD 1M/5M 双向物理收发通过 |
| 功能测试 | 164 帧；标准/扩展 ID；Classic 0-8 字节、FD 全部合法长度 |
| FD 5M 连续测试 | 64 字节，共 143,076 帧，缺失/重复/内容错误均为 0 |
| 最长同时双向窗口 | 60 秒；每方向各 54,929 帧，约 915 帧/秒 |
| 单向 10 秒窗口 | 约 1,660 帧/秒，有效载荷约 0.85 Mbit/s |
| CAN2 物理收发 | **未接线，未验证** |

5M 是 FD 数据段的配置位速率，仲裁段为 1M。没有示波器独立测量位宽，也没有把总线跑满；不能把脚本吞吐量当作硬件上限。当前结果不构成长线或数小时/数天稳定性结论。见 [完整报告](docs/CAN0-CAN1-FD5M-20261030.pdf) 和 [原始统计](evidence/)；上表是随包的历史实测快照。

## 接口变化

刷写前 `1d50:606f / gs_usb` 生成 `canX`；刷写后 `16d0:117e / USB CDC` 生成 `ttyACM*`，使用上游非标准 SLCAN FD 协议。Linux 普通 slcan 工具不保证支持该扩展。每个 USB CAN MCU 要分别刷写，不能一次刷入自动更新三路。

原版引脚：PB8=CAN_RX，PB9=CAN_TX，PA0=收发器待机（低有效工作），PC13=CAN IO 电源（高有效）。自研板修改引脚或主控时，须重新核对，USB 产品名称本身不能证明兼容。

## 安装与检查

```bash
git clone https://github.com/lizi-learn/ymbot-usb-canfd.git
cd ymbot-usb-canfd
python3 -m venv .venv
.venv/bin/pip install -e .
.venv/bin/python -m ymbot_usb_canfd.cli inventory
sudo .venv/bin/python -m ymbot_usb_canfd.cli version --serial YOUR_USB_SERIAL
```

硬件操作在 root 下检查现有端口占用。`version` 只查询版本/错误寄存器并关闭所选 CAN 通道；不发送 CAN 数据帧。序列号必须来自本机 inventory，不能照抄其他机器的 tty 编号。

## 收发验证

先将选定两路接成测试总线，确认 CANH/CANL/GND、终端和供电正确；测试接口不应连接业务执行器。明确选择两个不同 USB 序列号：

```bash
# Classic 1M，双向，8字节
sudo .venv/bin/python -m ymbot_usb_canfd.cli test \
  --tx FIRST_USB_SERIAL --rx SECOND_USB_SERIAL \
  --mode classic --length 8 --duration 10 --rate 500

# CAN FD：仲裁 1M / 数据 5M，BRS，64字节
sudo .venv/bin/python -m ymbot_usb_canfd.cli test \
  --tx FIRST_USB_SERIAL --rx SECOND_USB_SERIAL \
  --mode fd --data-bps 5000000 --length 64 --duration 60 --rate 1000 \
  --output results/fd5m.json
```

结果比较对端实收的 CAN ID、DLC、方向、序号和完整载荷，统计缺失、重复、格式错误和实际吞吐。请求帧率不等于实际帧率；固件 `E` 寄存器不是完整的控制器 TEC/REC 计数。测试有时限，结束关闭两路。

**已有进程占用端口时工具会拒绝测试。** 实测曾发现 root `battery` 进程扫描并抢读新出现的 `ttyACM*`；`TIOCEXCL` 不能阻止 root。原始实测在临时排除该进程访问测试端口后通过，权限随后恢复。正式接入应修正电池程序的设备选择；不要把抢读导致的截帧直接归咎于 CAN 物理链路。工具不会自动停止机器人服务或扩大服务权限。

## 固件备份与刷写

仅在目标 MCU 按板子 BOOT/RESET 流程进入 ROM DFU 后执行。工具同时校验 ROM 序列号和物理 USB 路径，先备份完整 128KiB 主 Flash，再烧录指定二进制并读回比较：

```bash
dfu-util -l
sudo .venv/bin/python -m ymbot_usb_canfd.cli flash \
  --serial YOUR_ROM_DFU_SERIAL --usb-path YOUR_PHYSICAL_USB_PATH \
  --image firmware/bin/canable2-b158aa7.bin \
  --backup-dir backups/new-unique-backup-directory
```

备份目录必须不存在；文件默认私有权限。完成后取消 BOOT 短接、复位，再运行 `version`。工具不执行 RDP 解锁、全片擦除或 BOOT0 选项字节改写。**上游启动代码本身可能将 BOR 设为 4 级（约 2.8V）**；主 Flash 备份不包含选项字节，本次未取得其前后快照。

提供的 BIN：26,468 字节，起始地址 `0x08000000`，SHA-256：

```text
a24290eea6050cf6245ade91353e2f47732f9e570baf21b2a05f0f2a2c8c08f8
```

## 复现与平台

`firmware/upstream/` 保存已按 Git blob 哈希核对的对应源码和来源清单；仅省略不参与本目标编译的 CMSIS DSP 示例/预编译数学库。安装 ARM GCC、binutils 和 newlib 后运行 `bash scripts/build-firmware.sh`。交付固件使用 GCC 10.3.1 构建，换编译器可能改变哈希；刷写工具只接受随包已验证 BIN。

```bash
python3 -m unittest discover -s tests -v
```

工具输出结构化 JSON；硬件测试和固件刷写分别执行。
