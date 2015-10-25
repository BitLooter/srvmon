"""sysinfo handles all the data-gathering tasks"""

#TODO: Autodetect system, allow to specify, system, etc.

from sysinfo.linuxinfo import *

displaylist_functions = {
    'VolumeFreeSpace': lambda x: VolumeInfo(x).free_space,
    'VolumeTotalSpace': lambda x: VolumeInfo(x).total_size,

    # Dummy functions used for testing
    '_TestNull': lambda x: None,
    '_TestEcho': lambda x: x,
}
