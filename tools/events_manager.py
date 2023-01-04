# -*- coding: utf-8 -*-
"""

"""

import os
import json
import time
from queue import Queue, Empty
from threading import Thread
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from tools.abaqus.Solver import Solver
from tools.abaqus.Postproc import Postproc
from tools.events_new import get_events_new


MAX_CPUS = int(os.getenv('MAX_CPUS'))


def dump_json(file_name, data):
    """
    Write JSON data to file.
    """
    with open(file_name, 'w') as f:
        return json.dump(data, f)


def load_json(file_name):
    """
    Read JSON data from file.
    """
    with open(file_name, 'r') as f:
        return json.load(f)


class EventManager:
    """
    事件管理器
    """

    def __init__(self):
        """初始化事件管理器"""
        # 事件对象列表
        self.__event_queue = Queue()
        # 事件管理器开关
        self.__active = False
        # 事件处理线程
        self.__thread = Thread(target=self.__run)
        self.count = 0
        self.thread_count = 0
        self.__max_cpus = MAX_CPUS
        self.__used_cpus = 0
        self.__events_running = []
        self.__events_done = []
        self.__events_reload = []
        self.f_in_queue = ''
        self.f_running = ''
        # 这里的__handlers是一个字典，用来保存对应的事件的响应函数
        # 其中每个键对应的值是一个列表，列表中保存了对该事件监听的响应函数，一对多
        self.__handlers = {}

    def set_filename(self, f_in_queue, f_running):
        self.f_in_queue = f_in_queue
        self.f_running = f_running
        
    def __run(self):
        """引擎运行"""
        print('{}_run'.format(self.count))
        while self.__active:
            print("\n  <__RUN::>开始get:", self.__event_queue)
            if self.__used_cpus < self.__max_cpus:
                try:
                    # 获取事件的阻塞时间设为1秒:如果在1s内队列中有元素，则取出；否则过1s之后报Empty异常
                    event = self.__event_queue.get(block=True, timeout=1)
                    event.dict['time'] = time.strftime('%Y-%m-%d %H:%M:%S')
                    print("  <__RUN::>取到事件了：", event)
                    self.__update_cpus(event)
                    self.__events_running.append(event)
                    self.__event_process(event)
                except Empty:
                    print("  <__RUN::>队列是空的")
            self.count += 1
            self.__update_running_status()
            for event in self.__events_reload:
                self.__event_process(event)
            print("  <__RUN::>Run中的count:", self.count)
            print("  <__RUN::>Run中的cpus:", self.__used_cpus)
            print("  <__RUN::>Run中的events:", self.__events_running)
            print("  <__RUN::>Run中的events_reload:", self.__events_reload)
            # self.update_status()
            time.sleep(2)

    def __event_process(self, event):
        """处理事件"""
        print('{}_EventProcess'.format(self.count))
        # 检查是否存在对该事件进行监听的处理函数
        if event.event_type in self.__handlers:
            # 若存在，则按顺序将事件传递给处理函数执行
            for handler in self.__handlers[event.event_type]:
                # 这里的handler就是放进去的监听函数，这里会跳转到listener.handler(event)
                is_reload = handler(event)
                if is_reload:
                    if event not in self.__events_reload:
                        self.__events_reload.append(event)
                else:
                    if event in self.__events_reload:
                        self.__events_reload.remove(event)
        self.count += 1

    def __update_cpus(self, event):
        """更新当前使用的cpu数量"""
        self.__used_cpus += int(event.dict['cpus'])

    def __update_running_status(self):
        """更新当前运行事件的状态"""
        for event in self.__events_running:
            if event.event_type == 'Solver':
                s = Solver(event.dict['job_path'])
                event.dict['status'] = s.solver_status()
                if s.is_done():
                    event.dict['time'] = time.strftime('%Y-%m-%d %H:%M:%S')
                    self.__events_running.remove(event)
                    self.__events_done.append(event)
                    self.__used_cpus -= int(event.dict['cpus'])
            if event.event_type == 'odb_to_npz':
                p = Postproc(event.dict['job_path'])
                event.dict['status'] = p.odb_to_npz_status()
                if p.is_odb_to_npz_done():
                    event.dict['time'] = time.strftime('%Y-%m-%d %H:%M:%S')
                    self.__events_running.remove(event)
                    self.__events_done.append(event)
                    self.__used_cpus -= int(event.dict['cpus'])
                    
    def start(self):
        """启动"""
        print('{}_start'.format(self.count))
        # 将事件管理器设为启动
        self.__active = True
        # 启动事件处理线程
        if self.thread_count == 0:
            try:
                self.__thread.start()
            except RuntimeError:
                self.__thread = Thread(target=self.__run)
                self.__thread.start()
            self.thread_count += 1
            self.count += 1

    def stop(self):
        """停止"""
        print('{}_stop'.format(self.count))
        # 将事件管理器设为停止
        self.__active = False
        # 等待事件处理线程退出
        if self.thread_count > 0:
            try:
                self.__thread.join()
            except RuntimeError:
                print('__thread.join() Error')
            self.thread_count -= 1
            self.count += 1

    def add_event_listener(self, event_type, handler):
        """绑定事件和监听器处理函数"""
        print('{}_add_event_listener'.format(self.count))
        # 尝试获取该事件类型对应的处理函数列表，若无则创建
        try:
            handlerList = self.__handlers[event_type]
        except KeyError:
            handlerList = []
            self.__handlers[event_type] = handlerList
        # 若要注册的处理器不在该事件的处理器列表中，则注册该事件
        if handler not in handlerList:
            handlerList.append(handler)
        print(self.__handlers)
        self.count += 1

    def remove_event_listener(self, event_type, handler):
        """移除监听器的处理函数"""
        print('{}_remove_event_listener'.format(self.count))
        try:
            handlerList = self.__handlers[event_type]
            # 如果该函数存在于列表中，则移除
            if handler in handlerList:
                handlerList.remove(handler)
            # 如果函数列表为空，则从引擎中移除该事件类型
            if not handlerList:
                del self.__handlers[event_type]
        except KeyError:
            pass
        self.count += 1

    def send_event(self, event):
        """发送事件，向事件队列中存入事件"""
        is_same = False
        event_dict = event.dict.copy()
        event_dict.pop('time')
        for current_event in self.__event_queue.queue:
            current_event_dict = current_event.dict.copy()
            current_event_dict.pop('time')
            if event.event_type == current_event.event_type and event_dict == current_event_dict:
                is_same = True

        if not is_same:
            print('{}_send_event'.format(self.count))
            self.__event_queue.put(event)
            self.count += 1
        else:
            print('%s已经在队列中' % event)

    def update_status(self):
        """发送事件，向事件队列中存入事件"""
        events_dict_in_queue = [event.dict for event in self.__event_queue.queue]
        events_dict_running = [event.dict for event in self.__events_running]
        dump_json(self.f_in_queue, events_dict_in_queue)
        dump_json(self.f_running, events_dict_running)
        
    def get_status(self):
        in_queue = [event.dict for event in self.__event_queue.queue]
        running = [event.dict for event in self.__events_running]
        done = [event.dict for event in self.__events_done]
        return in_queue, running, done
    
    def get_active(self):
        return self.__active

            
