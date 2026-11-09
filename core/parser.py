
import base64, json, os
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL") or None,
)
MODEL = os.getenv("MODEL", "gpt-4o-mini")

PROMPT = """أنت محلل فواتير تداول من البورصة المصرية.
استخرج من صورة الفاتورة كل عملية بيع أو شراء في جدول، وأرجع النتيجة JSON فقط بصيغة:
{"transactions":[{"date":"YYYY-MM-DD","stock":"اسم السهم","side":"شراء أو بيع","price":رقم,"qty":رقم,"commission":رقم أو null}]}
- date: تاريخ العملية، إن لم يوجد استخدم تاريخ اليوم
- side: "شراء" أو "بيع" حرفياً
- price: سعر السهم الواحد بالجنيه
- qty: عدد الأسهم
- commission: قيمة العمولة المكتوبة في الفاتورة بالجنيه، إن لم تكن موجودة اجعلها null
أرجع JSON فقط بدون أي شرح."""

def parse_invoice(image_bytes: bytes) -> list:
    b64 = base64.b64encode(image_bytes).decode()
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": [
            {"type": "text", "text": PROMPT},
            {"type": "image_url",
             "image_url": {"url": f"data:image/png;base64,{b64}"}},
        ]}],
        response_format={"type": "json_object"},
        temperature=0,
    )
    data = json.loads(resp.choices[0].message.content)
    return data.get("transactions", [])
