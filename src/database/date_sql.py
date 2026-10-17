"""Định dạng ngày tương thích SQLite local và PostgreSQL trên host.

Giữ phép cộng 7 giờ của code cũ; không đổi cách lưu timestamp hiện có.
"""
from sqlalchemy import String
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql.functions import FunctionElement


class display_date(FunctionElement):
    type = String()
    inherit_cache = False

    def __init__(self, pattern, column):
        self.pattern = pattern
        super().__init__(column)


@compiles(display_date, "sqlite")
def sqlite_date(element, compiler, **kw):
    column = compiler.process(list(element.clauses)[0], **kw)
    pattern = compiler.render_literal_value(element.pattern, String())
    return f"strftime({pattern}, {column}, '+7 hours')"


@compiles(display_date, "postgresql")
def postgres_date(element, compiler, **kw):
    # PostgreSQL dùng to_char và interval, không hỗ trợ strftime của SQLite.
    patterns = {
        "%H:00": "HH24:00", "%d/%m": "DD/MM", "%m": "MM",
        "%Y": "YYYY", "%m/%Y": "MM/YYYY",
        "%d/%m/%Y %H:%M": "DD/MM/YYYY HH24:MI",
    }
    column = compiler.process(list(element.clauses)[0], **kw)
    pattern = compiler.render_literal_value(patterns[element.pattern], String())
    return f"to_char(({column} + INTERVAL '7 hours'), {pattern})"
