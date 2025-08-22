from typing import *
import socket

def is_port_free(port: int, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((host, port))
            return True  # порт свободен
        except socket.error:
            return False  # порт занят

class Ports(dict):
	def __init__(self, start:int, end:int):
		super().__init__()
		for i in range(start, end):
			self[i] = False

	def get_port(self) -> Optional[int]:
		for i in self.keys():
			if not self[i]:
				if not is_port_free(i):
					self[i] = False
					continue
				self[i] = True
				return i
		return None

	def release_port(self, port:int):
		self[port] = False