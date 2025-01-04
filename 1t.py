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

# Example usage
sql_query = """
SELECT LTRIM(M.ACCT_NB,'0') JPMC_ACCT_NBR, RIGHT(M.FIRM_BANK_ID,3) BNK_NB, COALESCE(EDW.PROD_TX,EDW2.PROD_TX,EDW3.PROD_TX) PROD_TX, M.ENTP_PROD_CLS_CD PROD_CD, LPAD(M.SUB_PROD_CD,3,'0') SUB_PROD_CD, COALESCE(EDW.LOB_CD,EDW2.LOB_CD,EDW3.LOB_CD) CUST_LOB, S.EXTN_BANK_ACCT_NB FRB_ACCT_NBR, S.EXTN_SRC_SYS_UNQ_ID FRB_GAID, O.LOAN_ID NETOX_LOAN_ID, L.TRANCHE_ACCT_NBR FRB_TRANCHE_ACCT_NBR, L.BISYS_NBR_FMT FRB_BISYS_NBR_FMT, C.CDM_ACCT_KEY FROM (SELECT ACCT_NB, FIRM_BANK_ID, ENTP_PROD_CLS_CD, SUB_PROD_CD, RCRD_ID       FROM PROD_110575_ICDW_DB.CUSTOMERCORE_V.CST_FRC_MGRT_ACCT       qualify row_number() over (partition by ACCT_NB order by END_DT DESC) = 1) M JOIN PROD_110575_ICDW_DB.CUSTOMERCORE_V.CST_FRC_ACCT_MP MP ON M.RCRD_ID=MP.MGRT_ACCT_RCRD_ID LEFT JOIN (SELECT * FROM PROD_110575_ICDW_DB.CUSTOMERCORE_V.CST_FRC_SRC_ACCT            qualify row_number() over (partition by RCRD_ID order by END_DT DESC) = 1) S ON MP.SRC_ACCT_RCRD_ID=S.RCRD_ID  LEFT JOIN (SELECT ACCT_NB, LOB_CD, RIGHT(BANK_NB,3) BANK_NB, SYS_RCRD_CD, PROD_CD, SUB_PROD_CD, PROD_TX            FROM PROD_110575_ICDW_DB.CUSTOMERCORE_V.ENTP_PRTY_ACCT_DTL WHERE HRTG_ACCT_CD = 'FRB'            qualify row_number() over (partition by ACCT_NB, BANK_NB, PROD_CD, SUB_PROD_CD order by END_DT DESC) = 1) EDW      ON LPAD(LTRIM(M.ACCT_NB,'0'),20,'0')=EDW.ACCT_NB AND RIGHT(M.FIRM_BANK_ID,3)=RIGHT(EDW.BANK_NB,3)         AND M.ENTP_PROD_CLS_CD=EDW.PROD_CD AND LPAD(M.SUB_PROD_CD,3,'0') = EDW.SUB_PROD_CD  LEFT JOIN (SELECT ACCT_NB, LOB_CD, RIGHT(BANK_NB,3) BANK_NB, SYS_RCRD_CD, PROD_CD, SUB_PROD_CD, PROD_TX            FROM PROD_110575_ICDW_DB.CUSTOMERCORE_V.ENTP_PRTY_ACCT_DTL             WHERE PROD_CD IN ('070','074') and acct_nb like '0000000000700%'            qualify row_number() over (partition by ACCT_NB, BANK_NB, PROD_CD, SUB_PROD_CD order by END_DT DESC) = 1) EDW2      ON LPAD(LTRIM(M.ACCT_NB,'0'),20,'0')=EDW2.ACCT_NB --AND RIGHT(M.FIRM_BANK_ID,3)=RIGHT(EDW.BANK_NB,3)         AND M.ENTP_PROD_CLS_CD=EDW2.PROD_CD AND LPAD(M.SUB_PROD_CD,3,'0') = EDW2.SUB_PROD_CD  LEFT JOIN (SELECT ACCT_NB, LOB_CD, RIGHT(BANK_NB,3) BANK_NB, SYS_RCRD_CD, PROD_CD, SUB_PROD_CD, PROD_TX            FROM PROD_110575_ICDW_DB.CUSTOMERCORE_V.ENTP_PRTY_ACCT_DTL WHERE HRTG_ACCT_CD = 'FRB'            qualify row_number() over (partition by ACCT_NB, BANK_NB, PROD_CD order by END_DT DESC) = 1) EDW3      ON LPAD(LTRIM(M.ACCT_NB,'0'),20,'0')=EDW3.ACCT_NB AND RIGHT(M.FIRM_BANK_ID,3)=RIGHT(EDW3.BANK_NB,3)         AND M.ENTP_PROD_CLS_CD=EDW3.PROD_CD --AND LPAD(M.SUB_PROD_CD,3,'0') = EDW.SUB_PROD_CD          LEFT JOIN (SELECT ACCT_NBR, LOAN_ID FROM PROD_111894_DB.FRB_ODM_LOAN_SILVER_MART_V.T_DIM_ORIG_LOAN             WHERE CURRENT_FLAG = 'Y' AND SRC_TYPE_CD = 'NETOX' AND contains(application_nbr , '-')) O       ON O.ACCT_NBR = S.EXTN_BANK_ACCT_NB LEFT JOIN (SELECT DISTINCT ACCT_NBR, TRANCHE_ACCT_NBR, BISYS_NBR_FMT FROM PROD_111894_DB.FRB_RDM_LOAN_SILVER_MART_T.T_DIM_LOAN             WHERE CURRENT_FLAG = 'Y') L ON L.ACCT_NBR = S.EXTN_BANK_ACCT_NB     LEFT JOIN (SELECT ACCT_NBR, CDM_ACCT_KEY FROM PROD_111894_DB.FRB_CUSTDM_DBO_T.T_CDM_ACCT WHERE CURR_REC_IND = 1            qualify row_number() over (partition by ACCT_NBR order by UPDATE_DT DESC) = 1) C       ON C.ACCT_NBR = S.EXTN_BANK_ACCT_NB
"""

