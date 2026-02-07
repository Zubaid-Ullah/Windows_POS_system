from PyQt6.QtCore import QObject, QThread, pyqtSignal, QRunnable, QThreadPool, pyqtSlot
import traceback
import sys

class TaskWorker(QRunnable):
    """
    Standard worker to run any function in a background thread.
    """
    class Signals(QObject):
        finished = pyqtSignal(object)
        error = pyqtSignal(str)

    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = self.Signals()

    @pyqtSlot()
    def run(self):
        try:
            result = self.fn(*self.args, **self.kwargs)
            self.signals.finished.emit(result)
        except Exception:
            err = traceback.format_exc()
            self.signals.error.emit(err)

class BlockingTaskManager(QObject):
    """
    Global manager to prevent GUI hangs by offloading blocking operations.
    """
    def __init__(self):
        super().__init__()
        self.pool = QThreadPool.globalInstance()
        # Ensure we don't saturate the CPU but have enough threads for I/O
        self.pool.setMaxThreadCount(max(4, QThread.idealThreadCount()))

    def run_task(self, fn, on_finished=None, on_error=None, *args, **kwargs):
        """
        Runs a function in the background.
        :param fn: Function to run
        :param on_finished: Slot(result)
        :param on_error: Slot(error_string)
        """
        worker = TaskWorker(fn, *args, **kwargs)
        if on_finished:
            worker.signals.finished.connect(on_finished)
        if on_error:
            worker.signals.error.connect(on_error)
        else:
            worker.signals.error.connect(lambda e: print(f"[TaskManager] Error: {e}"))
            
        self.pool.start(worker)

# Global Instance
task_manager = BlockingTaskManager()
