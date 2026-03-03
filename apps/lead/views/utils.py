from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination


def parse_bool(value: str) -> bool:
    value = value.lower()
    if value in ["true", "1", "yes"]:
        return True
    if value in ["false", "0", "no"]:
        return False
    raise ValidationError("Boolean qiymat noto‘g‘ri.")


class LeadPagination(PageNumberPagination):
    page_size = 10
