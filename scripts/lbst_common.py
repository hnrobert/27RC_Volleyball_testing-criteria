"""长基线双目标定测试 —— 共用判档引擎与统计工具。

判档规则见 docs/test-procedures.md 第 2 节：定量指标四档打分
（优 100 / 良 80 / 合格 60 / 不合格 0），多指标取最低档（木桶原则）。
所有工具脚本仅依赖 Python 标准库（>= 3.8），无第三方依赖。
"""

import csv
import json
import math
from statistics import mean as _mean
from statistics import stdev as _stdev

BAND_ORDER = ("优", "良", "合格", "不合格")
BAND_SCORE = {"优": 100, "良": 80, "合格": 60, "不合格": 0}


def _tol(limit):
    """判档容差：吸收浮点尘埃（如 0.11-0.10 = 0.010000000000000009）。"""
    return max(abs(limit) * 1e-9, 1e-12)


def judge_le(value, limits):
    """上限型判档：value <= limits[0] 优，<= limits[1] 良，<= limits[2] 合格。"""
    for band, limit in zip(BAND_ORDER, limits):
        if value <= limit + _tol(limit):
            return band
    return "不合格"


def judge_ge(value, limits):
    """下限型判档（成功率类）：value >= limits[0] 优，依次类推。"""
    for band, limit in zip(BAND_ORDER, limits):
        if value >= limit - _tol(limit):
            return band
    return "不合格"


def dz_th_rel(z_m, f_px, b_m, dd_px=0.5):
    """理论深度相对误差 delta_Z_th / Z = Z * dd / (f * B)。"""
    return z_m * dd_px / (f_px * b_m)


def mean(values):
    """均值。空序列返回 0.0。"""
    return _mean(values) if values else 0.0


def sdev(values):
    """样本标准差。n < 2 时返回 0.0。"""
    return _stdev(values) if len(values) >= 2 else 0.0


def rms(values):
    """均方根。空序列返回 0.0。"""
    if not values:
        return 0.0
    return math.sqrt(sum(v * v for v in values) / len(values))


def percentile(values, q):
    """线性插值分位数，q 取 [0, 100]。"""
    xs = sorted(values)
    if not xs:
        return 0.0
    pos = (len(xs) - 1) * q / 100.0
    lo = math.floor(pos)
    hi = math.ceil(pos)
    if lo == hi:
        return xs[int(pos)]
    return xs[lo] + (xs[hi] - xs[lo]) * (pos - lo)


def p95(values):
    """95 分位数。"""
    return percentile(values, 95)


def linreg(xs, ys):
    """最小二乘线性拟合，返回 (slope, intercept, r2)。"""
    if len(xs) < 2 or len(xs) != len(ys):
        return 0.0, 0.0, 0.0
    mx, my = mean(xs), mean(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    syy = sum((y - my) ** 2 for y in ys)
    slope = sxy / sxx if sxx else 0.0
    r2 = sxy * sxy / (sxx * syy) if sxx and syy else 0.0
    return slope, my - slope * mx, r2


def read_csv_rows(path):
    """读取 CSV（首行表头，兼容 BOM），返回 list[dict]，跳过空行。"""
    with open(path, newline="", encoding="utf-8-sig") as fh:
        rows = [r for r in csv.DictReader(fh) if any(r.values())]
    if not rows:
        raise SystemExit(f"错误：{path} 无数据行")
    return rows


def num(row, key):
    """按列名取 float；缺列或非数值时报错退出。"""
    try:
        return float(row[key])
    except (KeyError, TypeError, ValueError):
        raise SystemExit(f"错误：CSV 缺少数值列 {key!r}") from None


def exit_code(band):
    """进程退出码：合格及以上 0，不合格 1（供 CI 判定）。"""
    return 1 if band == "不合格" else 0


class Report:
    """判档报告：逐行打印 指标/数值/阈值/档位/得分，按木桶原则汇总。"""

    def __init__(self, title):
        self.title = title
        self.rows = []
        self.warnings = []

    def add(self, metric, value, limits, text=None, fmt="{:.4g}",
            upper=True):
        """登记一个判档指标。text 覆盖数值显示，fmt 同时格式化阈值。"""
        if upper:
            band = judge_le(value, limits)
        else:
            band = judge_ge(value, limits)
        value_text = text if text is not None else fmt.format(value)
        limits_text = "/".join(fmt.format(v) for v in limits)
        self.rows.append((metric, value_text, limits_text, band))
        return band

    def add_raw(self, metric, text):
        """登记一个仅展示、不参与判档的行。"""
        self.rows.append((metric, text, "", None))

    def warn(self, message):
        """登记警告（打印在报告末尾，不参与判档）。"""
        self.warnings.append(message)

    def overall(self):
        """木桶原则：所有判档行中的最差档。无判档行时返回 None。"""
        bands = [b for _, _, _, b in self.rows if b is not None]
        if not bands:
            return None
        return max(bands, key=BAND_ORDER.index)

    def as_dict(self):
        """导出为可 JSON 序列化的 dict。"""
        return {
            "title": self.title,
            "rows": [
                {
                    "metric": m,
                    "value": v,
                    "limits": l,
                    "band": b,
                    "score": BAND_SCORE.get(b),
                }
                for m, v, l, b in self.rows
            ],
            "overall": self.overall(),
            "warnings": self.warnings,
        }

    def emit(self, json_path=None):
        """打印报告（可选导出 JSON），返回进程退出码。"""
        print(f"== {self.title} ==")
        print(f"{'指标':<24} {'数值':>12}  {'阈值 优/良/合格':<24}"
              f"{'档位':<4} {'得分':>4}")
        for metric, value, limits, band in self.rows:
            score = "" if band is None else str(BAND_SCORE[band])
            print(f"{metric:<24} {value:>12}  {limits:<24}"
                  f"{(band or ''):<4} {score:>4}")
        overall = self.overall()
        if overall is not None:
            print(f"单项档位（木桶原则）：{overall}"
                  f"（{BAND_SCORE[overall]} 分）")
        for message in self.warnings:
            print(f"!! {message}")
        if json_path:
            with open(json_path, "w", encoding="utf-8") as fh:
                json.dump(self.as_dict(), fh, ensure_ascii=False, indent=2)
                fh.write("\n")
            print(f"JSON 已写入：{json_path}")
        return exit_code(overall)
