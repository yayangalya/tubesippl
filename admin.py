from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, LetterRequest, Notification, RequestStatus


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ("nik",)
    list_display = ("nik", "nama", "email", "no_wa", "is_staff", "is_active")
    search_fields = ("nik", "nama", "email", "no_wa")
    list_filter = ("is_staff", "is_active")

    fieldsets = (
        (None, {"fields": ("nik", "password")}),
        ("Info", {"fields": ("nama", "email", "no_wa")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login",)}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("nik", "nama", "email", "no_wa", "password1", "password2", "is_staff", "is_active"),
        }),
    )

    filter_horizontal = ("groups", "user_permissions")


@admin.register(LetterRequest)
class LetterRequestAdmin(admin.ModelAdmin):
    ordering = ("-created_at",)
    list_display = ("id", "nik", "nama", "letter_type", "status", "created_at")
    list_filter = ("letter_type", "status")
    search_fields = ("nik", "nama")

    # Admin hanya boleh ubah STATUS. Data warga read-only.
    readonly_fields = (
        "user", "letter_type", "nama", "nik", "alamat", "payload",
        "created_at", "updated_at",
    )

    # Urutan tampilan detail
    fields = (
        "user", "letter_type", "status",
        "nama", "nik", "alamat", "payload",
        "created_at", "updated_at",
    )

    def has_add_permission(self, request):
        # Admin tidak boleh bikin pengajuan manual; harus dari warga.
        return False

    def save_model(self, request, obj, form, change):
        old_status = None
        if change and obj.pk:
            old_status = LetterRequest.objects.get(pk=obj.pk).status

        super().save_model(request, obj, form, change)

        # Buat notifikasi hanya jika status berubah
        if change and old_status != obj.status:
            if obj.status == RequestStatus.DISETUJUI:
                Notification.objects.create(
                    user=obj.user,
                    title="Surat Disetujui",
                    message=(
                        "Surat kamu telah disetujui. Silahkan datang ke kantor desa untuk mengambil surat. "
                        "Harap membawa KTP atau KK sebagai bukti pengambilan."
                    ),
                )
            elif obj.status == RequestStatus.TELAH_DIAMBIL:
                Notification.objects.create(
                    user=obj.user,
                    title="Surat Telah Diambil",
                    message=f"{obj.get_letter_type_display()} - Telah Diambil.",
                )


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    ordering = ("-created_at",)
    list_display = ("id", "user", "title", "is_read", "created_at")
    list_filter = ("is_read",)
    search_fields = ("user__nik", "user__nama", "title", "message")

    readonly_fields = ("user", "title", "message", "created_at", "is_read")
    fields = ("user", "title", "message", "created_at", "is_read")

    def has_add_permission(self, request):
        # Admin tidak boleh bikin notifikasi manual; harus otomatis dari sistem.
        return False

    def has_delete_permission(self, request, obj=None):
        # Optional: biar notifikasi tidak dihapus (audit)
        return False