# Parse the columns
columns = parse_sql_columns(sql_query)

# Print the results
print("Columns and Aliases:")
for col in columns:
    print(f"Expression: {col['expression']}")
    print(f"Alias: {col['alias']}")
    print("---")

"""
--// delete
SELECT LTRIM(M.ACCT_NB,'0') JPMC_ACCT_NBR, RIGHT(M.FIRM_BANK_ID,3) BNK_NB,
       COALESCE(EDW.PROD_TX, EDW2.PROD_TX, EDW3.PROD_TX) PROD_TX, M.ENTP_PROD_CLS_CD,
       LPAD(M.SUB_PROD_CD,3,'0') SUB_PROD_CD, COALESCE(EDW.LOB_CD, EDW2.LOB_CD, EDW3.LOB_CD),
       S.EXTN_BANK_ACCT_NB, S.EXTN_SRC_SYS_UNQ_ID FRB_GAID, O.LOAN_ID,
       L.TRANCHE_ACCT_NBR FRB_TRANCHE_ACCT_NBR, L.BISYS_NBR_FMT FRB_BISYS_NBR_FMT, C.CDM_ACCT_KEY
FROM (SELECT ACCT_NB, FIRM_BANK_ID, ENTP_PROD_CLS_CD, SUB_PROD_CD, RCRD_ID
      FROM PROD_110575_ICDW_DB.CUSTOMERCORE_V.CST_FRC_MGRT_ACCT
      QUALIFY ROW_NUMBER() OVER (PARTITION BY ACCT_NB ORDER BY END_DT DESC) = 1) M
JOIN PROD_110575_ICDW_DB.CUSTOMERCORE_V.CST_FRC_ACCT_MP MP
ON M.RCRD_ID = MP.MGRT_ACCT_RCRD_ID
"""    