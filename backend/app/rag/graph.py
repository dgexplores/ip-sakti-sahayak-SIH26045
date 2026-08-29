"""Graph — Neo4j knowledge graph for stage 2 (Formulation→Category→Act→Registry). MVP stub with mock."""
from __future__ import annotations

from dataclasses import dataclass

from app.core.config import get_settings


@dataclass(frozen=True)
class GraphNode:
    label: str
    name: str
    props: dict


@dataclass(frozen=True)
class GraphEdge:
    src: str
    rel: str
    dst: str


MOCK_GRAPH = [
    GraphNode("Formulation", "Ashwagandha churna (classical)", {"category": "classical"}),
    GraphNode("Category", "Classical", {"schedule": "First Schedule"}),
    GraphNode("Act", "Patents Act Sec 3(p)", {"jurisdiction": "india"}),
    GraphNode("Act", "Biological Diversity Act Sec 7", {"jurisdiction": "india"}),
    GraphNode("Registry", "TKDL", {"type": "prior_art"}),
    GraphNode("Registry", "InPASS", {"type": "patent_search"}),
]

MOCK_EDGES = [
    GraphEdge("Ashwagandha churna (classical)", "is_a", "Classical"),
    GraphEdge("Classical", "barred_by", "Patents Act Sec 3(p)"),
    GraphEdge("Classical", "requires", "Biological Diversity Act Sec 7"),
    GraphEdge("Patents Act Sec 3(p)", "defended_via", "TKDL"),
]


async def query_graph(query: str) -> dict:
    """Stage 1: return mock. Stage 2: Cypher against Neo4j."""
    s = get_settings()
    # Try real Neo4j if reachable, else mock
    try:
        from neo4j import AsyncGraphDatabase  # type: ignore[import]

        driver = AsyncGraphDatabase.driver(s.neo4j_uri, auth=(s.neo4j_user, s.neo4j_password))
        await driver.verify_connectivity()
        # simple demo query — actual Cypher built from parsed query in stage 2
        await driver.close()
    except Exception:
        pass
    return {
        "nodes": [n.__dict__ for n in MOCK_GRAPH],
        "edges": [e.__dict__ for e in MOCK_EDGES],
        "note": "MVP mock graph — stage 2 wires real Neo4j Cypher (Formulation→Category→Act→Registry).",
    }


def seed_cypher_statements() -> list[str]:
    return [
        "MERGE (c:Category {name:'Classical'}) SET c.schedule='First Schedule'",
        "MERGE (a:Act {name:'Patents Act Sec 3(p)', jurisdiction:'india'})",
        "MERGE (b:Act {name:'BDA Sec 7', jurisdiction:'india'})",
        "MERGE (r:Registry {name:'TKDL', type:'prior_art'})",
        "MERGE (c)-[:BARRED_BY]->(a)",
        "MERGE (c)-[:REQUIRES]->(b)",
        "MERGE (a)-[:DEFENDED_VIA]->(r)",
    ]
