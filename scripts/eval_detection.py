#!/usr/bin/env python3
"""T16 排球检测模型精度：Recall / Precision / 中心点误差判档。

输入 CSV（首行表头，每行一个检出或漏检事件）：
    segment,outcome,cx_err_px
    # outcome 取 TP / FP / FN；cx_err_px 仅 TP 行填写
    # （检出中心 vs 标注中心，px）；segment 为距离段标签，
    #  远段命名含“远”（或 far），如 近/中/远

用法:
    python scripts/eval_detection.py t16.csv [--json out.json]
"""

import argparse
from collections import defaultdict

from lbst_common import Report, mean, read_csv_rows

RECALL_BANDS_PCT = (99.0, 97.0, 95.0)
FAR_RECALL_BANDS_PCT = (97.0, 94.0, 90.0)
PRECISION_BANDS_PCT = (98.0, 95.0, 90.0)
CX_BANDS_PX = (2.0, 4.0, 8.0)


def main():
    ap = argparse.ArgumentParser(description="T16 检测模型精度判档")
    ap.add_argument("csv", help="输入 CSV：segment,outcome,cx_err_px")
    ap.add_argument("--json", dest="json_path", help="结果导出 JSON 路径")
    args = ap.parse_args()

    counts = defaultdict(lambda: {"TP": 0, "FP": 0, "FN": 0})
    cx_errs = []
    for row in read_csv_rows(args.csv):
        outcome = row["outcome"].strip().upper()
        if outcome not in ("TP", "FP", "FN"):
            raise SystemExit(
                f"错误：outcome 应为 TP/FP/FN，得到 {outcome!r}")
        counts[row["segment"].strip()][outcome] += 1
        if outcome == "TP" and row.get("cx_err_px") not in (None, ""):
            cx_errs.append(float(row["cx_err_px"]))

    def rates(keys):
        tp = sum(counts[k]["TP"] for k in keys)
        fp = sum(counts[k]["FP"] for k in keys)
        fn = sum(counts[k]["FN"] for k in keys)
        recall = tp / (tp + fn) * 100 if tp + fn else 0.0
        precision = tp / (tp + fp) * 100 if tp + fp else 0.0
        return recall, precision

    recall, precision = rates(list(counts))
    far_keys = [k for k in counts if "远" in k or "far" in k.lower()]

    rep = Report("T16 排球检测模型精度判档")
    rep.add("整体 Recall", recall, RECALL_BANDS_PCT, upper=False,
            fmt="{:.2f}%")
    if far_keys:
        far_recall, _ = rates(far_keys)
        rep.add("远段 Recall", far_recall, FAR_RECALL_BANDS_PCT,
                upper=False, fmt="{:.2f}%")
    else:
        rep.warn("无远段样本，远段 Recall 未判档")
    rep.add("Precision", precision, PRECISION_BANDS_PCT, upper=False,
            fmt="{:.2f}%")
    if cx_errs:
        rep.add("中心点误差(均值)", mean(cx_errs), CX_BANDS_PX,
                fmt="{:.2f} px")
        rep.add_raw("中心点误差(max)/样本数",
                    f"Max={max(cx_errs):.2f} px，n={len(cx_errs)}")
    else:
        rep.warn("无 TP 中心点误差数据，该项未判档")
    return rep.emit(args.json_path)


if __name__ == "__main__":
    raise SystemExit(main())
