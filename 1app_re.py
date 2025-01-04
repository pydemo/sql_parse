import streamlit as st
import pandas as pd
import re

def parse_sql_columns(sql_query):
    # Remove comments
    sql_query = re.sub(r'--.*$', '', sql_query, flags=re.MULTILINE)

    # Extract the SELECT clause (everything after SELECT until the first FROM)
    select_match = re.search(r'SELECT\s+(.*?)\s+FROM', sql_query, re.IGNORECASE | re.DOTALL)
    if not select_match:
        return []

    select_clause = select_match.group(1)

    def split_columns(clause):
        columns = []
        current_column = []
        paren_count = 0
        in_quote = False

        tokens = re.findall(r"'[^']*'|\b[A-Za-z_]+\b|\S", clause)

        for token in tokens:
            if token == '(':
                paren_count += 1
            elif token == ')':
                paren_count -= 1

            if token.startswith("'") and token.endswith("'"):
                current_column.append(token)
            elif token == "'":
                in_quote = not in_quote

            current_column.append(token)

            if paren_count == 0 and not in_quote and token == ',':
                column_str = ' '.join(current_column[:-1]).strip()
                columns.append(column_str)
                current_column = []

        if current_column:
            columns.append(' '.join(current_column).strip().rstrip(','))

        return columns

    parsed_columns = []
    for column in split_columns(select_clause):
        alias_match = re.search(r'\s+([A-Za-z_][A-Za-z0-9_]*)$', column)
        if alias_match:
            potential_alias = alias_match.group(1)
            potential_expr_without_alias = column[:-len(potential_alias)].strip()
            if re.match(r'^.*[\w\)]+\s*$', potential_expr_without_alias):
                parsed_columns.append({
                    'expression': potential_expr_without_alias.strip(),
                    'alias': potential_alias.strip()
                })
            else:
                parsed_columns.append({
                    'expression': column.strip(),
                    'alias': None
                })
        else:
            parsed_columns.append({
                'expression': column.strip(),
                'alias': None
            })
    return parsed_columns


def main():
    st.title("SQL Column Parser (re)")
    sql_query = st.text_area("Enter your SQL query:", height=300)

    if st.button("Parse Columns"):
        columns = parse_sql_columns(sql_query)
        if not columns:
            st.write("No columns found or invalid SQL SELECT statement.")
        else:
            # Convert the list of dicts to a DataFrame for tabular display
            df = pd.DataFrame(columns)
            st.table(df)  # or st.dataframe(df) for a scrollable format

if __name__ == "__main__":
    main()
