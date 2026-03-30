Excel importerlar ushbu tartibda ishga tushiriladi:

1. `env DEBUG=false .venv/bin/python scripts/excel_import/import_owner.py`
2. `env DEBUG=false .venv/bin/python scripts/excel_import/import_organization.py`
3. `env DEBUG=false .venv/bin/python scripts/excel_import/import_course_template.py`
4. `env DEBUG=false .venv/bin/python scripts/excel_import/import_branch.py`
5. `env DEBUG=false .venv/bin/python scripts/excel_import/import_teacher.py`
6. `env DEBUG=false .venv/bin/python scripts/excel_import/import_group.py`
7. `env DEBUG=false .venv/bin/python scripts/excel_import/import_student.py "/Users/maxsudtoshpulat/Downloads/CRM.xlsx"`

Istasangiz Excel file path ni argument qilib berishingiz mumkin:

`env DEBUG=false .venv/bin/python scripts/excel_import/import_owner.py "/path/to/file.xlsx"`

Eslatma:

- `owner` va `teacher` userlari uchun default password telefon raqami raqamlari ko'rinishida saqlanadi. Masalan `+998901234567` uchun password `998901234567`.
- `student` userlari uchun ham default password telefon raqami raqamlari ko'rinishida yaratiladi.
- `owner.role` ustunidagi `SEO` qiymati `ceo` sifatida import qilinadi.
- `branch.courses` ustuni bitta yoki bir nechta qator raqamini qabul qiladi. Masalan `1`, `1,2,3`.
- `CRM.xlsx` importida `SHARTNOMA` ustuni `Student.contract` boolean maydoniga yoziladi.
- `KELGAN SANA` da oy `01-03` bo'lsa yil majburan `2026`, boshqa oylar `2025` qilinadi.
- `BIRTHDAY` maydoni agar yosh ko'rinishida kelsa, yil `2026 - yosh` formulasi bilan topiladi va sana `01-01` qilinadi.
