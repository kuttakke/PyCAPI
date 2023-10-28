import json
from pathlib import Path
from typing import Dict, List, Union

import pytest
from pytest_mock import MockerFixture

from src.pycapi import PyCAPIAsync


@pytest.fixture
def pycapi():
    return PyCAPIAsync("http://127.0.0.1:9090", "token")


def make_mock_response(
    mocker: MockerFixture,
    obj: PyCAPIAsync,
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


@pytest.mark.asyncio
async def test_get_version(pycapi: PyCAPIAsync, mocker):
    make_mock_response(
        mocker,
        pycapi,
        "get",
        json_response={"meta": True, "version": "alpha-g3a9fc39"},
    )

    version = await pycapi.get_version()
    assert version.meta is True
    assert version.version == "alpha-g3a9fc39"


@pytest.mark.asyncio
async def test_get_proxies(pycapi: PyCAPIAsync, mocker):
    make_mock_response(
        mocker,
        pycapi,
        "get",
        json_response=load_example_data("example_proxies.json"),
    )

    proxies = await pycapi.get_proxies()
    assert proxies


@pytest.mark.asyncio
async def test_get_providers(pycapi: PyCAPIAsync, mocker):
    make_mock_response(
        mocker,
        pycapi,
        "get",
        json_response=[
            load_example_data("example_proxies.json"),
            load_example_data("example_providers.json"),
        ],
    )
    providers = await pycapi.get_providers()
    assert providers[0]
    assert providers[0].proxies


@pytest.mark.asyncio
async def test_get_selectors(pycapi: PyCAPIAsync, mocker):
    make_mock_response(
        mocker,
        pycapi,
        "get",
        json_response=[
            load_example_data("example_proxies.json"),
            load_example_data("example_providers.json"),
        ],
    )

    selectors = await pycapi.get_selectors()
    assert not bool(selectors[0].test_url)


@pytest.mark.asyncio
async def test_select_proxy_for_provider(pycapi: PyCAPIAsync, mocker):
    make_mock_response(
        mocker,
        pycapi,
        "put",
    )

    assert await pycapi.select_proxy_for_provider("test_provider", "test_proxy")

    make_mock_response(mocker, pycapi, "put", status_code=400)

    assert not await pycapi.select_proxy_for_provider("test_provider", "test_proxy")


@pytest.mark.asyncio
async def test_get_delay(pycapi: PyCAPIAsync, mocker):
    make_mock_response(
        mocker, pycapi, "get", status_code=200, json_response={"delay": 120}
    )
    assert await pycapi.get_delay("test_provider") == 120
    make_mock_response(
        mocker,
        pycapi,
        "get",
        status_code=400,
    )
    assert await pycapi.get_delay("test_provider") == 0


@pytest.mark.asyncio
async def test_get_connections(pycapi: PyCAPIAsync, mocker):
    make_mock_response(
        mocker,
        pycapi,
        "get",
        status_code=200,
        json_response=load_example_data("example_connections.json"),
    )
    connections = await pycapi.get_connections()
    assert connections
    assert connections.connections


@pytest.mark.asyncio
async def test_search_connections_by_host(pycapi: PyCAPIAsync, mocker):
    make_mock_response(
        mocker,
        pycapi,
        "get",
        status_code=200,
        json_response=load_example_data("example_connections.json"),
    )
    keyword = "qq.com"
    connections = await pycapi.search_connections_by_host(keyword)
    assert keyword in connections[0].metadata.host


@pytest.mark.asyncio
async def test_close_connection(pycapi: PyCAPIAsync, mocker):
    make_mock_response(
        mocker,
        pycapi,
        "delete",
        status_code=204,
    )
    assert await pycapi.close_connection("id")


@pytest.mark.asyncio
async def test_dns_query(pycapi: PyCAPIAsync, mocker):
    make_mock_response(
        mocker,
        pycapi,
        "get",
        status_code=200,
        json_response=load_example_data("example_dns_query.json"),
    )
    query = await pycapi.dns_query("baidu.com")
    assert query.Question
    assert query.Answer[0].data == "39.156.66.10"
    assert query.Answer[0].type == 1
