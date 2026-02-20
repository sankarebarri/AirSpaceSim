import threading
import time
from types import SimpleNamespace

from airspacesim.simulation.aircraft_manager import AircraftManager


def test_request_shutdown_sets_stop_event():
    manager = AircraftManager({})
    assert manager.stop_event.is_set() is False
    manager.request_shutdown()
    assert manager.stop_event.is_set() is True


def test_terminate_simulations_with_timeout_does_not_hang():
    manager = AircraftManager({})

    def worker():
        time.sleep(0.2)

    thread = threading.Thread(target=worker)
    thread.start()
    manager.threads.append(thread)

    manager.terminate_simulations(timeout_seconds=0.05)

    assert manager.stop_event.is_set() is True


def test_batched_mode_steps_without_spawning_threads():
    routes = {
        "R1": [
            {"dec_coords": [16.25, -0.03]},
            {"dec_coords": [16.35, 0.02]},
        ]
    }
    manager = AircraftManager(routes, execution_mode="batched")
    manager.add_aircraft("AC_BATCH_01", "R1", speed=600, altitude_ft=10000, vertical_rate_fpm=600)
    assert len(manager.threads) == 0

    manager.run_batched_for(duration_seconds=0.2, update_interval=0.05)
    assert manager.aircraft_list[0].position != [16.25, -0.03]
    assert manager.aircraft_list[0].altitude_ft > 10000


def test_cleanup_finished_aircraft_releases_lock_before_save(monkeypatch):
    manager = AircraftManager({})
    stop_flag = threading.Event()
    manager.aircraft_list = [
        SimpleNamespace(id="AC_OLD", finished_time=time.time() - 180),
    ]

    # Avoid waiting 10 seconds in cleanup loop.
    monkeypatch.setattr("airspacesim.simulation.aircraft_manager.time.sleep", lambda _: None)

    lock_acquired_inside_save = {"value": False}

    def fake_save_aircraft_data():
        # If cleanup still holds manager.lock, this acquire would fail and signal a regression.
        acquired = manager.lock.acquire(timeout=0.05)
        lock_acquired_inside_save["value"] = acquired
        if acquired:
            manager.lock.release()
        stop_flag.set()

    monkeypatch.setattr(manager, "save_aircraft_data", fake_save_aircraft_data)

    worker = threading.Thread(target=manager.cleanup_finished_aircraft, args=(stop_flag,))
    worker.start()
    worker.join(timeout=1.0)

    assert worker.is_alive() is False
    assert lock_acquired_inside_save["value"] is True
    assert manager.aircraft_list == []
