from __future__ import annotations

import contextlib
import time
from typing import TYPE_CHECKING, Iterable, cast
from collections import deque

from psygnal import EmitLoopError
from useq import MDASequence

from pymmcore_plus._logger import logger

from pymmcore_plus.mda._protocol import PMDAEngine
from pymmcore_plus.mda.events import PMDASignaler, _get_auto_MDA_callback_class
from pymmcore_plus.mda._runner import GeneratorMDASequence, MDARunner

if TYPE_CHECKING:
    from useq import MDAEvent



class EDARunner(MDARunner):
    """MDA Runner that uses a deque of events instead of a fixed one. This allows to add event
    on-the-fly during the acquisition.
    """

    def __init__(self) -> None:
        super().__init__()
        self.acq_events = None

        """Toggle the paused state of the current acquisition.

        To get whether the acquisition is currently paused use the
        [`is_paused`][pymmcore_plus.mda.MDARunner.is_paused] method. This method is a
        no-op if no acquistion is currently underway.
        """
        if self.is_running():
            self._paused = not self._paused
            self._events.sequencePauseToggled.emit(self._paused)

    def run(self, events: Iterable[MDAEvent]) -> None:
        """Run the multi-dimensional acquistion defined by `sequence`.

        Most users should not use this directly as it will block further
        execution. Instead, use the
        [`CMMCorePlus.run_mda`][pymmcore_plus.CMMCorePlus.run_mda] method which will
        run on a thread.

        Parameters
        ----------
        events : Iterable[MDAEvent]
            An iterable of `useq.MDAEvents` objects to execute.
        """

        self.acq_events = deque(events)


        error = None
        sequence = events if isinstance(events, MDASequence) else GeneratorMDASequence()
        try:
            self._prepare_to_run(sequence)
            self._engine = cast("PMDAEngine", self._engine)
            teardown_event = getattr(self._engine, "teardown_event", lambda e: None)

            while len(self.acq_events) > 0:
                event = self.acq_events.popleft()
                cancelled = self._wait_until_event(event)

                # If cancelled break out of the loop
                if cancelled:
                    break

                logger.info(event)
                if not self._running:
                    break

                self._engine.setup_event(event)

                output = self._engine.exec_event(event)

                if (img := getattr(output, "image", None)) is not None:
                    with contextlib.suppress(EmitLoopError):
                        self._events.frameReady.emit(img, event)

                teardown_event(event)

        except Exception as e:
            error = e
        with contextlib.suppress(Exception):
            self._finish_run(sequence)
        if error is not None:
            raise error

    def _wait_until_event(self, event: MDAEvent) -> bool:
        """Wait until the event's min start time, checking for pauses cancelations.

        Parameters
        ----------
        event : MDAEvent
            The event to wait for.

        Returns
        -------
        bool
            Whether the MDA was cancelled while waiting.
        """

        #TODO: CHeck if we would like to do something else here in case we add an event before the
        #next one
        if not self.is_running():
            return False
        if self._check_canceled():
            return True
        while self.is_paused() and not self._canceled:
            self._paused_time += self._pause_interval  # fixme: be more precise
            time.sleep(self._pause_interval)

            if self._check_canceled():
                return True

        if event.min_start_time:
            go_at = event.min_start_time + self._paused_time
            # We need to enter a loop here checking paused and canceled.
            # otherwise you'll potentially wait a long time to cancel
            to_go = go_at - self._time_elapsed()
            while to_go > 0:
                while self._paused and not self._canceled:
                    self._paused_time += self._pause_interval  # fixme: be more precise
                    to_go += self._pause_interval
                    time.sleep(self._pause_interval)

                if self._canceled:
                    break
                time.sleep(min(to_go, 0.5))
                to_go = go_at - self._time_elapsed()

        # check canceled again in case it was canceled
        # during the waiting loop
        return self._check_canceled()

    def _finish_run(self, sequence: MDASequence) -> None:
        """To be called at the end of an acquisition.

        Parameters
        ----------
        sequence : MDASequence
            The sequence that was finished.
        """
        #TODO: check if we sould do something here in case we did not record the data in the way we
        #thought initially
        self._running = False
        self._canceled = False

        if hasattr(self._engine, "teardown_sequence"):
            self._engine.teardown_sequence(sequence)  # type: ignore

        logger.info("MDA Finished: {}", sequence)
        self._events.sequenceFinished.emit(sequence)
