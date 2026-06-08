# ============================================================
# services/chat_service.py — AI чат-бот через Groq API
# ============================================================

import os
import json
import logging
import re
from typing import List, Optional

from sqlalchemy.orm import Session
from dotenv import load_dotenv
from groq import Groq

from models.schemas import ChatMessage, DEFAULT_LANG, SUPPORTED_LANGS
from services.calculator_service import assessment_chances_list
from routers.specialties import get_by_item
from logger_config import app_logging

load_dotenv()
app_logging()
logger = logging.getLogger(__name__)

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


# ============================================================
# Системный промпт — базовая личность, языкозависимая часть добавляется ниже
# ============================================================
SYSTEM_PROMPT_BASE = """Ты — AI-ассистент абитуриента Северо-Казахстанского университета имени Манаша Козыбаева (СКУ им. М. Козыбаева, англ. Kozybayev University), расположенного в городе Петропавловск, Казахстан.

Твоя задача — помогать абитуриентам выбрать специальность и разобраться с поступлением.

ТВОИ ЗНАНИЯ:

Ты знаешь все специальности университета Козыбаева, на которые в 2025 году выделялись гранты.

Ты понимаешь систему ЕНТ (Единое Национальное Тестирование) в Казахстане.

Ты знаешь действующие квоты МНВО РК: общий конкурс, сельская молодёжь, переселение в приоритетные регионы, многодетные семьи, неполные семьи, дети-сироты, инвалидность I/II/с детства, семья с ребёнком-инвалидом, қандасы, ветераны боевых действий.

Ты понимаешь систему грантов МНВО РК (Министерство науки и высшего образования РК — текущее название, не путай со старым МОН РК).

Максимальный балл ЕНТ = 140.

ПОРОГИ УЧАСТИЯ В КОНКУРСЕ ГРАНТОВ (приказ МНВО РК):
• Педагогические специальности (коды 6B01xxx): минимум 75 баллов.
• Юриспруденция (6B04201): минимум 75 баллов.
• Медицинские специальности (медицина, стоматология, фармация — 6B101xx): минимум 70 баллов.
• Технические, аграрные и прочие специальности: минимум 50 баллов.
Если балл абитуриента ниже порога — он НЕ допускается к конкурсу грантов по этим направлениям. Об этом нужно честно говорить.

ВАЖНО: льготы «после срочной военной службы» в калькуляторе НЕТ. Эти абитуриенты приходят с готовыми сертификатами на грант и попадают в министерский приказ напрямую, к публичному конкурсу не идут — не предлагай этот вариант.

ИНСТРУКЦИИ ПО ИСПОЛЬЗОВАНИЮ TOOLS:

Используй get_by_item, когда пользователь спрашивает о доступных специальностях по предметам.

Используй assessment_chances_list, ТОЛЬКО когда у тебя есть и комбинация предметов, и конкретный балл пользователя.

В аргумент item_comb всегда передавай предметы через пробел и плюс, например: 'Физика + Математика'. ЭТОТ АРГУМЕНТ ВСЕГДА НА РУССКОМ — это технический ключ в базе.

В аргумент quota всегда передавай 'общий', если пользователь не указал иное.

ВАЖНО: Если данных для вызова функций недостаточно (нет балла или предметов), НЕ вызывай функцию с пустыми значениями или нулями. Вместо этого вежливо попроси пользователя уточнить недостающую информацию.

Если инструмент вернул данные о шансах — ты ОБЯЗАН озвучить эти цифры и кратко их интерпретировать (высокие, средние или низкие шансы).

СТИЛЬ ОБЩЕНИЯ:

Будь дружелюбным и поддерживающим.

Задавай уточняющие вопросы про интересы и любимые предметы.

Конкретизируй рекомендации исходя из балла ЕНТ, но не давай ложных обещаний о 100% гарантии поступления.

Не упоминай балл пользователя в каждом предложении, делай это только когда это уместно в контексте рассуждения о шансах.

СТРУКТУРА ОТВЕТА:

Пиши короткими абзацами, не используй длинные списки.

Максимум 3-4 предложения на один пункт.

Заканчивай ответ вопросом или призывом к действию.
"""

LANG_INSTRUCTIONS = {
    "ru": "ВАЖНО: ВСЕГДА отвечай пользователю ТОЛЬКО на русском языке. Если пользователь пишет на другом языке — всё равно ОТВЕЧАЙ на русском.",
    "kk": "МАҢЫЗДЫ: пайдаланушыға ТЕК қазақ тілінде жауап бер. Егер пайдаланушы басқа тілде жазса да — жауап ҚАЗАҚ тілінде ғана болуы тиіс.",
    "en": "IMPORTANT: ALWAYS reply to the user ONLY in English. Even if the user writes in another language — answer in English.",
}


