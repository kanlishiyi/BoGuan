"""
PDF 报告生成器
==============
将告警分析结果生成为结构化 PDF 文档，支持中文字体和自定义水印。

用法::

    from boguan.core.pdf import generate_report_pdf
    pdf_bytes = generate_report_pdf("488197", report_markdown_text)
"""

import re
import time

from fpdf import FPDF

from ..config import settings


class ReportPDF(FPDF):
    """支持中文和水印的告警分析 PDF 报告。"""

    _in_watermark: bool = False  # 水印绘制递归保护

    def __init__(self):
        super().__init__()
        self.add_font("msyh", "", settings.PDF_FONT_REGULAR, uni=True)
        self.add_font("msyh", "B", settings.PDF_FONT_BOLD, uni=True)
        self.set_auto_page_break(auto=True, margin=20)

    # ---- 页眉 ----
    def header(self):
        if self._in_watermark:
            return
        self._draw_watermark()
        self.set_font("msyh", "B", 10)
        self.set_text_color(120, 120, 120)
        self.cell(0, 8, "博观告警分析平台 - 智能分析报告", align="L")
        self.cell(
            0, 8, time.strftime("%Y-%m-%d %H:%M"),
            align="R", new_x="LMARGIN", new_y="NEXT",
        )
        self.set_draw_color(59, 130, 246)
        self.set_line_width(0.5)
        self.line(10, self.get_y(), self.w - 10, self.get_y())
        self.ln(6)

    # ---- 水印 ----
    def _draw_watermark(self):
        """在当前页绘制重复斜向水印。"""
        if self._in_watermark:
            return
        self._in_watermark = True

        orig_x, orig_y = self.get_x(), self.get_y()
        self.set_font("Helvetica", "B", 32)
        self.set_text_color(225, 228, 236)

        watermark_text = settings.PDF_WATERMARK_TEXT
        angle = -35
        row_gap, col_gap = 55, 100
        for row_y in range(10, int(self.h), row_gap):
            for col_x in range(0, int(self.w), col_gap):
                with self.rotation(angle, col_x, row_y):
                    self.text(col_x, row_y, watermark_text)

        self.set_xy(orig_x, orig_y)
        self._in_watermark = False

    # ---- 页脚 ----
    def footer(self):
        self.set_y(-15)
        self.set_font("msyh", "", 8)
        self.set_text_color(160, 160, 160)
        self.cell(0, 10, f"第 {self.page_no()} 页", align="C")

    # ---- 页面分区控制 ----
    def accept_page_break(self):
        if self._in_watermark:
            return False
        return super().accept_page_break()

    # ---- 内容方法 ----
    def add_title(self, alert_id: str):
        self.set_font("msyh", "B", 20)
        self.set_text_color(30, 41, 59)
        self.cell(0, 16, "告警分析报告", align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_font("msyh", "", 12)
        self.set_text_color(100, 116, 139)
        self.cell(
            0, 10, f"告警 ID: {alert_id}",
            align="C", new_x="LMARGIN", new_y="NEXT",
        )
        self.ln(8)

    def add_section(self, title: str):
        self.ln(4)
        y = self.get_y()
        self.set_fill_color(59, 130, 246)
        self.rect(10, y, 3, 8, "F")
        self.set_font("msyh", "B", 14)
        self.set_text_color(30, 41, 59)
        self.set_x(18)
        self.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(3)

    def add_subsection(self, title: str):
        self.ln(2)
        self.set_font("msyh", "B", 11)
        self.set_text_color(59, 130, 246)
        self.cell(0, 7, f"  {title}", new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def add_body(self, text: str):
        self.set_font("msyh", "", 10)
        self.set_text_color(51, 65, 85)
        for line in text.split("\n"):
            stripped = line.strip()
            if not stripped:
                self.ln(3)
                continue
            if stripped.startswith(("- ", "* ", "• ")):
                self.set_x(16)
                self.multi_cell(self.w - 30, 6, f"  \u2022 {stripped[2:]}")
            else:
                self.set_x(12)
                self.multi_cell(self.w - 24, 6, stripped)

    def add_key_value(self, key: str, value: str):
        self.set_font("msyh", "B", 10)
        self.set_text_color(71, 85, 105)
        x_start = 16
        self.set_x(x_start)
        key_w = self.get_string_width(f"{key}: ") + 2
        self.cell(key_w, 6, f"{key}: ")
        self.set_font("msyh", "", 10)
        self.set_text_color(51, 65, 85)
        self.multi_cell(self.w - x_start - key_w - 12, 6, value)


# ================================================================
# Markdown 报告解析
# ================================================================

def _parse_report_sections(text: str) -> list[dict]:
    """将 Markdown 风格的报告文本解析为结构化章节列表。"""
    sections: list[dict] = []
    current: dict | None = None

    for line in text.split("\n"):
        # Markdown 标题
        m = re.match(r"^(#{1,4})\s+(.+)", line)
        if m:
            if current:
                current["body"] = current["body"].strip()
                sections.append(current)
            level = len(m.group(1))
            current = {"level": level, "title": m.group(2).strip(), "body": ""}
            continue

        # 中文编号标题（一、二、三...）
        m2 = re.match(r"^[一二三四五六七八九十]+、\s*(.+)", line)
        if m2:
            if current:
                current["body"] = current["body"].strip()
                sections.append(current)
            current = {"level": 2, "title": line.strip(), "body": ""}
            continue

        # 加粗键值对
        m3 = re.match(r"^\*\*(.+?)\*\*\s*[:：]?\s*(.*)", line)
        if m3 and not line.strip().startswith("- **") and len(m3.group(1)) < 30:
            if current:
                current["body"] += line + "\n"
            continue

        if current:
            current["body"] += line + "\n"
        else:
            current = {"level": 0, "title": "", "body": line + "\n"}

    if current:
        current["body"] = current["body"].strip()
        sections.append(current)

    return sections


def generate_report_pdf(alert_id: str, report_text: str) -> bytes:
    """
    将 Markdown 报告文本生成为 PDF 字节内容。

    Args:
        alert_id: 告警 ID
        report_text: Markdown 格式的报告全文

    Returns:
        PDF 文件的字节内容
    """
    pdf = ReportPDF()
    pdf.add_page()
    pdf.add_title(alert_id)

    sections = _parse_report_sections(report_text)

    if not sections:
        pdf.add_body(report_text)
    else:
        for sec in sections:
            if sec["level"] <= 2 and sec["title"]:
                pdf.add_section(sec["title"])
            elif sec["title"]:
                pdf.add_subsection(sec["title"])

            if sec["body"]:
                body = sec["body"]
                body = re.sub(r"\*\*(.+?)\*\*", r"\1", body)
                body = re.sub(r"`(.+?)`", r"\1", body)
                pdf.add_body(body)

    return bytes(pdf.output())
