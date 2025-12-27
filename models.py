from django.db import models
from django.core.validators import RegexValidator
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.conf import settings


class UserManager(BaseUserManager):
    def create_user(self, nik, password=None, **extra_fields):
        if not nik:
            raise ValueError("NIK wajib diisi")

        user = self.model(nik=nik, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, nik, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        return self.create_user(nik, password, **extra_fields)


nik_validator = RegexValidator(
    regex=r"^\d{16}$",
    message="NIK harus 16 digit angka.",
)

wa_validator = RegexValidator(
    regex=r"^\+?\d{9,15}$",
    message="No WA harus angka (boleh diawali +), panjang 9-15 digit.",
)


class User(AbstractBaseUser, PermissionsMixin):
    nik = models.CharField(max_length=16, unique=True, validators=[nik_validator])
    nama = models.CharField(max_length=100)

    no_wa = models.CharField(
        max_length=16,
        blank=True,
        validators=[wa_validator],
        help_text="Contoh: 081234567890 atau +6281234567890",
    )
    email = models.EmailField(blank=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = "nik"
    REQUIRED_FIELDS = ["nama"]

    objects = UserManager()

    def __str__(self):
        return f"{self.nik} - {self.nama}"


# ==========================
# SURAT (Permohonan Warga)
# ==========================

class LetterType(models.TextChoices):
    SKTM = "SKTM", "Surat Keterangan Tidak Mampu"
    DOMISILI = "DOMISILI", "Surat Keterangan Domisili"
    BELUM_MENIKAH = "BELUM_MENIKAH", "Surat Keterangan Belum Menikah"
    SKCK = "SKCK", "Surat Pengantar SKCK"


class RequestStatus(models.TextChoices):
    DIPROSES = "DIPROSES", "Dalam Proses"
    DISETUJUI = "DISETUJUI", "Disetujui"
    TELAH_DIAMBIL = "TELAH_DIAMBIL", "Telah Diambil"
    DITOLAK = "DITOLAK", "Ditolak"


class LetterRequest(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="letter_requests")

    letter_type = models.CharField(max_length=20, choices=LetterType.choices)
    status = models.CharField(max_length=20, choices=RequestStatus.choices, default=RequestStatus.DIPROSES)

    # snapshot tampilan cepat
    nama = models.CharField(max_length=100)
    nik = models.CharField(max_length=16, validators=[nik_validator])
    alamat = models.TextField()

    # data detail beda-beda tiap surat
    payload = models.JSONField(default=dict)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.nik} - {self.letter_type} - {self.status}"


class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    title = models.CharField(max_length=120)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.nik} - {self.title}"
