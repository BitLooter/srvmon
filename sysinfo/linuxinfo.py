"""sysinfo implementation for Linux"""

import os
from . import common

class VolumeInfo(common.VolumeInfo):
    def __init__(self, volume):
        #TODO: Verify volume is valid
        self.volume = volume.strip()
        self._stat = os.statvfs(self.volume)

    @property
    def free_space(self):
        return self._stat.f_bavail * self._stat.f_frsize

    @property
    def total_size(self):
        return self._stat.f_blocks * self._stat.f_frsize
