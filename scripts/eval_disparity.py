#!/usr/bin/env python3
"""T09 视差精度：实测视差与理论视差 d_theo = f*B/Z_GT 对比判档。

输入 CSV（首行表头）：
    z_gt,d_meas        # z_gt 单位 m；d_meas 单位 px

用法:
    python scripts/eval_disparity.py t09.csv --f 2200 --b 1.0 \
        [--json out.json]
"""

import argparse

from lbst_common import Report, mean, read_csv_rows

MEAN_BANDS = (0.10, 0.20, 0.30)
MAX_BANDS = (0.30, 0.50, 0.80)
BIAS_BANDS = (0.05, 0.10, 0.20)


def main():
    ap = argparse.ArgumentParser(description="T09 视差误差统计与判档")
    ap.add_argument("csv", help="输入 CSV：z_gt,d_meas")
    ap.add_argument("--f", type=float, required=True, help="焦距 f（px）")
    ap.add_argument("--b", type=float, required=True, help="基线 B（m）")
    ap.add_argument("--json", dest="json_path", help="结果导出 JSON 路径")
    args = ap.parse_args()

    deltas = [float(row["d_meas"]) - args.f * args.b / float(row["z_gt"])
              for row in read_csv_rows(args.csv)]

    rep = Report("T09 视差精度判档")
    rep.add("平均 |dd|", mean([abs(d) for d in deltas]), MEAN_BANDS,
            fmt="{:.3f} px")
    rep.add("最大 |dd|", max(abs(d) for d in deltas), MAX_BANDS,
            fmt="{:.3f} px")
    bias = abs(mean(deltas))
    rep.add("|bias_d|", bias, BIAS_BANDS, fmt="{:.3f} px")
    rep.add_raw("样本数", f"n={len(deltas)}")
    if bias > 0.05:
        rep.warn("bias_d 非零：提示 f / B / Z 向平移存在系统偏差，须溯源")
    return rep.emit(args.json_path)


if __name__ == "__main__":
    raise SystemExit(main())
