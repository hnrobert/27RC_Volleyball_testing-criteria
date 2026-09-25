#!/usr/bin/env python3
"""T14 时间同步：dt = t_L - t_R 序列统计与判档。

输入 CSV（首行表头）：
    dt_ms        # 每个同步事件的 dt（ms），建议 >= 100 个事件

用法:
    python scripts/eval_sync.py t14.csv [--json out.json]
"""

import argparse

from lbst_common import Report, mean, read_csv_rows, sdev

MEAN_BANDS = (0.1, 0.5, 1.0)
SIGMA_BANDS = (0.05, 0.2, 0.5)


def main():
    ap = argparse.ArgumentParser(description="T14 时间同步判档")
    ap.add_argument("csv", help="输入 CSV：dt_ms")
    ap.add_argument("--json", dest="json_path", help="结果导出 JSON 路径")
    args = ap.parse_args()

    dts = [float(r["dt_ms"]) for r in read_csv_rows(args.csv)]

    rep = Report("T14 时间同步判档")
    rep.add("|Mean(dt)|", abs(mean(dts)), MEAN_BANDS, fmt="{:.4f} ms")
    rep.add("sigma(dt)", sdev(dts), SIGMA_BANDS, fmt="{:.4f} ms")
    rep.add_raw(
        "Max|dt| / 样本数",
        f"Max={max(abs(d) for d in dts):.4f} ms，n={len(dts)}")
    if len(dts) < 100:
        rep.warn("同步事件 n < 100，建议补采")
    return rep.emit(args.json_path)


if __name__ == "__main__":
    raise SystemExit(main())
