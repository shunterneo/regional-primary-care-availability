#!/usr/bin/env python3
"""Build privacy-preserving static site, DOCX directory, PDF directory from a single JSON database."""
from __future__ import annotations
import datetime, json, pathlib, html, sys, collections, os
from common import ROOT, STATUSES, CITY_COORDS, load_data, effective_status
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, PageBreak
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.units import inch
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

today=datetime.date.today()
site=ROOT/'site'; docs=site/'documents'; docs.mkdir(parents=True,exist_ok=True)
D=load_data(); archived=[c for c in D['clinics'] if c.get('operating_status') in ('closed','archived')]; clinics=[c for c in D['clinics'] if c.get('operating_status') not in ('closed','archived')]; source_state=json.loads((ROOT/'data'/'source_state.json').read_text()); queue=json.loads((ROOT/'data'/'review_queue.json').read_text()); history=json.loads((ROOT/'data'/'review_history.json').read_text()); discovery=json.loads((ROOT/'data'/'discovery_queue.json').read_text()); discovery_state=json.loads((ROOT/'data'/'discovery_state.json').read_text())
for c in clinics: c['display_status']=effective_status(c,today)
ORDER=['accepting','reported','limited','waitlist','not_accepting','needs_review','unknown']
clinics.sort(key=lambda c:(ORDER.index(c['display_status']),c['community'].lower(),c['name'].lower()))
counts=collections.Counter(c['display_status'] for c in clinics)
report={
 'generated_on':today.isoformat(),'data_as_of':D.get('data_as_of',''),'count':len(clinics),'archived_count':len(archived),
 'communities':len({c['community'] for c in clinics}), 'status_counts':dict(counts),
 'source_urls_monitored':len(source_state['sources']),'pending_source_reviews':len([r for r in queue['items'] if r.get('review_status')=='pending']),
 'pending_new_clinic_leads':len([r for r in discovery['items'] if r.get('review_status')=='pending']),
 'last_source_scan':source_state.get('last_run'),'last_discovery_scan':discovery_state.get('last_run'),
}
(site/'report.json').write_text(json.dumps(report,indent=2)+'\n')

# DOCX helpers
def add_link(p, label, url):
    from docx.opc.constants import RELATIONSHIP_TYPE as RT
    part=p.part; rid=part.relate_to(url,RT.HYPERLINK,is_external=True)
    h=OxmlElement('w:hyperlink');h.set(qn('r:id'),rid)
    run=OxmlElement('w:r');props=OxmlElement('w:rPr')
    color=OxmlElement('w:color');color.set(qn('w:val'),'185B78');props.append(color)
    under=OxmlElement('w:u');under.set(qn('w:val'),'single');props.append(under)
    run.append(props);t=OxmlElement('w:t');t.text=label;run.append(t);h.append(run);p._p.append(h)

