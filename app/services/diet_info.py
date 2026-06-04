"""REQ-DIET-001 — 약물 관련 공식 외부 링크 진입점 제공.

콘텐츠 생성·수집·요약 없이 검색 URL 자동 생성 후 반환한다.
"""

from urllib.parse import quote

from app.dtos.diet_info import DietInfoResponse, DietLink

_DISCLAIMER = (
    "외부 사이트로 이동합니다. 본 앱은 공식 기관 진입점만 제공하며, 외부 콘텐츠를 수집·요약·재가공하지 않습니다."
)


class DietInfoService:
    """약품명으로 공식 외부 링크 4개를 생성해 반환한다."""

    def get_external_links(self, drug_name: str) -> DietInfoResponse:
        encoded = quote(drug_name)
        links = [
            DietLink(
                source="식약처 의약품안전나라",
                url=f"https://nedrug.mfds.go.kr/searchDrug?searchYn=true&itemName={encoded}",
                description="의약품 허가사항·복약정보",
            ),
            DietLink(
                source="약학정보원",
                url=f"https://www.health.kr/searchDrug/search_total_result.asp?drug_name={encoded}",
                description="일반인 대상 의약품 정보",
            ),
            DietLink(
                source="대한류마티스학회",
                url="https://www.rheum.or.kr/info/edu_data",
                description="자가면역 환자 교육 자료",
            ),
            DietLink(
                source="KDCA 만성질환 정보",
                url="https://www.kdca.go.kr/contents.es?mid=a20308010000",
                description="일반 건강 정보",
            ),
        ]
        return DietInfoResponse(
            drug_name=drug_name,
            external_links=links,
            disclaimer=_DISCLAIMER,
        )
