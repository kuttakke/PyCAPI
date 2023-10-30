from typing import Dict, List, Union
from urllib.parse import quote

from httpx import AsyncClient, Client

from .api import Api
from .model import Connection, Connections, DNSQueryResult, Provider, Proxy, Version


class Base:
    def __init__(self, host: str, token: str) -> None:
        self._host = host
        self._token = token

    def _make_proxy(self, proxy: Dict) -> Proxy:
        """
        Creates a Proxy instance from a dictionary.

        Args:
            proxy: The dictionary containing proxy information.

        Returns:
            A Proxy instance.
        """
        delay = 0
        if proxy["history"]:
            delay = proxy["history"][-1]["delay"]
        elif proxy["extra"]:
            delay = proxy["extra"].popitem()[1][-1]["delay"]
        return Proxy(
            name=proxy["name"],
            alive=proxy["alive"],
            delay=delay,
            type=proxy["type"],
            udp=proxy["udp"],
            xudp=proxy["xudp"],
        )

    def _make_provider(self, provider: Dict, proxies: Dict) -> Provider:
        """
        Creates a Provider instance from a dictionary.

        Args:
            provider: The dictionary containing provider information.

        Returns:
            A Provider instance.
        """
        return Provider(
            name=provider["name"],
            now=proxies[provider["name"]].get("now", None),
            proxies=list(map(lambda x: self._make_proxy(x), provider["proxies"])),
            test_url=provider["testUrl"],
            type=provider["type"],
            vehicleType=provider["vehicleType"],
        )

    def _convert_keys_to_snake_case(self, data: Union[Dict, List]) -> Union[Dict, List]:
        if isinstance(data, dict):
            new_data = {}
            for key, value in data.items():
                new_key = (
                    "".join([f"_{c.lower()}" if c.isupper() else c for c in key])
                    .lstrip("_")
                    .replace("_i_p", "_ip")
                )
                new_data[new_key] = self._convert_keys_to_snake_case(value)
            return new_data
        elif isinstance(data, list):
            return [self._convert_keys_to_snake_case(item) for item in data]
        else:
            return data


class PyClaAPI(Base):
    def __init__(self, host: str, token: str) -> None:
        """
        Initializes a PyClaAPI instance.

        Args:
            host: The host URL of the Clash API. Like http://127.0.0.1:9090
            token: The authentication token for accessing the Clash API.
        """
        super().__init__(host, token)
        # self._host = host
        # self._token = token
        self._client = Client(
            base_url=self._host, headers={"Authorization": f"Bearer {self._token}"}
        )

    def get_version(self) -> Version:
        """
        Retrieves the version information from the Clash API.

        Returns:
            A Version instance containing the version information.
        """
        return Version(**self._client.get(Api.VERSION).json())

    def get_proxies(self) -> List[Proxy]:
        """
        Retrieves a list of proxies from the Clash API.

        Returns:
            A list of Proxy instances.
        """
        all_info: dict = self._client.get(Api.PROXIES).json()["proxies"]
        return list(
            map(
                lambda f: self._make_proxy(f),
                filter(
                    lambda x: x["type"]
                    not in [
                        "Compatible",
                        "Selector",
                        "Direct",
                        "Pass",
                        "Reject",
                        "URLTest",
                        "LoadBalance",
                        "Fallback",
                    ],
                    all_info.values(),
                ),
            )
        )

    def get_providers(self, selectable_only: bool = False) -> List[Provider]:
        """
        Retrieves a list of providers from the Clash API.

        Args:
            selectable_only: If True, only returns selectable providers.

        Returns:
            A list of Provider instances.
        """
        proxies_info: dict = self._client.get(Api.PROXIES).json()["proxies"]
        all_info: dict = self._client.get(Api.PROVIDERS).json()["providers"]
        all_info.pop("default")  # ANCHOR - why default exists
        return list(
            map(
                lambda f: self._make_provider(f, proxies_info),
                filter(lambda x: not bool(x["testUrl"]), all_info.values())
                if selectable_only
                else all_info.values(),
            )
        )

    def get_selectors(self) -> List[Provider]:
        """
        Retrieves a list of selectable providers from the Clash API.

        Returns:
            A list of Provider instances.
        """
        return self.get_providers(selectable_only=True)

    def select_proxy_for_provider(
        self, provider: Union[str, Provider], proxy: Union[str, Proxy]
    ) -> bool:
        """
        Selects a proxy for a provider in the Clash API.

        Args:
            provider: The name of the provider or a Provider instance.
            proxy: The name of the proxy or a Proxy instance.

        Returns:
            True if the proxy selection was successful, False otherwise.
        """
        req = self._client.put(
            f"{Api.PROXIES}/{quote(provider.name if isinstance(provider, Provider) else provider)}",
            json={"name": proxy.name if isinstance(proxy, Proxy) else proxy},
        )
        return req.status_code == 204

    def get_delay(self, proxy: Union[str, Proxy]) -> int:
        """
        Test and return the delay for a proxy in the Clash API.

        Args:
            proxy: The name of the proxy or a Proxy instance.

        Returns:
            The delay for the proxy. 0 for error.
        """
        req = self._client.get(
            f"{Api.PROXIES}/{quote(proxy.name if isinstance(proxy, Proxy) else proxy)}"
            "/delay?timeout=5000&url=http:%2F%2Fwww.gstatic.com%2Fgenerate_204"
        )
        return 0 if req.status_code != 200 else req.json()["delay"]

    def get_connections(self) -> Connections:
        """
        Retrieves the connections from the Clash API.

        Returns:
            Connections: An object representing the connections retrieved from the API.
        """
        all_info = self._convert_keys_to_snake_case(
            self._client.get(Api.CONNECTIONS).json()
        )
        return Connections(**all_info)  # type: ignore

    def search_connections_by_host(self, host: str) -> List[Connection]:
        """
        Search for connections by host.

        Args:
            host: The host to search for.

        Returns:
            A list of connections that match the host.
        """
        return list(
            filter(
                lambda x: host.lower() in x.metadata.host,
                self.get_connections().connections,
            )
        )

    def close_connection(self, connection: Union[Connection, str]) -> bool:
        """
        Close a connection in the Clash API.

        Args:
            connection: The ID of the connection or a Connection instance.

        Returns:
            True if the connection was closed successfully.
        """
        req = self._client.delete(
            f"{Api.CONNECTIONS}/{connection.id if isinstance(connection, Connection) else connection}"
        )
        return req.status_code == 204

    def dns_query(self, name: str, type: str = "A") -> DNSQueryResult:
        info = self._client.get(f"{Api.DNS_QUERY}?name={name}&type={type}").json()
        return DNSQueryResult(**info)