class Event:
    """事件对象"""

    def __init__(self, event_type=None):
        # 事件类型
        self.event_type = event_type
        # 字典用于保存具体的事件数据
        self.dict = {}
        # print('实例化事件对象：事件类型：%s,事件：%s' % (self.event_type, self.dict))


class EventSource:
    """
    事件源
    """

    def __init__(self, event_manager):
        print('EventSource实例化\n')
        self.__event_manager = event_manager

    def set_event(self, event_type, event_dict):
        self.__event_type = event_type
        self.__event_dict = event_dict

    def send_event(self):
        event = Event(self.__event_type)
        event.dict = self.__event_dict
        print('EventSource发送新事件%s\n' % event)
        self.__event_manager.send_event(event)


class SolverListener:
    """
    监听器
    """

    def __init__(self, username):
        self.__username = username

    # 监听器的处理函数
    def handler(self, event):
        print(u'%s 收到新事件' % self.__username)
        print(u'事件内容：%s' % event.dict)
        is_reload = False
        job_path = event.dict['job_path']
        if os.path.exists(job_path):
            s = Solver(job_path)
            s.read_msg()
            s.clear()
            if s.check_files():
                proc = s.run()
                with open(os.path.join(job_path, '.solver_status'), 'w', encoding='utf-8') as f:
                    f.write('Submitting')
            else:
                print('缺少必要的计算文件。', 'warning')
        else:
            print('不存在目录%s。' % job_path, 'warning')
        return is_reload


