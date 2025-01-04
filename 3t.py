from pypeg2 import *
import re

e=sys.exit

# This pattern will match any amount of whitespace including newlines
ws = re.compile(r'\s*')
rest_of_line = re.compile(r'.*$', re.DOTALL)
rest_of_select_body = re.compile(r'(?:(?!;\s*$).)*', re.DOTALL)
condition = re.compile(r'[^;]+')

class Local(object):
	def set_fname(self): self.fname=__name__
		
		
class Condition(str):
	grammar = name(), '=',  word

# Using csl() to parse comma-separated lists that may span multiple lines
class ConditionList(List):
	grammar = csl(Condition)

class Select(List,  Local):
	grammar = ['SELECT', 'select'],condition,';'

class SQLExpression(List):
	grammar = maybe_some(Select)

test_string = '''
SELECT LTRIM(M.ACCT_NB,'0') JPMC_ACCT_NBR, RIGHT(M.FIRM_BANK_ID,3) BNK_NB,
       LPAD(M.SUB_PROD_CD,3,'0') SUB_PROD_CD
FROM (SELECT ACCT_NB, FIRM_BANK_ID
      FROM MyTable
      WHERE Something = 1) M;


'''
if 1:
	parsed_sql = parse(test_string, SQLExpression)

	print(parsed_sql)