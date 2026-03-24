ALLOWED_SCHEMA_PATHS = {
    "/api/token/",
    "/api/token/refresh/",
    "/apps/group/attendance/",
    "/apps/group/grades/",
    "/apps/group/group-studnets-attendance/{id}",
    "/apps/group/group-students-attendance/{id}",
    "/apps/group/group-students-grades/{id}",
    "/apps/teachers/my-groups/",
    "/apps/teachers/my-courses/",
    "/apps/teachers/my-courses/{course_id}/groups/",
    "/apps/teachers/me/",
    "/apps/teachers/list/",
    "/apps/teachers/create/",
    "/apps/teachers/detail/{pk}/",
    "/apps/teachers/{pk}/toggle-archive/",
    "/apps/teachers/{pk}/upload-image/",
    "/apps/teachers/delete/{pk}/",
    "/apps/teachers/update/{pk}/",
}


def filter_schema_endpoints(endpoints):
    return [endpoint for endpoint in endpoints if endpoint[0] in ALLOWED_SCHEMA_PATHS]
