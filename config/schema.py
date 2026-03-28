ALLOWED_SCHEMA_PATHS = {
    "/api/token",
    "/api/token/refresh",
    "/apps/user/change-password",
    "/apps/teachers/me",
    "/apps/teachers/my-courses/groups",
    "/apps/group/attendance",
    "/apps/group/attendance/update/{id}",
    "/apps/group/group-student/{id}",
    "/apps/group/group-monthly-attendance/{id}",
    "/apps/group/group-scores/create",
    "/apps/group/group-scores/update/{id}",
    "/apps/pupil/me",
    "/apps/pupil/my-groups",
    "/apps/pupil/my-courses",
    "/apps/pupil/my-today-coins",
    "/apps/pupil/my-attendance/{group_id}",
    "/apps/market/products",
    "/apps/market/orders",
    "/apps/market/orders/me",
}


def filter_schema_endpoints(endpoints):
    def normalize(path):
        return path.rstrip("/")

    return [endpoint for endpoint in endpoints if normalize(endpoint[0]) in ALLOWED_SCHEMA_PATHS]
