import httpx

from app.core import config
from app.core.cache.client import TTL_DRUG_SEARCH, cache_get_json, cache_set_json
from app.dtos.drug_info import DrugInfo, DrugSearchResponse


def _drug_cache_key(drug_name: str, num_of_rows: int) -> str:
    return f"cache:drug:search:{drug_name}:{num_of_rows}"


class DrugInfoService:
    """식약처 의약품 정보 조회 (REQ-PILL-003)"""

    def __init__(self):
        self.api_key = config.DRUG_API_KEY
        self.base_url = config.DRUG_API_BASE_URL

    async def search_drug(self, drug_name: str, num_of_rows: int = 5) -> DrugSearchResponse:
        """약품명으로 의약품 정보 검색"""
        key = _drug_cache_key(drug_name, num_of_rows)
        cached = await cache_get_json(key)
        if cached is not None:
            return DrugSearchResponse.model_validate(cached)

        # 공공데이터 API는 serviceKey를 params로 전달하면 이중 인코딩되어 403 발생
        # serviceKey는 URL에 직접 삽입하고, 나머지 파라미터만 httpx params 사용
        from urllib.parse import quote

        url = f"{self.base_url}/getDrbEasyDrugList?serviceKey={self.api_key}&itemName={quote(drug_name)}&type=json&numOfRows={num_of_rows}&pageNo=1"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

        body = data.get("body", {})
        items = body.get("items", [])
        total_count = body.get("totalCount", 0)

        if not isinstance(items, list):
            items = [items] if items else []

        drugs = []
        for item in items:
            drugs.append(
                DrugInfo(
                    item_name=item.get("itemName", ""),
                    entp_name=item.get("entpName"),
                    item_seq=item.get("itemSeq"),
                    efcy_qesitm=item.get("efcyQesitm"),
                    use_method_qesitm=item.get("useMethodQesitm"),
                    atpn_warn_qesitm=item.get("atpnWarnQesitm"),
                    atpn_qesitm=item.get("atpnQesitm"),
                    intrc_qesitm=item.get("intrcQesitm"),
                    se_qesitm=item.get("seQesitm"),
                    deposit_method_qesitm=item.get("depositMethodQesitm"),
                    item_image=item.get("itemImage"),
                )
            )

        result = DrugSearchResponse(query=drug_name, total_count=total_count, drugs=drugs)
        await cache_set_json(key, result.model_dump(), ttl=TTL_DRUG_SEARCH)
        return result
