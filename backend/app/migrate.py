"""Additive schema upgrades for databases created before a column existed.

`create_all` only creates missing tables, so columns added later are patched in
here. Every step checks the live schema first and is safe to run on each start.
"""

from sqlalchemy import Engine, inspect, text

from .models import ReviewItem

# (table, column, definition)
COLUMNS = [
    *((t, "plan", "VARCHAR(10) NOT NULL DEFAULT 'topic'") for t in ("users", "quiz_sessions", "attempts", "review_items")),
    ("questions", "ref", "VARCHAR(20)"),
]


def migrate(engine: Engine) -> None:
    with engine.begin() as conn:
        insp = inspect(conn)
        for table, column, definition in COLUMNS:
            if column not in {c["name"] for c in insp.get_columns(table)}:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {definition}"))

        # Reviews became per plan: widen the (user, question, stage) unique key.
        insp = inspect(conn)
        old = next(
            (u for u in insp.get_unique_constraints("review_items")
             if sorted(u["column_names"]) == ["question_id", "stage", "user_id"]),
            None,
        )
        if old is None:
            return
        if conn.dialect.name == "sqlite":
            # SQLite cannot drop a constraint: rebuild the table.
            for ix in insp.get_indexes("review_items"):
                conn.execute(text(f'DROP INDEX "{ix["name"]}"'))
            conn.execute(text("ALTER TABLE review_items RENAME TO review_items_old"))
            ReviewItem.__table__.create(conn)
            cols = "id, user_id, plan, question_id, stage, due_date, completed_at"
            conn.execute(text(f"INSERT INTO review_items ({cols}) SELECT {cols} FROM review_items_old"))
            conn.execute(text("DROP TABLE review_items_old"))
        else:
            conn.execute(text(f'ALTER TABLE review_items DROP CONSTRAINT "{old["name"]}"'))
            conn.execute(text(
                "ALTER TABLE review_items ADD CONSTRAINT uq_review_items_user_plan_question_stage "
                "UNIQUE (user_id, plan, question_id, stage)"
            ))
