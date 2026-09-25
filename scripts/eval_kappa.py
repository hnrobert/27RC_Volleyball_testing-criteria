#!/usr/bin/env python3
"""恶化系数 kappa 判档（T10 / T11 / T12 / T13 / T15 通用）。

kappa = 工况指标 / 基准指标，阈值按测试项选择：
    t10 / t11 / t15 : 优 1.2 / 良 1.5 / 合格 2.0
    t12 / t13       : 优 1.1 / 良 1.2 / 合格 1.5

用法:
    python scripts/eval_kappa.py --base 0.55 --values 0.62,0.71 \
        --bands t10
"""

import argparse

from lbst_common import Report

KAPPA_BANDS = {
    "t10": (1.2, 1.5, 2.0),
    "t11": (1.2, 1.5, 2.0),
    "t15": (1.2, 1.5, 2.0),
    "t12": (1.1, 1.2, 1.5),
    "t13": (1.1, 1.2, 1.5),
}


def main():
    ap = argparse.ArgumentParser(description="恶化系数 kappa 判档")
    ap.add_argument("--base", type=float, required=True,
                    help="基准指标值（正对姿态 / 静态 / 初始的误差）")
    ap.add_argument("--values", required=True, help="逗号分隔的工况指标值")
    ap.add_argument("--bands", choices=sorted(KAPPA_BANDS), default="t10",
                    help="阈值组（对应测试编号），默认 t10")
    ap.add_argument("--json", dest="json_path", help="结果导出 JSON 路径")
    args = ap.parse_args()

    if args.base <= 0:
        raise SystemExit("错误：--base 必须为正数")
    values = [float(x) for x in args.values.split(",") if x.strip()]
    if not values:
        raise SystemExit("错误：--values 为空")

    rep = Report(f"恶化系数判档（阈值组 {args.bands}）")
    for i, value in enumerate(values, start=1):
        rep.add(f"工况{i} kappa", value / args.base,
                KAPPA_BANDS[args.bands], fmt="{:.3f}")
    rep.add_raw("kappa(max)", f"{max(v / args.base for v in values):.3f}")
    return rep.emit(args.json_path)


if __name__ == "__main__":
    raise SystemExit(main())
