#!/usr/bin/env python3
"""T03 标定重复性：N 次独立标定的参数散布统计与判档。

输入 CSV（首行表头，每行一次独立标定，推荐 N = 10）：
    fx,fy,cx,cy,baseline_mm,roll_deg,pitch_deg,yaw_deg,rms

用法:
    python scripts/eval_repeatability.py t03.csv [--json out.json]
"""

import argparse

from lbst_common import Report, mean, read_csv_rows, sdev

SIGMA_REL_BANDS_PCT = (0.02, 0.05, 0.10)
SIGMA_C_BANDS = (0.5, 1.0, 2.0)
SIGMA_EULER_BANDS = (0.01, 0.02, 0.05)
KEYS = ("fx", "fy", "cx", "cy", "baseline_mm",
        "roll_deg", "pitch_deg", "yaw_deg", "rms")
EULERS = (("roll_deg", "roll"), ("pitch_deg", "pitch"),
          ("yaw_deg", "yaw"))


def main():
    ap = argparse.ArgumentParser(description="T03 标定重复性判档")
    ap.add_argument("csv", help="输入 CSV：" + ",".join(KEYS))
    ap.add_argument("--json", dest="json_path", help="结果导出 JSON 路径")
    args = ap.parse_args()

    rows = read_csv_rows(args.csv)
    cols = {k: [float(r[k]) for r in rows] for k in KEYS}

    def rel_sigma_pct(key):
        base = mean(cols[key])
        return sdev(cols[key]) / base * 100 if base else 0.0

    rep = Report("T03 标定重复性判档")
    n = len(rows)
    rep.add_raw("标定次数 N",
                f"N={n}" + ("（规程建议 10）" if n < 10 else ""))
    rep.add("sigma(B)/B", rel_sigma_pct("baseline_mm"),
            SIGMA_REL_BANDS_PCT, fmt="{:.4f}%")
    rep.add("sigma(fx)/fx", rel_sigma_pct("fx"), SIGMA_REL_BANDS_PCT,
            fmt="{:.4f}%")
    rep.add("sigma(fy)/fy", rel_sigma_pct("fy"), SIGMA_REL_BANDS_PCT,
            fmt="{:.4f}%")
    rep.add("sigma(cx)", sdev(cols["cx"]), SIGMA_C_BANDS, fmt="{:.3f} px")
    rep.add("sigma(cy)", sdev(cols["cy"]), SIGMA_C_BANDS, fmt="{:.3f} px")
    for key, name in EULERS:
        rep.add(f"sigma({name})", sdev(cols[key]), SIGMA_EULER_BANDS,
                fmt="{:.4f} deg")
    return rep.emit(args.json_path)


if __name__ == "__main__":
    raise SystemExit(main())
