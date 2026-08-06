"""
Report Service: Generates structured emergency reports in JSON and PDF.
"""
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path

REPORTS_DIR = Path("/tmp/rapidcare_reports")
REPORTS_DIR.mkdir(exist_ok=True)


def generate_report(incident_data: dict) -> dict:
    """
    Generate a structured emergency report from incident analysis data.
    Returns report as JSON dict, and optionally saves PDF.
    """
    incident_id = incident_data.get("incident_id", str(uuid.uuid4()))
    timestamp = datetime.utcnow().isoformat() + "Z"

    emergency_type = incident_data.get("emergency_type", "Unknown")
    severity = incident_data.get("severity_data", {})
    firstaid = incident_data.get("firstaid_data", {})
    hospitals = incident_data.get("hospitals", [])
    input_text = incident_data.get("input_text", "")
    nearest_hospital = hospitals[0] if hospitals else None

    report = {
        "report_id": str(uuid.uuid4()),
        "incident_id": incident_id,
        "generated_at": timestamp,
        "generated_by": "RapidCare AI v1.0",
        "incident_summary": {
            "description": input_text[:500] if input_text else "Emergency reported via multi-modal input",
            "emergency_type": emergency_type.replace("_", " ").title(),
            "severity_score": severity.get("severity_score", 0),
            "severity_level": severity.get("severity_level", "UNKNOWN"),
            "survival_probability_pct": round(severity.get("survival_probability", 0.5) * 100, 1),
            "reported_at": timestamp,
        },
        "ai_analysis": {
            "primary_diagnosis": emergency_type.replace("_", " ").title(),
            "confidence_pct": round(incident_data.get("confidence", 0.7) * 100, 1),
            "contributing_factors": severity.get("contributing_factors", []),
            "detected_keywords": incident_data.get("detected_keywords", []),
            "injury_indicators": incident_data.get("injury_indicators", []),
        },
        "response_plan": {
            "immediate_actions": firstaid.get("steps", [])[:4],
            "all_first_aid_steps": firstaid.get("steps", []),
            "critical_warnings": firstaid.get("warnings", []),
            "required_medical_specialties": firstaid.get("required_specialties", []),
        },
        "hospital_assignment": {
            "recommended_hospital": {
                "name": nearest_hospital["name"] if nearest_hospital else "N/A",
                "address": nearest_hospital["address"] if nearest_hospital else "N/A",
                "phone": nearest_hospital["phone"] if nearest_hospital else "112",
                "distance_km": nearest_hospital["distance_km"] if nearest_hospital else 0,
                "estimated_arrival_min": nearest_hospital["estimated_travel_min"] if nearest_hospital else 0,
                "trauma_center": nearest_hospital.get("trauma_center", False) if nearest_hospital else False,
                "icu_available": nearest_hospital.get("icu_beds_available", 0) if nearest_hospital else 0,
            },
            "alternative_hospitals": [
                {
                    "name": h["name"],
                    "distance_km": h["distance_km"],
                    "phone": h.get("phone", "112"),
                }
                for h in hospitals[1:3]
            ],
        },
        "emergency_contacts": {
            "ambulance": "108",
            "emergency": "112",
            "fire": "101",
            "police": "100",
            "disaster_management": "1070",
        },
        "metadata": {
            "ai_mode": incident_data.get("ai_mode", "demo"),
            "processing_time_ms": incident_data.get("processing_time_ms", 0),
            "input_modalities": [
                m for m, has in [
                    ("text", bool(input_text)),
                    ("image", incident_data.get("has_image", False)),
                    ("voice", incident_data.get("has_voice", False)),
                ] if has
            ],
        },
    }

    return report


