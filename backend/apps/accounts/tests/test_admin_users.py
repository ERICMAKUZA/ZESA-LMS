from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User


class AdminUserManagementTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email="admin@example.com",
            password="Password123!",
            first_name="Portal",
            last_name="Admin",
            role=User.Role.ADMIN,
        )
        self.trainer = User.objects.create_user(
            email="trainer@example.com",
            password="Password123!",
            first_name="Training",
            last_name="Trainer",
            role=User.Role.TRAINER,
        )
        self.lecturer = User.objects.create_user(
            email="lecturer@example.com",
            password="Password123!",
            first_name="Course",
            last_name="Lecturer",
            role=User.Role.LECTURER,
        )
        self.student = User.objects.create_user(
            email="student@example.com",
            password="Password123!",
            first_name="Course",
            last_name="Student",
            role=User.Role.STUDENT,
        )
        self.client.force_authenticate(self.admin)

    def test_admin_can_create_trainer(self):
        response = self.client.post(
            "/api/admin/users/",
            {
                "email": "new.trainer@zesa.co.zw",
                "first_name": "New",
                "last_name": "Trainer",
                "role": "TRAINER",
                "password": "Password123!",
                "password_confirm": "Password123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["role"], "TRAINER")
        self.assertTrue(User.objects.filter(email="new.trainer@zesa.co.zw").exists())

    def test_admin_can_create_lecturer(self):
        response = self.client.post(
            "/api/admin/users/",
            {
                "email": "new.lecturer@zesa.co.zw",
                "first_name": "New",
                "last_name": "Lecturer",
                "role": "LECTURER",
                "password": "Password123!",
                "password_confirm": "Password123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["role"], "LECTURER")
        self.assertTrue(User.objects.filter(email="new.lecturer@zesa.co.zw", role="LECTURER").exists())

    def test_admin_cannot_create_admin_account(self):
        response = self.client.post(
            "/api/admin/users/",
            {
                "email": "should.fail@zesa.co.zw",
                "first_name": "Wrong",
                "last_name": "Role",
                "role": "ADMIN",
                "password": "Password123!",
                "password_confirm": "Password123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("role", response.data)

    def test_assign_lecturer_changes_role_and_remains_listed(self):
        self.trainer.refresh_from_db()
        response = self.client.post(f"/api/admin/users/{self.trainer.id}/assign-lecturer/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.trainer.refresh_from_db()
        self.assertEqual(self.trainer.role, User.Role.LECTURER)

        lecturer_list = self.client.get("/api/admin/lecturers/")
        self.assertEqual(lecturer_list.status_code, status.HTTP_200_OK)
        self.assertIn(self.trainer.id, [item["id"] for item in lecturer_list.data])

    def test_deactivated_lecturer_does_not_show_in_available_lecturers(self):
        response = self.client.post(f"/api/admin/users/{self.lecturer.id}/deactivate/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        lecturer_list = self.client.get("/api/admin/lecturers/")
        self.assertEqual(lecturer_list.status_code, status.HTTP_200_OK)
        self.assertNotIn(self.lecturer.id, [item["id"] for item in lecturer_list.data])

    def test_reactivate_lecturer(self):
        self.client.post(f"/api/admin/users/{self.lecturer.id}/deactivate/")
        response = self.client.post(f"/api/admin/users/{self.lecturer.id}/reactivate/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.lecturer.refresh_from_db()
        self.assertTrue(self.lecturer.is_active)
        self.assertEqual(self.lecturer.role, User.Role.LECTURER)

    def test_non_admin_cannot_manage_users(self):
        self.client.force_authenticate(self.student)
        response = self.client.get("/api/admin/users/")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_cannot_assign_super_admin_as_lecturer(self):
        super_admin = User.objects.create_user(
            email="super.admin@example.com",
            password="Password123!",
            first_name="System",
            last_name="Super",
            role=User.Role.SUPERADMIN,
        )

        response = self.client.post(f"/api/admin/users/{super_admin.id}/assign-lecturer/")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        super_admin.refresh_from_db()
        self.assertEqual(super_admin.role, User.Role.SUPERADMIN)
