workers = 1  # 进程数
threads = 1  # 每个进程开启的线程数
proc_name = 'app'
pidfile = './app.pid'  # gunicorn进程id，kill掉该文件的id，gunicorn就停止
loglevel = 'debug'
logfile = './debug.log'  # debug日志
errorlog = './error.log'  # 错误信息日志
timeout = 90
