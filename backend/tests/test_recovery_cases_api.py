import uuid


def test_list_recovery_cases_returns_empty_list(client) -> None:
    response = client.get("/api/recovery-cases")

    assert response.status_code == 200
    assert response.json() == []


def test_unknown_recovery_case_returns_404(client) -> None:
    response = client.get(f"/api/recovery-cases/{uuid.uuid4()}")

    assert response.status_code == 404
    assert response.json() == {"detail": "Recovery case not found"}
