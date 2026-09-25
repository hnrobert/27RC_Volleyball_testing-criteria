#!/usr/bin/env python3
"""T17 检测推理速度：全链路延迟 / 帧率 / 长跑衰减判档。

输入 CSV（首行表头）：
    latency_ms        # 每帧全链路延迟（预处理 + 推理 + 后处理）

可选 --longrun 提供长跑（>= 10 min）段的同列 CSV，计算帧率衰减率。

用法:
    python scripts/eval_latency.py t17.csv [--longrun t17_long.csv] \
        [--json out.json]
"""

import argparse

from lbst_common import Report, mean, p95, percentile, read_csv_rows

P50_BANDS = (8.0, 12.0, 20.0)
P95_BANDS = (10.0, 15.0, 25.0)
FPS_BANDS = (60.0, 45.0, 30.0)
DEGRADE_BANDS_PCT = (5.0, 10.0, 20.0)


def load_latency(path):
    return [float(r["latency_ms"]) for r in read_csv_rows(path)]


def main():
    ap = argparse.ArgumentParser(description="T17 检测推理速度判档")
    ap.add_argument("csv", help="输入 CSV：latency_ms")
    ap.add_argument("--longrun", help="长跑段 CSV（同列），可选")
    ap.add_argument("--json", dest="json_path", help="结果导出 JSON 路径")
    args = ap.parse_args()

    lat = load_latency(args.csv)
    fps = 1000.0 / mean(lat) if lat else 0.0

    rep = Report("T17 检测推理速度判档")
    rep.add("延迟 P50", percentile(lat, 50), P50_BANDS, fmt="{:.2f} ms")
    rep.add("延迟 P95", p95(lat), P95_BANDS, fmt="{:.2f} ms")
    rep.add_raw("延迟 P99 / 均值",
                f"P99={percentile(lat, 99):.2f} ms，"
                f"mean={mean(lat):.2f} ms")
    rep.add("平均帧率", fps, FPS_BANDS, upper=False, fmt="{:.1f} FPS")
    rep.add_raw("样本数", f"n={len(lat)}")

    if args.longrun:
        lat2 = load_latency(args.longrun)
        fps2 = 1000.0 / mean(lat2) if lat2 else 0.0
        degrade = (fps - fps2) / fps * 100 if fps else 0.0
        rep.add("长跑帧率衰减", degrade, DEGRADE_BANDS_PCT, fmt="{:.2f}%")
    else:
        rep.warn("未提供 --longrun，长跑衰减未判档")
    return rep.emit(args.json_path)


if __name__ == "__main__":
    raise SystemExit(main())
