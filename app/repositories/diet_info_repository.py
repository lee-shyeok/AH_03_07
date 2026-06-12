from app.models.diet_info import DietInfo
from app.models.user_disease import DiseaseCode


class DietInfoRepository:
    @staticmethod
    async def get_by_disease_code(disease_code: DiseaseCode) -> list[DietInfo]:
        return await DietInfo.filter(disease_code=disease_code).order_by("food_category", "category", "id").all()

    @staticmethod
    async def get_all() -> list[DietInfo]:
        return await DietInfo.all().order_by("disease_code", "food_category", "category", "id")
