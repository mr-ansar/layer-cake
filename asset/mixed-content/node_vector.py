def node_vector(self, object_type, settings, input):
	role = ar.object_role()

	name_counts = ['"%s" (%d)' % (k, len(v)) for k, v in ap.pt.thread_classes.items()]

	executable = os.path.abspath(sys.argv[0])
	self.trace('Executable "%s" as node process (%d)' % (executable, os.getpid()))
	self.trace('Working folder "%s"' % (os.getcwd()))
	self.trace('Running object "%s"' % (object_type.__art__.path,))
	self.trace('Class threads (%d) %s' % (len(ap.pt.thread_classes), ','.join(name_counts)))

	# One source of directory information.
	# Persistent.
	p = role.properties

	# Start with the scope enumeration passed through from
	# create_node(). Where does this node exist within the
	# hierarchy of nodes?
	scope = node_settings.node_scope
	if scope is None:
		return ar.Failed(node_scope=('<null>', 'scope is undefined'))

	if scope == ScopeOfService.PROCESS:
		if node_settings.group_port is None:
			f = ar.Failed(node_process=(None, f'no group port available'))
			return f
		self.trace(f'Detected group port [{node_settings.group_port}]')
		connect_above = HostPort('127.0.0.1', node_settings.group_port)
		accept_below = HostPort(host=None)				# Null. Disabled.
	elif scope == ScopeOfService.GROUP:
		connect_above = p.connect_above
		accept_below = HostPort('127.0.0.1', 0)			# Ephemeral.
	elif scope == ScopeOfService.HOST:
		connect_above = p.connect_above
		accept_below = p.accept_below
	elif scope == ScopeOfService.LAN:
		connect_above = p.connect_above
		accept_below = p.accept_below
	elif scope == ScopeOfService.WAN:
		connect_above = HostPort(host=None)			# Nothing above.
		accept_below = HostPort('127.0.0.1', 0)			# Ephemeral.

	def show(a):
		if a is None:
			return '<null>'
		if isinstance(a, DirectoryAccess):
			return f'DirectoryAccess({a.directory_id} at "{a.access_ipp.host}")'
		if a.host is None:
			return 'HostPort(None)'
		return f'HostPort({a.host}:{a.port})'

	self.trace(f'Connecting to directory above at {show(connect_above)}')
	self.trace(f'Accepting directories from below at {show(accept_below)}')

	a = self.create(ServiceDirectory, scope, connect_above, accept_below)
	self.assign(a, 'node-directory')
	pb.directory = a

	# Wait for operational directory, esp. ephemeral.
	m = self.select(ar.Completed, HostPort, ar.Stop, ar.Faulted)
	if isinstance(m, ar.Completed):
		return m.value
	elif isinstance(m, ar.Stop):
		return ar.Aborted()
	elif isinstance(m, ar.Faulted):
		return m

	# Save the ephemeral.
	if scope in (ScopeOfService.GROUP, ScopeOfService.WAN):
		node_settings.accept_port = m.port

	def create(self):
		if input is not None:
			return self.create(object_type, settings, input)
		if settings is not None:
			return self.create(object_type, settings)
		return self.create(object_type)

	a = create(self)

	try:
		while True:
			m = self.select(ar.Completed, ar.Stop, ar.Pause, ar.Resume)

			if isinstance(m, ar.Completed):
				# Do a "fake" signaling. Sidestep all the platform machinery
				# and just set a global. It does avoid any complexities
				# arising from overlapping events. Spent far too much time
				# trying to untangle signals, exceptions and interrupted i/o.
				ar.co.signal_received = signal.SIGKILL
				return m.value
			elif isinstance(m, ar.Stop):
				# Received a Stop.
				self.send(m, a)
				m = self.select(ar.Completed)
				return m.value
			
			self.send(m, a)
	finally:
		pass

ar.bind_function(node_vector, lifecycle=True, message_trail=True, execution_trace=True)

