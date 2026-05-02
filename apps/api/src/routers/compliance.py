from fastapi import HTTPException

from ..core import document_repository

COMPLIANCE_ENDPOINTS = [
    "GET /api/v1/documents/{id}/compliance",
    "POST /api/v1/documents/{id}/compliance/check",
    "GET /api/v1/documents/{id}/compliance/score",
    "PUT /api/v1/documents/{id}/compliance/{requirement_id}",
]


DEFAULT_TENANT_ID = "00000000-0000-0000-0000-000000000001"


def _transform_requirement(
    record: dict[str, object],
    document_id: str,
) -> dict[str, object]:
    met = record.get("met")
    if met is True:
        status = "met"
    elif met is False:
        status = "unmet"
    else:
        status = "review"
    return {
        "id": record.get("id", ""),
        "tender_id": document_id,
        "clause": record.get("requirement_code", "") or "",
        "requirement": record.get("requirement_text", ""),
        "status": status,
        "evidence": record.get("actual_value", ""),
        "created_at": "",
    }


def get_document_compliance(document_id: str) -> dict[str, object]:
    document = document_repository.get_document(document_id, DEFAULT_TENANT_ID)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    report = document_repository.get_compliance_report(document_id)
    raw_requirements = document_repository.list_requirements(document_id)
    requirements = [_transform_requirement(r, document_id) for r in raw_requirements]

    if report is None:
        return {
            "id": document_id,
            "eligibility_score": None,
            "recommendation": None,
            "requirements": requirements,
            "report": None,
        }

    return {
        "id": document_id,
        "eligibility_score": report["eligibility_score"],
        "recommendation": report["recommendation"],
        "requirements": requirements,
        "report": report["report"],
    }


def get_compliance_score(document_id: str) -> dict[str, object]:
    document = document_repository.get_document(document_id, DEFAULT_TENANT_ID)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    report = document_repository.get_compliance_report(document_id)
    requirements = document_repository.list_requirements(document_id)
    met = sum(1 for r in requirements if r.get("met") is True)
    total = len(requirements)
    score = report["eligibility_score"] if report else None
    if score is not None:
        if score >= 80:
            go_no_go = "go"
        elif score >= 50:
            go_no_go = "review"
        else:
            go_no_go = "no-go"
    else:
        go_no_go = "review"
    return {
        "id": document_id,
        "eligibility_score": score,
        "total_requirements": total,
        "met_requirements": met,
        "recommendation": report["recommendation"] if report else None,
        "go_no_go": go_no_go,
    }


def update_compliance_requirement(
    document_id: str,
    requirement_id: str,
    payload: dict[str, object],
) -> dict[str, object]:
    document = document_repository.get_document(document_id, DEFAULT_TENANT_ID)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    status = str(payload.get("status", ""))
    if status not in ("met", "unmet", "review"):
        raise HTTPException(status_code=400, detail="Invalid status")
    updated = document_repository.update_requirement_status(
        document_id, requirement_id, status, str(payload.get("evidence", ""))
    )
    return updated


def run_compliance_check(document_id: str) -> dict[str, str]:
    document = document_repository.get_document(document_id, DEFAULT_TENANT_ID)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"status": "check_triggered", "document_id": document_id}


COMPLIANCE_ROUTES = [
    ("GET", "/documents/{document_id}/compliance", get_document_compliance),
    ("GET", "/documents/{document_id}/compliance/score", get_compliance_score),
    (
        "PUT",
        "/documents/{document_id}/compliance/{requirement_id}",
        update_compliance_requirement,
    ),
    ("POST", "/documents/{document_id}/compliance/check", run_compliance_check),
]
