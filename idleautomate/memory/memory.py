import ctypes
import ctypes.util
from ctypes import CFUNCTYPE, POINTER

libc = ctypes.CDLL(ctypes.util.find_library('c'))
libmono = ctypes.CDLL(ctypes.util.find_library('monosgen-2.0.1'))

TASK_DYLD_INFO = 17

class task_dyld_info(ctypes.Structure):
    _fields_ = [
        ("all_image_info_addr", ctypes.c_uint32),
        ("all_image_info_size", ctypes.c_uint32),
        ("all_image_info_format", ctypes.c_uint32),
    ]

TASK_DYLD_INFO_COUNT = ctypes.sizeof(task_dyld_info) // 4

VM_REGION_BASIC_INFO_64 = 9

class vm_region_basic_info_64(ctypes.Structure):
    _fields_ = [
        ('protection', ctypes.c_uint32),
        ('max_protection', ctypes.c_uint32),
        ('inheritance', ctypes.c_uint32),
        ('shared', ctypes.c_uint32),
        ('reserved', ctypes.c_uint32),
        ('offset', ctypes.c_ulonglong),
        ('behavior', ctypes.c_uint32),
        ('user_wired_count', ctypes.c_ushort),
    ]

VM_REGION_BASIC_INFO_COUNT_64 = ctypes.sizeof(vm_region_basic_info_64) // 4

class vm_region_submap_info_64(ctypes.Structure):
    _fields_ = [
        ('protection', ctypes.c_uint),
        ('max_protection', ctypes.c_uint),
        ('inheritance', ctypes.c_uint),
        ('offset', ctypes.c_ulonglong),
        ('user_tag', ctypes.c_uint),
        ('pages_resident', ctypes.c_uint),
        ('pages_shared_now_private', ctypes.c_uint),
        ('pages_swapped_out', ctypes.c_uint),
        ('pages_dirtied', ctypes.c_uint),
        ('ref_count', ctypes.c_uint),
        ('shadow_depth', ctypes.c_ushort),
        ('external_pager', ctypes.c_char),
        ('share_mode', ctypes.c_char),
        ('is_submap', ctypes.c_uint),
        ('behavior', ctypes.c_uint),
        ('object_id', ctypes.c_uint32),
        ('user_wired_count', ctypes.c_uint32),
        # ('pages_reusable', ctypes.c_uint32),
    ]

VM_REGION_SUBMAP_INFO_COUNT_64 = ctypes.sizeof(vm_region_submap_info_64) // 4

class vm_region_submap_short_info_data_64(ctypes.Structure):
  _fields_ = [
      ("protection", ctypes.c_uint32),
      ("max_protection", ctypes.c_uint32),
      ("inheritance", ctypes.c_uint32),
      ("offset", ctypes.c_ulonglong),
      ("user_tag", ctypes.c_uint32),
      ("ref_count", ctypes.c_uint32),
      ("shadow_depth", ctypes.c_uint16),
      ("external_pager", ctypes.c_byte),
      ("share_mode", ctypes.c_byte),
      ("is_submap", ctypes.c_uint32),
      ("behavior", ctypes.c_uint32),
      ("object_id", ctypes.c_uint32),
      ("user_wired_count", ctypes.c_uint32),
  ]

VM_REGION_SUBMAP_SHORT_INFO_DATA_64 = ctypes.sizeof(vm_region_submap_short_info_data_64) // 4

VM_PROT_READ = 1
VM_PROT_WRITE = 2
VM_PROT_EXECUTE = 4

MH_MAGIC_64 = 0xfeedfacf

class mach_header(ctypes.Structure):
    _fields_ = [
        ("magic", ctypes.c_uint32),
        ("cputype", ctypes.c_uint32),
        ("cpusubtype", ctypes.c_uint32),
        ("filetype", ctypes.c_uint32),
        ("ncmds", ctypes.c_uint32),
        ("sizeofcmds", ctypes.c_uint32),
        ("flags", ctypes.c_uint32),
        ("reserved", ctypes.c_uint32),
    ]

class segment_command(ctypes.Structure):
    _fields_ = [
        ("cmd", ctypes.c_uint32),
        ("cmdsize", ctypes.c_uint32),
        ("segname", ctypes.c_char*16),
        ("vmaddr", ctypes.c_uint64),
        ("vmsize", ctypes.c_uint64),
        ("fileoff", ctypes.c_uint64),
        ("filesize", ctypes.c_uint64),
        ("maxprot", ctypes.c_uint32),
        ("initprot", ctypes.c_uint32),
        ("nsects", ctypes.c_uint32),
        ("flags", ctypes.c_uint32),
    ]

