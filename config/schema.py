ALLOWED_SCHEMA_PATHS = {
    "/api/token/",
    "/apps/group/attendance/",
    "/apps/group/group-monthly-attendance/{id}",
    "/apps/group/group-student/{id}",
    "/apps/group/group-scores/create/",
    "/apps/teachers/my-courses/groups/",
}


def filter_schema_endpoints(endpoints):
    return [endpoint for endpoint in endpoints if endpoint[0] in ALLOWED_SCHEMA_PATHS]
