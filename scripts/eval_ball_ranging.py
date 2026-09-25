#!/usr/bin/env python3
"""T18 动态球测距：静态/动态测距 RMSE、有效率与抖动判档。

输入 CSV（首行表头，逐帧一行；静态与动态数据同格式，按 gt 距离分组）：
    dist_gt,dist_meas[,valid]     # 单位 m；valid 取 1/0，缺省为 1

用法:
    python scripts/eval_ball_ranging.py t18.csv --f 2200 --b 1.0 \
        [--json out.json]
"""

import argparse
from collections import defaultdict

from lbst_common import Report, dz_th_rel, read_csv_rows, rms, sdev

RMSE_MULT = (1.5, 2.5, 4.0)
VALID_RATE_BANDS_PCT = (98.0, 95.0, 90.0)
JITTER_RATIO_BANDS = (1.2, 1.5, 2.0)


def main():
    ap = argparse.ArgumentParser(description="T18 动态球测距判档")
    ap.add_argument("csv", help="输入 CSV：dist_gt,dist_meas[,valid]")
    ap.add_argument("--f", type=float, required=True, help="焦距 f（px）")
    ap.add_argument("--b", type=float, required=True, help="基线 B（m）")
    ap.add_argument("--dd", type=float, default=0.5,
                    help="视差误差基准 dd0（px），默认 0.5")
    ap.add_argument("--json", dest="json_path", help="结果导出 JSON 路径")
    args = ap.parse_args()

    groups = defaultdict(list)
    total = valid_total = 0
    for row in read_csv_rows(args.csv):
        gt = float(row["dist_gt"])
        flag = row.get("valid")
        ok = True if flag in (None, "") else bool(int(float(flag)))
        total += 1
        valid_total += int(ok)
        if ok:
            groups[round(gt, 3)].append((gt, float(row["dist_meas"])))

    rep = Report("T18 动态球测距判档")
    worst_ratio = 0.0
    for gt in sorted(groups):
        samples = groups[gt]
        group_rms = rms([m - g for g, m in samples])
        limits = tuple(m * dz_th_rel(gt, args.f, args.b, args.dd) * gt
                       for m in RMSE_MULT)
        rep.add(f"D={gt:g}m RMSE", group_rms, limits, fmt="{:.4f} m")
        jitter = sdev([m for _, m in samples])
        ratio = jitter / group_rms if group_rms else 0.0
        worst_ratio = max(worst_ratio, ratio)
        rep.add_raw(f"D={gt:g}m n/抖动",
                    f"n={len(samples)}，sigma={jitter:.4f} m，"
                    f"ratio={ratio:.2f}")

    rate = valid_total / total * 100 if total else 0.0
    rep.add("有效测距率", rate, VALID_RATE_BANDS_PCT, upper=False,
            fmt="{:.2f}%")
    rep.add("抖动/RMSE 最差比", worst_ratio, JITTER_RATIO_BANDS,
            fmt="{:.2f}")
    return rep.emit(args.json_path)


if __name__ == "__main__":
    raise SystemExit(main())
