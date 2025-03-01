#
#
import layer_cake as lc

# MESSAGES ------------------------------------------------------------------------------
class Cook(object):
	def __init__(self, a: int=None, b: dict[int, str]=None, c=None):	# Cant hint here (-> int). Would annoy checkers.
		self.a = a
		self.b = b
		self.c = c

class Radiating(object):
	pass

lc.bind_message(Cook, c=lc.PointerTo(lc.Boolean))
lc.bind_message(Radiating)

# 1. List of args and their types and a return type, from function hints.
# 2. Still must be default callable (policy around persisted settings).
# 3. Types provided on bind when hints fall short.
'''
# POINT AS STATELESS MACHINE ------------------------------------------------------------
class DbQuery(lc.Point, lc.Stateless):
	def __init__(self, a: int=None, b: dict[int, str]=None, c=None):
		super().__init__()
		self.a = a
		self.b = b
		self.c = c

def DbQuery_Start(self, message):
	pass

def DbQuery_T1(self, message):
	pass

def DbQuery_Stop(self, message):
	self.complete()

lc.bind_stateless(DbQuery, (lc.Start, lc.T1, lc.Stop),
	return_type=dict[int, str],
	c=lc.TimeSpan())

# 1. List of args and their types, from __init__ function hints.
# 2. Dispatch table (list of received types) on bind.
# 3. Dispatch types should be hints where possible, Portable when not.
# 4. A return_type is passed to bind.
# 2. Still must be default callable (policy around persisted settings).
# 3. Types provided on bind when hints fall short.

# POINT AS FINITE-STATE MACHINE ---------------------------------------------------------
class INITIAL: pass
class IDLE: pass
class COOKING: pass

class Microwave(lc.Threaded, lc.StateMachine):
	def __init__(self, a: int=None, b: dict[int, str]=None, c=None):
		super().__init__(INITIAL)
		self.a = a
		self.b = b
		self.c = c
		self.temperature = 0
		self.timeout = 0

def Microwave_INITIAL_Start(self, message):
	return IDLE

def Microwave_IDLE_Cook(self, message):
	self.reply(Radiating())
	return COOKING

def Microwave_COOKING_Stop(self, message):
	self.complete(44)

lc.bind_stateful(Microwave,
	{
		INITIAL: (
			(lc.Start,),
			()
		),
		IDLE: (
			(Cook,),
			()
		),
		COOKING: (
			(lc.Stop,),
			()
		)
	},
	return_type=dict[int, str],
	c=lc.TimeSpan())


class Cook(object):
	def __init__(self, a: int=None, b: dict[int, str]=None, c=None):	# Cant hint here (-> int). Would annoy checkers.
lc.bind_message(Cook, c=lc.PointerTo(lc.Boolean))
BR_1 = lc.branch(int, dict[int, str], lc.Start)
def main(self, a: int=None, b: dict[int, str]=None, c=None) -> int:
	i, m = self.select(BR_1)
RT_2 = lc.register(dict[int, str])

def poly(self, a: int=None, b: dict[int, str]=None, c=None) -> lc.Any:	# Or typing.Any? NO - DIFFERENT
	b = b or {}

	isinstance(a, int)
	isinstance(b, dict)

	m, i = self.select(BR_1)
	if i == 0:
		return (0, RT_1)

	return ({'a':1}, RT_2)

class DbQuery(lc.Point, lc.Stateless):
	def __init__(self, a: int=None, b: dict[int, str]=None, c=None):

lc.bind_stateless(DbQuery, (lc.Start, lc.T1, lc.Stop),

class Microwave(lc.Threaded, lc.StateMachine):
	def __init__(self, a: int=None, b: dict[int, str]=None, c=None):
		super().__init__(INITIAL)

lc.bind_stateful(Microwave,
	{
		INITIAL: (
			(lc.Start,),
			()
		),

1. Message.__init__(self, a: int=None, b: dict[int, str]=None, c=None):
2. bind_message(Cook, c=lc.PointerTo(lc.Boolean)))
3. BR_1 = lc.branch(int, dict[int, str], lc.Start)
4. def main(self, a: int=None, b: dict[int, str]=None, c=None) -> int:
5. i, m = self.select(BR_1)
6. RT_2 = lc.register(dict[int, str])
7. def poly(self, a: int=None, b: dict[int, str]=None, c=None) -> lc.Any:
8. m, i = self.select(BR_1)
9. return ({'a':1}, RT_2)
10: class DbQuery(lc.Point, lc.Stateless): def __init__(self, a: int=None, b: dict[int, str]=None, c=None):
11: lc.bind_stateless(DbQuery, (lc.Start, lc.T1, lc.Stop), return_type=dict[str,int])
12: class Microwave(lc.Threaded, lc.StateMachine): def __init__(self, a: int=None, b: dict[int, str]=None, c=None):
13. lc.bind_stateful(Microwave,	{ INITIAL: ((lc.Start,), () ),


1. get_type_hints(Message.__init__) --------------------------- bind_message, hints to Portable, lookup/install
2. compile_schema(Message, c=lc.PointerTo(lc.Boolean))--------- compile_schema, if k in kw, override
3. def branch(*a)
4. get_type_hints(main) --------------------------------------- bind_function, hints to Portable, return type, lookup/install
5. BR_2 = lc.branch_table(dict[int, str]) --------------------- branch_table, hints to Portable, lookup/install, return tuple
6. i, m = self.branch(table-of-types) ------------------------- i, m = self.select(table), new input strategy for new type system
7. RT_2 = lc.return_type(dict[int, str]) ---------------------- RT = return_type(), hint to Portable, lookup/install
8. get_type_hints(Stateless.__init__) ------------------------- bind_stateless, hints to Portable, lookup/install
9. compile_schema(Stateless, c=lc.PointerTo(lc.Boolean)) ------ bind_stateless, return_type
10. get_type_hints(StateMachine.__init__) --------------------- bind_statemachine, hints to Portable, lookup/install
11. compile_schema(StateMachine, c=lc.PointerTo(lc.Boolean)) -- bind_statemachine, return_type
12. def main(self, b: dict[int, str]=None) -> int: ------------ argv -> codec -> settings, return -> codec -> stdout

13. self.select(int, Start, ...) ------------------------------ keep as easy-but-slow, for learning
'''