def make_docx():
    doc=Document();sec=doc.sections[0];sec.top_margin=Inches(.68);sec.bottom_margin=Inches(.62);sec.left_margin=Inches(.75);sec.right_margin=Inches(.75)
    styles=doc.styles
    normal=styles['Normal'];normal.font.name='Carlito';normal.font.size=Pt(9.5);normal.font.color.rgb=RGBColor(39,57,66)
    normal.paragraph_format.space_after=Pt(4)
    for name,size,color in [('Title',23,(18,52,66)),('Heading 1',14,(16,82,103)),('Heading 2',11,(21,74,91))]:
        s=styles[name];s.font.name='Carlito';s.font.size=Pt(size);s.font.bold=True;s.font.color.rgb=RGBColor(*color)
    head=sec.header.paragraphs[0];head.text='PRIMARY CARE AVAILABILITY  |  REGIONAL DIRECTORY';head.style='Caption'
    foot=sec.footer.paragraphs[0];foot.text='Public clinic listings only  •  Not a guarantee of patient enrolment  •  Check the evidence before referral';foot.alignment=WD_ALIGN_PARAGRAPH.CENTER
    foot.runs[0].font.size=Pt(8)
    doc.add_heading('Primary care availability',0)
    p=doc.add_paragraph('Tillsonburg-centred region  •  75 km straight-line radius  •  Research starting set')
    p.style='Subtitle'
    doc.add_paragraph('Generated '+today.strftime('%B %-d, %Y')+'  |  Last human research audit: '+D['data_as_of']+'  |  '+str(len(clinics))+' clinic/service listings across '+str(report['communities'])+' communities')
    doc.add_paragraph('IMPORTANT: Intake status is based on public information, not live telephone confirmation. An application does not guarantee attachment. Green means an intake process was advertised in the dated source, not a guaranteed opening. Records become “Needs reconfirmation” when their review date expires.').italic=True
    doc.add_paragraph('Clinics are shown by published office address; map positions are community-centre estimates. No patient home-address search, client data, or patient information is collected.')
    p=doc.add_paragraph('Directory key: ')
    for st in ORDER:
        if counts[st]:
            x=p.add_run(f'{STATUSES[st][0]}: {counts[st]}  |  ');x.bold=(st=='accepting')
    for st in ORDER:
        records=[c for c in clinics if c['display_status']==st]
        if not records:continue
        doc.add_heading(f'{STATUSES[st][0]}  ({len(records)})',level=1)
        if st=='reported':doc.add_paragraph('These are leads from regional lists and require direct confirmation before referral.')
        if st=='needs_review':doc.add_paragraph('These records aged out of their verification window. They must not be described as currently accepting or closed without new evidence.')
        if st=='unknown':doc.add_paragraph('No current, reliable intake statement recorded; unknown is not equivalent to closed.')
        for c in records:
            p=doc.add_paragraph(style='Heading 2');p.paragraph_format.keep_with_next=True;p.add_run(f'{c["community"]}  |  {c["name"]}')
            t=doc.add_table(rows=0,cols=2);t.autofit=False;t.columns[0].width=Inches(1.00);t.columns[1].width=Inches(5.9)
            for label,value in [('Office',c['address']),('Type',c['clinic_type']),('Phone',c.get('phone','') or 'Not listed'),('Intake note',c.get('intake_detail','') or 'No current details'),('Reviewed',c['last_reviewed']+' (research snapshot)')]:
                row=t.add_row();row.cells[0].text=label;row.cells[1].text=value
                row.cells[0].paragraphs[0].runs[0].bold=True
                for cell in row.cells:
                    cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
                    for cp in cell.paragraphs:cp.paragraph_format.space_after=Pt(1);cp.paragraph_format.space_before=Pt(1)
            p=doc.add_paragraph();p.paragraph_format.space_after=Pt(8)
            if c.get('evidence_url'):add_link(p,'Open supporting evidence',c['evidence_url'])
    out=docs/'primary-care-directory.docx';doc.save(out);return out

