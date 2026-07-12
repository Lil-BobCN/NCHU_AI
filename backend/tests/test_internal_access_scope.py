from __future__ import annotations

from pathlib import Path
import sys
import unittest

from sqlalchemy.dialects import postgresql


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.api.v1.internal import (  # noqa: E402
    AccessScope,
    UserContext,
    _custom_document_access_condition,
    _document_access_condition,
    _document_access_sql,
)


def _compiled_where(scope: AccessScope, user: UserContext, allow_explicit_attach: bool = False) -> str:
    condition = _document_access_condition(user, scope, allow_explicit_attach)
    return str(
        condition.compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": True},
        )
    )


def _compiled_custom_where(scope: AccessScope) -> str:
    condition = _custom_document_access_condition(scope)
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

    def test_custom_scope_only_uses_explicit_java_scope(self) -> None:
        sql = _compiled_custom_where(
            AccessScope(scope_mode="custom", allowed_attach_ids=[101], allowed_dept_ids=[]),
        )

        self.assertIn("documents.java_attach_id IN (101)", sql)
        self.assertNotIn("documents.publish_scope = 'public'", sql)
        self.assertNotIn("documents.owner_user_id", sql)

    def test_custom_scope_sql_does_not_fall_back_to_public_documents(self) -> None:
        sql, params, cache_key = _document_access_sql(
            AccessScope(scope_mode="custom", allowed_attach_ids=[101]),
            UserContext(user_id="1001"),
        )

        self.assertIn("d.java_attach_id = ANY", sql)
        self.assertNotIn("d.publish_scope = 'public'", sql)
        self.assertNotIn("d.owner_user_id", sql)
        self.assertEqual(params["allowed_attach_ids"], [101])
        self.assertEqual(cache_key["allowed_attach_ids"], [101])


if __name__ == "__main__":
    unittest.main()