class Process(object):
    def __init__(self, pid=None):
        super().__init__()
        if pid is None:
            raise Exception("No PID given.")
        self.pid = pid
        self.task = None
        self.mytask = None
        self.Open()


    def __enter__(self):
        self.Open()
        return self


    def __exit__(self, exc_type=None, exc_val=None, exc_tb=None):
        pass


    def Close(self):
        pass


    def Open(self):
        # this might break in the future if macos doesn't allow
        # reuse of mach tasks, move to each funtion like region()
        self.task = ctypes.c_uint32()

        self.mytask = libc.mach_task_self()
        ret = libc.task_for_pid(self.mytask, ctypes.c_int(self.pid), ctypes.pointer(self.task))
        if ret != 0:
            raise Exception(f"task_for_pid failed, error code: {ret}")


    def vm_read(self, addr, bytes=8):
        pdata = ctypes.c_void_p(0)
        data_cnt = ctypes.c_uint32(0)

        ret = libc.mach_vm_read(self.task, 
                                ctypes.c_ulonglong(addr),
                                ctypes.c_ulonglong(bytes),
                                ctypes.pointer(pdata),
                                ctypes.pointer(data_cnt))

        if ret != 0:
            raise Exception(f"mach_vm_read failed, error code: {ret}")

        buf = ctypes.string_at(pdata.value, data_cnt.value)
        return buf


    def find_region(self, dylib_name=None):
        iter = 0
        lsize = ctypes.c_ulong(0)
        depth = 0
        bytes_read = 0
        info = vm_region_submap_short_info_data_64()
        count = ctypes.c_uint32(VM_REGION_SUBMAP_SHORT_INFO_DATA_64)

        while True:
            c_depth = ctypes.c_uint32(depth)
            addr = ctypes.c_ulong(iter)
            bytes_read = ctypes.c_uint32()
            region = libc.vm_region_recurse_64(self.task, ctypes.pointer(addr),
                                            ctypes.pointer(lsize), 
                                            ctypes.pointer(c_depth),
                                            ctypes.pointer(info), 
                                            ctypes.pointer(count))

            if region == 1:
                break

            if region != 0:
                raise Exception(f"Error in vm_region_recurse_64: {region}")

            mh = mach_header()
            kr = libc.mach_vm_read_overwrite(self.task, addr, 
                                            ctypes.sizeof(mach_header), 
                                            ctypes.pointer(mh), 
                                            ctypes.pointer(bytes_read))

            if bytes_read.value == ctypes.sizeof(mach_header) and mh.magic == MH_MAGIC_64:   
                if dylib_name is not None:
                    if dylib_name.encode() in self.vm_read(addr.value, mh.sizeofcmds):
                        return addr.value, lsize.value
                else:
                    return addr.value

            iter = addr.value + lsize.value


    def region(self, start_offset=None, end_offset=None):
        task = ctypes.c_uint32()
        mytask = libc.mach_task_self()
        ret = libc.task_for_pid(mytask, ctypes.c_int(self.pid), ctypes.pointer(task))

        map = []
        iter = 0
        lsize = ctypes.c_ulong(0)
        depth = 0
        bytes_read = 0
        info = vm_region_submap_short_info_data_64()
        count = ctypes.c_uint32(VM_REGION_SUBMAP_SHORT_INFO_DATA_64)

        if start_offset is not None:
            iter = start_offset

        while True:
            c_depth = ctypes.c_uint32(depth)
            addr = ctypes.c_ulong(iter)
            bytes_read = ctypes.c_uint32()
            region = libc.vm_region_recurse_64(self.task, ctypes.pointer(addr),
                                            ctypes.pointer(lsize), 
                                            ctypes.pointer(c_depth),
                                            ctypes.pointer(info), 
                                            ctypes.pointer(count))

            if region == 1:
                break
            if region != 0:
                raise Exception(f"Error in vm_region_recurse_64: {region}")
            if end_offset is not None:
                if addr.value > end_offset:
                    break

            map.append((addr.value,lsize.value))
            iter = addr.value + lsize.value
        return map
