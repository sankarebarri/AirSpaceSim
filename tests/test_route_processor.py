from airspacesim.routes.processor import process_waypoints


def test_process_waypoints_handles_mixed_coords_and_distances():
    waypoints = [
        {"coords": {"lat": [16, 10, 0, "N"], "lon": [0, 3, 0, "W"]}},
        {"dec_coords": [16.45, 0.08]},
        {"coords": {"lat": [16, 30, 0, "N"], "lon": [0, 5, 0, "E"]}, "distance": 42},
    ]

    processed = process_waypoints(waypoints)

    assert "dec_coords" in processed[0]
    assert processed[0]["distance"] is not None
    assert processed[2]["distance"] == 42


def test_process_waypoints_does_not_compute_last_distance():
    waypoints = [
        {"dec_coords": [10.0, 10.0]},
        {"dec_coords": [10.1, 10.1]},
    ]

    processed = process_waypoints(waypoints)

    assert "distance" in processed[0]
    assert "distance" not in processed[1]
