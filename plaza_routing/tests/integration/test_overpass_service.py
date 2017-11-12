import pytest

from plaza_routing.integration import overpass_service


def test_get_public_transport_stops():
    expected_response = {'Zürich, Kreuzstrasse', 'Zürich, Opernhaus', 'Zürich, Bürkliplatz',
                         'Zürich, Kunsthaus', 'Zürich Stadelhofen FB', 'Zürich, Bellevue',
                         'Zürich Stadelhofen', 'Zürich, Helmhaus'}
    sechselaeutenplatz = (47.3661, 8.5458)
    stops = overpass_service.get_public_transport_stops(sechselaeutenplatz)
    assert expected_response == stops


def test_get_public_transport_stops_empty_result():
    obersee = (47.2100, 8.8249)
    with pytest.raises(ValueError):
        overpass_service.get_public_transport_stops(obersee)


def test_get_initial_public_transport_stop_position():
    """
    To get from Zürich, Messe/Hallenstadion to Zürich, Sternen Oerlikon you have to take
    the bus with the number 94 that travels from Zentrum Glatt to Zürich, Bahnhof Oerlikon
    at a specific public transport stop (node with id 701735028 and (47,4106724, 8,5520512)).

    Public transport stops at Zürich, Messe/Hallenstadion have the uic_ref 8591273.
    Public transport stops at Zürich, Sternen Oerlikon have the uic_ref 8591382.
    """
    current_location = (47.41077, 8.55240)
    bus_number = '94'
    start_stop_uicref = '8591273'
    exit_stop_uicref = '8591382'
    stop_position = overpass_service.get_initial_public_transport_stop_position(current_location,
                                                                                bus_number,
                                                                                start_stop_uicref,
                                                                                exit_stop_uicref)
    assert (47.4106724, 8.5520512) == stop_position


def test_get_initial_public_transport_stop_position_other_direction():
    """
    Same as test_get_initial_public_transport_stop_position() but in the other
    direction of travel (from Zürich, Messe/Hallenstadion to Zürich, Hallenbad Oerlikon).
    Should return the public transport stop on the other side of the street
    as in test_get_initial_public_transport_stop_position().

    Public transport stops at Zürich, Messe/Hallenstadion have the uic_ref 8591273.
    Public transport stops at Zürich, Hallenbad Oerlikon have the uic_ref 8591175.
    """
    current_location = (47.41077, 8.55240)
    bus_number = '94'
    start_stop_uicref = '8591273'
    exit_stop_uicref = '8591175'
    stop_position = overpass_service.get_initial_public_transport_stop_position(current_location,
                                                                                bus_number,
                                                                                start_stop_uicref,
                                                                                exit_stop_uicref)
    assert (47.4107102, 8.5528703) == stop_position


def test_get_initial_public_transport_stop_position_end_terminal():
    """
    Terminals have usually the nature that both direction of travel
    are served from the same stop.

    Public transport stops at Zürich, Sternen Oerlikon have the uic_ref 8591382.
    Public transport stops at Zürich, Bahnhof Oerlikon have the uic_ref 8580449.
    """
    current_location = (47.41025, 8.54679)
    bus_number = '94'
    start_stop_uicref = '8591382'
    exit_stop_uicref = '8580449'
    stop_position = overpass_service.get_initial_public_transport_stop_position(current_location,
                                                                                bus_number,
                                                                                start_stop_uicref,
                                                                                exit_stop_uicref)
    assert (47.4102250, 8.5467743) == stop_position


def test_get_initial_public_transport_stop_position_start_terminal():
    """
    Same as test_get_initial_public_transport_stop_position_end_terminal
    but with a terminal (Zürich, Bahnhof Oerlikon) as an initial stop position.

    Public transport stops at Zürich, Bahnhof Oerlikon have the uic_ref 8580449.
    Public transport stops at Zürich, Sternen Oerlikon have the uic_ref 8591382.
    """
    current_location = (47.41142, 8.54466)
    bus_number = '94'
    start_stop_uicref = '8580449'
    exit_stop_uicref = '8591382'
    stop_position = overpass_service.get_initial_public_transport_stop_position(current_location,
                                                                                bus_number,
                                                                                start_stop_uicref,
                                                                                exit_stop_uicref)
    assert (47.4114541, 8.5447442) == stop_position


def test_get_initial_public_transport_stop_position_fallback():
    """
    Initial stop position for the line 161 to get from Zürich, Rote Fabrik to Zürich, Stadtgrenze.

    Both stops do not provide an uic_ref so the fallback method will be used
    to determine the initial public transport stop position.
    """
    current_location = (47.34252, 8.53608)
    bus_number = '161'
    start_stop_uicref = '8587347'  # TODO how does search.ch get these uic_refs?
    exit_stop_uicref = '8591357'
    stop_position = overpass_service.get_initial_public_transport_stop_position(current_location,
                                                                                bus_number,
                                                                                start_stop_uicref,
                                                                                exit_stop_uicref)
    assert (47.3424624, 8.5362646) == stop_position


def test_get_initial_public_transport_stop_position_corrupt_relation():
    """
    Initial stop position for the line S6 to get from Zürich, Bahnhof Oerlikon to Zürich, Hardbrücke.
    The stop in Zürich, Bahnhof Oerlikon does not provide an uic_ref for the line S6.
    The fallback method will be used in this case.

    The relation for the S6 is wrongly (order of nodes is not correct) mapped and the fallback method will fail too.

    Public transport stops at Zürich, Bahnhof Oerlikon have the uic_ref 8503006.
    Public transport stops at Zürich, Hardbrücke have the uic_ref 8503020.
    """
    current_location = (47.41012, 8.54644)
    train_number = 'S6'
    start_stop_uicref = '8503006'
    exit_stop_uicref = '8503020'
    with pytest.raises(ValueError):
        overpass_service.get_initial_public_transport_stop_position(current_location,
                                                                    train_number,
                                                                    start_stop_uicref,
                                                                    exit_stop_uicref)


def test_get_initial_public_transport_stop_position_relation_without_uic_ref():
    """
    Start node does not have an uic_ref, the exit node however holds an uic_ref.
    For the exit node it is not possible to retrieve relations based on the exit_uic_ref because there does not
    exist one with it. This is the reasons why all reachable public stop nodes have to be returned
    in _get_destination_stops() and not just the nodes at the destination.
    """
    current_location = (47.33937, 8.53810)
    bus_number = '161'
    start_stop_uicref = '8591357'
    exit_stop_uicref = '8591317'
    stop_position = overpass_service.get_initial_public_transport_stop_position(current_location,
                                                                                bus_number,
                                                                                start_stop_uicref,
                                                                                exit_stop_uicref)
    assert (47.3385962, 8.5383397) == stop_position