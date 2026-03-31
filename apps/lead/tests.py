from django.db import IntegrityError, transaction
from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.lead.models import Lead, Note, Situation, Source
from apps.group.models import CourseTemplate
from apps.settings.models import Organization, Branch
from apps.user.models import Operator, User
from apps.lead.serializers import LeadModelSerializer, SituationModelSerializer


class BaseTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            phone_number="+998901112233",
            password="testpass123",
        )
        self.org = Organization.objects.create(
            owner=self.user,
            name="Test Org",
            latitude=41.0,
            longitude=69.0,
        )
        self.branch = Branch.objects.create(
            name="Test Branch",
            organization=self.org,
            latitude=41.0,
            longitude=69.0
        )
        self.course = CourseTemplate.objects.create(
            name="Test Course",
            center=self.org,
        )
        # CourseTemplate va Branch M2M bog'lanishi
        self.branch.courses.add(self.course)

        self.source = Source.objects.create(
            name="Test Source",
            center=self.org,
            icon=SimpleUploadedFile("icon.png", b"fake", content_type="image/png"),
        )


class LeadModelTests(BaseTestCase):
    def test_lead_str_returns_phone_number(self):
        lead = Lead.objects.create(
            full_name="John Doe",
            phone_number="+998900000000",
            course=self.course,
            source=self.source,
            center=self.org
        )
        self.assertEqual(str(lead), "+998900000000")

    def test_lead_save_assigns_center_from_course(self):
        # Lead yaratilganda center berilmasa, course.center dan olishi kerak
        lead = Lead.objects.create(
            full_name="Auto Center Lead",
            phone_number="+998900000001",
            course=self.course,
            source=self.source,
        )
        self.assertEqual(lead.center, self.org)


class SituationModelTests(BaseTestCase):
    def test_static_with_org_constraint(self):
        with self.assertRaises(IntegrityError):
            Situation.objects.create(
                organization=self.org,
                title="Static With Org",
                is_static=True,
            )

    def test_static_without_org_ok(self):
        situation = Situation.objects.create(title="Static", is_static=True)
        self.assertEqual(str(situation), "Static")

    def test_org_with_static_false_ok(self):
        situation = Situation.objects.create(
            organization=self.org, title="Org Situation", is_static=False
        )
        self.assertEqual(str(situation), "Org Situation")


class LeadSerializerTests(BaseTestCase):
    def test_valid_lead_serializer(self):
        data = {
            "full_name": "Serializer Test",
            "phone_number": "+998901234567",
            "course": self.course.id,
            "source": self.source.id,
            "temperature": "hot",
        }
        serializer = LeadModelSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        lead = serializer.save()
        self.assertEqual(lead.full_name, "Serializer Test")
        self.assertEqual(lead.center, self.org)


class LeadViewTests(APITestCase):
    def setUp(self):
        # 1. Test uchun foydalanuvchi yaratish
        self.user = User.objects.create_user(
            phone_number="+998901112299", 
            password="testpassword"
        )
        
        # 2. Tashkilot yaratish (longitude imlosiga e'tibor bering)
        self.organization = Organization.objects.create(
            owner=self.user, 
            name="Test Org View", 
            latitude=41.0, 
            longitude=69.0  # 't' harfi olib tashlandi
        )
        
        # 3. Filial yaratish
        self.branch = Branch.objects.create(
            name="Main Branch View",
            organization=self.organization,
            latitude=41.1,
            longitude=69.1
        )
        
        # 4. Kurs yaratish
        self.course = CourseTemplate.objects.create(
            name="Test Course View", 
            center=self.organization
        )
        self.branch.courses.add(self.course)

        # 5. Manba (Source) yaratish
        self.source = Source.objects.create(
            name="Test Source View",
            center=self.organization,
            icon=SimpleUploadedFile("icon.png", b"fake", content_type="image/png"),
        )
        
        # 6. Avtorizatsiyadan o'tkazish
        self.client.force_authenticate(user=self.user)

    def test_create_situation_unauthenticated(self):
        """Tizimga kirmagan foydalanuvchi situation yarata olmasligini tekshirish"""
        self.client.logout()
        url = reverse("situation-create")
        data = {"title": "New Situation", "organization": self.organization.id}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_situation_as_owner(self):
        """Ega (owner) sifatida situation yaratishni tekshirish"""
        url = reverse("situation-create")
        data = {"title": "Owner's Situation", "organization": self.organization.id}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Situation.objects.filter(title="Owner's Situation").exists())

    def test_list_situation_as_owner(self):
        """Situation'lar ro'yxatini ko'rishni tekshirish"""
        Situation.objects.create(title="Static Situation", is_static=True)
        Situation.objects.create(title="Org Situation", organization=self.organization)
        
        url = reverse("situation-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # 1 ta static + 1 ta org situation = 2 ta bo'lishi kerak
        if isinstance(response.data, dict) and "count" in response.data and "results" in response.data:
            self.assertEqual(response.data["count"], 2)
            self.assertEqual(len(response.data["results"]), 2)
        else:
            self.assertEqual(len(response.data), 2)

    def test_create_lead_authenticated(self):
        """Lead yaratilganda center avtomatik birikishini tekshirish"""
        url = reverse("lead-create")
        data = {
            "full_name": "New Lead",
            "phone_number": "+998991234567",
            "course": self.course.id,
            "source": self.source.id,
        }
        response = self.client.post(url, data, format="json")
        
        # Statusni tekshirish
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Bazada borligini tekshirish
        lead = Lead.objects.get(full_name="New Lead")
        
        # ASOSIY QISM: Center None emasligini tekshirish
        self.assertIsNotNone(lead.center, "Lead yaratilganda center bo'sh qolmasligi kerak")
        self.assertEqual(lead.center, self.organization)

    def test_list_leads_filter_by_branch(self):
        """Leadlarni filial bo'yicha filterlashni tekshirish"""
        Lead.objects.create(
            full_name="Branch Lead",
            phone_number="+998901111111",
            course=self.course,
            source=self.source,
            center=self.organization
        )
        url = reverse("lead-list")
        # branch_id parametri bilan filterlash
        response = self.client.get(url, {"branch_id": self.branch.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Agar Pagination ishlatayotgan bo'lsangiz response.data['count'] ni tekshiring
        # Agar yo'q bo'lsa len(response.data) ni tekshiring
        if "count" in response.data:
            self.assertEqual(response.data["count"], 1)
        else:
            self.assertEqual(len(response.data), 1)
