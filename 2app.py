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
    
    # Split columns carefully, handling complex expressions
    def split_columns(clause):
        columns = []
        current_column = []
        paren_count = 0
        in_quote = False
        
        tokens = re.findall(r"'[^']*'|\b[A-Za-z_]+\b|\S", clause)
        
        for token in tokens:
            # Handle parentheses
            if token == '(':
                paren_count += 1
            elif token == ')':
                paren_count -= 1
            
            # Handle quotes
            if token.startswith("'") and token.endswith("'"):
                current_column.append(token)
            elif token == "'":
                in_quote = not in_quote
            
            current_column.append(token)
            
            # If we're at top-level (no open parentheses or quotes) and we see a comma
            if paren_count == 0 and not in_quote and token == ',':
                # Remove the comma and join the column tokens
                column_str = ' '.join(current_column[:-1]).strip()
                columns.append(column_str)
                current_column = []
        
        # Add the last column
        if current_column:
            columns.append(' '.join(current_column).strip().rstrip(','))
        
        return columns
    
    # Parse column expressions
    parsed_columns = []
    for column in split_columns(select_clause):
        # Attempt to find an explicit alias
        # Look for a word at the end that follows a column/function expression
        alias_match = re.search(r'\s+([A-Za-z_][A-Za-z0-9_]*)$', column)
        
        if alias_match:
            potential_alias = alias_match.group(1)
            potential_expr_without_alias = column[:-len(potential_alias)].strip()
            
            # Check if the potential alias is a true alias
            # It should come after a complete function or identifier expression
            if re.match(r'^.*[\w\)]+\s*$', potential_expr_without_alias):
                parsed_columns.append({
                    'expression': potential_expr_without_alias.strip(),
                    'alias': potential_alias.strip()
                })
            else:
                # If not a true alias, treat as part of the expression
                parsed_columns.append({
                    'expression': column.strip(),
                    'alias': None
                })
        else:
            # No alias found
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
