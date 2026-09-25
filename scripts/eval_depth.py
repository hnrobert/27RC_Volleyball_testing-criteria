#!/usr/bin/env python3
"""T05 不同距离深度误差 + T06 深度精度：统计与判档。

输入 CSV（首行表头）：
    z_gt,z_stereo        # 单位 m；同一 z_gt 的样本自动归为一组距离

判档口径（与细则一致）：
    T05：每距离 Er(RMS) <= 分档系数 x delta_Z_th(Z)，任一距离不合格即 0 分
         （木桶原则已覆盖）；另输出 log-log 拟合斜率 k（应接近 2）。
    T06：跨距离归一化误差 eps = Er / delta_Z_th(Z) 的 RMSE / Max / 3 sigma。

用法:
    python scripts/eval_depth.py t05.csv --f 2200 --b 1.0 [--json out.json]
"""

import argparse
import math
from collections import defaultdict

from lbst_common import (Report, dz_th_rel, linreg, mean, read_csv_rows, rms,
                         sdev)

T05_MULT = (1.5, 2.5, 4.0)
T06_RMSE_BANDS = (1.5, 2.5, 4.0)
T06_MAX_BANDS = (2.0, 3.5, 6.0)
T06_3SIGMA_BANDS = (2.5, 4.0, 6.0)


def parse_args():
    ap = argparse.ArgumentParser(
        description="T05/T06 深度误差统计与判档（Er 与归一化误差 eps）")
    ap.add_argument("csv", help="输入 CSV：z_gt,z_stereo（m）")
    ap.add_argument("--f", type=float, required=True, help="焦距 f（px）")
    ap.add_argument("--b", type=float, required=True, help="基线 B（m）")
    ap.add_argument("--dd", type=float, default=0.5,
                    help="视差误差基准 dd0（px），默认 0.5")
    ap.add_argument("--json", dest="json_path", help="结果导出 JSON 路径")
    return ap.parse_args()


def main():
    args = parse_args()

    groups = defaultdict(list)
    for row in read_csv_rows(args.csv):
        z_gt = float(row["z_gt"])
        groups[round(z_gt, 3)].append((z_gt, float(row["z_stereo"])))

    rep = Report("T05/T06 深度误差判档")
    rep.add_raw("配置", f"f={args.f:g} px，B={args.b:g} m，dd0={args.dd:g} px")

    zs, er_rms_by_z, eps_all = [], [], []
    for z in sorted(groups):
        samples = groups[z]
        er = [abs(z_s - z_g) / z_g for z_g, z_s in samples]
        eps_all += [e / dz_th_rel(z_g, args.f, args.b, args.dd)
                    for e, (z_g, _) in zip(er, samples)]
        zs.append(z)
        er_rms_by_z.append(rms(er))
        limits = tuple(m * dz_th_rel(z, args.f, args.b, args.dd) * 100
                       for m in T05_MULT)
        rep.add(f"Z={z:g}m Er(RMS)", er_rms_by_z[-1] * 100, limits,
                fmt="{:.3f}%")
        rep.add_raw(
            f"Z={z:g}m n/Er(Mean)/Er(Max)",
            f"n={len(samples)}，{mean(er) * 100:.3f}%，"
            f"{max(er) * 100:.3f}%")

    rep.add("RMSE(eps)", rms(eps_all), T06_RMSE_BANDS, fmt="{:.3f}")
    rep.add("Max(eps)", max(eps_all), T06_MAX_BANDS, fmt="{:.3f}")
    rep.add("3*sigma(eps)", 3 * sdev(eps_all), T06_3SIGMA_BANDS,
            fmt="{:.3f}")
    rep.add_raw("eps 样本数", f"n={len(eps_all)}")

    if len(zs) >= 3:
        slope, _, r2 = linreg([math.log(z) for z in zs],
                              [math.log(v) for v in er_rms_by_z])
        rep.add_raw("log-log 拟合", f"k={slope:.3f}，R2={r2:.3f}")
        if not 1.5 <= slope <= 2.5:
            rep.warn("拟合斜率 k 偏离 [1.5, 2.5]：偏小提示与距离无关的"
                     "系统偏差（标定 bias），偏大提示匹配质量随距离退化")
    else:
        rep.warn("距离点 < 3，无法做 log-log 拟合")
    return rep.emit(args.json_path)


if __name__ == "__main__":
    raise SystemExit(main())