# PDF uses scalable textual directory and clickable source links.
def make_pdf():
    font='/usr/share/fonts/truetype/crosextra/Carlito-Regular.ttf'
    bold='/usr/share/fonts/truetype/crosextra/Carlito-Bold.ttf'
    if not pathlib.Path(font).exists():font='/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf';bold='/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf'
    if not (pathlib.Path(font).exists() and pathlib.Path(bold).exists()):
        import reportlab
        packaged=pathlib.Path(reportlab.__file__).parent/'fonts'
        font=str(packaged/'Vera.ttf');bold=str(packaged/'VeraBd.ttf')
    if pathlib.Path(font).exists() and pathlib.Path(bold).exists():
        regular_name='ClinicSans';bold_name='ClinicSans-Bold'
        pdfmetrics.registerFont(TTFont(regular_name,font));pdfmetrics.registerFont(TTFont(bold_name,bold))
        from reportlab.pdfbase.pdfmetrics import registerFontFamily
        registerFontFamily(regular_name,normal=regular_name,bold=bold_name,italic=regular_name,boldItalic=bold_name)
    else:
        # Runners without system font packages can still produce PDFs.
        regular_name='Helvetica';bold_name='Helvetica-Bold'
    dark=colors.HexColor('#15354A');teal=colors.HexColor('#18617B'); muted=colors.HexColor('#55717F')
    title=ParagraphStyle('Title',fontName=bold_name,fontSize=20,leading=24,textColor=dark,spaceAfter=9)
    h1=ParagraphStyle('Section',fontName=bold_name,fontSize=13,leading=16,textColor=teal,spaceBefore=14,spaceAfter=7,keepWithNext=True)
    h2=ParagraphStyle('Clinic',fontName=bold_name,fontSize=10.5,leading=13,textColor=dark,spaceBefore=7,spaceAfter=4,keepWithNext=True)
    body=ParagraphStyle('Body',fontName=regular_name,fontSize=9,leading=12.5,textColor=dark,spaceAfter=6)
    small=ParagraphStyle('Small',fontName=regular_name,fontSize=8.3,leading=11,textColor=muted,spaceAfter=3)
    story=[Paragraph('Primary care availability',title),Paragraph(f'75 km around Tillsonburg  |  Generated {today.isoformat()}  |  {len(clinics)} listings, {report["communities"]} communities',body),
        Paragraph('<b>Research directory, not live enrolment confirmation.</b> Intake advertisements do not guarantee attachment. Records past their verification window are marked “Needs reconfirmation”. Map positions are approximate community centres, not exact offices.',body)]
    for st in ORDER:
        records=[c for c in clinics if c['display_status']==st]
        if not records:continue
        story.append(Paragraph(f'{STATUSES[st][0]} ({len(records)})',h1))
        if st=='reported':story.append(Paragraph('Regional listings require confirmation with the practice before referral.',small))
        for c in records:
            e=html.escape
            lines=[Paragraph(e(c['community'])+'  |  '+e(c['name']),h2),
                Paragraph('<b>Office:</b> '+e(c['address'])+'   <b>Type:</b> '+e(c['clinic_type'])+'   <b>Phone:</b> '+e(c.get('phone') or 'Not listed'),small),
                Paragraph(e(c.get('intake_detail') or 'No current intake details'),body),
                Paragraph('Source reviewed: '+e(c['last_reviewed'])+'  |  <link href="'+e(c['evidence_url'],quote=True)+'" color="#185B78">Supporting source</link>',small)]
            story.append(KeepTogether(lines))
    out=docs/'primary-care-directory.pdf'
    pd=SimpleDocTemplate(str(out),pagesize=(612,792),rightMargin=51,leftMargin=51,topMargin=54,bottomMargin=53,title='Regional Primary Care Directory')
    def footer(canvas,doc):
        canvas.saveState();canvas.setFont(regular_name,8);canvas.setFillColor(muted)
        canvas.drawString(51,31,'Public clinic information only  |  Verify current intake with the practice')
        canvas.drawRightString(561,31,f'Page {doc.page}')
        canvas.restoreState()
    pd.build(story,onFirstPage=footer,onLaterPages=footer);return out

site_json={
 'generated_on':today.isoformat(), 'data_as_of':D['data_as_of'], 'center':D['center'], 'community_coords':CITY_COORDS,
 'counts':dict(counts), 'archived_count':len(archived), 'queue_count':len([r for r in queue['items'] if r.get('review_status')=='pending']), 'discovery_queue_count':len([r for r in discovery['items'] if r.get('review_status')=='pending']), 'monitored_count':len(source_state['sources']), 'last_source_scan':source_state.get('last_run'),'last_discovery_scan':discovery_state.get('last_run'), 'change_history':history[-15:][::-1], 'clinics':clinics,
}
# Avoid literal closing script tags in inlined source text.
jsdata=json.dumps(site_json,ensure_ascii=False,separators=(',',':')).replace('</','<\\/')
template=(ROOT/'scripts'/'site_template.html').read_text(encoding='utf8')
html_text=template.replace('<!--INLINE_DATA-->',f'<script id="clinic-data" type="application/json">{jsdata}</script>')
(site/'index.html').write_text(html_text,encoding='utf-8')
print(f'Site: {site / "index.html"} ({len(clinics)} clinics, {len(counts)} statuses)')
print('DOCX:',make_docx())
print('PDF:',make_pdf())
