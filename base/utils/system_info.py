import psutil
import platform


def system_info():
    info = {}

    # 获取操作系统信息
    # info['os_type'] = platform.system()
    # info['os_version'] = platform.version()
    # info['architecture'] = platform.architecture()
    # info['network_name'] = platform.node()
    info['操作系统'] = platform.system()
    info['操作系统版本'] = platform.version()
    info['架构'] = platform.architecture()
    info['设备名称'] = platform.node()

    # 获取CPU信息
    # info['physical_cores'] = psutil.cpu_count(logical=False)
    # info['logical_cores'] = psutil.cpu_count(logical=True)
    # info['cpu_freq'] = psutil.cpu_freq()._asdict()
    # info['cpu_usage'] = psutil.cpu_percent(interval=1)
    info['物理核心数'] = psutil.cpu_count(logical=False)
    info['逻辑物理核心数'] = psutil.cpu_count(logical=True)
    info['CPU频率'] = psutil.cpu_freq()._asdict()
    info['CPU使用率'] = psutil.cpu_percent(interval=1)

    # 获取内存信息
    # info['virtual_memory'] = psutil.virtual_memory()._asdict()
    # info['swap_memory'] = psutil.swap_memory()._asdict()
    info['虚拟内存'] = psutil.virtual_memory()._asdict()
    info['交换内存'] = psutil.swap_memory()._asdict()

    # 获取磁盘信息
    # info['disk_partitions'] = [p._asdict() for p in psutil.disk_partitions()]
    # info['disk_usage'] = psutil.disk_usage('/')._asdict()
    # info['disk_io'] = psutil.disk_io_counters()._asdict()
    info['硬盘分区'] = [p._asdict() for p in psutil.disk_partitions()]
    info['硬盘使用率'] = psutil.disk_usage('/')._asdict()
    info['硬盘IO'] = psutil.disk_io_counters()._asdict()

    # 获取网络信息
    # info['net_io'] = psutil.net_io_counters()._asdict()
    # info['net_if_addrs'] = {k: [i._asdict() for i in v] for k, v in psutil.net_if_addrs().items()}
    # info['net_if_stats'] = {k: v._asdict() for k, v in psutil.net_if_stats().items()}

    return info


if __name__ == "__main__":
    info = system_info()
    for key, value in info.items():
        print(f"{key}: {value}")
