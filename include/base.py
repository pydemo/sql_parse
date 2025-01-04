import re, os, sys
from pprint import pprint as pp
import include.config.init_config as init_config  
apc = init_config.apc

e=sys.exit


class Local(object):
	def set_fname(self): self.fname=__name__
		
		
class BaseBase(object):
	

	def get_type(self):
		return f'{self.__class__.__name__}'
	def init(self, parent, lid):
		self.lid = lid
		self.set_fname()
		self.attr={k:v for k, v in self.__dict__.items() if k not in ['position_in_text', 'fname','lid']}
		self.parent=parent
		
		self.gid = gid = apc.get_gid(self)
		#print(1111,gid)
		self.set_name()
		self.tname=self.__class__.__name__
		apc.cntr.inc(self)
		#self.dfrom=None
		
	


	def get_name(self):
		return self.name,  self.label
	def get_dot(self):
		return f'{self.name} [shape="box",label="{self.level} {self.tname} {apc.cntr.get(self)}" ];'
	def set_name(self):
		p,c=self.parent, self
		assert self.lid >=0
		if type(c) in [StringVal]:
			obj=self.val
			self.name, self.label = f'l{self.level}_{c.get_type()}_{self.lid}_{self.gid}', c.get_type()
		else:
			obj=self
			#print('parent:',type(p))
			print(1, c.get_type())
			self.name, self.label = f'l{c.get_type()}_{self.lid}_{self.gid}', c.get_type()

def clean_for_graphviz(multi_line_string):
	# Escape backslashes first
	cleaned_string=multi_line_string
	cleaned_string = multi_line_string.replace("\\", "")
	# Escape double quotes
	cleaned_string = cleaned_string.replace("'", '')
	# Replace line breaks with \l to align left in Graphviz
	cleaned_string = cleaned_string.replace('\n', '')
	# Add the final line break for the last line
	#cleaned_string += '\\l'
	return cleaned_string

def clean_for_html_display(multi_line_string):
	# Convert special HTML characters to their respective HTML entities
	html_cleaned_string = multi_line_string.replace("&", "&amp;")  # Ampersand
	html_cleaned_string = html_cleaned_string.replace("<", "&lt;")  # Less than
	html_cleaned_string = html_cleaned_string.replace(">", "&gt;")  # Greater than
	html_cleaned_string = html_cleaned_string.replace('"', "&quot;")  # Double quotes
	html_cleaned_string = html_cleaned_string.replace("'", "&#39;")  # Single quotes
	#html_cleaned_string = html_cleaned_string.replace('\n', '\\n')  # Single quotes

	return html_cleaned_string

