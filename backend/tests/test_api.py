from fastapi.testclient import TestClient


def register_user(client: TestClient, username: str, email: str) -> dict:
    response = client.post(
        "/auth/register",
        json={"username": username, "email": email, "password": "secure-password-123"},
    )
    assert response.status_code == 201, response.text
    return response.json()


def login(client: TestClient, identity: str) -> str:
    response = client.post(
        "/auth/token",
        data={"username": identity, "password": "secure-password-123"},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def test_auth_registration_login_and_current_user(client: TestClient) -> None:
    user = register_user(client, "arjun", "arjun@example.com")
    assert user["username"] == "arjun"
    assert "hashed_password" not in user

    token = login(client, "arjun@example.com")
    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["email"] == "arjun@example.com"

    missing_token = client.get("/auth/me")
    assert missing_token.status_code == 401


def test_project_membership_and_issue_crud(client: TestClient) -> None:
    owner = register_user(client, "owner", "owner@example.com")
    member = register_user(client, "developer", "developer@example.com")
    owner_token = login(client, "owner")
    member_token = login(client, "developer@example.com")
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    member_headers = {"Authorization": f"Bearer {member_token}"}

    project_response = client.post(
        "/projects",
        json={"name": "Platform", "key": "PLAT", "description": "Platform issues"},
        headers=owner_headers,
    )
    assert project_response.status_code == 201, project_response.text
    project = project_response.json()
    project_id = project["id"]
    assert [item["id"] for item in client.get("/projects", headers=owner_headers).json()] == [project_id]

    added_member = client.post(
        f"/projects/{project_id}/members",
        json={"identity": "developer@example.com", "role": "developer"},
        headers=owner_headers,
    )
    assert added_member.status_code == 201, added_member.text
    assert added_member.json()["user_id"] == member["id"]

    duplicate_member = client.post(
        f"/projects/{project_id}/members",
        json={"identity": "developer", "role": "viewer"},
        headers=owner_headers,
    )
    assert duplicate_member.status_code == 409

    non_member_assignee = register_user(client, "outsider", "outsider@example.com")
    invalid_assignee = client.post(
        f"/projects/{project_id}/issues",
        json={"title": "Cannot assign outside team", "assignee_id": non_member_assignee["id"]},
        headers=owner_headers,
    )
    assert invalid_assignee.status_code == 422

    issue_response = client.post(
        f"/projects/{project_id}/issues",
        json={
            "title": "Login form fails on Safari",
            "description": "A reproducible issue",
            "issue_type": "bug",
            "priority": "high",
            "assignee_id": member["id"],
        },
        headers=owner_headers,
    )
    assert issue_response.status_code == 201, issue_response.text
    issue = issue_response.json()
    assert issue["issue_key"] == "PLAT-1"
    assert issue["reporter_id"] == owner["id"]
    assert issue["assignee_id"] == member["id"]

    second_issue = client.post(
        f"/projects/{project_id}/issues",
        json={"title": "Add account recovery", "issue_type": "feature"},
        headers=member_headers,
    )
    assert second_issue.status_code == 201
    assert second_issue.json()["issue_key"] == "PLAT-2"

    listed = client.get(f"/projects/{project_id}/issues", headers=member_headers)
    assert listed.status_code == 200
    assert len(listed.json()) == 2

    updated = client.patch(
        f"/projects/{project_id}/issues/{issue['id']}",
        json={"status": "in_progress", "description": None},
        headers=member_headers,
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "in_progress"
    assert updated.json()["description"] is None

    comment = client.post(
        f"/projects/{project_id}/issues/{issue['id']}/comments",
        json={"content": "I can reproduce this on Safari."},
        headers=member_headers,
    )
    assert comment.status_code == 201
    assert comment.json()["author_id"] == member["id"]

    deleted = client.delete(
        f"/projects/{project_id}/issues/{issue['id']}", headers=owner_headers
    )
    assert deleted.status_code == 204
    missing = client.get(
        f"/projects/{project_id}/issues/{issue['id']}", headers=owner_headers
    )
    assert missing.status_code == 404


def test_non_member_cannot_read_project_issues(client: TestClient) -> None:
    register_user(client, "owner", "owner@example.com")
    outsider = register_user(client, "outsider", "outsider@example.com")
    owner_headers = {"Authorization": f"Bearer {login(client, 'owner')}"}
    outsider_headers = {"Authorization": f"Bearer {login(client, 'outsider')}"}

    project = client.post(
        "/projects", json={"name": "Private", "key": "PRIV"}, headers=owner_headers
    ).json()
    response = client.get(
        f"/projects/{project['id']}/issues", headers=outsider_headers
    )
    assert response.status_code == 404


def test_issue_search_filters_and_pagination(client: TestClient) -> None:
    register_user(client, "owner", "owner@example.com")
    developer = register_user(client, "developer", "developer@example.com")
    owner_headers = {"Authorization": f"Bearer {login(client, 'owner')}"}

    project = client.post(
        "/projects", json={"name": "Platform", "key": "PLAT"}, headers=owner_headers
    ).json()
    client.post(
        f"/projects/{project['id']}/members",
        json={"identity": "developer", "role": "developer"},
        headers=owner_headers,
    )

    safari_issue = client.post(
        f"/projects/{project['id']}/issues",
        json={
            "title": "Safari login failure",
            "description": "Repro steps included",
            "issue_type": "bug",
            "priority": "high",
            "assignee_id": developer["id"],
        },
        headers=owner_headers,
    ).json()
    password_issue = client.post(
        f"/projects/{project['id']}/issues",
        json={"title": "Password reset request", "issue_type": "feature", "priority": "low"},
        headers=owner_headers,
    ).json()
    client.patch(
        f"/projects/{project['id']}/issues/{safari_issue['id']}",
        json={"status": "done"},
        headers=owner_headers,
    )

    filtered = client.get(
        f"/projects/{project['id']}/issues",
        params={
            "search": "SAFARI",
            "status": "done",
            "issue_type": "bug",
            "priority": "high",
            "assignee_id": developer["id"],
            "sort": "oldest",
        },
        headers=owner_headers,
    )
    assert filtered.status_code == 200
    assert filtered.headers["x-total-count"] == "1"
    assert [item["id"] for item in filtered.json()] == [safari_issue["id"]]

    unassigned = client.get(
        f"/projects/{project['id']}/issues",
        params={"unassigned": "true", "limit": 1, "sort": "oldest"},
        headers=owner_headers,
    )
    assert unassigned.headers["x-total-count"] == "1"
    assert [item["id"] for item in unassigned.json()] == [password_issue["id"]]

    paged = client.get(
        f"/projects/{project['id']}/issues",
        params={"limit": 1, "offset": 1, "sort": "oldest"},
        headers=owner_headers,
    )
    assert paged.headers["x-total-count"] == "2"
    assert [item["id"] for item in paged.json()] == [password_issue["id"]]


def test_viewers_can_read_but_cannot_modify_issues_or_comments(client: TestClient) -> None:
    owner = register_user(client, "owner", "owner@example.com")
    viewer = register_user(client, "viewer", "viewer@example.com")
    owner_headers = {"Authorization": f"Bearer {login(client, 'owner')}"}
    viewer_headers = {"Authorization": f"Bearer {login(client, 'viewer')}"}

    project = client.post(
        "/projects", json={"name": "Platform", "key": "PLAT"}, headers=owner_headers
    ).json()
    client.post(
        f"/projects/{project['id']}/members",
        json={"identity": "viewer", "role": "viewer"},
        headers=owner_headers,
    )
    issue = client.post(
        f"/projects/{project['id']}/issues",
        json={"title": "Read-only issue"},
        headers=owner_headers,
    ).json()
    issue_url = f"/projects/{project['id']}/issues/{issue['id']}"
    comments_url = f"{issue_url}/comments"
    comment = client.post(
        comments_url,
        json={"content": "Release notes are ready."},
        headers=owner_headers,
    )
    assert comment.status_code == 201
    assert comment.json()["author_id"] == owner["id"]

    listed = client.get(f"/projects/{project['id']}/issues", headers=viewer_headers)
    assert listed.status_code == 200
    visible_comments = client.get(comments_url, headers=viewer_headers).json()
    assert [item["content"] for item in visible_comments] == ["Release notes are ready."]
    assert client.post(
        f"/projects/{project['id']}/issues",
        json={"title": "Viewer cannot create"},
        headers=viewer_headers,
    ).status_code == 403
    update_attempt = client.patch(issue_url, json={"status": "done"}, headers=viewer_headers)
    assert update_attempt.status_code == 403
    delete_attempt = client.delete(issue_url, headers=viewer_headers)
    assert delete_attempt.status_code == 403
    assert client.post(
        comments_url,
        json={"content": "Viewer cannot comment"},
        headers=viewer_headers,
    ).status_code == 403
    remaining_issue = client.get(issue_url, headers=viewer_headers)
    assert remaining_issue.status_code == 200
