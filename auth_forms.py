from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

User = get_user_model()


class WargaRegisterForm(forms.Form):
    nama = forms.CharField(
        label="Nama",
        max_length=100,
        widget=forms.TextInput(attrs={"class": "input", "placeholder": "Nama sesuai KTP"}),
    )
    nik = forms.CharField(
        label="NIK",
        max_length=16,
        widget=forms.TextInput(
            attrs={"class": "input", "inputmode": "numeric", "pattern": r"\d*", "placeholder": "16 digit"}
        ),
    )
    no_wa = forms.CharField(
        label="Nomor WhatsApp",
        max_length=13,
        widget=forms.TextInput(attrs={"class": "input", "placeholder": "08xxxxxxxxxx"}),
    )
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={"class": "input", "placeholder": "nama@email.com"}),
    )
    password1 = forms.CharField(
        label="Kata sandi",
        widget=forms.PasswordInput(attrs={"class": "input", "placeholder": "Minimal 8 karakter"}),
    )
    password2 = forms.CharField(
        label="Ulangi kata sandi",
        widget=forms.PasswordInput(attrs={"class": "input", "placeholder": "Ulangi kata sandi"}),
    )

    def clean_nik(self):
        nik = (self.cleaned_data.get("nik") or "").strip()
        if not nik.isdigit():
            raise ValidationError("NIK hanya boleh angka.")
        if len(nik) != 16:
            raise ValidationError("NIK harus 16 digit.")
        if User.objects.filter(nik=nik).exists():
            raise ValidationError("NIK sudah terdaftar. Silahkan login.")
        return nik

    def clean_no_wa(self):
        no_wa = (self.cleaned_data.get("no_wa") or "").strip()
        # sederhana: angka + panjang masuk akal
        digits = no_wa.replace("+", "")
        if not digits.isdigit():
            raise ValidationError("No WA harus angka (boleh diawali +).")
        if len(digits) < 9 or len(digits) > 15:
            raise ValidationError("No WA panjang 9–15 digit.")
        return no_wa

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("password1") or ""
        p2 = cleaned.get("password2") or ""
        if len(p1) < 8:
            self.add_error("password1", "Kata sandi minimal 8 karakter.")
        if p1 and p2 and p1 != p2:
            self.add_error("password2", "Kata sandi tidak sama.")
        return cleaned
