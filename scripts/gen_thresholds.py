#!/usr/bin/env python3
"""生成距离类分档阈值表（对应细则附录 A / T05 / T06 换算规则）。

阈值(Z) = 分档系数 x Z*dd0/(f*B)，分档系数：优 1.5 / 良 2.5 / 合格 4.0。

用法:
    python scripts/gen_thresholds.py --f 2200 --b 1.0
    python scripts/gen_thresholds.py --f 2400 --b 0.8 \
        --distances 5,10,25,50 --markdown
"""

import argparse

from lbst_common import dz_th_rel

MULTS = (1.5, 2.5, 4.0)


def parse_args():
    ap = argparse.ArgumentParser(
        description="生成 T05/T06 距离类误差分档阈值表（附录 A）")
    ap.add_argument("--f", type=float, default=2200.0,
                    help="焦距 f（px，标定值），默认 2200")
    ap.add_argument("--b", type=float, default=1.0,
                    help="基线 B（m），默认 1.0")
    ap.add_argument("--dd", type=float, default=0.5,
                    help="视差误差基准 dd0（px），默认 0.5")
    ap.add_argument("--distances", default="5,10,20,30,50,70,100",
                    help="逗号分隔的距离点（m）")
    ap.add_argument("--markdown", action="store_true",
                    help="输出 Markdown 表格（默认为对齐文本）")
    return ap.parse_args()


def main():
    args = parse_args()
    distances = [float(x) for x in args.distances.split(",") if x.strip()]
    print(f"参考配置：B = {args.b:g} m，f = {args.f:g} px，"
          f"dd0 = {args.dd:g} px\n")
    if args.markdown:
        print("| 距离 Z | 理论线 | 优（1.5x） | 良（2.5x） | 合格（4.0x） |")
        print("| ---: | ---: | ---: | ---: | ---: |")
        for z in distances:
            base = dz_th_rel(z, args.f, args.b, args.dd) * 100
            cells = " | ".join(f"{m * base:.2f}%" for m in MULTS)
            print(f"| {z:g} m | {base:.2f}% | {cells} |")
    else:
        print(f"{'距离':>7} {'理论线':>9} {'优1.5x':>9} "
              f"{'良2.5x':>9} {'合格4.0x':>10}")
        for z in distances:
            base = dz_th_rel(z, args.f, args.b, args.dd) * 100
            print(f"{z:>6g}m {base:>8.2f}% {MULTS[0] * base:>8.2f}% "
                  f"{MULTS[1] * base:>8.2f}% {MULTS[2] * base:>9.2f}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
