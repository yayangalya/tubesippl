from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),  # <-- ini tambahan

    # Auth warga
    path("daftar/", views.daftar_warga, name="daftar_warga"),
    path("login/", views.login_warga, name="login_warga"),
    path("logout/", views.logout_view, name="logout"),

    # Dashboard warga
    path("warga/", views.warga_home, name="warga_home"),

    # Pengajuan surat
    path("warga/ajukan/", views.ajukan_surat, name="ajukan_surat"),
    path("warga/ajukan/verifikasi/", views.verifikasi_pengajuan, name="verifikasi_pengajuan"),
    path("warga/ajukan/diproses/", views.pengajuan_diproses, name="pengajuan_diproses"),
    path("warga/ajukan/berhasil/", views.pengajuan_berhasil, name="pengajuan_berhasil"),

    # dinamis taruh bawah
    path("warga/ajukan/<str:letter_type>/", views.isi_surat, name="isi_surat"),

    # Status & Notifikasi
    path("warga/status/", views.status_surat, name="status_surat"),
    path("warga/notifikasi/", views.notifikasi, name="notifikasi"),
]