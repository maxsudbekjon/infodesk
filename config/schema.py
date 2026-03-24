ALLOWED_SCHEMA_PATHS = {
    "/api/token/",
    "/api/token/refresh/",
    "/apps/group/attendance/",
    "/apps/group/grades/",
    "/apps/group/group-studnets-attendance/{id}",
    "/apps/group/group-students-attendance/{id}",
    "/apps/group/group-students-grades/{id}",
}


def filter_schema_endpoints(endpoints):
    return [endpoint for endpoint in endpoints if endpoint[0] in ALLOWED_SCHEMA_PATHS]
