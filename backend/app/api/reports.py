"""
Report generation API routes.
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from app.services.report_service import generate_report, generate_pdf_report
import os

router = APIRouter(prefix="/api/reports", tags=["reports"])


class ReportRequest(BaseModel):
    incident_data: dict


@router.post("/generate")
async def create_report(req: ReportRequest):
    """Generate a structured emergency report from incident data."""
    report = generate_report(req.incident_data)
    return report


@router.post("/generate-pdf")
async def create_pdf_report(req: ReportRequest):
    """Generate and return a PDF emergency report."""
    report = generate_report(req.incident_data)
    pdf_path = generate_pdf_report(report)
    if not pdf_path or not os.path.exists(pdf_path):
        raise HTTPException(status_code=500, detail="PDF generation failed.")
    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=f"rapidcare_report_{report['report_id'][:8]}.pdf"
    )