def split_equally_by_words(text, num_lines=2):
	# Split the text by spaces to get words
	words = text.split()
	
	# Calculate roughly the number of words per line
	words_per_line = max(1, len(words) // num_lines)
	
	# Create a list to hold the lines
	lines = []
	
	# Split the words into lines
	for i in range(num_lines - 1):
		# Take the next slice of words_per_line words
		line = ' '.join(words[i*words_per_line:(i+1)*words_per_line])
		lines.append(line)
	
	# Add the last line, which includes the remaining words
	lines.append(' '.join(words[(num_lines - 1)*words_per_line:]))
	
	# If the last line is significantly shorter, redistribute the words
	if lines[-1] and len(lines[-1].split()) < words_per_line / 2:
		# Redistribute the words more evenly
		return split_equally_by_words(text, num_lines - 1)
	
	return lines
import math
class StringVal(BaseBase, Local):
	def __init__(self, val, level):
		self.val=val
		self.level=level
	def get_full_dot(self, parent, dfrom, lid, hdot, fdot, level):
		self.init(parent, lid)
		self.dfrom=dfrom
		#gid =apc.get_gid()
		
		print('A'*40, type(self.val))
		pp(self.val)
		out=[]
		val=clean_for_html_display(self.val)
		limit=60
		
		if len(val)>0:
			for line in split_equally_by_words(val,math.ceil(len(val)/limit)):
				out.append(f'<TR><TD >{line}</TD></TR>')
		else:
			out.append(f'<TR><TD >{val}</TD></TR>')
			
		hdot.append( f'''
		{self.name} [shape=none, margin=0, label=<
			<TABLE BORDER="1" CELLBORDER="1" CELLSPACING="0">
				
				{os.linesep.join(out)}
			</TABLE>
		>];''')
		
		if 1:
			dto, label = self.get_name()
			label= str(self.val).replace('"',"'")
			if 1:
				fdot.append(f'{self.dfrom} -> {dto}[label="StringVal ({level})" ];')


class StringTable(BaseBase):
	def get_full_dot(self, parent, dfrom, lid, hdot, fdot, level):
		self.level=level
		self.init(parent, lid)
		self.dfrom=dfrom
		#gid =apc.get_gid()
		val=self
		print('A'*40, type(val))
		pp(val)
		out=[]
		val=clean_for_html_display(val)
		limit=60
		
		if len(val)>0:
			for line in split_equally_by_words(val,math.ceil(len(val)/limit)):
				out.append(f'<TR><TD >{line}</TD></TR>')
		else:
			out.append(f'<TR><TD >{val}</TD></TR>')
			
		hdot.append( f'''
		{self.name} [shape=none, margin=0, label=<
			<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0" CELLPADDING="4" BGCOLOR="lightyellow">
				<TR><TD >{self.tname}</TD></TR>
				{os.linesep.join(out)}
			</TABLE>
		>];''')
		
		if 1:
			dto, label = self.get_name()
			label= str(val).replace('"',"'")
			if 1:
				fdot.append(f'{self.dfrom} -> {dto}[label="{self.tname} ({level})" ];')

class Comment(str, StringTable, Local):
	# Matches the rest of the line after a comment
	rest_of_line = re.compile(r'.*?(?=\n|$)')
	grammar = '--', rest_of_line
	def _get_dot(self):
		return f'{self.name} [shape="box",  color="gray", label="{self.level} {self.label}\n{self.tname} {self.gid} {self.lid}\n {str(self)}\n {apc.cntr.get(self)}" ];'

	def get_full_dot(self, parent, dfrom, lid, hdot, fdot, level):
		self.level=level
		self.init(parent, lid)
		self.dfrom=dfrom
		#gid =apc.get_gid()
		val=self
		print('A'*40, type(val))
		pp(val)
		out=[]
		val=clean_for_html_display(val)
		limit=60
		
		if len(val)>0:
			for line in split_equally_by_words(val,math.ceil(len(val)/limit)):
				out.append(f'<TR><TD >{line}</TD></TR>')
		else:
			out.append(f'<TR><TD >{val}</TD></TR>')
			
		hdot.append( f'''
		{self.name} [shape=none, margin=0, label=<
			<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0" CELLPADDING="4" BGCOLOR="whitesmoke">
				{os.linesep.join(out)}
			</TABLE>
		>];''')
		if 0:
			assert lid<len(parent), f'comment: {lid} > {len(parent)}'
			
			dto, label = parent[lid+1].get_name()
			label= str(val).replace('"',"'")
			if 1:
				fdot.append(f'{self.dfrom} -> {dto}[label="({level})" ];')
		if lid==len(parent):
			dto, label = self.get_name()
			label= str(val).replace('"',"'")
			if 1:
				fdot.append(f'{self.dfrom} -> {dto}[label="({level})" ];')
				
class String(BaseBase):
	def get_full_dot(self, parent, dfrom, lid, hdot, fdot, level):
		self.init(parent, lid)
		self.dfrom=dfrom
		self.level=level
		
		

		hdot.append(f'{self.get_dot()}')
		
		if 1:
			dto, label = self.get_name()
			label= str(self).replace('"',"'")
			fdot.append(f'{self.dfrom} -> {dto}[label="String\n{label} ({level})" ];')
			
class Base(BaseBase):
	def get_str_dot(self,  dfrom,  hdot, fdot):
		self.init(self.parent, self.lid)
		parent =self.parent
		lid=self.lid
		self.dfrom=dfrom
		
		

		hdot.append(f'{self.get_dot()}')
		
		if 1:
			dto, label = self.get_name()
			fdot.append(f'{self.dfrom} -> {dto}[label="Base.get_str_dot" ];')

	def get_dot_attr(self, hdot, fdot):
		
		if self.attr:
		
			print(self.gid)
			out=[]
			for k, v in self.attr.items():
				out.append(f'<TR><TD>{k}</TD><TD>{repr(v)[:30]}</TD></TR>')
				print(k,v, type(v))
				#if type(v) in [str]:
				#	e()
			hdot.append(f'''
		TableNode_{self.gid} [shape=none, margin=0, label=<
			<TABLE BORDER="1" CELLBORDER="1" CELLSPACING="0">
				
				{os.linesep.join(out)}
			</TABLE>
		>];''')			
			cfrom, clabel = self.get_name()
			fdot.append(f'{cfrom} -> TableNode_{self.gid}[label="attr2" ];')
					
	def get_full_dot(self, parent, dfrom, lid, hdot, fdot, level, label=''):

		self.init(parent, lid)
		self.dfrom=dfrom
		
		self.level=level
		hdot.append(f'{self.get_dot()}')
		cfrom=self.name
		if 1:
			dto, _ = self.get_name()
			fdot.append(f'{self.dfrom} -> {dto}[label="{label} ({self.level}) " ];')


		self.show_children(self, hdot, fdot)
		self.show_attr(hdot, fdot)

	def show_children(self, parent, hdot, fdot):
		base_classes = self.__class__.__bases__
		print('Base: ',base_classes, str in base_classes)
		cfrom=parent
		if str in base_classes:
			print('STR in BASE', type(self), self)
			#self.get_str_dot(self.name, hdot, fdot)
			#self.get_dot_attr( hdot, fdot)
		else:	
			for cid,c in enumerate(self):
				print (self.name, type(c), f'>{c}<')

				print (self.name, type(c))
				if type(c) in [str]:
					
					c = StringVal(c, self.level+1)
					c.get_full_dot(self, cfrom.name, cid, hdot, fdot, self.level+cid+1)
					
				else:
					comm=None
					if type(cfrom) in [Comment]:
						comm=cfrom
						print(111, cid, comm.lid, type(c), parent)
						
						#e()
						if comm.lid == 0:
							cfrom=parent
						else:
							cfrom=parent[comm.lid-1]
							
					c.get_full_dot(self, cfrom.name, cid, hdot, fdot, self.level+cid+1)
					if comm:
						fdot.append(f'{comm.name} -> {c.name}[label="comm ({self.level}) " style=dashed color="lightblue"];')
						comm=None
				cfrom = c

	def show_attr(self, hdot, fdot):
		print('SHOW ATTR')
		self.get_dot_attr( hdot, fdot)