class PostprocListener:
    """
    监听器
    """

    def __init__(self, username):
        self.__username = username

    # 监听器的处理函数
    def handler(self, event):
        print(u'%s 收到新事件' % self.__username)
        print(u'事件内容：%s' % event.dict)
        is_reload = False
        job_path = event.dict['job_path']
        if os.path.exists(job_path):
            p = Postproc(job_path)
            s = Solver(job_path)
            if p.check_setting_files():
                if s.is_done():
                    if p.has_odb():
                        proc = p.odb_to_npz()
                        with open(os.path.join(job_path, '.odb_to_npz_status'), 'w', encoding='utf-8') as f:
                            f.write('Submitting')
                        with open(os.path.join(job_path, '.odb_to_npz_proc'), 'w', encoding='utf-8') as f:
                            f.write('0.0\n')
                    else:
                        print('缺少odb文件。', 'warning')
                else:
                    # 如果此时算例s正在计算中，则后处理过程p要等待其完成后再继续执行
                    with open(os.path.join(job_path, '.odb_to_npz_status'), 'w', encoding='utf-8') as f:
                        f.write('Waiting for solving')
                    with open(os.path.join(job_path, '.odb_to_npz_proc'), 'w', encoding='utf-8') as f:
                        f.write('0.0\n')
                    is_reload = True
            else:
                print('缺少odb_to_npz.json配置文件。', 'warning')
        else:
            print('不存在目录%s。' % job_path, 'warning')
        return is_reload

            
class StatusEventHandler(FileSystemEventHandler):
    def __init__(self, status_file, event_source):
        self.status_file = status_file
        self.event_source = event_source

    def on_any_event(self, event):
        pass

    def on_moved(self, event):
        pass

    def on_deleted(self, event):
        pass

    def on_modified(self, event):
        if event.src_path == self.status_file:
            for job in get_events_new(self.status_file):
                event_type = job['type']
                event_dict = job
                self.event_source.set_event(event_type, event_dict)
                self.event_source.send_event()
            dump_json(self.status_file, [])
            time.sleep(1)


def monitor(path, f_new, f_in_queue, f_running):
    
    # 1.实例化『监听器』
    solver_listener = SolverListener('Solver')

    # 2.实例化『事件管理器』
    event_manager = EventManager()
    event_manager.set_filename(f_in_queue, f_running)

    # 3.绑定『事件』和『监听器响应函数』
    event_manager.add_event_listener('Solver', solver_listener.handler)

    # 4.启动『事件管理器』
    # 4.1 这里会启动一个新的事件处理线程，一直监听下去，可以看__run()中while循环；
    # 4.2 同时主线程会继续执行下去
    event_manager.start()

    # 5.实例化『事件源』
    event_source = EventSource(event_manager)

    # 6.定时启动『事件源』中的『生成事件对象以及发送事件』
    observer = Observer()
    if not os.path.exists(path):
        os.mkdir(path)
    status_handler = StatusEventHandler(f_new, event_source)
    observer.schedule(status_handler, path, True)
    observer.start()

    try:
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        observer.stop()
        event_manager.stop()
        
        
if __name__ == '__main__':
    path = 'F:\\Github\\base\\files\\queue'
    f_new = 'F:\\Github\\base\\files\\queue\\.events_new'
    f_in_queue = 'F:\\Github\\base\\files\\queue\\.events_in_queue'
    f_running = 'F:\\Github\\base\\files\\queue\\.events_running'
    monitor(path, f_new, f_in_queue, f_running)