def _resolve_lang(lang: Optional[str]) -> str:
    if lang and lang.lower() in SUPPORTED_LANGS:
        return lang.lower()
    return DEFAULT_LANG


def get_chat_response(
    message:   str,
    history:   List[ChatMessage],
    db:        Session,
    ent_score: Optional[int] = None,
    lang:      Optional[str] = None,
) -> str:
    """Отправляет сообщение в Groq API и возвращает ответ на нужном языке."""
    lang = _resolve_lang(lang)

    tools = [
        {
            "type": "function",
            "function": {
                "name": "assessment_chances_list",
                "description": "Рассчитать шансы на поступление на основе баллов ЕНТ и комбинаций предметов",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "ent_score": {
                            "type": "integer",
                            "description": "ЕНТ балл пользователя (от 0 до 140)"
                        },
                        "item_comb": {
                            "type": "string",
                            "description": "Комбинация предметов строго в формате 'Предмет 1 + Предмет 2' (с пробелами). Пример: 'Биология + География'. ВСЕГДА НА РУССКОМ ЯЗЫКЕ. Пиши названия предметов КОРРЕКТНО."
                        },
                        "quota": {
                            "type": "string",
                            "enum": [
                                "общий", "сельская", "rural_move",
                                "large_family", "single_parent",
                                "orphan", "disability_self", "disability_family",
                                "kazakh_diaspora", "veteran"
                            ],
                            "description": "Код квоты пользователя. Если не указан — использовать 'общий'. Льготы 'conscript' (после срочной службы) НЕ существует — не используй её."
                        }
                    },
                    "required": ["ent_score", "item_comb", "quota"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_by_item",
                "description": "Сведения о специальностях по комбинации предметов",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "item_comb": {
                            "type": "string",
                            "description": "Комбинация предметов строго в формате 'Предмет 1 + Предмет 2' (с пробелами). Пример: 'Биология + География'. ВСЕГДА НА РУССКОМ ЯЗЫКЕ."
                        }
                    },
                    "required": ["item_comb"]
                }
            }
        }
    ]

    enriched_message = message
    if ent_score is not None:
        enriched_message = f"[Балл ЕНТ пользователя: {ent_score}]\n{message}"

    system_prompt = SYSTEM_PROMPT_BASE + "\n\n" + LANG_INSTRUCTIONS[lang]

    chat_messages = [{"role": "system", "content": system_prompt}]
    for msg in history:
        chat_messages.append({"role": msg.role, "content": msg.content})
    chat_messages.append({"role": "user", "content": enriched_message})

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=chat_messages,
            tools=tools,
            temperature=0.4,
            max_tokens=1500,
        )
        message_obj = response.choices[0].message

        if message_obj.tool_calls:
            chat_messages.append(message_obj)
            for tool_call in message_obj.tool_calls:
                function_name = tool_call.function.name
                args = json.loads(tool_call.function.arguments)

                # нормализация "и" → " + "
                if "item_comb" in args and args["item_comb"]:
                    clean_item = re.sub(r"\s+и\s+", " + ", args["item_comb"])
                    args["item_comb"] = clean_item.strip()

                logger.info("Бот вызывает tool=%s args=%s lang=%s", function_name, args, lang)

                func_output = None
                if function_name == "assessment_chances_list":
                    score = args.get("ent_score")
                    item = args.get("item_comb")
                    quota = args.get("quota")
                    if score and score > 0 and item and item.strip() and quota and quota.strip():
                        func_output = assessment_chances_list(
                            db=db,
                            ent_score=score,
                            item_comb=item,
                            quota=quota,
                            lang=lang,
                        )
                    else:
                        func_output = {"error": "недостаточно данных"}
                elif function_name == "get_by_item":
                    item_args = args.get("item_comb")
                    if item_args and item_args.strip():
                        func_output = get_by_item(item_comb=item_args, lang=lang, db=db)
                    else:
                        func_output = {"error": "не указана комбинация предметов"}

                chat_messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": function_name,
                    "content": json.dumps(func_output, ensure_ascii=False, default=str),
                })

            final_response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=chat_messages,
            )
            res_content = final_response.choices[0].message.content
            return res_content or "Я получил данные, но не смог обработать. Попробуйте уточнить вопрос."

        return message_obj.content or "Извините, я не совсем понял ваш вопрос."

    except Exception as e:
        logger.exception("Ошибка при запросе бота: %s", e)
        return "Повторите попытку"
