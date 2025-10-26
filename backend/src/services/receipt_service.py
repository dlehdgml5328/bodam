"""기부 영수증 PDF 생성 서비스"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

# 한국 시간대 (KST = UTC+9)
KST = timezone(timedelta(hours=9))


@dataclass
class ReceiptData:
    donor_name: str
    fire_station_name: str
    amount: float
    issue_date: date
    receipt_number: str
    donor_email: str | None = None
    fire_station_region: str | None = None
    currency: str = "KRW"
    toss_order_id: str | None = None


class ReceiptService:
    """기부 영수증 PDF 생성 서비스"""

    def __init__(self):
        # 한글 폰트 등록 시도 (없으면 기본 폰트 사용)
        try:
            # NanumGothic 폰트가 시스템에 있다면 등록
            pdfmetrics.registerFont(TTFont("NanumGothic", "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"))
            self.font_name = "NanumGothic"
        except Exception:
            # 폰트가 없으면 Helvetica 사용
            self.font_name = "Helvetica"

    def render_pdf(self, data: ReceiptData) -> bytes:
        """
        기부 영수증 PDF 생성

        Args:
            data: 영수증 데이터

        Returns:
            PDF 바이너리 데이터
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=20*mm,
            leftMargin=20*mm,
            topMargin=20*mm,
            bottomMargin=20*mm,
        )

        # 스타일 정의
        styles = getSampleStyleSheet()

        # 제목 스타일
        title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Heading1"],
            fontName=self.font_name,
            fontSize=24,
            textColor=colors.HexColor("#DC2626"),  # Red-600
            alignment=TA_CENTER,
            spaceAfter=30,
        )

        # 본문 스타일
        body_style = ParagraphStyle(
            "CustomBody",
            parent=styles["Normal"],
            fontName=self.font_name,
            fontSize=11,
            alignment=TA_LEFT,
            spaceAfter=12,
        )

        # 문서 구성
        story = []

        # 제목
        story.append(Paragraph("기부 영수증", title_style))
        story.append(Spacer(1, 10*mm))

        # 기부 정보 테이블
        table_data = [
            ["영수증 번호", str(data.receipt_number)],
            ["기부자 성명", data.donor_name],
        ]

        if data.donor_email:
            table_data.append(["기부자 이메일", data.donor_email])

        # 금액 포맷팅
        if data.currency == "KRW":
            amount_str = f"{int(data.amount):,}원"
        else:
            amount_str = f"{data.amount:,.2f} {data.currency}"

        table_data.append(["기부 금액", amount_str])

        # 소방서 정보
        fire_station_info = data.fire_station_name
        if data.fire_station_region:
            fire_station_info += f" ({data.fire_station_region})"
        table_data.append(["기부처", fire_station_info])

        # 기부 일시 (한국시간으로 변환)
        if isinstance(data.issue_date, datetime):
            # timezone-aware datetime을 KST로 변환
            if data.issue_date.tzinfo is None:
                # naive datetime이면 UTC로 간주하고 KST로 변환
                kst_date = data.issue_date.replace(tzinfo=timezone.utc).astimezone(KST)
            else:
                kst_date = data.issue_date.astimezone(KST)
            date_str = kst_date.strftime("%Y년 %m월 %d일 %H:%M")
        else:
            date_str = data.issue_date.strftime("%Y년 %m월 %d일")
        table_data.append(["기부 일시", date_str])

        if data.toss_order_id:
            table_data.append(["주문 번호", data.toss_order_id])

        table = Table(table_data, colWidths=[60*mm, 100*mm])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F3F4F6")),  # Gray-100
            ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#1F2937")),  # Gray-800
            ("ALIGN", (0, 0), (0, -1), "LEFT"),
            ("ALIGN", (1, 0), (1, -1), "LEFT"),
            ("FONTNAME", (0, 0), (-1, -1), self.font_name),
            ("FONTSIZE", (0, 0), (-1, -1), 11),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
            ("TOPPADDING", (0, 0), (-1, -1), 12),
            ("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#E5E7EB")),  # Gray-200
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))

        story.append(table)
        story.append(Spacer(1, 15*mm))

        # 안내 문구
        notice_text = """
        본 영수증은 보담(BoDam) 플랫폼을 통해 진행된 기부 거래에 대한 증빙 서류입니다.<br/>
        기부금은 지정하신 소방서에 전액 전달되며, 소방관들의 복지 향상에 사용됩니다.<br/><br/>

        기부해주셔서 감사합니다.
        """
        story.append(Paragraph(notice_text, body_style))
        story.append(Spacer(1, 10*mm))

        # 발급일 (한국시간)
        issue_date_str = datetime.now(KST).strftime("%Y년 %m월 %d일")
        issue_text = f"<para align=right>발급일: {issue_date_str}</para>"
        story.append(Paragraph(issue_text, body_style))

        # 발급 기관
        story.append(Spacer(1, 5*mm))
        issuer_text = "<para align=right>보담(BoDam) 플랫폼</para>"
        story.append(Paragraph(issuer_text, body_style))

        # PDF 생성
        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()

        return pdf_bytes


__all__ = ["ReceiptService", "ReceiptData"]
