from __future__ import annotations

from pathlib import Path
import sys
import unittest

from sqlalchemy.dialects import postgresql


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.api.v1.internal import AccessScope, UserContext, _document_access_condition  # noqa: E402


def _compiled_where(scope: AccessScope, user: UserContext, allow_explicit_attach: bool = False) -> str:
    condition = _document_access_condition(user, scope, allow_explicit_attach)
    return str(
        condition.compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": True},
        )
    )


class InternalAccessScopeTests(unittest.TestCase):
    def test_dept_scope_allows_public_and_matching_department_documents(self) -> None:
        sql = _compiled_where(
            AccessScope(scope_mode="dept", allowed_dept_ids=["finance"]),
            UserContext(user_id="1001", dept_id="finance"),
        )

        self.assertIn("documents.publish_scope = 'public'", sql)
        self.assertIn("documents.publish_scope = 'dept'", sql)
        self.assertIn("documents.publish_dept_id IN ('finance')", sql)
        self.assertIn("documents.allowed_dept_ids && ARRAY['finance']", sql)

    def test_private_scope_matches_owner_user(self) -> None:
        sql = _compiled_where(
            AccessScope(scope_mode="dept", allowed_dept_ids=["finance"]),
            UserContext(user_id="1001", dept_id="finance"),
        )

        self.assertIn("documents.publish_scope = 'private'", sql)
        self.assertIn("documents.owner_user_id = '1001'", sql)

    def test_custom_scope_can_match_allowed_user_and_explicit_attach(self) -> None:
        sql = _compiled_where(
            AccessScope(scope_mode="custom", allowed_attach_ids=[101], allowed_dept_ids=[]),
            UserContext(user_id="1001"),
            allow_explicit_attach=True,
        )

        self.assertIn("documents.publish_scope = 'custom'", sql)
        self.assertIn("'1001' = ANY (documents.allowed_user_ids)", sql)
        self.assertIn("documents.java_attach_id IN (101)", sql)


if __name__ == "__main__":
    unittest.main()
