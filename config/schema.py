ALLOWED_SCHEMA_PATHS = {
    "/api/token",
    "/apps/teachers/my-courses/groups",
    "/apps/group/attendance",
    "/apps/group/group-student/{id}",
    "/apps/group/group-monthly-attendance/{id}",
    "/apps/group/group-scores/create",
    "/apps/pupil/my-courses",
    "/apps/pupil/my-attendance/{group_id}",
    "/apps/market/products",
    "/apps/market/orders",
    "/apps/market/orders/me",
}


def filter_schema_endpoints(endpoints):
    def normalize(path):
        return path.rstrip("/")

    return [endpoint for endpoint in endpoints if normalize(endpoint[0]) in ALLOWED_SCHEMA_PATHS]
