#!/usr/bin/env python3
"""T12 机械稳定性 / T13 温度稳定性：标定参数漂移统计与判档。

输入 CSV（首行表头，每行一次复测标定）：
    fx,fy,cx,cy,baseline_mm,roll_deg,pitch_deg,yaw_deg[,temp_c][,er_rms]
    # temp_c：T13 必填（温点，摄氏度）；er_rms：可选，该次复测深度 Er(RMS)

模式：
    t12：首行为初始基准，逐行计算 |dB|/B、dR（任一欧拉角最大）、
         Er 恶化系数；任一 |dB|/B 或 dR 超合格档即提示否决项 V3。
    t13：按温度线性回归，指标以每 10 摄氏度变化量表征（取最大漂移）。

用法:
    python scripts/eval_drift.py t12.csv --mode t12 [--json out.json]
    python scripts/eval_drift.py t13.csv --mode t13 [--json out.json]
"""

import argparse

from lbst_common import Report, linreg, read_csv_rows

BASE_KEYS = ("fx", "fy", "cx", "cy", "baseline_mm",
             "roll_deg", "pitch_deg", "yaw_deg")
DB_BANDS_PCT = (0.02, 0.05, 0.10)
DR_BANDS_DEG = (0.01, 0.02, 0.05)
KAPPA_BANDS = (1.1, 1.2, 1.5)
RATE_REL_BANDS_PCT = (0.02, 0.05, 0.10)
RATE_C_BANDS_PX = (0.5, 1.0, 2.0)


def parse_rows(path):
    data = []
    for row in read_csv_rows(path):
        item = {k: float(row[k]) for k in BASE_KEYS}
        for extra in ("temp_c", "er_rms"):
            value = row.get(extra)
            if value not in (None, ""):
                item[extra] = float(value)
        data.append(item)
    return data


def run_t12(data, json_path):
    base = data[0]
    rep = Report("T12 机械稳定性判档（基准 = 首行）")
    for i, cur in enumerate(data[1:], start=1):
        db = (abs(cur["baseline_mm"] - base["baseline_mm"])
              / base["baseline_mm"] * 100)
        rep.add(f"工况{i} |dB|/B", db, DB_BANDS_PCT, fmt="{:.4f}%")
        dr = max(abs(cur[k] - base[k])
                 for k in ("roll_deg", "pitch_deg", "yaw_deg"))
        rep.add(f"工况{i} dR(max)", dr, DR_BANDS_DEG, fmt="{:.4f} deg")
        if "er_rms" in cur and base.get("er_rms"):
            rep.add(f"工况{i} Er 恶化系数", cur["er_rms"] / base["er_rms"],
                    KAPPA_BANDS, fmt="{:.3f}")
    fail_core = any(
        b == "不合格" for m, _, _, b in rep.rows
        if "|dB|" in m or "dR" in m)
    if fail_core:
        rep.warn("否决项 V3 触发（标定失效）：须重新标定并复测 T01-T10")
    return rep.emit(json_path)


def run_t13(data, json_path):
    temps = [d["temp_c"] for d in data]
    rep = Report("T13 温度稳定性判档（指标按每 10 摄氏度变化量）")

    def rate_rel_pct(key):
        base = sum(d[key] for d in data) / len(data)
        slope = linreg(temps, [d[key] for d in data])[0]
        return abs(slope) * 10 / abs(base) * 100 if base else 0.0

    f_rates = [rate_rel_pct(k) for k in ("fx", "fy")]
    rep.add("|df/f|/10C (fx,fy)", max(f_rates), RATE_REL_BANDS_PCT,
            fmt="{:.4f}%")
    rep.add("|dB|/B /10C", rate_rel_pct("baseline_mm"),
            RATE_REL_BANDS_PCT, fmt="{:.4f}%")
    c_rates = [abs(linreg(temps, [d[k] for d in data])[0]) * 10
               for k in ("cx", "cy")]
    rep.add("|dc|/10C (cx,cy)", max(c_rates), RATE_C_BANDS_PX,
            fmt="{:.3f} px")
    if all("er_rms" in d for d in data) and data[0]["er_rms"]:
        slope = linreg(temps, [d["er_rms"] for d in data])[0]
        rep.add("Er 恶化/10C", abs(slope) * 10 / data[0]["er_rms"],
                KAPPA_BANDS, fmt="{:.3f}")
    rep.add_raw("温点",
                f"{len(temps)} 点：" + ",".join(f"{t:g}" for t in temps)
                + " 摄氏度")
    return rep.emit(json_path)


def main():
    ap = argparse.ArgumentParser(description="T12/T13 参数漂移判档")
    ap.add_argument("csv", help="输入 CSV（表头见模块 docstring）")
    ap.add_argument("--mode", choices=("t12", "t13"), required=True)
    ap.add_argument("--json", dest="json_path", help="结果导出 JSON 路径")
    args = ap.parse_args()

    data = parse_rows(args.csv)
    if args.mode == "t12":
        if len(data) < 2:
            raise SystemExit("错误：T12 至少需要 2 行（基准 + 工况）")
        return run_t12(data, args.json_path)
    if any("temp_c" not in d for d in data):
        raise SystemExit("错误：--mode t13 需要每行提供 temp_c 列")
    return run_t13(data, args.json_path)


if __name__ == "__main__":
    raise SystemExit(main())
