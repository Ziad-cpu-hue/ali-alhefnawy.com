from django.db import migrations, models


def populate_full_name_and_phone(apps, schema_editor):
    """
    خطوة نقل البيانات:
    - full_name = الاسم الأول + الاسم الأخير (لكل الطلاب الموجودين بالفعل)
    - لو parent_phone_number فاضي، نملأه من phone_number القديم
      (طالما الرقم ده مش مستخدم بالفعل عند طالب تاني كـ parent_phone_number،
       عشان منكسرش قيد unique)
    """
    Student = apps.get_model('accounts', 'Student')

    for student in Student.objects.all():
        first = (getattr(student, 'first_name', '') or '').strip()
        last = (getattr(student, 'last_name', '') or '').strip()
        full_name = f"{first} {last}".strip()
        student.full_name = full_name or "طالب"

        if not student.parent_phone_number:
            old_phone = getattr(student, 'phone_number', None)
            if old_phone:
                collision = (
                    Student.objects.filter(parent_phone_number=old_phone)
                    .exclude(pk=student.pk)
                    .exists()
                )
                if not collision:
                    student.parent_phone_number = old_phone

        # حالة نادرة جدًا: لسه من غير parent_phone_number (تعارض أو مفيش رقم أصلًا)
        # بنحط قيمة مؤقتة فريدة بدل ما الترحيل يفشل بالكامل، وتحتاج مراجعة يدوية
        # من لوحة التحكم بعد كده (هتلاحظها لأنها أرقام غريبة مكرر فيها الـ ID).
        if not student.parent_phone_number:
            student.parent_phone_number = f"000000{student.pk}".rjust(15, '0')[:15]

        student.save()


def reverse_noop(apps, schema_editor):
    # ترحيل بيانات باتجاه واحد فقط (مفيش تراجع تلقائي آمن هنا)
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0019_alter_student_grade_alter_subscription_target_grade'),
    ]

    operations = [
        # 1) أضف full_name مبدئيًا اختياري عشان نقدر نملأه بالبيانات القديمة أول
        migrations.AddField(
            model_name='student',
            name='full_name',
            field=models.CharField(max_length=150, default='', blank=True, verbose_name='الاسم رباعي'),
            preserve_default=False,
        ),

        # 2) انقل البيانات القديمة (الاسم الأول+الأخير -> full_name، ورقم الهاتف -> رقم ولي الأمر لو فاضي)
        migrations.RunPython(populate_full_name_and_phone, reverse_noop),

        # 3) ثبّت full_name كحقل إلزامي (بعد ما اتملى لكل الصفوف)
        migrations.AlterField(
            model_name='student',
            name='full_name',
            field=models.CharField(max_length=150, verbose_name='الاسم رباعي'),
        ),

        # 4) ثبّت parent_phone_number كحقل إلزامي وفريد (بعد ما اتملى لكل الصفوف)
        migrations.AlterField(
            model_name='student',
            name='parent_phone_number',
            field=models.CharField(max_length=15, unique=True, verbose_name='رقم هاتف ولي الأمر'),
        ),

        # 5) احذف الحقول القديمة بعد ما بياناتها اتنقلت بالكامل
        migrations.RemoveField(
            model_name='student',
            name='first_name',
        ),
        migrations.RemoveField(
            model_name='student',
            name='last_name',
        ),
        migrations.RemoveField(
            model_name='student',
            name='phone_number',
        ),
    ]
