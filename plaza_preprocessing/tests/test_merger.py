import os.path
import pytest
from shapely.geometry import LineString, Point
import testfilemanager
import utils
from plaza_preprocessing.optimizer import shortest_paths
from plaza_preprocessing import configuration
import plaza_preprocessing.merger.merger as merger
import plaza_preprocessing.merger.plazatransformer as plazatransformer
from plaza_preprocessing.optimizer.graphprocessor.spiderwebgraph import SpiderWebGraphProcessor
from plaza_preprocessing.optimizer.graphprocessor.visibilitygraph import VisibilityGraphProcessor


@pytest.fixture(params=['visibility', 'spiderweb'])
def process_strategy(request):
    if request.param == 'visibility':
        return VisibilityGraphProcessor(visibility_delta_m=0.1)
    elif request.param == 'spiderweb':
        return SpiderWebGraphProcessor(spacing_m=5, visibility_delta_m=0.1)


@pytest.fixture(params=['astar', 'dijkstra'])
def shortest_path_strategy(request):
    if request.param == 'astar':
        return shortest_paths.compute_dijkstra_shortest_paths
    elif request.param == 'dijkstra':
        return shortest_paths.compute_astar_shortest_paths


@pytest.fixture
def config():
    config_path = 'testconfig.yml'
    yield configuration.load_config(config_path)
    os.remove(config_path)


def test_transform_plaza():
    plaza_transformer = plazatransformer.PlazaTransformer(0, 0, {})
    plaza = create_test_plaza()
    plaza_transformer.transform_plaza(plaza)
    assert len(plaza_transformer.nodes) == 4
    assert len(plaza_transformer.ways) == 2
    assert plaza_transformer.ways[1].nodes[2] == plaza_transformer.ways[0].nodes[1]
    assert len(plaza_transformer.entry_node_mappings[99]) == 1


def test_transform_real_plaza(process_strategy, shortest_path_strategy, config):
    plaza = utils.process_plaza('helvetiaplatz', 4533221, process_strategy, shortest_path_strategy, config)
    assert plaza

    plaza_transformer = plazatransformer.PlazaTransformer(0, 0, config['footway-tags'])
    plaza_transformer.transform_plaza(plaza)
    assert len(plaza_transformer.ways) == len(plaza['graph_edges'])
    way_id = 259200019  # footway with 2 entry points
    assert way_id in plaza_transformer.entry_node_mappings
    assert len(plaza_transformer.entry_node_mappings[way_id]) == 2


def test_write_to_file(config):
    plaza = create_test_plaza()
    node_file = 'test_nodes.osm'
    way_file = 'test_ways.osm'
    try:
        plazatransformer.transform_plazas([plaza], node_file, way_file, config['footway-tags'])
        assert os.path.exists(node_file)
        assert os.path.exists(way_file)
    finally:
        os.remove(node_file)
        os.remove(way_file)


def test_write_to_file_real_plaza(process_strategy, shortest_path_strategy, config):
    plaza = utils.process_plaza(
        'helvetiaplatz', 4533221, process_strategy, shortest_path_strategy, config)
    assert plaza

    node_file = 'test_nodes.osm'
    way_file = 'test_ways.osm'
    try:
        plazatransformer.transform_plazas([plaza], node_file, way_file, config['footway-tags'])
        assert os.path.exists(node_file)
        assert os.path.exists(way_file)
    finally:
        os.remove(node_file)
        os.remove(way_file)


def test_merge_plaza_graphs(process_strategy, shortest_path_strategy, config):
    plaza = utils.process_plaza(
        'helvetiaplatz', 4533221, process_strategy, shortest_path_strategy, config)
    assert plaza

    merged_filename = 'testfile-merged.osm'
    try:
        merger.merge_plaza_graphs(
            [plaza], testfilemanager.get_testfile_name('helvetiaplatz'),
            merged_filename, config['footway-tags'])
        assert os.path.exists(merged_filename)

    finally:
        os.remove(merged_filename)


def test_merge_simple_plaza(process_strategy, shortest_path_strategy, config):
    plaza = utils.process_plaza(
        'helvetiaplatz', 39429064, process_strategy, shortest_path_strategy, config)
    assert plaza

    merged_filename = 'testfile-merged.osm'
    try:
        merger.merge_plaza_graphs(
            [plaza], testfilemanager.get_testfile_name('helvetiaplatz'),
            merged_filename, config['footway-tags'])
        assert os.path.exists(merged_filename)
    finally:
        os.remove(merged_filename)


def test_find_exact_insert_position():
    entry_point = Point(2, 2)
    way_nodes = [
        {'id': 1, 'coords': (0, 0)},
        {'id': 2, 'coords': (2, 0)},
        {'id': 3, 'coords': (2, 2)},
        {'id': 4, 'coords': (0, 2)},
    ]
    pos = merger._find_exact_insert_position(entry_point, way_nodes)
    assert pos == 2


def test_find_interpolated_insert_position():
    entry_point = Point(2.5, 1)
    way_nodes = [
        {'id': 1, 'coords': (0, 0)},
        {'id': 2, 'coords': (2, 0)},
        {'id': 3, 'coords': (3, 2)},
        {'id': 4, 'coords': (1, 2)},
    ]
    pos = merger._find_interpolated_insert_position(
        entry_point, way_nodes)
    assert pos == 2


def test_insert_entry_nodes():
    entry_ways = {
        '42': {
            'version': 1,
            'nodes': [
                {'id': 1, 'coords': (0, 0)},
                {'id': 2, 'coords': (2, 0)},
                {'id': 3, 'coords': (3, 2)},
                {'id': 4, 'coords': (1, 2)},
            ]
        }
    }
    entry_node_mappings = {
        '42': [
            {'id': -99, 'coords': (0, 0)},
            {'id': -98, 'coords': (1, 0)},
            {'id': -97, 'coords': (1.5, 2)},
            {'id': -96, 'coords': (1, 2)},
        ]
    }
    entry_ways_expected = {
        '42': {
            'version': 1,
            'nodes': [
                {'id': -99, 'coords': (0, 0)},
                {'id': 1, 'coords': (0, 0)},
                {'id': -98, 'coords': (1, 0)},
                {'id': 2, 'coords': (2, 0)},
                {'id': 3, 'coords': (3, 2)},
                {'id': -97, 'coords': (1.5, 2)},
                {'id': -96, 'coords': (1, 2)},
                {'id': 4, 'coords': (1, 2)}
            ]
        }
    }
    merger._insert_entry_nodes(entry_ways, entry_node_mappings)
    assert entry_ways == entry_ways_expected


def create_test_plaza():
    edges = [
        LineString([(0, 0), (1, 1)]),
        LineString([(0, 1), (3, 4), (1, 1)])
    ]
    entry_points = [Point(0, 0), Point(3, 4)]
    plaza = {
        'graph_edges': edges,
        'entry_points': entry_points,
        'entry_lines': [
            {
                'way_id': 99,
                'entry_points': [Point(0, 0)]
            },
            {
                'way_id': 98,
                'entry_points': [Point(3, 4)]
            }
        ]
    }
    return plaza
