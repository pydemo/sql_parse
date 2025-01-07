import streamlit as st
import pandas as pd
import sqlparse
from sqlparse.sql import IdentifierList, Identifier
from sqlparse.tokens import Keyword, DML
from pprint import pprint as pp

################################################################################
# Using sqlparse to extract table aliases and columns
################################################################################

def extract_table_aliases(parsed):
    """Extract table aliases and their corresponding table names from the parsed SQL."""
    table_aliases = {}
    from_seen = False

    for token in parsed.tokens:
        if token.ttype is DML and token.value.upper() == 'SELECT':
            continue
        if token.is_group:
            table_aliases.update(extract_table_aliases(token))
        if token.ttype is Keyword:
            if token.value.upper() in ('FROM', 'JOIN'):
                from_seen = True
                continue
        if from_seen:
            if isinstance(token, IdentifierList):
                for identifier in token.get_identifiers():
                    real_name = identifier.get_real_name()
                    alias = identifier.get_alias() or real_name
                    table_aliases[alias] = real_name
            elif isinstance(token, Identifier):
                real_name = token.get_real_name()
                alias = token.get_alias() or real_name
                table_aliases[alias] = real_name
            from_seen = False
    return table_aliases

def extract_columns_with_metadata(parsed, table_aliases):
    """Extract columns, aliases, and prepare metadata dynamically."""
    columns = []
    select_seen = False

    for token in parsed.tokens:
        if token.ttype is DML and token.value.upper() == 'SELECT':
            select_seen = True
            continue
        if select_seen:
            if isinstance(token, IdentifierList):
                for identifier in token.get_identifiers():
                    expression = identifier.get_real_name() or identifier.value
                    alias = identifier.get_alias()
                    # Infer source table and column
                    source_table, source_column = None, None
                    if '.' in expression:
                        parts = expression.split('.')
                        source_table = parts[0]
                        source_column = parts[1]
                        # Map alias to actual table name
                        if source_table in table_aliases:
                            source_table = table_aliases[source_table]
                    else:
                        source_column = expression
                    columns.append({
                        'Source_Table': source_table,
                        'Source_Column': source_column,
                        'Alias': alias,
                        'Source_Expression': expression,
                    })
            elif isinstance(token, Identifier):
                expression = token.get_real_name() or token.value
                alias = token.get_alias()
                # Infer source table and column
                source_table, source_column = None, None
                if '.' in expression:
                    parts = expression.split('.')
                    source_table = parts[0]
                    source_column = parts[1]
                    # Map alias to actual table name
                    if source_table in table_aliases:
                        source_table = table_aliases[source_table]
                else:
                    source_column = expression
                columns.append({
                    'Source_Table': source_table,
                    'Source_Column': source_column,
                    'Alias': alias,
                    'Source_Expression': expression,
                })
            select_seen = False
    return columns

################################################################################
# Streamlit App
################################################################################

def parse_sql_columns(sql_query):
    """Parse SQL query to extract columns and table aliases using sqlparse."""
    parsed = sqlparse.parse(sql_query)
    if not parsed:
        return []

    parsed = parsed[0]  # Assuming single statement

    # Extract table aliases
    table_aliases = extract_table_aliases(parsed)
    pp(table_aliases)
    pp(table_aliases.keys())

    # Extract columns with metadata
    columns = extract_columns_with_metadata(parsed, table_aliases)

    return columns

def main():
    st.title("SQL Column and Table Parser with Dynamic Metadata (sqlparse)")

    initial_sql = (
        "SELECT LTRIM(M.ACCT_NB, '0') AS JPMC_ACCT_NBR, RIGHT(M.FIRM_BANK_ID, 3) AS BNK_NB,  "
        "M.ENTP_PROD_CLS_CD AS PROD_CD, LPAD(M.SUB_PROD_CD, 3, '0') AS SUB_PROD_CD, AAA.INTNT_ACCT_RCRD_ID "
        "FROM  (SELECT  ACCT_NB, FIRM_BANK_ID, ENTP_PROD_CLS_CD, SUB_PROD_CD, RCRD_ID FROM   PROD_110575_ICDW_DB.CUSTOMERCORE_V.CST_FRC_MGRT_ACCT  QUALIFY  ROW_NUMBER() OVER (PARTITION BY ACCT_NB ORDER BY END_DT DESC) = 1 ) M "
        "JOIN  (SELECT A.INTNT_ACCT_RCRD_ID, A.SRC_ACCT_RCRD_ID, B.RCRD_ID FROM PROD_110575_ICDW_DB.CUSTOMERCORE_V.CST_FRC_ACCT_MP A "
        "LEFT JOIN PROD_110575_ICDW_DB.CUSTOMERCORE_V.CST_FRC_MGRT_ACCT B ON A.MGRT_ACCT_RCRD_ID = B.RCRD_ID) AAA ON M.RCRD_ID = AAA.RCRD_ID;"
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
            st.table(df)

if __name__ == "__main__":
    main()
