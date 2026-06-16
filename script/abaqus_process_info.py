import psutil

def is_abaqus_process(proc):
    """判断一个进程是否是Abaqus相关进程"""
    abaqus_keywords = ['abaqus', 'standard', 'explicit', 'pre', 'cae']
    try:
        if proc.name() and any(keyword in proc.name().lower() for keyword in abaqus_keywords):
            return True
        exe_path = proc.exe()
        if exe_path and any(keyword in exe_path.lower() for keyword in abaqus_keywords):
            return True
    except (psutil.AccessDenied, psutil.NoSuchProcess, psutil.ZombieProcess):
        pass
    return False

def get_abaqus_processes_info():
    """获取并打印所有Abaqus相关进程的详细信息（含命令行）"""
    print("正在搜索系统中的Abaqus相关进程...")
    abaqus_procs_info = []

    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'memory_info', 'num_threads', 'status']):
        try:
            if is_abaqus_process(proc):
                # 获取 CPU 亲和性
                cpu_cores = []
                try:
                    cpu_cores = proc.cpu_affinity()
                except AttributeError:
                    cpu_cores = list(range(psutil.cpu_count()))
                except (psutil.AccessDenied, psutil.NoSuchProcess):
                    pass

                # 获取命令行
                cmdline_str = ""
                try:
                    cmdline_list = proc.cmdline()
                    if cmdline_list:
                        cmdline_str = ' '.join(cmdline_list)
                except (psutil.AccessDenied, psutil.NoSuchProcess, psutil.ZombieProcess):
                    cmdline_str = "<无法获取命令行>"

                info = {
                    'pid': proc.info['pid'],
                    'name': proc.info['name'],
                    'cpu_percent': proc.info['cpu_percent'],
                    'memory_percent': proc.info['memory_percent'],
                    'memory_rss_mb': proc.info['memory_info'].rss / (1024 * 1024) if proc.info['memory_info'] else None,
                    'num_threads': proc.info['num_threads'],
                    'status': proc.info['status'],
                    'cpu_affinity_cores': cpu_cores,
                    'cpu_core_count': len(cpu_cores),
                    'cmdline': cmdline_str,
                }
                abaqus_procs_info.append(info)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    if not abaqus_procs_info:
        print("未找到正在运行的Abaqus相关进程。")
        return

    # 按 CPU 使用率降序排序
    abaqus_procs_info.sort(key=lambda x: x['cpu_percent'], reverse=True)

    # 定义截断长度（可根据需要调整）
    CMD_MAX_LEN = 800

    print("\n找到以下Abaqus相关进程：")
    # 表头增加了 Command 列
    print("-" * (120 + CMD_MAX_LEN))
    header = (f"{'PID':>8} | {'Process Name':<25} | {'CPU%':>6} | {'MEM%':>6} | {'MEM(MB)':>10} | "
              f"{'Threads':>8} | {'Cores':>8} | {'Status':<10} | {'Command':<{CMD_MAX_LEN}}")
    print(header)
    print("-" * (120 + CMD_MAX_LEN))

    for proc in abaqus_procs_info:
        cmd_display = proc['cmdline']
        if len(cmd_display) > CMD_MAX_LEN:
            cmd_display = cmd_display[:CMD_MAX_LEN-3] + "..."
        print(f"{proc['pid']:>8} | {proc['name']:<25} | {proc['cpu_percent']:>6.1f} | "
              f"{proc['memory_percent']:>6.1f} | {proc['memory_rss_mb']:>10.1f} | "
              f"{proc['num_threads']:>8} | {proc['cpu_core_count']:>8} | {proc['status']:<10} | "
              f"{cmd_display:<{CMD_MAX_LEN}}")

    print("-" * (120 + CMD_MAX_LEN))
    print(f"总计找到 {len(abaqus_procs_info)} 个Abaqus相关进程。")

    print(abaqus_procs_info)

if __name__ == "__main__":
    get_abaqus_processes_info()