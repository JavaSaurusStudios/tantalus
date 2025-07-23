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

    def read_double(self, addr):
        try:
            data = self.pm.read_bytes(addr, 8)
            return struct.unpack("<d", data)[0]
        except Exception:
            return None

    def write_double(self, addr, value):
        try:
            data = struct.pack('<d', value)  # Pack as little-endian double
            self.pm.write_bytes(addr, data, 8)
            return True
        except Exception as e:
            print(f"Write failed: {e}")
            return False

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

    def write_string(self, addr, string_data, null_terminated=True):
        try:
            if null_terminated:
                string_data += '\x00'  # Add null terminator
            byte_data = string_data.encode('utf-8')
            self.pm.write_bytes(addr, byte_data, len(byte_data))
            return True
        except Exception as e:
            print(f"Error writing string: {e}")
            return False
        
    def read_string(self, addr, max_length=256, null_terminated=True):
        try:
            raw_bytes = self.pm.read_bytes(addr, max_length)
            if null_terminated:
                # Cut off at the first null byte
                raw_bytes = raw_bytes.split(b'\x00', 1)[0]
            return raw_bytes.decode('utf-8', errors='replace')
        except Exception as e:
            print(f"Error reading string: {e}")
            return None

    def replace_string_preserve_size(self, addr, new_string, max_read=256, pad_char=' ', null_terminated=True):
        """
        Replace a string in memory at `addr` using the same size as the original (in bytes).
        Truncates or pads `new_string` to match the original's size.
        """
        try:
            # Step 1: Read the original string from memory
            original_bytes = self.pm.read_bytes(addr, max_read)
            original_bytes = original_bytes.split(b'\x00', 1)[0]  # Null-terminated slice
            original_size = len(original_bytes)

            # Step 2: Prepare new string of same byte size
            new_fixed = new_string.encode('utf-8')[:original_size]  # Truncate to fit
            new_fixed = new_fixed.ljust(original_size, pad_char.encode('utf-8'))  # Pad if too short

            # Optional null terminator
            if null_terminated:
                new_fixed += b'\x00'

            # Step 3: Write it back
            self.pm.write_bytes(addr, new_fixed, len(new_fixed))
            return True
        except Exception as e:
            print(f"Error replacing string at {hex(addr)}: {e}")
            return False
