import httpx

from app.core import config
from app.dtos.drug_info import DrugInfo, DrugSearchResponse


class DrugInfoService:
    """식약처 의약품 정보 조회 (REQ-PILL-003)"""

    def __init__(self):
        self.api_key = config.DRUG_API_KEY
        self.base_url = config.DRUG_API_BASE_URL

    async def search_drug(self, drug_name: str, num_of_rows: int = 5) -> DrugSearchResponse:
        """약품명으로 의약품 정보 검색"""
        url = f"{self.base_url}/getDrbEasyDrugList"

        params = {
            "serviceKey": self.api_key,
            "itemName": drug_name,
            "type": "json",
            "numOfRows": num_of_rows,
            "pageNo": 1,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

        # 응답 파싱
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

        return DrugSearchResponse(
            query=drug_name,
            total_count=total_count,
            drugs=drugs,
        )
