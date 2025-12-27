# core/views.py
from datetime import date, datetime

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods

from .auth_forms import WargaRegisterForm
from .forms import (
    SKTMForm,
    DomisiliForm,
    BelumMenikahForm,
    SKCKForm,
    VerifikasiForm,
)
from .models import LetterRequest, LetterType, RequestStatus, Notification


FORM_BY_TYPE = {
    LetterType.SKTM: SKTMForm,
    LetterType.DOMISILI: DomisiliForm,
    LetterType.BELUM_MENIKAH: BelumMenikahForm,
    LetterType.SKCK: SKCKForm,
}


def _jsonable(value):
    """Convert date/datetime (dan nested dict/list) jadi aman untuk JSON/session."""
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: _jsonable(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_jsonable(v) for v in value]
    return value


# ==========================
# AUTH
# ==========================

@require_http_methods(["GET", "POST"])
def login_warga(request):
    error = None
    if request.method == "POST":
        nik = (request.POST.get("nik") or "").strip()
        password = request.POST.get("password") or ""

        user = authenticate(request, username=nik, password=password)
        if user is None:
            error = "NIK atau kata sandi salah."
        else:
            login(request, user)
            if user.is_staff:
                return redirect("/admin/")
            return redirect("warga_home")

    return render(request, "core/login.html", {"error": error})

def home(request):
    # kalau sudah login, arahkan sesuai role
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect("/admin/")
        return redirect("warga_home")
    # kalau belum login, arahkan ke login
    return redirect("login_warga")

@require_http_methods(["GET", "POST"])
def daftar_warga(request):
    # Kalau sudah login, jangan boleh daftar akun baru dari sesi ini
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect("/admin/")
        return render(request, "core/daftar.html", {"blocked": True})

    if request.method == "POST":
        form = WargaRegisterForm(request.POST)
        if form.is_valid():
            from django.contrib.auth import get_user_model
            User = get_user_model()

            User.objects.create_user(
                nik=form.cleaned_data["nik"],
                password=form.cleaned_data["password1"],
                nama=form.cleaned_data["nama"],
                no_wa=form.cleaned_data["no_wa"],
                email=form.cleaned_data["email"],
            )
            return redirect("login_warga")
    else:
        form = WargaRegisterForm()

    return render(request, "core/daftar.html", {"form": form})


@require_http_methods(["POST"])
def logout_view(request):
    logout(request)
    return redirect("login_warga")


# ==========================
# DASHBOARD WARGA
# ==========================

@login_required
def warga_home(request):
    if request.user.is_staff:
        return redirect("/admin/")
    return render(request, "core/warga_home.html")


# ==========================
# FLOW AJUKAN SURAT
# ==========================

@login_required
@require_http_methods(["GET", "POST"])
def ajukan_surat(request):
    if request.user.is_staff:
        return redirect("/admin/")

    if request.method == "POST":
        letter_type = request.POST.get("letter_type")
        if letter_type in FORM_BY_TYPE:
            request.session["letter_type"] = letter_type
            return redirect("isi_surat", letter_type=letter_type)

    return render(request, "core/ajukan_pilih.html", {"types": LetterType})


@login_required
@require_http_methods(["GET", "POST"])
def isi_surat(request, letter_type):
    if request.user.is_staff:
        return redirect("/admin/")

    if letter_type not in FORM_BY_TYPE:
        return redirect("ajukan_surat")

    FormCls = FORM_BY_TYPE[letter_type]

    if request.method == "POST":
        form = FormCls(request.POST, user=request.user)
        if form.is_valid():
            payload = _jsonable(form.cleaned_data)  # date -> string
            request.session["surat_payload"] = payload
            request.session["letter_type"] = letter_type
            return redirect("verifikasi_pengajuan")
    else:
        form = FormCls(
            user=request.user,
            initial={"nama": request.user.nama, "nik": request.user.nik},
        )

    return render(
        request,
        "core/ajukan_isi.html",
        {
            "form": form,
            "letter_type": letter_type,
            "letter_label": dict(LetterType.choices).get(letter_type),
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def verifikasi_pengajuan(request):
    if request.user.is_staff:
        return redirect("/admin/")

    letter_type = request.session.get("letter_type")
    payload = request.session.get("surat_payload")

    if not letter_type or not payload:
        return redirect("ajukan_surat")

    if request.method == "POST":
        form = VerifikasiForm(request.POST, user=request.user, expected_type=letter_type)
        if form.is_valid():
            lr = LetterRequest.objects.create(
                user=request.user,
                letter_type=letter_type,
                status=RequestStatus.DIPROSES,
                nama=form.cleaned_data["nama"],
                nik=form.cleaned_data["nik"],
                alamat=form.cleaned_data["alamat"],
                payload=payload,
            )
            request.session["last_request_id"] = lr.id
            return redirect("pengajuan_diproses")
    else:
        form = VerifikasiForm(
            user=request.user,
            expected_type=letter_type,
            initial={
                "nama": request.user.nama,
                "nik": request.user.nik,
                "alamat": payload.get("alamat", ""),
                "jenis_surat": letter_type,
            },
        )

    return render(request, "core/verifikasi.html", {"form": form, "letter_type": letter_type})


@login_required
def pengajuan_diproses(request):
    if request.user.is_staff:
        return redirect("/admin/")

    req_id = request.session.get("last_request_id")
    if not req_id:
        return redirect("warga_home")

    lr = get_object_or_404(LetterRequest, id=req_id, user=request.user)
    return render(request, "core/diproses.html", {"lr": lr})


@login_required
def pengajuan_berhasil(request):
    if request.user.is_staff:
        return redirect("/admin/")

    req_id = request.session.get("last_request_id")
    if not req_id:
        return redirect("warga_home")

    lr = get_object_or_404(LetterRequest, id=req_id, user=request.user)
    return render(request, "core/berhasil.html", {"lr": lr})


@login_required
def status_surat(request):
    if request.user.is_staff:
        return redirect("/admin/")

    items = LetterRequest.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "core/status_surat.html", {"items": items})


@login_required
def notifikasi(request):
    if request.user.is_staff:
        return redirect("/admin/")

    items = Notification.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "core/notifikasi.html", {"items": items})
