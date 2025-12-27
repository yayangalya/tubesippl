from django.test import TestCase
from django.contrib.auth import get_user_model
from core.forms import SKTMForm


class TestCleanNikPaths(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            nik="3201234501010003",
            password="Password123!",
            nama="Naswa Malika",
            no_wa="081234567890",
            email="naswa@example.com",
        )

    def base_data(self, **overrides):
        data = {
            "nama": "Naswa Malika",
            "nik": "3201234501010003",
            "tempat_lahir": "Bandung",
            "tanggal_lahir": "2000-01-01",
            "jenis_kelamin": "P",
            "pekerjaan": "Mahasiswa",
            "alamat": "Jl. Contoh No. 1",
        }
        data.update(overrides)
        return data

    def test_P1_valid(self):
        form = SKTMForm(data=self.base_data(), user=self.user)
        self.assertTrue(form.is_valid(), msg=form.errors.as_text())

    def test_P2_non_digit(self):
        form = SKTMForm(data=self.base_data(nik="32012A4501010003"), user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn("NIK hanya boleh angka", str(form.errors))

    def test_P3_wrong_length(self):
        form = SKTMForm(data=self.base_data(nik="32012345"), user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn("NIK harus 16 digit", str(form.errors))

    def test_P4_mismatch_user(self):
        form = SKTMForm(data=self.base_data(nik="3201234501010004"), user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn("NIK harus sama dengan NIK akun login", str(form.errors))
