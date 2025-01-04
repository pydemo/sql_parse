import re
from pypeg2 import List, attr, parse, maybe_some, optional

# -----------------------------
# 1) Case-insensitive keywords
# -----------------------------
class SelectKeyword(str):
    grammar = re.compile(r"(?i)SELECT")

class FromKeyword(str):
    grammar = re.compile(r"(?i)FROM")

# -----------------------------
# 2) Expression handling
# -----------------------------
class Expression(str):
    def __init__(self, value=None, alias=None):
        super().__init__()
        self.value = value
        self.alias = alias

    def parse(self, parser, text, pos=0):
        # If 'text' is given as (pos, string), unpack
        if isinstance(text, (list, tuple)):
            if len(text) >= 2:
                pos, text = text[0], text[1]
            else:
                raise SyntaxError("Invalid input format")

        paren_count = 0
        current_pos = pos
        text_len = len(text)

        while current_pos < text_len:
            char = text[current_pos]

            if char == '(':
                paren_count += 1
            elif char == ')':
                paren_count -= 1
            elif char == ',' and paren_count == 0:
                # Expression ends at a comma
                break
            elif char.upper() == 'F' and paren_count == 0:
                # Check if the remaining text starts with FROM
                remaining = text[current_pos:].lstrip()
                if remaining.upper().startswith('FROM'):
                    break

            current_pos += 1

        # Extract the expression text and leftover
        expr_text = text[pos:current_pos].strip()
        leftover_text = text[current_pos:]

        # Attempt to identify an alias: e.g. "LTRIM(M.ACCT_NB,'0') JPMC_ACCT_NBR"
        parts = expr_text.split()
        alias = None

        if len(parts) > 1 and not any(c in parts[-1] for c in "(),'"):
            # The last token doesn't contain parentheses/commas, treat it as alias
            alias = parts[-1]
            expr_value = ' '.join(parts[:-1])
        else:
            expr_value = expr_text

        # Populate this instance
        self.value = expr_value
        self.alias = alias

        # IMPORTANT: Return leftover *string* and the grammar object (self)
        return leftover_text, self

# -----------------------------
# 3) Column definitions
# -----------------------------
class Column:
    grammar = attr("expression", Expression)

class Columns(List):
    grammar = Column, maybe_some(",", Column)

# -----------------------------
# 4) Main SQL components
# -----------------------------
class SelectClause(List):
    grammar = SelectKeyword, attr("columns", Columns)

class FromClause(str):
    grammar = re.compile(r".*", re.DOTALL)

class SQL(List):
    grammar = (
        attr("select", SelectClause),
        FromKeyword,
        attr("from_clause", FromClause),
    )

# -----------------------------
# 5) Example usage
# -----------------------------
sql_query = """
SELECT LTRIM(M.ACCT_NB,'0') JPMC_ACCT_NBR, RIGHT(M.FIRM_BANK_ID,3) BNK_NB,
       LPAD(M.SUB_PROD_CD,3,'0') SUB_PROD_CD
FROM (SELECT ACCT_NB, FIRM_BANK_ID
      FROM MyTable
      WHERE Something = 1) M
"""

try:
    # Clean and normalize input
    normalized_query = ' '.join(
        line.strip() for line in sql_query.splitlines() if line.strip()
    )
    print("Normalized query:")
    print(normalized_query)
    print("\nAttempting to parse...")

    parsed_sql = parse(normalized_query, SQL)

    print("\nSuccessfully parsed!")
    print("\nExtracted columns:")
    for i, col in enumerate(parsed_sql.select.columns, 1):
        expr_obj = col.expression
        print(f"Column {i}:")
        print(f"  Expression: [{expr_obj.value}]")
        print(f"  Alias: [{expr_obj.alias}]" if expr_obj.alias else "  Alias: None")

except SyntaxError as e:
    print("\nSyntax error while parsing:")
    print(f"Error message: {str(e)}")
    if hasattr(e, 'text'):
        print("Context:")
        print(e.text)
        if e.offset:
            print(" " * (e.offset - 1) + "^")
except Exception as e:
    import traceback
    print(f"\nError type: {type(e).__name__}")
    print(f"Error details: {str(e)}")
    print("\nFull traceback:")
    print(traceback.format_exc())
