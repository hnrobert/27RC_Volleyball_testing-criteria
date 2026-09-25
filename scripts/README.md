# 测试工具脚本

配合 [../docs/test-procedures.md](../docs/test-procedures.md) 使用的计算与判档工具。
**纯 Python 标准库（>= 3.8），无第三方依赖**；判档阈值与细则文档一一对应，
输出四档结果（优 100 / 良 80 / 合格 60 / 不合格 0）并按木桶原则汇总。

## 脚本与测试项对照

| 测试 | 脚本 | 输入 CSV 列（首行表头） | 关键参数 |
| --- | --- | --- | --- |
| T03 | `eval_repeatability.py` | `fx,fy,cx,cy,baseline_mm,roll_deg,pitch_deg,yaw_deg,rms` | — |
| T04 | `eval_zones.py` | `zone,reproj_err,epipolar_err`（zone 1–9，5 为中心） | — |
| T05 / T06 | `eval_depth.py` | `z_gt,z_stereo`（m，同距离样本自动分组） | `--f --b`（必填） |
| T07 | `eval_xyz.py` | `x_gt,y_gt,z_gt,x,y,z`（m） | `--f --b`（Z 轴判档用） |
| T08 | `eval_epipolar.py` | `y_l,y_r`（校正后像素坐标） | — |
| T09 | `eval_disparity.py` | `z_gt,d_meas` | `--f --b`（必填） |
| T12 / T13 | `eval_drift.py` | 同 T03 表头，可加 `temp_c`（T13 必填）、`er_rms`（可选） | `--mode t12\|t13` |
| T14 | `eval_sync.py` | `dt_ms` | — |
| T10 / T11 / T15 恶化系数 | `eval_kappa.py` | 命令行参数 `--base --values` | `--bands t10\|t11\|t12\|t13\|t15` |
| 附录 A 阈值表 | `gen_thresholds.py` | — | `--f --b [--dd] [--distances] [--markdown]` |

## 用法示例

先构造一份示例数据再运行（实际使用时替换为真实采集数据）：

```bash
cd <仓库根目录>

# T05/T06：z_gt,z_stereo（m）
printf 'z_gt,z_stereo\n5,5.012\n5,4.991\n10,10.03\n10,9.97\n20,20.06\n' > /tmp/t05.csv
python3 scripts/eval_depth.py /tmp/t05.csv --f 2200 --b 1.0

# T08：y_l,y_r（校正后）
printf 'y_l,y_r\n1000.12,1000.31\n800.44,800.60\n600.02,600.15\n' > /tmp/t08.csv
python3 scripts/eval_epipolar.py /tmp/t08.csv

# T09：z_gt,d_meas
printf 'z_gt,d_meas\n10,219.9\n20,110.1\n' > /tmp/t09.csv
python3 scripts/eval_disparity.py /tmp/t09.csv --f 2200 --b 1.0

# T12：机械稳定性（首行 = 初始基准）
printf 'fx,fy,cx,cy,baseline_mm,roll_deg,pitch_deg,yaw_deg,rms,er_rms\n2200.1,2200.3,1224.5,1024.2,1000.20,0.10,0.05,0.02,0.28,0.004\n2200.2,2200.4,1224.6,1024.3,1000.24,0.10,0.06,0.02,0.29,0.0042\n' > /tmp/t12.csv
python3 scripts/eval_drift.py /tmp/t12.csv --mode t12

# 附录 A：按实际设备生成阈值表（Markdown 可直接粘贴进报告）
python3 scripts/gen_thresholds.py --f 2400 --b 0.8 --markdown
```

所有脚本均支持 `--json out.json` 导出机器可读结果（指标、阈值、档位、得分、汇总）。

## 判档与退出码

- 多指标取最低档（木桶原则），与细则 2.1 节一致；
- 退出码 `0` = 全部指标合格及以上，`1` = 存在不合格指标，可直接接入 CI；
- 触发否决项条件时（V2 于 `eval_epipolar.py`，V3 于 `eval_drift.py --mode t12`）
  报告末尾给出显式警告。

## 自检

```bash
autopep8 --diff --recursive --max-line-length 79 scripts/
isort --check-only scripts/
flake8 scripts/
```
