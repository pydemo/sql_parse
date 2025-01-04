import re
from pypeg2 import parse, List, csl, re as preg, maybe_some

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
    """Extract columns and aliases using regex directly"""
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

if __name__ == "__main__":
    test_string = """
SELECT LTRIM(M.ACCT_NB,'0') JPMC_ACCT_NBR, RIGHT(M.FIRM_BANK_ID,3) BNK_NB, COALESCE(EDW.PROD_TX,EDW2.PROD_TX,EDW3.PROD_TX) PROD_TX, M.ENTP_PROD_CLS_CD PROD_CD, LPAD(M.SUB_PROD_CD,3,'0') SUB_PROD_CD, COALESCE(EDW.LOB_CD,EDW2.LOB_CD,EDW3.LOB_CD) CUST_LOB, S.EXTN_BANK_ACCT_NB FRB_ACCT_NBR, S.EXTN_SRC_SYS_UNQ_ID FRB_GAID, O.LOAN_ID NETOX_LOAN_ID, L.TRANCHE_ACCT_NBR FRB_TRANCHE_ACCT_NBR, L.BISYS_NBR_FMT FRB_BISYS_NBR_FMT, C.CDM_ACCT_KEY FROM (SELECT ACCT_NB, FIRM_BANK_ID, ENTP_PROD_CLS_CD, SUB_PROD_CD, RCRD_ID       FROM PROD_110575_ICDW_DB.CUSTOMERCORE_V.CST_FRC_MGRT_ACCT       qualify row_number() over (partition by ACCT_NB order by END_DT DESC) = 1) M JOIN PROD_110575_ICDW_DB.CUSTOMERCORE_V.CST_FRC_ACCT_MP MP ON M.RCRD_ID=MP.MGRT_ACCT_RCRD_ID LEFT JOIN (SELECT * FROM PROD_110575_ICDW_DB.CUSTOMERCORE_V.CST_FRC_SRC_ACCT            qualify row_number() over (partition by RCRD_ID order by END_DT DESC) = 1) S ON MP.SRC_ACCT_RCRD_ID=S.RCRD_ID  LEFT JOIN (SELECT ACCT_NB, LOB_CD, RIGHT(BANK_NB,3) BANK_NB, SYS_RCRD_CD, PROD_CD, SUB_PROD_CD, PROD_TX            FROM PROD_110575_ICDW_DB.CUSTOMERCORE_V.ENTP_PRTY_ACCT_DTL WHERE HRTG_ACCT_CD = 'FRB'            qualify row_number() over (partition by ACCT_NB, BANK_NB, PROD_CD, SUB_PROD_CD order by END_DT DESC) = 1) EDW      ON LPAD(LTRIM(M.ACCT_NB,'0'),20,'0')=EDW.ACCT_NB AND RIGHT(M.FIRM_BANK_ID,3)=RIGHT(EDW.BANK_NB,3)         AND M.ENTP_PROD_CLS_CD=EDW.PROD_CD AND LPAD(M.SUB_PROD_CD,3,'0') = EDW.SUB_PROD_CD  LEFT JOIN (SELECT ACCT_NB, LOB_CD, RIGHT(BANK_NB,3) BANK_NB, SYS_RCRD_CD, PROD_CD, SUB_PROD_CD, PROD_TX            FROM PROD_110575_ICDW_DB.CUSTOMERCORE_V.ENTP_PRTY_ACCT_DTL             WHERE PROD_CD IN ('070','074') and acct_nb like '0000000000700%'            qualify row_number() over (partition by ACCT_NB, BANK_NB, PROD_CD, SUB_PROD_CD order by END_DT DESC) = 1) EDW2      ON LPAD(LTRIM(M.ACCT_NB,'0'),20,'0')=EDW2.ACCT_NB --AND RIGHT(M.FIRM_BANK_ID,3)=RIGHT(EDW.BANK_NB,3)         AND M.ENTP_PROD_CLS_CD=EDW2.PROD_CD AND LPAD(M.SUB_PROD_CD,3,'0') = EDW2.SUB_PROD_CD  LEFT JOIN (SELECT ACCT_NB, LOB_CD, RIGHT(BANK_NB,3) BANK_NB, SYS_RCRD_CD, PROD_CD, SUB_PROD_CD, PROD_TX            FROM PROD_110575_ICDW_DB.CUSTOMERCORE_V.ENTP_PRTY_ACCT_DTL WHERE HRTG_ACCT_CD = 'FRB'            qualify row_number() over (partition by ACCT_NB, BANK_NB, PROD_CD order by END_DT DESC) = 1) EDW3      ON LPAD(LTRIM(M.ACCT_NB,'0'),20,'0')=EDW3.ACCT_NB AND RIGHT(M.FIRM_BANK_ID,3)=RIGHT(EDW3.BANK_NB,3)         AND M.ENTP_PROD_CLS_CD=EDW3.PROD_CD --AND LPAD(M.SUB_PROD_CD,3,'0') = EDW.SUB_PROD_CD          LEFT JOIN (SELECT ACCT_NBR, LOAN_ID FROM PROD_111894_DB.FRB_ODM_LOAN_SILVER_MART_V.T_DIM_ORIG_LOAN             WHERE CURRENT_FLAG = 'Y' AND SRC_TYPE_CD = 'NETOX' AND contains(application_nbr , '-')) O       ON O.ACCT_NBR = S.EXTN_BANK_ACCT_NB LEFT JOIN (SELECT DISTINCT ACCT_NBR, TRANCHE_ACCT_NBR, BISYS_NBR_FMT FROM PROD_111894_DB.FRB_RDM_LOAN_SILVER_MART_T.T_DIM_LOAN             WHERE CURRENT_FLAG = 'Y') L ON L.ACCT_NBR = S.EXTN_BANK_ACCT_NB     LEFT JOIN (SELECT ACCT_NBR, CDM_ACCT_KEY FROM PROD_111894_DB.FRB_CUSTDM_DBO_T.T_CDM_ACCT WHERE CURR_REC_IND = 1            qualify row_number() over (partition by ACCT_NBR order by UPDATE_DT DESC) = 1) C       ON C.ACCT_NBR = S.EXTN_BANK_ACCT_NB
    """

    column_pairs = extract_columns(test_string)
    if column_pairs:
        for expr, alias in column_pairs:
            print(f"Column: {expr}")
            print(f"Alias:  {alias}")
            print("-" * 50)
    else:
        print("Failed to parse SQL statement")