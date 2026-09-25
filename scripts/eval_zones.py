#!/usr/bin/env python3
"""T04 标定板空间覆盖：3x3 分区误差矩阵与判档。

输入 CSV（首行表头）：
    zone,reproj_err,epipolar_err
    # zone 取 1..9：1 左上、2 上中、3 右上、4 左中、5 中心、
    #              6 右中、7 左下、8 下中、9 右下（逐角点/逐点一行）

用法:
    python scripts/eval_zones.py t04.csv [--json out.json]
"""

import argparse

from lbst_common import Report, read_csv_rows, rms

REPROJ_BANDS = (0.30, 0.45, 0.60)
RATIO_BANDS = (1.3, 1.6, 2.0)
EPIPOLAR_BANDS = (0.30, 0.40, 0.50)
EDGE_ZONES = (1, 2, 3, 4, 6, 7, 8, 9)
CENTER = 5


def show_matrix(name, per_zone):
    """打印 3x3 分区 RMS 矩阵（左上 -> 右下）。"""
    print(f"{name} RMS 3x3 矩阵（1 左上 -> 9 右下）：")
    for r in range(3):
        cells = [f"{per_zone.get(r * 3 + c + 1, float('nan')):7.3f}"
                 for c in range(3)]
        print("  " + " ".join(cells))
    print()


def main():
    ap = argparse.ArgumentParser(description="T04 分区覆盖判档")
    ap.add_argument("csv", help="输入 CSV：zone,reproj_err,epipolar_err")
    ap.add_argument("--json", dest="json_path", help="结果导出 JSON 路径")
    args = ap.parse_args()

    buckets = {z: {"reproj": [], "epi": []} for z in range(1, 10)}
    for row in read_csv_rows(args.csv):
        zone = int(float(row["zone"]))
        if zone not in buckets:
            raise SystemExit(f"错误：zone 应为 1..9，得到 {zone}")
        buckets[zone]["reproj"].append(float(row["reproj_err"]))
        buckets[zone]["epi"].append(float(row["epipolar_err"]))

    rep = Report("T04 标定板空间覆盖判档")
    missing = [z for z, v in buckets.items() if not v["reproj"]]
    if missing:
        rep.warn(f"分区 {missing} 无数据，判档仅基于已有分区")

    reproj_rms = {z: rms(v["reproj"]) for z, v in buckets.items()
                  if v["reproj"]}
    epi_rms = {z: rms(v["epi"]) for z, v in buckets.items() if v["epi"]}
    show_matrix("重投影", reproj_rms)
    show_matrix("极线", epi_rms)

    if reproj_rms:
        rep.add("最差分区重投影 RMS", max(reproj_rms.values()),
                REPROJ_BANDS, fmt="{:.3f} px")
        center = reproj_rms.get(CENTER, 0.0)
        edges = [reproj_rms[z] for z in EDGE_ZONES if z in reproj_rms]
        if center > 0 and edges:
            rep.add("边缘/中心 RMS 比", max(edges) / center,
                    RATIO_BANDS, fmt="{:.2f}")
    if epi_rms:
        rep.add("最差分区极线 RMS", max(epi_rms.values()), EPIPOLAR_BANDS,
                fmt="{:.3f} px")
    return rep.emit(args.json_path)


if __name__ == "__main__":
    raise SystemExit(main())
