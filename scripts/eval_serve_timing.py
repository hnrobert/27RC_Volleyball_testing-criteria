#!/usr/bin/env python3
"""T19 发球时机与自动击球闭环：成功率 / 时序误差 / 误触发判档。

输入 CSV（首行表头，每次击球试验一行）：
    speed_group,success,timing_err_ms
    # speed_group：低速/中速/高速（高速组判定含“高”或 high）
    # success：1 有效击中，0 未中；timing_err_ms 可留空（未中可无时序）

误触发率经 --false-triggers N --scenes N 提供（非时机挥拍数 / 场景总数）。

用法:
    python scripts/eval_serve_timing.py t19.csv \
        [--false-triggers 2 --scenes 60] [--json out.json]
"""

import argparse

from lbst_common import Report, read_csv_rows, rms

SUCCESS_BANDS_PCT = (90.0, 80.0, 70.0)
HIGH_SPEED_BANDS_PCT = (85.0, 75.0, 65.0)
TIMING_BANDS_MS = (20.0, 40.0, 80.0)
FALSE_TRIG_BANDS_PCT = (1.0, 3.0, 5.0)


def main():
    ap = argparse.ArgumentParser(description="T19 发球闭环判档")
    ap.add_argument("csv", help="输入 CSV：speed_group,success,timing_err_ms")
    ap.add_argument("--false-triggers", type=int, default=None,
                    help="非时机挥拍次数")
    ap.add_argument("--scenes", type=int, default=None,
                    help="误触发统计场景总数")
    ap.add_argument("--json", dest="json_path", help="结果导出 JSON 路径")
    args = ap.parse_args()

    n_all = n_hit = n_high = n_high_hit = 0
    timing_errs = []
    for row in read_csv_rows(args.csv):
        ok = int(float(row["success"]))
        n_all += 1
        n_hit += ok
        label = row["speed_group"]
        if "高" in label or "high" in label.lower():
            n_high += 1
            n_high_hit += ok
        err = row.get("timing_err_ms")
        if err not in (None, ""):
            timing_errs.append(float(err))

    rep = Report("T19 发球时机与自动击球闭环判档")
    rate = n_hit / n_all * 100 if n_all else 0.0
    rep.add("击球成功率(整体)", rate, SUCCESS_BANDS_PCT, upper=False,
            fmt="{:.2f}%")
    if n_high:
        rep.add("击球成功率(高速组)", n_high_hit / n_high * 100,
                HIGH_SPEED_BANDS_PCT, upper=False, fmt="{:.2f}%")
    else:
        rep.warn("无高速组样本，高速组成功率未判档")
    if timing_errs:
        rep.add("时序误差 RMS", rms(timing_errs), TIMING_BANDS_MS,
                fmt="{:.2f} ms")
    else:
        rep.warn("无时序误差数据，该项未判档")
    rep.add_raw("样本数", f"总 {n_all} 次，命中 {n_hit} 次")
    if args.false_triggers is not None and args.scenes:
        rep.add("误触发率", args.false_triggers / args.scenes * 100,
                FALSE_TRIG_BANDS_PCT, fmt="{:.2f}%")
    else:
        rep.warn("未提供 --false-triggers/--scenes，误触发率未判档")
    return rep.emit(args.json_path)


if __name__ == "__main__":
    raise SystemExit(main())
