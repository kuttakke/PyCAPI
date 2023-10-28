import json
from pathlib import Path
from typing import Dict, List, Union

import pytest
from pytest_mock import MockerFixture

from src.pyclaapi import PyClaAPI


@pytest.fixture
def pyclaapi():
    return PyClaAPI("http://127.0.0.1:9090", "token")


def make_mock_response(
    mocker: MockerFixture,
    obj: PyClaAPI,
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


def test_get_version(pyclaapi: PyClaAPI, mocker):
    make_mock_response(
        mocker,
        pyclaapi,
        "get",
        json_response={"meta": True, "version": "alpha-g3a9fc39"},
    )

    version = pyclaapi.get_version()
    assert version.meta is True
    assert version.version == "alpha-g3a9fc39"


def test_get_proxies(pyclaapi: PyClaAPI, mocker):
    make_mock_response(
        mocker, pyclaapi, "get", json_response=load_example_data("example_proxies.json")
    )

    proxies = pyclaapi.get_proxies()
    assert proxies


def test_get_providers(pyclaapi: PyClaAPI, mocker):
    make_mock_response(
        mocker,
        pyclaapi,
        "get",
        json_response=[
            load_example_data("example_proxies.json"),
            load_example_data("example_providers.json"),
        ],
    )
    providers = pyclaapi.get_providers()
    assert providers[0]
    assert providers[0].proxies


def test_get_selectors(pyclaapi: PyClaAPI, mocker):
    make_mock_response(
        mocker,
        pyclaapi,
        "get",
        json_response=[
            load_example_data("example_proxies.json"),
            load_example_data("example_providers.json"),
        ],
    )

    selectors = pyclaapi.get_selectors()
    assert not bool(selectors[0].test_url)


def test_select_proxy_for_provider(pyclaapi: PyClaAPI, mocker):
    make_mock_response(
        mocker,
        pyclaapi,
        "put",
    )

    assert pyclaapi.select_proxy_for_provider("test_provider", "test_proxy")

    make_mock_response(mocker, pyclaapi, "put", status_code=400)

    assert not pyclaapi.select_proxy_for_provider("test_provider", "test_proxy")


def test_get_delay(pyclaapi: PyClaAPI, mocker):
    make_mock_response(
        mocker, pyclaapi, "get", status_code=200, json_response={"delay": 120}
    )
    assert pyclaapi.get_delay("test_provider") == 120
    make_mock_response(
        mocker,
        pyclaapi,
        "get",
        status_code=400,
    )
    assert pyclaapi.get_delay("test_provider") == 0


def test_get_connections(pyclaapi: PyClaAPI, mocker):
    make_mock_response(
        mocker,
        pyclaapi,
        "get",
        status_code=200,
        json_response=load_example_data("example_connections.json"),
    )
    connections = pyclaapi.get_connections()
    assert connections
    assert connections.connections


def test_search_connections_by_host(pyclaapi: PyClaAPI, mocker):
    make_mock_response(
        mocker,
        pyclaapi,
        "get",
        status_code=200,
        json_response=load_example_data("example_connections.json"),
    )
    keyword = "qq.com"
    connections = pyclaapi.search_connections_by_host(keyword)
    assert keyword in connections[0].metadata.host


def test_close_connection(pyclaapi: PyClaAPI, mocker):
    make_mock_response(
        mocker,
        pyclaapi,
        "delete",
        status_code=204,
    )
    assert pyclaapi.close_connection("id")


def test_dns_query(pyclaapi: PyClaAPI, mocker):
    make_mock_response(
        mocker,
        pyclaapi,
        "get",
        status_code=200,
        json_response=load_example_data("example_dns_query.json"),
    )
    query = pyclaapi.dns_query("baidu.com")
    assert query.Question
    assert query.Answer[0].data == "39.156.66.10"
    assert query.Answer[0].type == 1
