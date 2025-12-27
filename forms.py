# core/forms.py (UPDATED: radio -> dropdown untuk kewarganegaraan/agama/status/jenis_surat, gender tetap radio)

from django import forms
from django.core.exceptions import ValidationError
from .models import LetterType


AGAMA_CHOICES = [
    ("ISLAM", "Islam"),
    ("KRISTEN", "Kristen (Protestan)"),
    ("KATOLIK", "Katolik"),
    ("HINDU", "Hindu"),
    ("BUDDHA", "Buddha"),
    ("KONGHUCU", "Konghucu"),
]

STATUS_NIKAH_CHOICES = [
    ("MENIKAH", "Menikah"),
    ("BELUM_MENIKAH", "Belum Menikah"),
]

KEWARGANEGARAAN_CHOICES = [
    ("WNI", "WNI"),
    ("WNA", "WNA"),
]

GENDER_CHOICES = [
    ("L", "Laki-laki"),
    ("P", "Perempuan"),
]


def _apply_input_class(form: forms.Form):
    """
    Set class="input" untuk widget input standar.
    Select / Radio punya styling/struktur beda, jadi kita set manual di field-nya.
    """
    for name, field in form.fields.items():
        if isinstance(
            field.widget,
            (
                forms.TextInput,
                forms.EmailInput,
                forms.DateInput,
                forms.Textarea,
                forms.NumberInput,
                forms.PasswordInput,
            ),
        ):
            field.widget.attrs.setdefault("class", "input")


def _select_with_input_class(*, choices, placeholder: str):
    """
    Helper dropdown (panah kebawah) dengan placeholder.
    """
    return forms.Select(
        attrs={"class": "input"},
        choices=[("", placeholder)] + list(choices),
    )


class BaseSuratForm(forms.Form):
    nama = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={"class": "input"}),
    )
    nik = forms.CharField(
        max_length=16,
        widget=forms.TextInput(
            attrs={"class": "input", "inputmode": "numeric", "pattern": r"\d*"}
        ),
    )
    tempat_lahir = forms.CharField(
        max_length=60,
        widget=forms.TextInput(attrs={"class": "input"}),
    )
    tanggal_lahir = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date", "class": "input"}),
    )

    # Gender tetap radio (sesuai requirement kamu)
    jenis_kelamin = forms.ChoiceField(
        choices=GENDER_CHOICES,
        widget=forms.RadioSelect,
    )

    pekerjaan = forms.CharField(
        max_length=60,
        widget=forms.TextInput(attrs={"class": "input"}),
    )
    alamat = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 3, "class": "input"}),
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        _apply_input_class(self)

    def clean_nik(self):
        nik = (self.cleaned_data["nik"] or "").strip()
        if not nik.isdigit():
            raise ValidationError("NIK hanya boleh angka.")
        if len(nik) != 16:
            raise ValidationError("NIK harus 16 digit.")
        if self.user and nik != self.user.nik:
            raise ValidationError("NIK harus sama dengan NIK akun login.")
        return nik

    def clean_nama(self):
        nama = (self.cleaned_data["nama"] or "").strip()
        if self.user and nama.casefold() != self.user.nama.strip().casefold():
            raise ValidationError("Nama harus sama dengan nama akun (sesuai data akun desa).")
        return nama


class SKTMForm(BaseSuratForm):
    pass


class DomisiliForm(BaseSuratForm):
    # UPGRADE: dropdown (Select) bukan radio
    kewarganegaraan = forms.ChoiceField(
        choices=KEWARGANEGARAAN_CHOICES,
        widget=_select_with_input_class(
            choices=KEWARGANEGARAAN_CHOICES,
            placeholder="Pilih kewarganegaraan",
        ),
    )
    agama = forms.ChoiceField(
        choices=AGAMA_CHOICES,
        widget=_select_with_input_class(
            choices=AGAMA_CHOICES,
            placeholder="Pilih agama",
        ),
    )
    status_pernikahan = forms.ChoiceField(
        choices=STATUS_NIKAH_CHOICES,
        widget=_select_with_input_class(
            choices=STATUS_NIKAH_CHOICES,
            placeholder="Pilih status pernikahan",
        ),
    )


class BelumMenikahForm(BaseSuratForm):
    # UPGRADE: dropdown
    agama = forms.ChoiceField(
        choices=AGAMA_CHOICES,
        widget=_select_with_input_class(
            choices=AGAMA_CHOICES,
            placeholder="Pilih agama",
        ),
    )


class SKCKForm(BaseSuratForm):
    # UPGRADE: dropdown
    agama = forms.ChoiceField(
        choices=AGAMA_CHOICES,
        widget=_select_with_input_class(
            choices=AGAMA_CHOICES,
            placeholder="Pilih agama",
        ),
    )
    status_pernikahan = forms.ChoiceField(
        choices=STATUS_NIKAH_CHOICES,
        widget=_select_with_input_class(
            choices=STATUS_NIKAH_CHOICES,
            placeholder="Pilih status pernikahan",
        ),
    )


class VerifikasiForm(forms.Form):
    nama = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={"class": "input"}),
    )
    nik = forms.CharField(
        max_length=16,
        widget=forms.TextInput(
            attrs={"class": "input", "inputmode": "numeric", "pattern": r"\d*"}
        ),
    )
    alamat = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 3, "class": "input"}),
    )

    # UPGRADE: jenis_surat jadi dropdown (Select) bukan radio
    jenis_surat = forms.ChoiceField(
        choices=LetterType.choices,
        widget=_select_with_input_class(
            choices=LetterType.choices,
            placeholder="Pilih jenis surat",
        ),
    )

    def __init__(self, *args, user=None, expected_type=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.expected_type = expected_type
        _apply_input_class(self)

        # tampilkan jenis surat, tapi dikunci supaya payload tidak mismatch
        if expected_type:
            self.fields["jenis_surat"].initial = expected_type
            self.fields["jenis_surat"].disabled = True

            # Kalau disabled, placeholder ga penting, tapi tetap aman
            # (Django akan render select disabled)

    def clean_nik(self):
        nik = (self.cleaned_data["nik"] or "").strip()
        if not nik.isdigit():
            raise ValidationError("NIK hanya boleh angka.")
        if len(nik) != 16:
            raise ValidationError("NIK harus 16 digit.")
        if self.user and nik != self.user.nik:
            raise ValidationError("NIK verifikasi harus sama dengan akun login.")
        return nik

    def clean_nama(self):
        nama = (self.cleaned_data["nama"] or "").strip()
        if self.user and nama.casefold() != self.user.nama.strip().casefold():
            raise ValidationError("Nama verifikasi harus sama dengan nama akun.")
        return nama
