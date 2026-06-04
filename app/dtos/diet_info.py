from pydantic import BaseModel


class DietLink(BaseModel):
    source: str
    url: str
    description: str


class DietInfoResponse(BaseModel):
    drug_name: str
    external_links: list[DietLink]
    disclaimer: str
