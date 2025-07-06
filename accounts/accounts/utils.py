import re
from datetime import datetime, timedelta
from PIL import Image
import pytesseract, piexif, imagehash
from .models import PaymentRequest

def verify_payment_request(req: PaymentRequest):
    # 1) قم بفتح الصورة وقراءة النص
    img = Image.open(req.screenshot.path)
    text = pytesseract.image_to_string(img)

    # 2) تأكد من المبلغ العشري الفريد
    if not re.search(rf'\b{float(req.amount_required)}\b', text):
        return False, "المبلغ غير مطابق"

    # 3) تأكد من رقم المعاملة
    if req.txn_id and not re.search(rf'\b{req.txn_id}\b', text):
        return False, "رقم المعاملة غير موجود"

    # 4) تحقق من EXIF Timestamp
    try:
        exif = piexif.load(req.screenshot.path)['0th']
        dt_bytes = exif.get(piexif.ImageIFD.DateTime)
        dt_str = dt_bytes.decode() if isinstance(dt_bytes, bytes) else dt_bytes
        pic_time = datetime.strptime(dt_str, '%Y:%m:%d %H:%M:%S')
        if abs(pic_time - req.created_at) > timedelta(minutes=15):
            return False, "الصورة ليست حديثة"
    except Exception:
        return False, "بيانات EXIF غير صالحة"

    # 5) Perceptual Hash
    ph = imagehash.phash(img)
    accepted = PaymentRequest.objects.filter(paid=True).exclude(_phash__isnull=True)
    for prev in accepted:
        prev_ph = imagehash.hex_to_hash(prev._phash)
        if ph - prev_ph < 5:
            return False, "الصورة مكررة أو معدّلة"
    # لو نجح، خزن البصمة
    req._phash = str(ph)
    return True, "نجحت كل الفحوص"
