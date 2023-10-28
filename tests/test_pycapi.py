import json
from pathlib import Path
from typing import Dict, List, Union

import pytest
from pytest_mock import MockerFixture

from src.pycapi import PyCAPI


@pytest.fixture
def pycapi():
    return PyCAPI("http://127.0.0.1:9090", "token")


def make_mock_response(
    mocker: MockerFixture,
    obj: PyCAPI,
    method: str,
    status_code: int = 204,
    json_response: Union[Dict, List, None] = None,
):
    mock_response = mocker.Mock()
    if isinstance(json_response, List):
        mock_response.json.side_effect = json_response
    else:
        mock_response.json.return_value = json_response
    mock_response.status_code = status_code
    mocker.patch.object(obj._client, method, return_value=mock_response)


def load_example_data(filename: str) -> Dict:
    """
    Loads example data from the example data directory
    """
    path = Path(__file__).parent / "example_data" / filename
    return json.loads(path.read_text(encoding="utf-8"))


def test_get_version(pycapi: PyCAPI, mocker):
    make_mock_response(
        mocker, pycapi, "get", json_response={"meta": True, "version": "alpha-g3a9fc39"}
    )

    version = pycapi.get_version()
    assert version.meta is True
    assert version.version == "alpha-g3a9fc39"


def test_get_proxies(pycapi: PyCAPI, mocker):
    make_mock_response(
        mocker, pycapi, "get", json_response=load_example_data("example_proxies.json")
    )

    proxies = pycapi.get_proxies()
    assert proxies


def test_get_providers(pycapi: PyCAPI, mocker):
    make_mock_response(
        mocker,
        pycapi,
        "get",
        json_response=[
            load_example_data("example_proxies.json"),
            load_example_data("example_providers.json"),
        ],
    )
    providers = pycapi.get_providers()
    assert providers[0]
    assert providers[0].proxies


def test_get_selectors(pycapi: PyCAPI, mocker):
    make_mock_response(
        mocker,
        pycapi,
        "get",
        json_response=[
            load_example_data("example_proxies.json"),
            load_example_data("example_providers.json"),
        ],
    )

    selectors = pycapi.get_selectors()
    assert not bool(selectors[0].test_url)


def test_select_proxy_for_provider(pycapi: PyCAPI, mocker):
    make_mock_response(
        mocker,
        pycapi,
        "put",
    )

    assert pycapi.select_proxy_for_provider("test_provider", "test_proxy")

    make_mock_response(mocker, pycapi, "put", status_code=400)

    assert not pycapi.select_proxy_for_provider("test_provider", "test_proxy")


def test_get_delay(pycapi: PyCAPI, mocker):
    make_mock_response(
        mocker, pycapi, "get", status_code=200, json_response={"delay": 120}
    )
    assert pycapi.get_delay("test_provider") == 120
    make_mock_response(
        mocker,
        pycapi,
        "get",
        status_code=400,
    )
    assert pycapi.get_delay("test_provider") == 0


def test_get_connections(pycapi: PyCAPI, mocker):
    make_mock_response(
        mocker,
        pycapi,
        "get",
        status_code=200,
        json_response=load_example_data("example_connections.json"),
    )
    connections = pycapi.get_connections()
    assert connections
    assert connections.connections


def test_search_connections_by_host(pycapi: PyCAPI, mocker):
    make_mock_response(
        mocker,
        pycapi,
        "get",
        status_code=200,
        json_response=load_example_data("example_connections.json"),
    )
    keyword = "qq.com"
    connections = pycapi.search_connections_by_host(keyword)
    assert keyword in connections[0].metadata.host


def test_close_connection(pycapi: PyCAPI, mocker):
    make_mock_response(
        mocker,
        pycapi,
        "delete",
        status_code=204,
    )
    assert pycapi.close_connection("id")


def test_dns_query(pycapi: PyCAPI, mocker):
    make_mock_response(
        mocker,
        pycapi,
        "get",
        status_code=200,
        json_response=load_example_data("example_dns_query.json"),
    )
    query = pycapi.dns_query("baidu.com")
    assert query.Question
    assert query.Answer[0].data == "39.156.66.10"
    assert query.Answer[0].type == 1
