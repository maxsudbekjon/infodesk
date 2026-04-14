import calendar
import random
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.group.choices import GROUP_DAYS_CHOICES, GROUP_STATUS
from apps.group.models import Attendance, CourseTemplate, Day, Group, GroupScore, Room
from apps.lead.choices import LEAD_STATUS, LEAD_TEMPERATURE
from apps.lead.models import Lead, Situation, Source
from apps.market.models import MARKET_ORDER_STATUS, MarketOrder, Product
from apps.pupil.choices import STUDENT_PAYMENT, STUDENT_STATUS
from apps.pupil.models import Student, StudentNote
from apps.settings.models import Branch, Organization
from apps.teacher.models import Specialty, Teacher
from apps.user.choices import ROLE
from apps.user.models import Operator, User


DEMO_PHONE_PREFIX = "+998799"
DEMO_CENTER_NAME = "Infodesk Demo Center"
DEMO_BRANCH_NAME = "Demo Chilonzor Filial"
ONE_PIXEL_GIF = (
    b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!"
    b"\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00"
    b"\x00\x02\x02D\x01\x00;"
)


def demo_image(name: str) -> SimpleUploadedFile:
    return SimpleUploadedFile(name, ONE_PIXEL_GIF, content_type="image/gif")


def month_dates_for_weekdays(year: int, month: int, weekdays: set[int]) -> list[date]:
    last_day = calendar.monthrange(year, month)[1]
    dates = []
    for day in range(1, last_day + 1):
        current = date(year, month, day)
        if current.weekday() in weekdays:
            dates.append(current)
    return dates


