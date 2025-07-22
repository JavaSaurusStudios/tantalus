import struct

class MemoryManager:
    def __init__(self, process_name):
        self.process_name = process_name
        self.pm = None
        self.base_module = None
        self.attached = False

    def attach(self):
        try:
            import pymem
            import pymem.process
            self.pm = pymem.Pymem(self.process_name)
            self.base_module = self.get_module_base(self.process_name)
            self.attached = True
            return True
        except Exception:
            self.attached = False
            return False

    def get_module_base(self, module_name):
        import pymem
        import pymem.process
        module = pymem.process.module_from_name(self.pm.process_handle, module_name)
        return module.lpBaseOfDll

    def read_pointer_chain(self, base_addr, offsets):
        addr = base_addr
        for offset in offsets:
            if addr == 0:
                return None
            try:
                addr = self.pm.read_int(addr)
            except Exception:
                return None
            if addr == 0:
                return None
            addr += offset
        return addr

    def read_float(self, addr):
        try:
            data = self.pm.read_bytes(addr, 4)
            return struct.unpack("<f", data)[0]
        except Exception:
            return None

    def read_int(self, addr):
        try:
            data = self.pm.read_bytes(addr, 4)
            return struct.unpack("<i", data)[0]
        except Exception:
            return None

    def read_ushort(self, addr):
        try:
            data = self.pm.read_bytes(addr, 2)
            return struct.unpack("<H", data)[0]
        except Exception:
            return None
