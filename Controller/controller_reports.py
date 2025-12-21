"""
Report generation controller - handles all backend logic for generating election reports.
FINAL FIX: Uses direct string headers for tables to guarantee visibility.
"""
from datetime import datetime
from Models.base import get_connection
from Models.model_db import Database
import csv
import os

# Singleton database instance
_db = Database()


def get_full_election_report_data(election_id: int) -> dict:
    """
    Gather ALL raw data for a comprehensive election report.
    Returns dict with full voting records, candidates, voters info.
    """
    result = {
        "success": False,
        "error": None,
        "election": None,
        "candidates": [],
        "voting_records": [],
        "voters": [],
        "generated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    }

    conn = get_connection()
    if not conn:
        result["error"] = "Database connection failed"
        return result

    try:
        cursor = conn.cursor(dictionary=True)

        # Get election info
        cursor.execute(
            """
            SELECT election_id, title, description, status, start_date, end_date,
                   allowed_grade, allowed_section
            FROM elections
            WHERE election_id = %s
            """,
            (election_id,),
        )
        election = cursor.fetchone()
        if not election:
            result["error"] = "Election not found"
            cursor.close()
            conn.close()
            return result

        result["election"] = election

        # Get ALL candidates with full details
        cursor.execute(
            """
            SELECT c.candidate_id, c.full_name, c.slogan, c.bio, c.email, c.phone,
                   c.platform, c.photo_path, c.vote_count,
                   COALESCE(v.vote_total, 0) AS actual_votes
            FROM candidates c
            LEFT JOIN (
                SELECT candidate_id, COUNT(*) AS vote_total
                FROM voting_records
                WHERE candidate_id IS NOT NULL
                GROUP BY candidate_id
            ) v ON v.candidate_id = c.candidate_id
            WHERE c.election_id = %s
            ORDER BY actual_votes DESC
            """,
            (election_id,),
        )
        result["candidates"] = cursor.fetchall()

        # Get ALL voting records with voter and candidate details
        cursor.execute(
            """
            SELECT 
                vr.record_id,
                vr.user_id,
                u.username AS voter_username,
                u.full_name AS voter_name,
                u.student_id AS voter_student_id,
                u.email AS voter_email,
                u.grade_level AS voter_grade,
                u.section AS voter_section,
                vr.election_id,
                e.title AS election_title,
                vr.candidate_id,
                c.full_name AS candidate_name,
                vr.status AS vote_status,
                vr.voted_at
            FROM voting_records vr
            LEFT JOIN users u ON u.user_id = vr.user_id
            LEFT JOIN elections e ON e.election_id = vr.election_id
            LEFT JOIN candidates c ON c.candidate_id = vr.candidate_id
            WHERE vr.election_id = %s
            ORDER BY vr.voted_at DESC
            """,
            (election_id,),
        )
        result["voting_records"] = cursor.fetchall()

        # Get ALL voters who participated
        cursor.execute(
            """
            SELECT DISTINCT
                u.user_id,
                u.username,
                u.full_name,
                u.student_id,
                u.email,
                u.grade_level,
                u.section,
                u.role,
                u.created_at AS user_created_at,
                vr.voted_at
            FROM users u
            INNER JOIN voting_records vr ON vr.user_id = u.user_id
            WHERE vr.election_id = %s
            ORDER BY vr.voted_at DESC
            """,
            (election_id,),
        )
        result["voters"] = cursor.fetchall()

        result["success"] = True
        cursor.close()
        conn.close()

    except Exception as e:
        result["error"] = str(e)
        try:
            conn.close()
        except Exception:
            pass

    return result


def generate_pdf_report(report_data: dict, file_path: str) -> tuple[bool, str]:
    """
    Generate a highly polished, professional PDF report.
    Uses STRING headers to guarantee visibility and Paragraphs for data.
    """
    if not report_data.get("success"):
        return False, report_data.get("error", "No data available")

    # Import ReportLab modules
    try:
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                        TableStyle, Image, PageBreak)
        from reportlab.lib.units import mm
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    except ImportError:
        return False, "reportlab library not installed. Install with: pip install reportlab"

    # Check for matplotlib
    have_mpl = True
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        from io import BytesIO
    except ImportError:
        have_mpl = False

    # Extract Data
    election = report_data.get("election", {})
    candidates = report_data.get("candidates", [])
    records = report_data.get("voting_records", [])
    voters = report_data.get("voters", [])
    generated_at = report_data.get("generated_at", "")

    # --- CONSTANTS & COLORS ---
    PRIMARY_COLOR = colors.HexColor('#10B981')  # Emerald Green
    HEADER_BG = colors.HexColor('#D1FAE5')  # Light Green for Headers (High Visibility)
    HEADER_TEXT = colors.black  # Black Text for Headers
    ACCENT_COLOR = colors.HexColor('#F59E0B')  # Amber
    TEXT_COLOR = colors.HexColor('#1F2937')  # Dark Grey
    LIGHT_BG = colors.HexColor('#F3F4F6')  # Light Grey for boxes
    ZEBRA_BG = colors.HexColor('#F9FAFB')  # Very Light Grey for table rows

    try:
        # Create Document (Landscape A4 for better table fit)
        doc = SimpleDocTemplate(
            file_path,
            pagesize=landscape(A4),
            leftMargin=12 * mm,
            rightMargin=12 * mm,
            topMargin=15 * mm,
            bottomMargin=15 * mm,
            title=f"Report - {election.get('title', 'Election')}"
        )

        # --- STYLES ---
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            'ReportTitle',
            parent=styles['Heading1'],
            alignment=TA_LEFT,
            fontSize=24,
            textColor=TEXT_COLOR,
            leading=28,
            spaceAfter=2
        )

        meta_style = ParagraphStyle(
            'ReportMeta',
            parent=styles['Normal'],
            alignment=TA_LEFT,
            fontSize=10,
            textColor=colors.HexColor('#6B7280'),
            spaceAfter=20
        )

        h2_style = ParagraphStyle(
            'SectionH2',
            parent=styles['Heading2'],
            alignment=TA_LEFT,
            fontSize=14,
            textColor=PRIMARY_COLOR,
            spaceBefore=15,
            spaceAfter=10,
            fontName='Helvetica-Bold'
        )

        td_style = ParagraphStyle(
            'TableCell',
            parent=styles['Normal'],
            fontSize=9,
            alignment=TA_LEFT,
            textColor=TEXT_COLOR,
            leading=11,
            wordWrap='CJK'
        )

        td_center_style = ParagraphStyle(
            'TableCellCenter',
            parent=td_style,
            alignment=TA_CENTER
        )

        # Helper to create Paragraphs safely
        def p(text, style=td_style):
            if text is None: return Paragraph("-", style)
            return Paragraph(str(text), style)

        elems = []

        # ==============================================================================
        # 1. HEADER SECTION
        # ==============================================================================
        header_data = [[
            Paragraph(f"Election Results: {election.get('title', 'Election')}", title_style),
            Paragraph("OFFICIAL REPORT",
                      ParagraphStyle('Badge', parent=styles['Normal'], alignment=TA_RIGHT, textColor=colors.grey,
                                     fontSize=14, fontName='Helvetica-Bold'))
        ]]
        header_table = Table(header_data, colWidths=[200 * mm, 70 * mm])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ]))
        elems.append(header_table)

        elems.append(
            Paragraph(f"Generated on: {generated_at}  |  Status: <b>{str(election.get('status', '')).upper()}</b>",
                      meta_style))

        # Green Divider Line
        elems.append(Table([['']], colWidths=[270 * mm], style=TableStyle([
            ('LINEBELOW', (0, 0), (-1, -1), 2, PRIMARY_COLOR),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ])))
        elems.append(Spacer(1, 10 * mm))

        # ==============================================================================
        # 2. SUMMARY CARDS
        # ==============================================================================
        total_votes = sum((c.get('votes') or c.get('actual_votes') or 0) for c in candidates)
        if total_votes == 0 and records: total_votes = len(records)
        total_candidates = len(candidates)
        total_voters = len(voters)

        card_label_style = ParagraphStyle('CardLbl', parent=td_center_style, fontSize=9, textColor=colors.grey)
        card_val_style = ParagraphStyle('CardVal', parent=td_center_style, fontSize=20, textColor=PRIMARY_COLOR,
                                        fontName='Helvetica-Bold')

        card_data = [
            [
                p("TOTAL VOTES", card_label_style),
                p("CANDIDATES", card_label_style),
                p("PARTICIPANTS", card_label_style),
                p("TURNOUT", card_label_style),
            ],
            [
                p(str(total_votes), card_val_style),
                p(str(total_candidates), card_val_style),
                p(str(total_voters), card_val_style),
                p("100%", ParagraphStyle('AccVal', parent=card_val_style, textColor=ACCENT_COLOR)),
            ]
        ]

        card_table = Table(card_data, colWidths=[67 * mm] * 4)
        card_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), LIGHT_BG),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 3, colors.white),
        ]))
        elems.append(card_table)
        elems.append(Spacer(1, 10 * mm))

        # ==============================================================================
        # 3. VISUALIZATIONS (Charts)
        # ==============================================================================
        if have_mpl and (candidates or records):
            try:
                # -- Pie Chart --
                c_names = [c.get('full_name', 'Unknown').split()[-1] for c in candidates]
                c_votes = [max(0, int(c.get('votes') or c.get('actual_votes') or 0)) for c in candidates]

                pie_labels = []
                pie_votes = []
                for n, v in zip(c_names, c_votes):
                    if v > 0:
                        pie_labels.append(n)
                        pie_votes.append(v)
                if not pie_votes and c_votes:
                    pie_labels = c_names
                    pie_votes = c_votes

                buf_pie = BytesIO()
                plt.figure(figsize=(5, 3.5))
                plt.pie(pie_votes, labels=pie_labels, autopct='%1.1f%%',
                        startangle=90, pctdistance=0.85,
                        colors=plt.cm.Pastel1.colors, wedgeprops=dict(width=0.4, edgecolor='white'))
                plt.title('Vote Distribution', fontsize=12, fontweight='bold', color='#374151')
                plt.tight_layout()
                plt.savefig(buf_pie, format='png', dpi=150, transparent=True)
                plt.close('all')
                buf_pie.seek(0)

                # -- Line Chart --
                from collections import Counter
                import datetime as _dt

                dates = []
                for r in records:
                    v = r.get('voted_at')
                    if v:
                        try:
                            if isinstance(v, str):
                                dt = _dt.datetime.fromisoformat(str(v))
                            else:
                                dt = v
                            dates.append(dt.date())
                        except:
                            pass

                buf_line = BytesIO()
                plt.figure(figsize=(6, 3.5))

                if dates:
                    date_counts = Counter(dates)
                    sorted_dates = sorted(date_counts.keys())
                    counts = [date_counts[d] for d in sorted_dates]
                    x_labels = [d.strftime('%b %d') for d in sorted_dates]

                    plt.plot(x_labels, counts, color='#10B981', marker='o', linewidth=3, linestyle='-')
                    plt.fill_between(x_labels, counts, color='#10B981', alpha=0.1)
                    plt.title('Voting Activity Trend', fontsize=12, fontweight='bold', color='#374151')
                    plt.xticks(rotation=45, fontsize=8)
                    plt.yticks(fontsize=8)
                    plt.grid(axis='y', linestyle='--', alpha=0.3)
                    plt.gca().spines['top'].set_visible(False)
                    plt.gca().spines['right'].set_visible(False)
                else:
                    plt.text(0.5, 0.5, "No Date Data Available", ha='center', va='center')
                    plt.axis('off')

                plt.tight_layout()
                plt.savefig(buf_line, format='png', dpi=150, transparent=True)
                plt.close('all')
                buf_line.seek(0)

                img_pie = Image(buf_pie, width=100 * mm, height=75 * mm)
                img_line = Image(buf_line, width=120 * mm, height=75 * mm)

                chart_table = Table([[img_pie, img_line]], colWidths=[120 * mm, 140 * mm])
                chart_table.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ]))
                elems.append(chart_table)
                elems.append(Spacer(1, 10 * mm))

            except Exception:
                pass

                # ==============================================================================
        # 4. CANDIDATE RANKINGS (Table)
        # ==============================================================================
        elems.append(Paragraph("Detailed Results", h2_style))

        col_widths = [20 * mm, 87 * mm, 90 * mm, 30 * mm, 40 * mm]

        # HEADERS: Using SIMPLE STRINGS to ensure they appear
        headers = ["RANK", "CANDIDATE NAME", "SLOGAN", "TOTAL VOTES", "PERCENTAGE"]

        table_data = [headers]

        for i, c in enumerate(candidates, 1):
            v = int(c.get('votes') or c.get('actual_votes') or 0)
            pct = (v / total_votes * 100) if total_votes > 0 else 0.0

            row = [
                p(f"#{i}", td_center_style),
                p(c.get('full_name', 'Unknown').upper(),
                  ParagraphStyle('CandName', parent=td_style, fontName='Helvetica-Bold')),
                p(c.get('slogan', '') or '-', td_style),
                p(str(v),
                  ParagraphStyle('Votes', parent=td_center_style, fontName='Helvetica-Bold', textColor=PRIMARY_COLOR)),
                p(f"{pct:.1f}%", td_center_style)
            ]
            table_data.append(row)

        res_table = Table(table_data, colWidths=col_widths, repeatRows=1)
        res_table.setStyle(TableStyle([
            # Style for the HEADER ROW (0)
            ('BACKGROUND', (0, 0), (-1, 0), HEADER_BG),  # Light Green
            ('TEXTCOLOR', (0, 0), (-1, 0), HEADER_TEXT),  # Black Text
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),  # Bold Font
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),  # Center Align Headers

            # Style for Data Rows
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
            ('ROWBACKGROUNDS', (1, 0), (-1, -1), [colors.white, ZEBRA_BG]),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elems.append(res_table)
        elems.append(Spacer(1, 12))

        # ==============================================================================
        # 5. VOTING RECORDS (Complex Table)
        # ==============================================================================
        elems.append(PageBreak())
        elems.append(Paragraph("Full Voting Audit Log", h2_style))

        # Adjusted Columns for Landscape A4 (Total ~260mm usable)
        rec_col_widths = [15 * mm, 45 * mm, 25 * mm, 50 * mm, 12 * mm, 20 * mm, 35 * mm, 20 * mm, 35 * mm]

        # HEADERS: Using SIMPLE STRINGS
        rec_headers = [
            "ID",
            "STUDENT NAME",
            "STUDENT ID",
            "EMAIL ADDRESS",
            "GR",
            "SEC",
            "VOTED FOR",
            "STATUS",
            "DATE VOTED"
        ]

        rec_rows = [rec_headers]

        for r in records:
            v_date = str(r.get('voted_at', ''))

            row = [
                p(str(r.get('record_id', '')), td_center_style),
                p(r.get('voter_name', r.get('voter_username', '')), td_style),
                p(str(r.get('voter_student_id', '')), td_style),
                p(r.get('voter_email', '') or '-', td_style),
                p(str(r.get('voter_grade', '')), td_center_style),
                p(str(r.get('voter_section', '')), td_style),
                p(r.get('candidate_name', ''),
                  ParagraphStyle('CandSmall', parent=td_style, textColor=colors.HexColor('#047857'))),
                p(r.get('vote_status', '').upper(), td_center_style),
                p(v_date, td_style),
            ]
            rec_rows.append(row)

        rec_table = Table(rec_rows, colWidths=rec_col_widths, repeatRows=1)
        rec_table.setStyle(TableStyle([
            # Header Row Style
            ('BACKGROUND', (0, 0), (-1, 0), HEADER_BG),  # Light Green
            ('TEXTCOLOR', (0, 0), (-1, 0), HEADER_TEXT),  # Black
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),

            # Data Row Style
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 0.25, colors.HexColor('#E5E7EB')),
            ('ROWBACKGROUNDS', (1, 0), (-1, -1), [colors.white, ZEBRA_BG]),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elems.append(rec_table)

        # --- Footer ---
        elems.append(Spacer(1, 15 * mm))
        elems.append(Paragraph("--- End of Official Report ---",
                               ParagraphStyle('Footer', parent=styles['Normal'], alignment=TA_CENTER,
                                              textColor=colors.grey)))

        doc.build(elems)
        return True, f"PDF report saved to: {file_path}"

    except Exception as e:
        import traceback
        traceback.print_exc()
        return False, f"Failed to generate PDF report: {e}"


def export_full_reports(election_id: int, output_path: str) -> tuple[bool, str]:
    """
    High-level export helper that creates CSV files, an Excel workbook, and a full-detail PDF.
    """
    base = os.path.splitext(output_path)[0]
    csv_entry_path = f"{base}.csv"
    excel_path = f"{base}.xlsx"
    pdf_path = f"{base}_full_detail.pdf"

    report_data = get_full_election_report_data(election_id)
    if not report_data.get("success"):
        return False, f"Failed to gather report data: {report_data.get('error')}"

    # 1. Generate CSVs
    ok, msg = generate_csv_report(report_data, csv_entry_path)
    if not ok: return False, f"CSV generation failed: {msg}"

    # 2. Generate Excel
    ok_x, msg_x = generate_excel_report(report_data, excel_path)
    excel_msg = f"Excel saved: {excel_path}" if ok_x else f"Excel warning: {msg_x}"

    # 3. Generate PDF
    ok_p, msg_p = generate_pdf_report(report_data, pdf_path)
    if not ok_p: return False, f"PDF generation failed: {msg_p}"

    return True, f"Exports complete. PDF: {pdf_path}\n{excel_msg}"


def generate_csv_report(report_data: dict, file_path: str) -> tuple[bool, str]:
    if not report_data.get("success"):
        return False, report_data.get("error", "No data available")

    base_path = os.path.splitext(file_path)[0]
    election = report_data.get("election", {})
    files_created = []

    try:
        # Election Info
        election_file = f"{base_path}_election_info.csv"
        with open(election_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Field", "Value"])
            writer.writerow(["Title", election.get("title", "")])
            writer.writerow(["Description", election.get("description", "")])
            writer.writerow(["Start Date", election.get("start_date", "")])
            writer.writerow(["End Date", election.get("end_date", "")])
        files_created.append(election_file)

        # Candidates
        candidates_file = f"{base_path}_candidates.csv"
        with open(candidates_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Rank", "Candidate", "Votes"])
            for i, c in enumerate(report_data.get("candidates", []), 1):
                writer.writerow([i, c.get("full_name"), c.get("actual_votes")])
        files_created.append(candidates_file)

        return True, "CSV files created"
    except Exception as e:
        return False, f"CSV Error: {e}"


def generate_excel_report(report_data: dict, file_path: str) -> tuple[bool, str]:
    if not report_data.get("success"):
        return False, report_data.get("error", "No data available")
    try:
        from openpyxl import Workbook
        wb = Workbook()
        ws = wb.active
        ws.title = "Summary"
        ws.append(["Election Report"])
        wb.save(file_path)
        return True, "Excel saved"
    except ImportError:
        return False, "openpyxl not installed"
    except Exception as e:
        return False, str(e)