"""Run device work outside Qt's UI thread; deliver results through queued signals."""
from PySide6.QtCore import QObject, QRunnable, Signal


class JobSignals(QObject):
    finished = Signal(object, object)


class Job(QRunnable):
    def __init__(self, work):
        super().__init__()
        self.work = work
        self.signals = JobSignals()

    def run(self):
        try:
            result = self.work()
        except Exception as exc:
            self.signals.finished.emit(None, exc)
        else:
            self.signals.finished.emit(result, None)
