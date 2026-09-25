#!/usr/bin/env python3
"""T08 极线校正质量：e_y = |y_L - y_R| 统计与判档。

输入 CSV（首行表头）：
    y_l,y_r        # 校正后左右对应点的像素纵坐标，建议 >= 1000 对

用法:
    python scripts/eval_epipolar.py t08.csv [--json out.json]
"""

import argparse

from lbst_common import Report, mean, p95, read_csv_rows, rms

BANDS = (
    ("Mean(e_y)", (0.15, 0.25, 0.40)),
    ("RMS(e_y)", (0.20, 0.30, 0.50)),
    ("P95(e_y)", (0.40, 0.60, 1.00)),
    ("Max(e_y)", (1.0, 1.5, 2.0)),
)


def main():
    ap = argparse.ArgumentParser(description="T08 极线误差统计与判档")
    ap.add_argument("csv", help="输入 CSV：y_l,y_r（px，校正后）")
    ap.add_argument("--json", dest="json_path", help="结果导出 JSON 路径")
    args = ap.parse_args()

    eyes = [abs(num_l - num_r) for num_l, num_r in
            ((float(r["y_l"]), float(r["y_r"]))
             for r in read_csv_rows(args.csv))]

    values = {
        "Mean(e_y)": mean(eyes),
        "RMS(e_y)": rms(eyes),
        "P95(e_y)": p95(eyes),
        "Max(e_y)": max(eyes),
    }
    rep = Report("T08 极线校正质量判档")
    for name, limits in BANDS:
        rep.add(name, values[name], limits, fmt="{:.2f} px")
    rep.add_raw("样本数", f"n={len(eyes)}")
    if values["RMS(e_y)"] > 0.50:
        rep.warn("否决项 V2 触发：RMS(e_y) > 0.50 px，整体判 F")
    if len(eyes) < 1000:
        rep.warn("匹配点对 n < 1000，建议覆盖全视场与代表性距离补采")
    return rep.emit(args.json_path)


if __name__ == "__main__":
    raise SystemExit(main())
