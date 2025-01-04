import re
from pypeg2 import List, attr, parse, maybe_some, optional

# -----------------------------
# 1) Case-insensitive keywords
# -----------------------------
class SelectKeyword(str):
    grammar = re.compile(r"(?i)SELECT")  # matches SELECT in any case

class FromKeyword(str):
    grammar = re.compile(r"(?i)FROM")    # matches FROM in any case

# -----------------------------------------------------------
# 2) Basic approach: each column is everything until next comma
#    (does NOT handle commas inside function calls, etc.!)
# -----------------------------------------------------------
class Expression(str):
    # Match everything up to the next comma or up to FROM
    grammar = re.compile(r"[^,]+")  # minimal approach

class Column(List):
    # We skip "AS" entirely in this simplistic approach
    # If you need optional aliases, you can do:
    grammar = attr("expression", Expression), optional(attr("alias", Expression))

class Columns(List):
    grammar = Column, maybe_some(",", Column)

# -------------------------------
# 3) High-level SELECT-FROM
# -------------------------------
class SelectClause(List):
    grammar = SelectKeyword, attr("columns", Columns)

# FromClause: capture everything after "FROM"
class FromClause(str):
    grammar = re.compile(r".*", re.DOTALL)

class SQL(List):
    grammar = (
        attr("select", SelectClause),  # SELECT ...
        FromKeyword,                   # FROM
        attr("from_clause", FromClause)
    )

# ------------------------------------------------
# 4) Example usage
# ------------------------------------------------
sql_query = """
SELECT LTRIM(M.ACCT_NB,'0') JPMC_ACCT_NBR, RIGHT(M.FIRM_BANK_ID,3) BNK_NB,
       LPAD(M.SUB_PROD_CD,3,'0') SUB_PROD_CD
FROM (SELECT ACCT_NB, FIRM_BANK_ID
      FROM MyTable
      WHERE Something = 1) M
"""

parsed_sql = parse(sql_query, SQL)

print("Extracted columns:")
for i, col in enumerate(parsed_sql.select.columns, start=1):
    alias = col.alias.strip() if col.alias else "None"
    print(f"  Col {i}: Expression=[{col.expression.strip()}], Alias=[{alias}]")
