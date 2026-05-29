# ============================================================
# services/chat_service.py — AI чат-бот через Claude API
# ============================================================

import os
import json
import logging
import re
from sqlalchemy.orm import Session
from typing import List
from models.schemas import ChatMessage
from groq import Groq
from dotenv import load_dotenv
from services.calculator_service import assessment_chances_list
from routers.specialties import get_by_item
from logger_config import app_logging
load_dotenv()
app_logging()
logger = logging.getLogger(__name__)
# Создаём клиент Anthropic (API ключ берётся из переменной окружения)
client = Groq(api_key=os.getenv("GROQ_API_KEY"))



# ============================================================
# Системный промпт — "личность" и знания нашего бота
# ============================================================
SYSTEM_PROMPT = """"Ты — AI-ассистент абитуриента Северо-Казахстанского университета имени Манаша Козыбаева (СКУ им. М. Козыбаева), расположенного в городе Петропавловск, Казахстан.

Твоя задача — помогать абитуриентам выбрать специальность и разобраться с поступлением.

ТВОИ ЗНАНИЯ:

Ты знаешь все специальности университета Козыбаева.

Ты понимаешь систему ЕНТ (Единое Национальное Тестирование) в Казахстане.

Ты знаешь о квотах: общий (general), сельская (rural), для сирот (orphan), для лиц с инвалидностью.

Ты понимаешь систему грантов МОН РК.

Максимальный балл ЕНТ = 140.

ИНСТРУКЦИИ ПО ИСПОЛЬЗОВАНИЮ TOOLS:

Используй get_by_item, когда пользователь спрашивает о доступных специальностях по предметам.

Используй assessment_chances_list, ТОЛЬКО когда у тебя есть и комбинация предметов, и конкретный балл пользователя.

В аргумент item_comb всегда передавай предметы через пробел и плюс, например: 'Физика + Математика'.

В аргумент quota всегда передавай 'общий', если пользователь не указал иное.

ВАЖНО: Если данных для вызова функций недостаточно (нет балла или предметов), НЕ вызывай функцию с пустыми значениями или нулями. Вместо этого вежливо попроси пользователя уточнить недостающую информацию.

Если инструмент вернул данные о шансах — ты ОБЯЗАН озвучить эти цифры и кратко их интерпретировать (высокие, средние или низкие шансы).

СТИЛЬ ОБЩЕНИЯ:

Отвечай на языке пользователя (казахский, русский или оба).

Будь дружелюбным и поддерживающим.

Задавай уточняющие вопросы про интересы и любимые предметы.

Конкретизируй рекомендации исходя из балла ЕНТ, но не давай ложных обещаний о 100% гарантии поступления.

Не упоминай балл пользователя в каждом предложении, делай это только когда это уместно в контексте рассуждения о шансах.


СТРУКТУРА ОТВЕТА:

Пиши короткими абзацами, не используй длинные списки.

Максимум 3-4 предложения на один пункт.

Заканчивай ответ вопросом или призывом к действию.
"""


def get_chat_response(
    message:   str,
    history:   List[ChatMessage],
    db : Session,
    ent_score: int = None
) -> str:
    """
    Отправляет сообщение в Groq API и возвращает ответ.
    
    Аргументы:
        message   — текущее сообщение пользователя
        history   — список предыдущих сообщений [{role, content}]
        ent_score — балл ЕНТ (если пользователь указал в форме)
    
    Возвращает:
        Строку с ответом AI
    """
    tools = [
        {
            "type" : "function",
            "function" : {
                "name" : "assessment_chances_list",
                "description" : "Рассчитать шансы на поступление на основе баллов ент и комбинаций предметов",
                "parameters" : {
                    "type" : "object",
                    "properties" : {
                        "ent_score" : {
                            "type" : "integer",
                            "description" : "ЕНТ балл пользователя (от 0 до 140)"
                        },
                        "item_comb" : {
                            "type" : "string",
                            "description" : "Комбинация предметов строго в формате 'Предмет 1 + Предмет 2' (с пробелами). Пример: 'Биология + География'. Пиши названия предметов КОРРЕКТНО. Не сокращай и не меняй буквы в словах."
                        },
                        "quota" : {
                            "type" : "string",
                            "enum" : ["общий","сельская","сироты","инвалидность"],
                            "description" : "Тип квоты пользователя. Если не указан — использовать 'общий'."
                        }
                    },
                    "required" : ["ent_score", "item_comb", "quota"]
                }
            }
        },
        {
           "type" : "function",
           "function" : {
                "name" : "get_by_item",
                "description" : "Сведения об специальностей в БД",
                "parameters" : {
                    "type" : "object",
                    "properties" : {
                        "item_comb" : {
                            "type" : "string" ,
                            "description" : "Комбинация предметов строго в формате 'Предмет 1 + Предмет 2' (с пробелами). Пример: 'Биология + География'. Пиши названия предметов КОРРЕКТНО. Не сокращай и не меняй буквы в словах." 
                        }
                    },
                    "required" : ["item_comb"]
                }
           }     
        }
    ]
    # Если есть балл ЕНТ — добавляем его в контекст сообщения
    if ent_score is not None:
        enriched_message = f"[Балл ЕНТ пользователя: {ent_score}]\n{message}"
    else:
        enriched_message = message

    # Формируем историю сообщений в формате Groq API
    chat_messages = [{
        "role" : "system",
        "content" : SYSTEM_PROMPT
    }]
    for msg in history:
        chat_messages.append({"role" : msg.role , "content" : msg.content})
    chat_messages.append({"role" : "user" , "content" : enriched_message})


    try:
    # Делаем запрос к Claude API
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=chat_messages,
            tools=tools,
            temperature=0.4,
            max_tokens=1500
        )
    # Возвращаем текст ответа
        message = response.choices[0].message
        if message.tool_calls:
            chat_messages.append(message) 
            for tool_call in message.tool_calls:
                function_name = tool_call.function.name
                args = json.loads(tool_call.function.arguments)

                if "item_comb" in args and args["item_comb"]: 
                    clean_item = re.sub(r'\s+и\s+' , ' + ' , args["item_comb"])
                    args["item_comb"] = clean_item.strip()
                    
                logger.info(f"Бот принял решение использовать {function_name}")
                logger.info(f"Аргументы бота {args}")
                func_output = None
                if function_name == "assessment_chances_list":
                    score = args.get("ent_score")
                    item = args.get("item_comb")
                    quota = args.get("quota") 
                    if score > 0 and item and item.strip() and quota and quota.strip():
                        func_output = assessment_chances_list(
                        **args,
                        db = db
                        )
                    else:
                        func_output = "Ошибка данные неправильно указаны"
                elif function_name == "get_by_item":
                    item_args = args.get("item_comb")
                    if item_args and item_args.strip():
                        func_output = get_by_item(
                        **args,
                        db = db
                        )
                    else:
                        func_output = "Ошибка: не указана комбинация предметов"
                logger.info(f"Результат базы для бота {func_output}")
                chat_messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": function_name,
                    "content": json.dumps(func_output, ensure_ascii=False)
                })
            final_response = client.chat.completions.create(
                model = "llama-3.3-70b-versatile",
                messages = chat_messages
            )
            res_content = final_response.choices[0].message.content
            return res_content if res_content else "Я получил данные , но не смог обработать . Попробуйте уточнить вопрос"
        return message.content if message.content else "Извините, я не совсем понял ваш вопрос."
    except Exception as e:
        print(f"Ошибка при запросе бота {e}")
        return "Повторите попытку"