from dataclasses import dataclass
from typing import List


@dataclass
class Version:
    meta: bool  # meta core or not
    version: str


@dataclass
class Proxy:
    # id: str
    name: str
    alive: bool
    # 最近一次测速的delay , delay of the latest speed test
    delay: int
    type: str
    udp: bool
    xudp: bool


@dataclass
class Provider:
    name: str
    now: str
    proxies: List[Proxy]
    test_url: str
    type: str
    vehicleType: str


@dataclass
class MetaData:
    network: str
    type: str
    source_ip: str
    destination_ip: str
    source_port: str
    destination_port: str
    inbound_ip: str
    inbound_port: str
    inbound_name: str
    inbound_user: str
    host: str
    dns_mode: str
    uid: int
    process: str
    process_path: str
    special_proxy: str
    special_rules: str
    remote_destination: str
    sniff_host: str


@dataclass
class Connection:
    id: str
    metadata: MetaData
    upload: int
    download: int
    start: str
    chains: List[str]
    rule: str
    rule_payload: str

    def __post_init__(self):
        self.metadata = MetaData(**self.metadata)  # type: ignore


@dataclass
class Connections:
    download_total: int
    upload_total: int
    connections: List[Connection]
    memory: int

    def __post_init__(self):
        self.connections = [Connection(**data) for data in self.connections]  # type: ignore


@dataclass
class AnswerEntry:
    """
    Represents an answer entry in the DNS query result.
    """

    TTL: int  # Time to Live (how long the record can be cached).
    data: str  # The data associated with the answer.
    name: str  # The domain name being queried.
    type: int  # The type of the DNS record.


@dataclass
class QuestionEntry:
    """
    Represents a question entry in the DNS query result.
    """

    Name: str  # The domain name being queried.
    Qtype: int  # The type of the DNS record being queried.
    Qclass: int  # The class of the DNS record being queried.


@dataclass
class DNSQueryResult:
    """
    Represents the result of a DNS query.
    """

    AD: bool  # Whether the response contains an answer that is authoritative data.
    Answer: List[AnswerEntry]  # List of answer entries.
    CD: bool  # Whether the response is signed or not.
    Question: List[QuestionEntry]  # List of question entries.
    RA: bool  # Whether the recursive query was available in the server.
    RD: bool  # Whether the client requested recursive query.
    Status: int  # Status of the DNS query.
    TC: bool  # Whether the message was truncated or not.

    def __post_init__(self):
        self.Answer = [AnswerEntry(**x) for x in self.Answer]  # type: ignore
        self.Question = [QuestionEntry(**x) for x in self.Question]  # type: ignore
