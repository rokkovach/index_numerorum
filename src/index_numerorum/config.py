from dataclasses import dataclass


@dataclass(frozen=True)
class ModelInfo:
    id: str
    dim: int
    size_mb: int
    description: str
    shortcut: str


MODEL_REGISTRY: dict[str, ModelInfo] = {
    "mini": ModelInfo(
        id="all-MiniLM-L6-v2",
        dim=384,
        size_mb=80,
        description="Fast, good quality",
        shortcut="mini",
    ),
    "bge-large": ModelInfo(
        id="BAAI/bge-large-en-v1.5",
        dim=1024,
        size_mb=1300,
        description="Top accuracy",
        shortcut="bge-large",
    ),
    "nomic": ModelInfo(
        id="nomic-ai/nomic-embed-text-v1.5",
        dim=768,
        size_mb=550,
        description="Long context",
        shortcut="nomic",
    ),
    "gte": ModelInfo(
        id="Alibaba-NLP/gte-large-en-v1.5",
        dim=1024,
        size_mb=1300,
        description="Cutting-edge",
        shortcut="gte",
    ),
    "e5": ModelInfo(
        id="intfloat/e5-large-v2",
        dim=1024,
        size_mb=1300,
        description="Well-tested",
        shortcut="e5",
    ),
    "address": ModelInfo(
        id="pawan2411/address-emnet",
        dim=768,
        size_mb=420,
        description="Address matching & dedup",
        shortcut="address",
    ),
    "entity": ModelInfo(
        id="themelder/arctic-embed-xs-entity-resolution",
        dim=384,
        size_mb=90,
        description="Company names, entity resolution",
        shortcut="entity",
    ),
}

DEFAULT_DECIMALS: int = 2

COLUMN_MODEL_KEYWORDS: dict[str, list[str]] = {
    "address": [
        "address",
        "addr",
        "street",
        "city",
        "state",
        "zip",
        "postal",
        "location",
        "country",
        "region",
    ],
    "entity": [
        "company",
        "vendor",
        "supplier",
        "customer",
        "client",
        "organization",
        "org",
        "employer",
        "counterparty",
        "partner",
        "institution",
        "firm",
    ],
}


def suggest_model_for_column(column_name: str) -> str:
    lower = column_name.lower()
    for model_shortcut, keywords in COLUMN_MODEL_KEYWORDS.items():
        for kw in keywords:
            if kw in lower:
                return model_shortcut
    return DEFAULT_MODEL


METRICS: dict[str, dict[str, object]] = {
    "cosine": {"sort_ascending": False, "range": "[-1, 1]"},
    "euclidean": {"sort_ascending": True, "range": "[0, inf)"},
    "manhattan": {"sort_ascending": True, "range": "[0, inf)"},
    "dot": {"sort_ascending": False, "range": "(-inf, inf)"},
}

DEFAULT_MODEL: str = "mini"
DEFAULT_METRIC: str = "cosine"
DEFAULT_TOP_K: int = 10
DEFAULT_BATCH_SIZE: int = 64
EMBEDDING_COLUMN_PREFIX: str = "_emb_"
COMPOSITE_KEY_COLUMN: str = "_composite_key"
METADATA_SHEET: str = "_metadata"
STATS_SHEET: str = "_stats"


def resolve_model(shortcut_or_id: str) -> ModelInfo:
    if shortcut_or_id in MODEL_REGISTRY:
        return MODEL_REGISTRY[shortcut_or_id]
    for model in MODEL_REGISTRY.values():
        if model.id == shortcut_or_id:
            return model
    shortcuts = ", ".join(sorted(MODEL_REGISTRY))
    raise ValueError(f"Unknown model '{shortcut_or_id}'. Available shortcuts: {shortcuts}")
