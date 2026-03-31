from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.group.choices import GROUP_DAYS_CHOICES
from apps.group.models.course import CourseTemplate
from apps.group.models.group import Group
from apps.group.models.score import GroupScore
from apps.market.models import MARKET_ORDER_STATUS, MarketOrder, Product
from apps.pupil.models import Student
from apps.settings.models import Branch, Organization
from apps.user.choices import ROLE
from apps.user.models import User


class MarketAPITests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            phone_number="+998900299999",
            password="ownerpass123",
        )
        self.organization = Organization.objects.create(
            owner=self.owner,
            name="Org",
            latitude=41,
            longitude=69,
        )
        self.branch = Branch.objects.create(
            organization=self.organization,
            name="Main branch",
            latitude=41,
            longitude=69,
        )
        self.course = CourseTemplate.objects.create(
            name="English",
            center=self.organization,
            duration_months=6,
        )
        self.branch.courses.add(self.course)

        self.student_user = User.objects.create_user(
            phone_number="+998900200001",
            password="studentpass123",
            role=ROLE.STUDENT,
        )
        self.student = Student.objects.create(
            user=self.student_user,
            full_name="Student One",
            phone_number="+998900200001",
            center=self.organization,
        )

        self.other_student_user = User.objects.create_user(
            phone_number="+998900200002",
            password="studentpass456",
            role=ROLE.STUDENT,
        )
        self.other_student = Student.objects.create(
            user=self.other_student_user,
            full_name="Student Two",
            phone_number="+998900200002",
            center=self.organization,
        )
        self.group = Group.objects.create(
            title="English-1",
            course=self.course,
            branch=self.branch,
            lessons_days_choice=GROUP_DAYS_CHOICES.EVERAY_DAY,
            start_lesson="09:00:00",
            end_lesson="10:00:00",
        )
        self.group.students.add(self.student)
        self.student.group = self.group
        self.student.save(update_fields=["group"])
        GroupScore.objects.create(
            group=self.group,
            student=self.student,
            score=40,
            reason="Weekly reward",
        )

        self.product = Product.objects.create(
            image=SimpleUploadedFile("product.jpg", b"market-image-bytes", content_type="image/jpeg"),
            title="Notebook",
            price="25.00",
            description="Useful notebook",
            count=3,
        )

    def test_product_list_returns_products(self):
        self.client.force_authenticate(user=self.student_user)

        response = self.client.get(reverse("market-product-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertEqual(len(response.data), 1)
        product = response.data[0]
        self.assertEqual(product["id"], self.product.id)
        self.assertEqual(product["title"], self.product.title)
        self.assertEqual(product["price"], "25.00")
        self.assertEqual(product["description"], self.product.description)
        self.assertEqual(product["count"], self.product.count)
        self.assertTrue(product["image"])

    def test_product_list_can_filter_affordable_products(self):
        cheap_product = Product.objects.create(
            image=SimpleUploadedFile("cheap.jpg", b"cheap-image-bytes", content_type="image/jpeg"),
            title="Pen",
            price="10.00",
            description="Cheap item",
            count=5,
        )
        Product.objects.create(
            image=SimpleUploadedFile("expensive-filter.jpg", b"expensive-filter-bytes", content_type="image/jpeg"),
            title="Headphones",
            price="50.00",
            description="Expensive item",
            count=2,
        )
        self.student.used_coin = 30
        self.student.save(update_fields=["used_coin"])
        self.student.refresh_from_db()
        self.assertEqual(self.student.total_coin, 10)
        self.client.force_authenticate(user=self.student_user)

        response = self.client.get(
            reverse("market-product-list"),
            {"affordable": "true"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], cheap_product.id)

    def test_create_order_generates_secret_code(self):
        self.client.force_authenticate(user=self.student_user)

        response = self.client.post(
            reverse("market-order-create"),
            {"product": self.product.id},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["product_id"], self.product.id)
        self.assertEqual(response.data["product_title"], self.product.title)
        self.assertEqual(response.data["product_count"], 2)
        self.assertEqual(response.data["price"], "25.00")
        self.assertEqual(response.data["status"], "created")

        secret_code = response.data["secret_code"]
        self.assertRegex(secret_code, r"^(?=.*[A-Z])(?=.*\d)[A-Z0-9]{6}$")
        self.assertEqual(MarketOrder.objects.count(), 1)
        self.assertEqual(MarketOrder.objects.first().secret_code, secret_code)
        self.product.refresh_from_db()
        self.student.refresh_from_db()
        self.assertEqual(self.product.count, 2)
        self.assertEqual(self.student.used_coin, 25)
        self.assertEqual(self.student.total_coin, 15)

    def test_student_orders_list_shows_only_own_orders(self):
        MarketOrder.objects.create(student=self.student, product=self.product)
        other_product = Product.objects.create(
            image=SimpleUploadedFile("other-product.jpg", b"other-image-bytes", content_type="image/jpeg"),
            title="Backpack",
            price="40.00",
            description="Useful backpack",
            count=1,
        )
        MarketOrder.objects.create(student=self.other_student, product=other_product)

        self.client.force_authenticate(user=self.student_user)

        response = self.client.get(reverse("market-order-me"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertEqual(len(response.data), 1)
        order = response.data[0]
        self.assertEqual(order["product_id"], self.product.id)
        self.assertEqual(order["product_title"], self.product.title)
        self.assertEqual(order["product_count"], self.product.count)
        self.assertEqual(order["status"], "created")
        self.assertTrue(order["secret_code"])
        self.assertRegex(order["secret_code"], r"^(?=.*[A-Z])(?=.*\d)[A-Z0-9]{6}$")

    def test_cancelled_created_order_returns_product_and_student_coins(self):
        self.client.force_authenticate(user=self.student_user)
        self.client.post(
            reverse("market-order-create"),
            {"product": self.product.id},
            format="json",
        )

        order = MarketOrder.objects.get(student=self.student, product=self.product)
        order.status = MARKET_ORDER_STATUS.CANCELLED
        order.save(update_fields=["status"])

        self.student.refresh_from_db()
        self.product.refresh_from_db()
        order.refresh_from_db()

        self.assertEqual(order.status, MARKET_ORDER_STATUS.CANCELLED)
        self.assertEqual(self.student.used_coin, 0)
        self.assertEqual(self.student.total_coin, 40)
        self.assertEqual(self.product.count, 3)

    def test_cancelled_delivered_order_does_not_return_product_or_coins(self):
        self.client.force_authenticate(user=self.student_user)
        self.client.post(
            reverse("market-order-create"),
            {"product": self.product.id},
            format="json",
        )

        order = MarketOrder.objects.get(student=self.student, product=self.product)
        order.status = MARKET_ORDER_STATUS.DELIVERED
        order.save(update_fields=["status"])
        order.status = MARKET_ORDER_STATUS.CANCELLED
        order.save(update_fields=["status"])

        self.student.refresh_from_db()
        self.product.refresh_from_db()
        order.refresh_from_db()

        self.assertEqual(order.status, MARKET_ORDER_STATUS.CANCELLED)
        self.assertEqual(self.student.used_coin, 25)
        self.assertEqual(self.student.total_coin, 15)
        self.assertEqual(self.product.count, 2)

    def test_cannot_create_order_when_product_is_out_of_stock(self):
        sold_out_product = Product.objects.create(
            image=SimpleUploadedFile("sold-out.jpg", b"sold-out-bytes", content_type="image/jpeg"),
            title="Pen",
            price="5.00",
            description="Blue pen",
            count=0,
        )
        self.client.force_authenticate(user=self.student_user)

        response = self.client.post(
            reverse("market-order-create"),
            {"product": sold_out_product.id},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(str(response.data["product"]), "Bu mahsulot tugagan.")
        self.assertEqual(MarketOrder.objects.count(), 0)

    def test_cannot_create_order_when_student_has_not_enough_coins(self):
        expensive_product = Product.objects.create(
            image=SimpleUploadedFile("expensive.jpg", b"expensive-bytes", content_type="image/jpeg"),
            title="Tablet",
            price="50.00",
            description="Expensive item",
            count=2,
        )
        self.client.force_authenticate(user=self.student_user)

        response = self.client.post(
            reverse("market-order-create"),
            {"product": expensive_product.id},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(str(response.data["product"]), "Studentda coin yetarli emas.")
        self.student.refresh_from_db()
        self.assertEqual(self.student.used_coin, 0)
