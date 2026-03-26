from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.market.models import MarketOrder, Product
from apps.pupil.models import Student
from apps.user.choices import ROLE
from apps.user.models import User


class MarketAPITests(APITestCase):
    def setUp(self):
        self.student_user = User.objects.create_user(
            phone_number="+998900200001",
            password="studentpass123",
            role=ROLE.STUDENT,
        )
        self.student = Student.objects.create(
            user=self.student_user,
            full_name="Student One",
            phone_number="+998900200001",
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
        )

        self.product = Product.objects.create(
            image=SimpleUploadedFile("product.jpg", b"market-image-bytes", content_type="image/jpeg"),
            title="Notebook",
            price="25.00",
            description="Useful notebook",
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
        self.assertTrue(product["image"])

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
        self.assertEqual(response.data["price"], "25.00")

        secret_code = response.data["secret_code"]
        self.assertRegex(secret_code, r"^(?=.*[A-Z])(?=.*\d)[A-Z0-9]{6}$")
        self.assertEqual(MarketOrder.objects.count(), 1)
        self.assertEqual(MarketOrder.objects.first().secret_code, secret_code)

    def test_student_orders_list_shows_only_own_orders(self):
        MarketOrder.objects.create(student=self.student, product=self.product)
        other_product = Product.objects.create(
            image=SimpleUploadedFile("other-product.jpg", b"other-image-bytes", content_type="image/jpeg"),
            title="Backpack",
            price="40.00",
            description="Useful backpack",
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
        self.assertTrue(order["secret_code"])
        self.assertRegex(order["secret_code"], r"^(?=.*[A-Z])(?=.*\d)[A-Z0-9]{6}$")
