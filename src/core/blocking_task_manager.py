from PyQt6.QtCore import QObject, QThread, pyqtSignal, QRunnable, QThreadPool, pyqtSlot
import traceback
import sys

class WorkerSignals(QObject):
    """
    Separate signals object to ensure thread-safe communication.
    """
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

class TaskWorker(QRunnable):
    """
    Standard worker to run any function in a background thread.
    """
    def __init__(self, fn, signals_parent, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        # Give signals a parent (the manager) so they aren't GC'd early
        self.signals = WorkerSignals(signals_parent)

    @pyqtSlot()
    def run(self):
        try:
            result = self.fn(*self.args, **self.kwargs)
            # Check if signals haven't been deleted already
            try:
                self.signals.finished.emit(result)
            except RuntimeError:
                pass # Already shutting down
        except Exception:
            err = traceback.format_exc()
            try:
                self.signals.error.emit(err)
            except RuntimeError:
                pass

class BlockingTaskManager(QObject):
    """
    Global manager to prevent GUI hangs by offloading blocking operations.
    """
    def __init__(self):
        super().__init__()
        self.pool = QThreadPool.globalInstance()
        # Ensure we don't saturate the CPU but have enough threads for I/O
        self.pool.setMaxThreadCount(max(4, QThread.idealThreadCount()))
        # Keep references to prevent GC
        self._active_workers = set()

    def run_task(self, fn, on_finished=None, on_error=None, *args, **kwargs):
        """
        Runs a function in the background.
        """
        worker = TaskWorker(fn, self, *args, **kwargs)
        self._active_workers.add(worker)

        def cleanup_worker():
            """Safe cleanup of worker references and signals."""
            try:
                if worker in self._active_workers:
                    self._active_workers.remove(worker)
                worker.signals.deleteLater()
            except:
                pass

        # Connect signals
        if on_finished:
            worker.signals.finished.connect(on_finished)
        
        worker.signals.finished.connect(cleanup_worker)
        
        if on_error:
            worker.signals.error.connect(on_error)
        else:
            worker.signals.error.connect(lambda e: print(f"[TaskManager] Error: {e}"))
        
        worker.signals.error.connect(cleanup_worker)
            
        self.pool.start(worker)

# Global Instance
task_manager = BlockingTaskManager()
