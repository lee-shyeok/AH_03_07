from pydantic import BaseModel


class DrugInfo(BaseModel):
    item_name: str
    entp_name: str | None = None
    item_seq: str | None = None
    efcy_qesitm: str | None = None
    use_method_qesitm: str | None = None
    atpn_warn_qesitm: str | None = None
    atpn_qesitm: str | None = None
    intrc_qesitm: str | None = None
    se_qesitm: str | None = None
    deposit_method_qesitm: str | None = None
    item_image: str | None = None


class DrugSearchResponse(BaseModel):
    query: str
    total_count: int
    drugs: list[DrugInfo]