class Command(BaseCommand):
    help = "Populate the database with realistic demo data for the customized admin."

    def add_arguments(self, parser):
        parser.add_argument("--students", type=int, default=20, help="How many demo students to create.")

    @transaction.atomic
    def handle(self, *args, **options):
        student_count = max(options["students"], 20)
        rng = random.Random(20260407)

        self.stdout.write("Old demo data tozalanmoqda...")
        self._reset_demo_data()

        owner = User.objects.create_user(
            phone_number=f"{DEMO_PHONE_PREFIX}90000",
            password="demo12345",
            full_name="Demo Admin",
            role=ROLE.ADMIN,
            is_staff=True,
            is_superuser=False,
        )
        organization = Organization.objects.create(
            owner=owner,
            name=DEMO_CENTER_NAME,
            organization_phone=f"{DEMO_PHONE_PREFIX}91000",
            description="Admin panelni ko'rsatish uchun demo ma'lumotlar.",
            latitude=Decimal("41.285680"),
            longitude=Decimal("69.203464"),
            address="Chilonzor, Tashkent",
        )
        branch = Branch.objects.create(
            organization=organization,
            name=DEMO_BRANCH_NAME,
            phone=f"{DEMO_PHONE_PREFIX}92000",
            address="Bunyodkor ko'chasi, 12-uy",
            latitude=Decimal("41.285680"),
            longitude=Decimal("69.203464"),
            manager=owner,
        )

        day_map = {
            "Dushanba": Day.objects.get_or_create(day="Dushanba")[0],
            "Seshanba": Day.objects.get_or_create(day="Seshanba")[0],
            "Chorshanba": Day.objects.get_or_create(day="Chorshanba")[0],
            "Payshanba": Day.objects.get_or_create(day="Payshanba")[0],
            "Juma": Day.objects.get_or_create(day="Juma")[0],
            "Shanba": Day.objects.get_or_create(day="Shanba")[0],
        }

        specialties = [
            Specialty.objects.get_or_create(title=title)[0]
            for title in ["Matematika", "Ingliz tili", "Frontend", "IELTS", "Robototexnika"]
        ]

        rooms = [
            Room.objects.create(branch=branch, name=f"Xona {index}", capacity=16 + index * 4)
            for index in range(1, 5)
        ]

        courses = [
            CourseTemplate.objects.create(
                name=name,
                center=organization,
                duration_months=duration,
                price=Decimal(price),
                note=note,
            )
            for name, duration, price, note in [
                ("Demo Matematika", 6, "450000", "Abituriyentlar uchun intensiv kurs."),
                ("Demo Ingliz tili", 8, "520000", "Speaking va grammar balanslangan yo'nalish."),
                ("Demo Frontend", 5, "680000", "HTML, CSS, JS va React asoslari."),
                ("Demo IELTS", 4, "750000", "Mock test va writing analysis bilan."),
                ("Demo Robototexnika", 6, "610000", "Lego va arduino mashg'ulotlari."),
            ]
        ]
        branch.courses.add(*courses)

        operator_names = ["Malika Operator", "Akmal Operator", "Diyor Operator"]
        operators = []
        for index, full_name in enumerate(operator_names, start=1):
            user = User.objects.create_user(
                phone_number=f"{DEMO_PHONE_PREFIX}93{index:03d}",
                password="12345678",
                full_name=full_name,
                role=ROLE.MANAGER,
            )
            operators.append(
                Operator.objects.create(
                    user=user,
                    center=organization,
                    monthly_salary=Decimal("4500000"),
                    bonus_point=index * 2,
                )
            )

        sources = [
            Source.objects.create(center=organization, name=name, icon=demo_image(f"source-{idx}.gif"))
            for idx, name in enumerate(["Instagram", "Telegram", "Referal"], start=1)
        ]
        situations = [
            Situation.objects.create(organization=organization, title=title)
            for title in ["Yangi lead", "Bog'landi", "Sinov darsiga yozildi", "To'lov qilgan"]
        ]

        teacher_specs = [
            ("Dilshod Karimov", courses[0], [specialties[0]]),
            ("Madina Yusupova", courses[1], [specialties[1], specialties[3]]),
            ("Sardor Raximov", courses[2], [specialties[2]]),
            ("Mubina Rahmatova", courses[3], [specialties[1], specialties[3]]),
            ("Aziz Tursunov", courses[4], [specialties[4]]),
        ]
        teachers = []
        for index, (full_name, _course, teacher_specialties) in enumerate(teacher_specs, start=1):
            user = User.objects.create_user(
                phone_number=f"{DEMO_PHONE_PREFIX}94{index:03d}",
                password="12345678",
                full_name=full_name,
                role=ROLE.TEACHER,
            )
            teacher = Teacher.objects.create(
                user=user,
                branch=branch,
                monthly_salary=Decimal("7000000") + Decimal(index * 250000),
                percentage_share=Decimal("15.00"),
                lesson_fee=Decimal("80000"),
                per_student_fee=Decimal("120000"),
            )
            teacher.specialty.set(teacher_specialties)
            teachers.append(teacher)

        group_configs = [
            ("Algoritm A", courses[0], teachers[0], rooms[0], ["Dushanba", "Chorshanba", "Juma"], time(9, 0), time(10, 30)),
            ("Grammar Plus", courses[1], teachers[1], rooms[1], ["Seshanba", "Payshanba", "Shanba"], time(10, 0), time(11, 30)),
            ("React N1", courses[2], teachers[2], rooms[2], ["Dushanba", "Chorshanba", "Juma"], time(14, 0), time(15, 30)),
            ("IELTS 6+", courses[3], teachers[3], rooms[1], ["Seshanba", "Payshanba"], time(16, 0), time(17, 30)),
            ("Robokids", courses[4], teachers[4], rooms[3], ["Shanba"], time(11, 0), time(13, 0)),
            ("Matematika Evening", courses[0], teachers[0], rooms[0], ["Seshanba", "Payshanba"], time(18, 0), time(19, 30)),
        ]

        current_date = timezone.localdate()
        groups = []
        weekday_map = {
            "Dushanba": 0,
            "Seshanba": 1,
            "Chorshanba": 2,
            "Payshanba": 3,
            "Juma": 4,
            "Shanba": 5,
        }
        group_weekdays = {}
        for index, (title, course, teacher, room, day_names, start_at, end_at) in enumerate(group_configs, start=1):
            group = Group.objects.create(
                title=title,
                course=course,
                branch=branch,
                teacher=teacher,
                room=room,
                lessons_days_choice=GROUP_DAYS_CHOICES.EVERY_DAY,
                status=GROUP_STATUS.ACTIVE if index < 6 else GROUP_STATUS.TEST_LESSON,
                start_lesson=start_at,
                end_lesson=end_at,
                started_at=current_date.replace(day=1),
                total_student=0,
            )
            group.lessons_days.set([day_map[name] for name in day_names])
            groups.append(group)
            group_weekdays[group.id] = {weekday_map[name] for name in day_names}

        first_names = [
            "Aziza", "Jasur", "Muhammadali", "Shahzoda", "Bekzod", "Nilufar", "Rustam", "Malika",
            "Oybek", "Madina", "Farrux", "Lola", "Kamron", "Sabina", "Doston", "Sevinch",
            "Umid", "Feruza", "Sardor", "Nodira", "Ulug'bek", "Asal", "Temur", "Mubina",
        ]
        last_names = [
            "Karimov", "Yusupova", "Ergashev", "To'raev", "Shukurov", "Raximova", "Toshpulatov", "Normatova",
            "Salimov", "Usmonova", "Aliyev", "Abdullayeva", "Rasulov", "Ismoilova", "Sodiqov", "Qodirova",
        ]
        payment_statuses = [
            STUDENT_PAYMENT.NO_DEBT,
            STUDENT_PAYMENT.NEAR_PAYMENT,
            STUDENT_PAYMENT.DEBTOR,
            STUDENT_PAYMENT.OVER_PAYMENT,
        ]

        students = []
        for index in range(student_count):
            full_name = f"{first_names[index % len(first_names)]} {last_names[index % len(last_names)]}"
            user = User.objects.create_user(
                phone_number=f"{DEMO_PHONE_PREFIX}95{index:03d}",
                password="12345678",
                full_name=full_name,
                role=ROLE.STUDENT,
            )
            primary_group = groups[index % len(groups)]
            student = Student.objects.create(
                user=user,
                full_name=full_name,
                phone_number=user.phone_number,
                center=organization,
                group=primary_group,
                status=STUDENT_STATUS.ACTIVE if index % 7 != 0 else STUDENT_STATUS.FROZEN,
                payment_status=payment_statuses[index % len(payment_statuses)],
                next_payment_date=current_date + timedelta(days=(index % 10) - 4),
                contract=index % 2 == 0,
                comment="Demo o'quvchi",
            )
            primary_group.students.add(student)

            if index % 5 == 0:
                secondary_group = groups[(index + 2) % len(groups)]
                secondary_group.students.add(student)

            students.append(student)

        for group in groups:
            group.total_student = group.students.count()
            group.save(update_fields=["total_student"])

        session_dates_by_group = {
            group.id: month_dates_for_weekdays(current_date.year, current_date.month, group_weekdays[group.id])
            for group in groups
        }
        for group in groups:
            for student in group.students.all():
                for lesson_date in session_dates_by_group[group.id]:
                    roll = rng.randint(1, 100)
                    if roll <= 74:
                        is_present = True
                    elif roll <= 92:
                        is_present = False
                    else:
                        is_present = None

                    Attendance.objects.create(
                        group=group,
                        student=student,
                        date=lesson_date,
                        is_present=is_present,
                        note="" if is_present is not False else "Demo qoldirgan dars",
                    )

        score_reasons = ["Faollik", "Uyga vazifa", "Mini test", "Vaqtida kelgan"]
        for index, student in enumerate(students):
            student_groups = list(student.groups.all())
            if index % 3 != 0:
                for _ in range(rng.randint(2, 5)):
                    group = rng.choice(student_groups)
                    created_at = timezone.make_aware(
                        datetime.combine(
                            rng.choice(session_dates_by_group[group.id]),
                            time(hour=rng.choice([9, 11, 15, 18]), minute=rng.choice([0, 20, 40])),
                        )
                    )
                    GroupScore.objects.create(
                        group=group,
                        student=student,
                        score=rng.randint(5, 20),
                        reason=rng.choice(score_reasons),
                        created_at=created_at,
                    )

                student.refresh_from_db(fields=["total_coin", "used_coin"])
                if student.total_coin > 10 and index % 4 == 0:
                    student.used_coin = min(student.total_coin // 2, rng.randint(5, 18))
                    student.save(update_fields=["used_coin"])

            if index % 4 == 0:
                StudentNote.objects.create(
                    student=student,
                    operator=rng.choice(operators),
                    text="Demo izoh: o'quvchi bilan aloqa yaxshi, davomati nazoratda.",
                )

        lead_statuses = [LEAD_STATUS.NEW, LEAD_STATUS.PROCESS, LEAD_STATUS.SOLD, LEAD_STATUS.CANCELED]
        lead_temps = [LEAD_TEMPERATURE.HOT, LEAD_TEMPERATURE.COOL, LEAD_TEMPERATURE.COLD]
        for index in range(12):
            full_name = f"Lead {first_names[index]} {last_names[(index + 3) % len(last_names)]}"
            course = courses[index % len(courses)]
            group = groups[index % len(groups)] if index % 2 == 0 else None
            status = lead_statuses[index % len(lead_statuses)]
            Lead.objects.create(
                full_name=full_name,
                phone_number=f"{DEMO_PHONE_PREFIX}96{index:03d}",
                center=organization,
                course=course,
                group=group,
                operator=operators[index % len(operators)],
                source=sources[index % len(sources)],
                situation=situations[index % len(situations)],
                status=status,
                temperature=lead_temps[index % len(lead_temps)],
                is_active=status in {LEAD_STATUS.NEW, LEAD_STATUS.PROCESS, LEAD_STATUS.SOLD},
                is_archived=status == LEAD_STATUS.CANCELED,
                comment="Demo buyurtma",
            )

        products = [
            Product.objects.create(
                title=title,
                description=description,
                price=Decimal(price),
                count=25,
                image=demo_image(f"product-{index}.gif"),
            )
            for index, (title, description, price) in enumerate([
                ("Demo Daftar", "Brendli daftar va stiker to'plami.", "35"),
                ("Demo Futbolka", "Markaz logotipi tushirilgan futbolka.", "80"),
                ("Demo Hoodie", "Sovuq mavsum uchun issiq hoodie.", "120"),
                ("Demo Mug", "Kundalik foydalanish uchun krujka.", "45"),
            ], start=1)
        ]

        students_with_coin = [student for student in students if student.total_coin > 0]
        for index, student in enumerate(students_with_coin[:8]):
            MarketOrder.objects.create(
                student=student,
                product=products[index % len(products)],
                price=products[index % len(products)].price,
                status=[
                    MARKET_ORDER_STATUS.CREATED,
                    MARKET_ORDER_STATUS.DELIVERED,
                    MARKET_ORDER_STATUS.CANCELLED,
                ][index % 3],
            )

        self.stdout.write(self.style.SUCCESS(
            f"Demo data tayyor: {len(teachers)} teacher, {len(groups)} guruh, {len(students)} student, 12 lead, {len(products)} product."
        ))

    def _reset_demo_data(self):
        demo_product_titles = ["Demo Daftar", "Demo Futbolka", "Demo Hoodie", "Demo Mug"]

        Product.objects.filter(title__in=demo_product_titles).delete()
        Source.objects.filter(center__name=DEMO_CENTER_NAME).delete()
        Situation.objects.filter(organization__name=DEMO_CENTER_NAME).delete()
        Organization.objects.filter(name=DEMO_CENTER_NAME).delete()
        User.objects.filter(phone_number__startswith=DEMO_PHONE_PREFIX).delete()
