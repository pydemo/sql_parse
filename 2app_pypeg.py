import streamlit as st
import pandas as pd
import re
from pypeg2 import parse, List, csl, re as preg, maybe_some

################################################################################
# pypeg2-based parsing
################################################################################
class Column(List):
    """Single column definition with optional alias"""
    grammar = preg.compile(r'''
        ([^,]+?)                     # Column expression (non-greedy match until comma or end)
        (?:                          # Non-capturing group for alias part
            (?:\s+AS\s+|\s+)        # Optional AS or just space
            ([A-Za-z][A-Za-z0-9_]*) # Alias
        )?                          # Entire alias part is optional
        (?=\s*(?:,|FROM|$))         # Lookahead for comma, FROM, or end
    ''', re.VERBOSE | re.IGNORECASE)

    def __init__(self, match=None):
        super().__init__()
        if match:
            self.expression = match[0].strip()
            self.alias = match[1].strip() if match[1] else None

    def __str__(self):
        return f"Column(expression={self.expression!r}, alias={self.alias!r})"

def extract_columns(sql):
    """Extract columns and aliases using a parenthesis-aware method."""
    # Normalize whitespace
    sql = ' '.join(sql.split())
    
    # Extract the column list portion (between SELECT and FROM)
    select_match = re.match(r'SELECT\s+(.*?)\s+FROM', sql, re.IGNORECASE)
    if not select_match:
        return []
    
    column_text = select_match.group(1)
    
    # Split the columns taking into account nested parentheses
    columns = []
    current_col = []
    paren_count = 0
    
    for char in column_text + ',':  # Add comma to handle last column
        if char == ',' and paren_count == 0:
            if current_col:
                columns.append(''.join(current_col).strip())
                current_col = []
        else:
            if char == '(':
                paren_count += 1
            elif char == ')':
                paren_count -= 1
            current_col.append(char)
    
    # Process each column to extract expression and alias
    result = []
    for col in columns:
        # Match function call or column name, followed by optional alias
        match = re.match(r'(.*?)(?:\s+AS\s+|\s+)([A-Za-z][A-Za-z0-9_]*)$', col.strip(), re.IGNORECASE)
        if match:
            result.append((match.group(1).strip(), match.group(2).strip()))
        else:
            # Column without alias
            result.append((col.strip(), None))
            
    return result

################################################################################
# Wrapper function that uses the pypeg2-based approach
################################################################################
def parse_sql_columns(sql_query):
    """Wrapper for the pypeg2-based column extractor."""
    column_pairs = extract_columns(sql_query)
    # Convert into list of dicts
    parsed_columns = []
    for expr, alias in column_pairs:
        parsed_columns.append({
            'expression': expr,
            'alias': alias
        })
    return parsed_columns

################################################################################
# Streamlit App
################################################################################
def main():
    st.title("SQL Column Parser (pypeg2)")

    with st.form("sql_form"):
        sql_query = st.text_area("Enter your SQL query:", height=300)
        parse_button = st.form_submit_button("Parse Columns")

    if parse_button:
        columns = parse_sql_columns(sql_query)
        if not columns:
            st.write("No columns found or invalid SQL SELECT statement.")
        else:
            df = pd.DataFrame(columns)
            st.table(df)

if __name__ == "__main__":
    main()