def generate_pdf_report(report: dict) -> Optional[str]:
    """Generate PDF version of the report. Returns file path."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.colors import HexColor, white
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
        from reportlab.lib.units import cm
        from reportlab.lib.enums import TA_CENTER, TA_LEFT

        pdf_path = REPORTS_DIR / f"{report['report_id']}.pdf"
        doc = SimpleDocTemplate(str(pdf_path), pagesize=A4,
                                leftMargin=2*cm, rightMargin=2*cm,
                                topMargin=2*cm, bottomMargin=2*cm)

        styles = getSampleStyleSheet()
        RED = HexColor("#EF4444")
        DARK = HexColor("#1E293B")
        ORANGE = HexColor("#F59E0B")
        GREEN = HexColor("#10B981")

        title_style = ParagraphStyle("title", parent=styles["Heading1"],
                                     textColor=RED, fontSize=20, spaceAfter=4, alignment=TA_CENTER)
        heading_style = ParagraphStyle("heading", parent=styles["Heading2"],
                                       textColor=DARK, fontSize=13, spaceBefore=12, spaceAfter=4)
        body_style = ParagraphStyle("body", parent=styles["Normal"],
                                    fontSize=10, spaceAfter=3)

        story = []
        summary = report["incident_summary"]
        analysis = report["ai_analysis"]
        response = report["response_plan"]
        hospital = report["hospital_assignment"]["recommended_hospital"]

        # Header
        story.append(Paragraph("🚨 RapidCare AI — Emergency Medical Report", title_style))
        story.append(Paragraph(f"Report ID: {report['report_id']}", body_style))
        story.append(Paragraph(f"Generated: {report['generated_at']}", body_style))
        story.append(HRFlowable(width="100%", thickness=2, color=RED))
        story.append(Spacer(1, 0.3*cm))

        # Incident Summary
        story.append(Paragraph("INCIDENT SUMMARY", heading_style))
        sev_color = RED if summary["severity_level"] == "CRITICAL" else ORANGE if summary["severity_level"] == "SEVERE" else GREEN
        sev_style = ParagraphStyle("sev", parent=body_style, textColor=sev_color, fontSize=12, fontName="Helvetica-Bold")
        story.append(Paragraph(f"Emergency Type: {summary['emergency_type']}", body_style))
        story.append(Paragraph(f"Severity: {summary['severity_level']} ({summary['severity_score']}/100)", sev_style))
        story.append(Paragraph(f"Survival Probability: {summary['survival_probability_pct']}%", body_style))
        story.append(Paragraph(f"Description: {summary['description']}", body_style))
        story.append(Spacer(1, 0.3*cm))

        # First Aid Steps
        story.append(Paragraph("IMMEDIATE FIRST AID STEPS", heading_style))
        for i, step in enumerate(response["all_first_aid_steps"], 1):
            story.append(Paragraph(f"{i}. {step}", body_style))
        story.append(Spacer(1, 0.3*cm))

        # Warnings
        story.append(Paragraph("⚠️ CRITICAL WARNINGS", heading_style))
        for w in response["critical_warnings"]:
            story.append(Paragraph(f"• {w}", body_style))
        story.append(Spacer(1, 0.3*cm))

        # Hospital
        story.append(Paragraph("NEAREST HOSPITAL", heading_style))
        story.append(Paragraph(f"<b>{hospital['name']}</b>", body_style))
        story.append(Paragraph(f"Address: {hospital['address']}", body_style))
        story.append(Paragraph(f"Phone: {hospital['phone']}", body_style))
        story.append(Paragraph(f"Distance: {hospital['distance_km']} km | ETA: {hospital['estimated_arrival_min']} min", body_style))
        story.append(Spacer(1, 0.3*cm))

        # Emergency Contacts
        story.append(Paragraph("EMERGENCY NUMBERS", heading_style))
        contacts = report["emergency_contacts"]
        contact_data = [[k.title(), v] for k, v in contacts.items()]
        t = Table(contact_data, colWidths=[6*cm, 4*cm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), DARK),
            ("TEXTCOLOR", (0, 0), (-1, 0), white),
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("GRID", (0, 0), (-1, -1), 0.5, DARK),
            ("ROWBACKGROUNDS", (0, 0), (-1, -1), [white, HexColor("#F8FAFC")]),
        ]))
        story.append(t)

        doc.build(story)
        return str(pdf_path)

    except Exception as e:
        print(f"[Report] PDF generation failed: {e}")
        return None
