#!/usr/bin/env python3
"""T07 三轴（X/Y/Z）定位精度：统计与判档。

输入 CSV（首行表头）：
    x_gt,y_gt,z_gt,x,y,z        # 单位 m

判档口径：
    X/Y 轴：逐样本相对误差 |delta|/Z 的 RMS（优 0.05% / 良 0.10% /
    合格 0.20%），另判系统偏差比 |bias|/RMSE（同一轴）。
    Z 轴：提供 --f --b 时按 T06 归一化误差 eps 判档；否则仅输出统计值。

用法:
    python scripts/eval_xyz.py t07.csv [--f 2200 --b 1.0] [--json out.json]
"""

import argparse

from lbst_common import Report, dz_th_rel, mean, read_csv_rows, rms, sdev

XY_RMS_BANDS_PCT = (0.05, 0.10, 0.20)
BIAS_RATIO_BANDS = (0.3, 0.5, 0.8)
T06_EPS_BANDS = ((1.5, 2.5, 4.0), (2.0, 3.5, 6.0), (2.5, 4.0, 6.0))


def axis_stats(values):
    """单轴误差统计（values 为带符号误差序列）。"""
    return {
        "mae": mean([abs(v) for v in values]),
        "rmse": rms(values),
        "max": max(abs(v) for v in values),
        "bias": mean(values),
    }


def parse_args():
    ap = argparse.ArgumentParser(description="T07 三轴定位精度判档")
    ap.add_argument("csv", help="输入 CSV：x_gt,y_gt,z_gt,x,y,z（m）")
    ap.add_argument("--f", type=float, help="焦距 f（px），用于 Z 轴判档")
    ap.add_argument("--b", type=float, help="基线 B（m），用于 Z 轴判档")
    ap.add_argument("--json", dest="json_path", help="结果导出 JSON 路径")
    return ap.parse_args()


def main():
    args = parse_args()

    err = {"X": [], "Y": [], "Z": []}
    z_gts = []
    for row in read_csv_rows(args.csv):
        gt = {k: float(row[f"{k}_gt"]) for k in "xyz"}
        cur = {k: float(row[k]) for k in "xyz"}
        for axis in "XYZ":
            err[axis].append(cur[axis.lower()] - gt[axis.lower()])
        z_gts.append(gt["z"])

    rep = Report("T07 三轴定位精度判档")
    for axis in ("X", "Y"):
        st = axis_stats(err[axis])
        rel_rms = rms([abs(e) / g for e, g in zip(err[axis], z_gts)])
        rep.add(f"{axis} 轴 RMSE(|d|/Z)", rel_rms * 100,
                XY_RMS_BANDS_PCT, fmt="{:.3f}%")
        ratio = abs(st["bias"]) / st["rmse"] if st["rmse"] else 0.0
        rep.add(f"{axis} 轴 |bias|/RMSE", ratio, BIAS_RATIO_BANDS,
                fmt="{:.3f}")
        rep.add_raw(f"{axis} 轴 统计",
                    f"MAE={st['mae']:.4f} m，RMSE={st['rmse']:.4f} m，"
                    f"Max={st['max']:.4f} m")

    st_z = axis_stats(err["Z"])
    er = [abs(e) / g for e, g in zip(err["Z"], z_gts)]
    if args.f and args.b:
        eps = [e / dz_th_rel(g, args.f, args.b) for e, g in zip(er, z_gts)]
        rep.add("Z 轴 RMSE(eps)", rms(eps), T06_EPS_BANDS[0], fmt="{:.3f}")
        rep.add("Z 轴 Max(eps)", max(eps), T06_EPS_BANDS[1], fmt="{:.3f}")
        rep.add("Z 轴 3*sigma(eps)", 3 * sdev(eps), T06_EPS_BANDS[2],
                fmt="{:.3f}")
    else:
        rep.add_raw("Z 轴 Er(RMS)",
                    f"{rms(er) * 100:.4f}%（未提供 --f/--b，不判档）")
    rep.add_raw("Z 轴 统计",
                f"MAE={st_z['mae']:.4f} m，RMSE={st_z['rmse']:.4f} m，"
                f"Max={st_z['max']:.4f} m")
    return rep.emit(args.json_path)


if __name__ == "__main__":
    raise SystemExit(main())
