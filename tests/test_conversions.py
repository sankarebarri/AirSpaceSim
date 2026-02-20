from airspacesim.utils.conversions import dms_to_decimal, haversine


def test_dms_to_decimal_north_west():
    assert dms_to_decimal(16, 30, 0, "N") == 16.5
    assert dms_to_decimal(0, 2, 0, "W") == -(2 / 60)


def test_dms_to_decimal_south_east():
    assert dms_to_decimal(10, 0, 0, "S") == -10.0
    assert dms_to_decimal(10, 0, 0, "E") == 10.0


def test_haversine_same_point_zero():
    assert haversine(0, 0, 0, 0) == 0


def test_haversine_known_reasonable_distance_nm():
    # Roughly 1 degree latitude ~= 60 NM.
    distance = haversine(0, 0, 1, 0)
    assert 59.5 <= distance <= 60.5
