import os
from pathlib import Path
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas to dynamically compute and print 'Page X of Y' in the footer.
    """
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super(NumberedCanvas, self).showPage()
        super(NumberedCanvas, self).save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#4a5568"))
        
        # Header (pages after first)
        if self._pageNumber > 1:
            self.drawString(36, 805, "IIT Gandhinagar — Academic Office — SAPC Course Proposal (ACAD-SAPC-01)")
            self.setStrokeColor(colors.HexColor("#cbd5e0"))
            self.setLineWidth(0.5)
            self.line(36, 800, 559, 800)
            
        # Footer
        self.setStrokeColor(colors.HexColor("#cbd5e0"))
        self.setLineWidth(0.5)
        self.line(36, 38, 559, 38)
        
        footer_text = "SAPC Course Proposal System — Academic Office, IIT Gandhinagar"
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawString(36, 26, footer_text)
        self.drawRightString(559, 26, page_str)
        self.restoreState()


class PDFGenerator:
    @staticmethod
    def generate_proposal_pdf(proposal_data, output_dir=None):
        """
        Generates a publication-grade ACAD-SAPC-01 Course Proposal PDF.
        Returns the absolute filepath and filename of the created PDF.
        """
        proposal_id = proposal_data.get('proposal_id', 'DRAFT')
        filename = f"{proposal_id}.pdf"
        
        if output_dir is None:
            from ..config import Config
            output_dir = Path(Config.PDF_STORAGE_DIR)
        else:
            output_dir = Path(output_dir)

        output_dir.mkdir(parents=True, exist_ok=True)
        filepath = output_dir / filename

        # A4 size is 595.27 x 841.89 points. 36pt = 0.5 inch margins. Printable width = 523pt.
        doc = SimpleDocTemplate(
            str(filepath),
            pagesize=A4,
            leftMargin=36,
            rightMargin=36,
            topMargin=42,
            bottomMargin=46
        )

        styles = getSampleStyleSheet()
        
        # Custom Typography
        style_title = ParagraphStyle(
            'HeaderTitle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=13,
            leading=16,
            textColor=colors.HexColor('#002147'),
            alignment=1 # Center
        )
        style_subtitle = ParagraphStyle(
            'HeaderSubtitle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=11,
            leading=14,
            textColor=colors.HexColor('#1a365d'),
            alignment=1
        )
        style_meta = ParagraphStyle(
            'HeaderMeta',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor('#4a5568'),
            alignment=2 # Right
        )
        style_cell_label = ParagraphStyle(
            'CellLabel',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor('#1a202c')
        )
        style_cell_value = ParagraphStyle(
            'CellValue',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor('#2d3748')
        )
        style_block_text = ParagraphStyle(
            'BlockText',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8.5,
            leading=12,
            textColor=colors.HexColor('#2d3748')
        )
        style_notice = ParagraphStyle(
            'NoticeText',
            parent=styles['Normal'],
            fontName='Helvetica-Oblique',
            fontSize=8,
            leading=10.5,
            textColor=colors.HexColor('#4a5568')
        )

        story = []

        # ---------------------------------------------------------
        # Document Header
        # ---------------------------------------------------------
        meta_text = f"<b>Form:</b> ACAD-SAPC-01<br/><b>Proposal ID:</b> {proposal_id}<br/><b>Status:</b> {proposal_data.get('status', 'Pending')}"
        if proposal_data.get('sapc_number'):
            meta_text += f"<br/><b>SAPC No:</b> {proposal_data.get('sapc_number')}"
        if proposal_data.get('approval_date'):
            app_d = str(proposal_data.get('approval_date'))[:10]
            meta_text += f"<br/><b>Approved:</b> {app_d}"

        header_table_data = [
            [
                Paragraph("<b>INDIAN INSTITUTE OF TECHNOLOGY GANDHINAGAR</b><br/>"
                          "<font size='9.5' color='#4a5568'>Academic Office — Senate Academic Programme Committee (SAPC)</font><br/>"
                          "<b>Proposal for New Courses / Modification of Existing Courses</b>", style_title),
                Paragraph(meta_text, style_meta)
            ]
        ]
        header_table = Table(header_table_data, colWidths=[385, 138])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('TOPPADDING', (0,0), (-1,-1), 0),
        ]))
        story.append(header_table)
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#002147"), spaceBefore=4, spaceAfter=8))

        # Helper to format field value
        def val(k, default="—"):
            v = proposal_data.get(k)
            if v is None or str(v).strip() == "":
                return default
            return str(v).strip()

        # ---------------------------------------------------------
        # Section 1: Course Identity & Proposers
        # ---------------------------------------------------------
        sub_date = proposal_data.get('submission_date', '')
        if isinstance(sub_date, datetime):
            sub_date_str = sub_date.strftime('%d %B %Y, %I:%M %p')
        elif sub_date:
            sub_date_str = str(sub_date)[:19].replace('T', ' ')
        else:
            sub_date_str = datetime.now().strftime('%d %B %Y')

        is_mod = proposal_data.get('is_modification', False)
        mod_text = f"YES (Existing Code: {val('existing_course_code')})" if is_mod else "NO (New Course Proposal)"

        s1_data = [
            [Paragraph("Title of the Course", style_cell_label), 
             Paragraph(f"<b>{val('course_title')}</b>", style_cell_value)],
            [Paragraph("Potential Instructor(s)", style_cell_label), 
             Paragraph(val('potential_instructors'), style_cell_value)],
            [Paragraph("Name of Proposer", style_cell_label), 
             Paragraph(val('proposer_name'), style_cell_value)],
            [Paragraph("Faculty / Recipient Email", style_cell_label), 
             Paragraph(val('faculty_email'), style_cell_value)],
            [Paragraph("Modification of Existing Course?", style_cell_label), 
             Paragraph(mod_text, style_cell_value)],
            [Paragraph("Date of Submission", style_cell_label), 
             Paragraph(sub_date_str, style_cell_value)]
        ]
        s1_table = Table(s1_data, colWidths=[150, 373])
        s1_table.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e0')),
            ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#f7fafc')),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('LEFTPADDING', (0,0), (-1,-1), 6),
            ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(s1_table)
        story.append(Spacer(1, 6))

        # ---------------------------------------------------------
        # Section 2: Structure, Level, L-T-P-C & Duration
        # ---------------------------------------------------------
        level_str = f"Level {val('course_level')}"
        if proposal_data.get('course_level_secondary'):
            level_str += f" & Level {proposal_data['course_level_secondary']}"
        level_note = " (Level 1–5: UG, Level 6: PG)"

        course_type_str = val('course_type')
        if course_type_str == 'Others' and proposal_data.get('course_type_other'):
            course_type_str += f" ({proposal_data['course_type_other']})"

        freq_str = val('expected_frequency')
        if freq_str == 'Others' and proposal_data.get('expected_frequency_other'):
            freq_str += f" ({proposal_data['expected_frequency_other']})"

        ltpc_breakdown = f"{val('course_l_t_p_c')} [L: {proposal_data.get('lecture_hours', 0)}, T: {proposal_data.get('tutorial_hours', 0)}, P: {proposal_data.get('practical_hours', 0)}, C: {proposal_data.get('credits', 0)}]"

        s2_data = [
            [Paragraph("Course Type", style_cell_label), Paragraph(course_type_str, style_cell_value),
             Paragraph("Course Level", style_cell_label), Paragraph(f"{level_str} <font size='7' color='#718096'>{level_note}</font>", style_cell_value)],
            [Paragraph("Course L-T-P-C", style_cell_label), Paragraph(ltpc_breakdown, style_cell_value),
             Paragraph("Course Duration", style_cell_label), Paragraph(val('course_duration'), style_cell_value)],
            [Paragraph("Expected Frequency of Offering", style_cell_label), Paragraph(freq_str, style_cell_value),
             Paragraph("Elective Basket for BTech", style_cell_label), Paragraph(val('elective_basket_btech', 'None / N/A'), style_cell_value)]
        ]
        s2_table = Table(s2_data, colWidths=[120, 141, 120, 142])
        s2_table.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e0')),
            ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#f7fafc')),
            ('BACKGROUND', (2,0), (2,-1), colors.HexColor('#f7fafc')),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('LEFTPADDING', (0,0), (-1,-1), 6),
            ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(s2_table)
        story.append(Spacer(1, 6))

        # ---------------------------------------------------------
        # Section 3: Curricular Classifications & Specializations
        # ---------------------------------------------------------
        btech_de = val('discipline_elective_btech', 'None')
        if proposal_data.get('discipline_basket_btech'):
            btech_de += f" (Basket: {proposal_data['discipline_basket_btech']})"

        minors_str = val('minors', 'None')
        if proposal_data.get('minor_basket_thematic_area'):
            minors_str += f" [Basket/Thematic Area: {proposal_data['minor_basket_thematic_area']}]"

        mtech_str = val('courses_discipline_mtech', 'None')
        if proposal_data.get('mtech_sub_specialization'):
            mtech_str += f" (Sub-spec: {proposal_data['mtech_sub_specialization']})"

        s3_data = [
            [Paragraph("Discipline-specific Elective (BTech)", style_cell_label), Paragraph(btech_de, style_cell_value)],
            [Paragraph("Minor(s) in (if applicable)", style_cell_label), Paragraph(minors_str, style_cell_value)],
            [Paragraph("Reason for Adding Course as Minor", style_cell_label), Paragraph(val('minor_reason', '—'), style_cell_value)],
            [Paragraph("Discipline-specific Elective (MSc)", style_cell_label), Paragraph(val('discipline_elective_msc', 'None'), style_cell_value)],
            [Paragraph("Courses Specified for MTech", style_cell_label), Paragraph(mtech_str, style_cell_value)],
            [Paragraph("Discipline-specific Elective (MDes)", style_cell_label), Paragraph(val('discipline_elective_mdes', 'None'), style_cell_value)],
            [Paragraph("Prior Knowledge / Expertise Expected", style_cell_label), Paragraph(val('prior_knowledge', 'None / Open to students meeting prerequisites'), style_cell_value)]
        ]

        # Append custom fields if provided
        custom_data_raw = proposal_data.get('custom_fields_data')
        if custom_data_raw:
            import json
            try:
                if isinstance(custom_data_raw, str):
                    cfields = json.loads(custom_data_raw)
                else:
                    cfields = custom_data_raw
                if isinstance(cfields, dict):
                    for cf_key, cf_val in cfields.items():
                        clean_label = cf_key.replace('_', ' ').title()
                        s3_data.append([
                            Paragraph(f"{clean_label} (Custom Field)", style_cell_label),
                            Paragraph(str(cf_val or '—'), style_cell_value)
                        ])
            except Exception:
                pass
        s3_table = Table(s3_data, colWidths=[175, 348])
        s3_table.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e0')),
            ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#f7fafc')),
            ('TOPPADDING', (0,0), (-1,-1), 3.5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3.5),
            ('LEFTPADDING', (0,0), (-1,-1), 6),
            ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(s3_table)
        story.append(Spacer(1, 8))

        # ---------------------------------------------------------
        # Section 4: Course Contents & Academic Syllabus
        # ---------------------------------------------------------
        def make_content_box(title, instruction, content):
            header_cell = [
                Paragraph(f"<b>{title}</b>" + (f" <font size='7.5' color='#718096'><i>{instruction}</i></font>" if instruction else ""), style_cell_label)
            ]
            content_cell = [
                Paragraph(content.replace('\n', '<br/>'), style_block_text)
            ]
            tbl = Table([[header_cell], [content_cell]], colWidths=[523])
            tbl.setStyle(TableStyle([
                ('BOX', (0,0), (-1,-1), 0.75, colors.HexColor('#002147')),
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#edf2f7')),
                ('TOPPADDING', (0,0), (-1,0), 3),
                ('BOTTOMPADDING', (0,0), (-1,0), 3),
                ('TOPPADDING', (0,1), (-1,1), 5),
                ('BOTTOMPADDING', (0,1), (-1,1), 6),
                ('LEFTPADDING', (0,0), (-1,-1), 6),
                ('RIGHTPADDING', (0,0), (-1,-1), 6),
            ]))
            return tbl

        story.append(make_content_box(
            "Course Contents",
            "[Please include one paragraph with relevant details of the contents, separated by semicolons]",
            val('course_contents')
        ))
        story.append(Spacer(1, 8))

        story.append(make_content_box(
            "Texts and References",
            "[Please include texts and references in standard format (MLA, APA etc.)]",
            val('texts_and_references')
        ))
        story.append(Spacer(1, 8))

        story.append(make_content_box(
            "Learning Outcomes",
            "",
            val('learning_outcomes')
        ))
        story.append(Spacer(1, 8))

        story.append(make_content_box(
            "Overlap with Other Approved Courses",
            "",
            val('overlap_courses', 'No significant overlap reported.')
        ))
        story.append(Spacer(1, 8))

        story.append(make_content_box(
            "Any Other Relevant Information Not Covered Above",
            "[May also include applications of concepts taught in the course for industry sectors/academia etc.]",
            val('other_relevant_info', 'None')
        ))
        story.append(Spacer(1, 10))

        # ---------------------------------------------------------
        # Institutional Sign-off and Routing Box (ACAD-SAPC-01 Notice)
        # ---------------------------------------------------------
        footer_notice_data = [
            [
                Paragraph("<b>Approval Protocol:</b> Course proposals are to be approved by the Chairman, Senate on recommendation of the SAPC.<br/>"
                          "<b>Office Routing:</b> Please send the completed course proposal form to <u>ar.ug@iitgn.ac.in</u>, with a copy to <u>doaa@iitgn.ac.in</u>.", style_notice)
            ]
        ]
        footer_tbl = Table(footer_notice_data, colWidths=[523])
        footer_tbl.setStyle(TableStyle([
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#a0aec0')),
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f7fafc')),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('LEFTPADDING', (0,0), (-1,-1), 6),
            ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(footer_tbl)

        # Build document with NumberedCanvas
        doc.build(story, canvasmaker=NumberedCanvas)

        return str(filepath), filename