class PyClaAPIAsync(Base):
    def __init__(self, host: str, token: str) -> None:
        """
        Initializes a PyClaAPIAsync instance.

        Args:
            host: The host URL of the Clash API. Like http://127.0.0.1:9090
            token: The authentication token for accessing the Clash API.
        """
        super().__init__(host, token)
        self._client = AsyncClient(
            base_url=self._host, headers={"Authorization": f"Bearer {self._token}"}
        )

    async def get_version(self) -> Version:
        """
        Retrieves the version information from the Clash API.

        Returns:
            A Version instance containing the version information.
        """
        return Version(**(await self._client.get(Api.VERSION)).json())

    async def get_proxies(self) -> List[Proxy]:
        """
        Retrieves a list of proxies from the Clash API.

        Returns:
            A list of Proxy instances.
        """
        all_info: dict = (await self._client.get(Api.PROXIES)).json()["proxies"]
        return list(
            map(
                lambda f: self._make_proxy(f),
                filter(
                    lambda x: x["type"]
                    not in [
                        "Compatible",
                        "Selector",
                        "Direct",
                        "Pass",
                        "Reject",
                        "URLTest",
                        "LoadBalance",
                        "Fallback",
                    ],
                    all_info.values(),
                ),
            )
        )

    async def get_providers(self, selectable_only: bool = False) -> List[Provider]:
        """
        Retrieves a list of providers from the Clash API.

        Args:
            selectable_only: If True, only returns selectable providers.

        Returns:
            A list of Provider instances.
        """
        proxies_info: dict = (await self._client.get(Api.PROXIES)).json()["proxies"]
        all_info: dict = (await self._client.get(Api.PROVIDERS)).json()["providers"]
        all_info.pop("default")
        return list(
            map(
                lambda f: self._make_provider(f, proxies_info),
                filter(lambda x: not bool(x["testUrl"]), all_info.values())
                if selectable_only
                else all_info.values(),
            )
        )

    async def get_selectors(self) -> List[Provider]:
        """
        Retrieves a list of selectable providers from the Clash API.

        Returns:
            A list of Provider instances.
        """
        return await self.get_providers(selectable_only=True)

    async def select_proxy_for_provider(
        self, provider: Union[str, Provider], proxy: Union[str, Proxy]
    ) -> bool:
        """
        Selects a proxy for a provider in the Clash API.

        Args:
            provider: The name of the provider or a Provider instance.
            proxy: The name of the proxy or a Proxy instance.

        Returns:
            True if the proxy selection was successful, False otherwise.
        """
        req = await self._client.put(
            f"{Api.PROXIES}/{quote(provider.name if isinstance(provider, Provider) else provider)}",
            json={"name": proxy.name if isinstance(proxy, Proxy) else proxy},
        )
        return req.status_code == 204

    async def get_delay(self, proxy: Union[str, Proxy]) -> int:
        """
        Test and return the delay for a proxy in the Clash API.

        Args:
            proxy: The name of the proxy or a Proxy instance.

        Returns:
            The delay for the proxy. 0 for error.
        """
        req = await self._client.get(
            f"{Api.PROXIES}/{quote(proxy.name if isinstance(proxy, Proxy) else proxy)}"
            "/delay?timeout=5000&url=http:%2F%2Fwww.gstatic.com%2Fgenerate_204"
        )
        return 0 if req.status_code != 200 else req.json()["delay"]

    async def get_connections(self) -> Connections:
        """
        Retrieves the connections from the Clash API.

        Returns:
            Connections: An object representing the connections retrieved from the API.
        """
        all_info = self._convert_keys_to_snake_case(
            (await self._client.get(Api.CONNECTIONS)).json()
        )
        return Connections(**all_info)  # type: ignore

    async def search_connections_by_host(self, host: str) -> List[Connection]:
        """
        Search for connections by host.

        Args:
            host: The host to search for.

        Returns:
            A list of connections that match the host.
        """
        return list(
            filter(
                lambda x: host.lower() in x.metadata.host,
                (await self.get_connections()).connections,
            )
        )

    async def close_connection(self, connection: Union[Connection, str]) -> bool:
        """
        Close a connection in the Clash API.

        Args:
            connection: The ID of the connection or a Connection instance.

        Returns:
            True if the connection was closed successfully.
        """
        req = await self._client.delete(
            f"{Api.CONNECTIONS}/{connection.id if isinstance(connection, Connection) else connection}"
        )
        return req.status_code == 204

    async def dns_query(self, name: str, type: str = "A") -> DNSQueryResult:
        info = (
            await self._client.get(f"{Api.DNS_QUERY}?name={name}&type={type}")
        ).json()
        return DNSQueryResult(**info)
