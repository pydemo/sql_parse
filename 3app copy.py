import streamlit as st
import pandas as pd
import re
from pypeg2 import parse, List, csl, re as preg, maybe_some
from pprint import pprint as pp

################################################################################
# pypeg2-based parsing with enhanced support for any SQL
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

def extract_columns_with_metadata(sql):
    """Extract columns, aliases, and prepare metadata dynamically."""
    sql = ' '.join(sql.split())  # Normalize whitespace

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

    # Process each column to extract metadata dynamically
    parsed_columns = []
    for col in columns:
        match = re.match(r'(.*?)(?:\s+AS\s+|\s+)([A-Za-z][A-Za-z0-9_]*)$', col.strip(), re.IGNORECASE)
        expression = match.group(1).strip() if match else col.strip()
        alias = match.group(2).strip() if match else None

        # Infer source table and column using heuristic pattern matching
        source_table, source_column = None, None

        # Extract alias dynamically and infer column
        source_column_match = re.search(r'\b(\w+)\.([A-Za-z0-9_]+)', expression)
        if source_column_match:
            source_table = source_column_match.group(1)  # Table alias
            source_column = source_column_match.group(2)  # Column name
        pp(alias)
        parsed_columns.append({
            'Source_Table': source_table,
            'Source_Column': source_column,
            'Destination': alias,
            'Source_Expression': expression,
        })

    return parsed_columns

def extract_table_aliases(sql):
    """Extract table aliases and their corresponding table names, including subqueries."""
    sql = ' '.join(sql.split())  # Normalize whitespace
    
    # First, handle normal table references
    # Match pattern: database.schema.table alias or table alias
    table_aliases = {}
    
    # Pattern for direct table references
    direct_refs = re.finditer(
        r'FROM|JOIN\s+(\w+(?:\.\w+){0,2})\s+(?:AS\s+)?(\w+)',
        sql,
        re.IGNORECASE
    )
    for match in direct_refs:
        if match.group(1) and match.group(2):
            table_aliases[match.group(2).lower()] = match.group(1)
    
    # Pattern for subqueries
    # Find all subqueries with their aliases
    subquery_pattern = r'\((SELECT[^()]+(?:\([^()]*\)[^()]*)*)\)\s+(?:AS\s+)?(\w+)'
    subqueries = re.finditer(subquery_pattern, sql, re.IGNORECASE)
    
    for match in subqueries:
        subquery = match.group(1)
        alias = match.group(2)
        
        # Extract the main table from the subquery
        table_match = re.search(r'FROM\s+(\w+(?:\.\w+){0,2})', subquery, re.IGNORECASE)
        if table_match:
            table_name = table_match.group(1)
            table_aliases[alias.lower()] = table_name
    
    # Print for debugging
    print("Extracted table aliases:", table_aliases)
    
    return table_aliases

def parse_sql_columns(sql_query):
    """Parse columns and resolve table aliases dynamically."""
    columns = extract_columns_with_metadata(sql_query)
    table_aliases = extract_table_aliases(sql_query)
    
    for col in columns:
        if col['Source_Table']:
            alias = col['Source_Table'].lower()
            if alias in table_aliases:
                col['Source_Table'] = table_aliases[alias]
            else:
                # Try to match table alias from the first part of column reference
                alias_match = re.match(r'(\w+)\.', col['Source_Expression'])
                if alias_match and alias_match.group(1).lower() in table_aliases:
                    col['Source_Table'] = table_aliases[alias_match.group(1).lower()]
                else:
                    col['Source_Table'] = "Unknown"
    
    return columns




################################################################################
# Streamlit App
################################################################################
def main():
    st.title("SQL Column and Table Parser with Dynamic Metadata (pypeg2)")



    initial_sql = (
        "select LTRIM(M.ACCT_NB, '0') AS JPMC_ACCT_NBR,  RIGHT(M.FIRM_BANK_ID, 3) AS BNK_NB,  "
        "M.ENTP_PROD_CLS_CD AS PROD_CD,  LPAD(M.SUB_PROD_CD, 3, '0') AS SUB_PROD_CD, AAA.INTNT_ACCT_RCRD_ID "
        "FROM  (SELECT  ACCT_NB,  FIRM_BANK_ID,  ENTP_PROD_CLS_CD, SUB_PROD_CD, RCRD_ID FROM   PROD_110575_ICDW_DB.CUSTOMERCORE_V.CST_FRC_MGRT_ACCT  QUALIFY  ROW_NUMBER() OVER (PARTITION BY ACCT_NB ORDER BY END_DT DESC) = 1 ) M "
        "JOIN  (select A.INTNT_ACCT_RCRD_ID, A.SRC_ACCT_RCRD_ID  , B.RCRD_ID  from PROD_110575_ICDW_DB.CUSTOMERCORE_V.CST_FRC_ACCT_MP A "
        "left join PROD_110575_ICDW_DB.CUSTOMERCORE_V.CST_FRC_MGRT_ACCT B on A.MGRT_ACCT_RCRD_ID = B.RCRD_ID) AAA ON M.RCRD_ID = AAA.RCRD_ID;"
    )

    with st.form("sql_form"):
        sql_query = st.text_area("Enter your SQL query:", value=initial_sql, height=300)
        parse_button = st.form_submit_button("Parse Columns")

    if parse_button:
        columns = parse_sql_columns(sql_query)
        if not columns:
            st.write("No columns found or invalid SQL SELECT statement.")
        else:
            df = pd.DataFrame(columns)
            st.dataframe(df, use_container_width=True)

if __name__ == "__main__":
    main()
