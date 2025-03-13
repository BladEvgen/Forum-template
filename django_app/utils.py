import re
import pytz
from django_app import models
from django.urls import reverse
from django.conf import settings
from django.core.mail import send_mail
from django.utils.html import format_html


def transliterate(name):
    slovar = {
        "а": "a",
        "б": "b",
        "в": "v",
        "г": "g",
        "д": "d",
        "е": "e",
        "ё": "yo",
        "ж": "zh",
        "з": "z",
        "и": "i",
        "й": "y",
        "к": "k",
        "л": "l",
        "м": "m",
        "н": "n",
        "о": "o",
        "п": "p",
        "р": "r",
        "с": "s",
        "т": "t",
        "у": "u",
        "ф": "f",
        "х": "h",
        "ц": "ts",
        "ч": "ch",
        "ш": "sh",
        "щ": "sch",
        "ъ": "",
        "ы": "y",
        "ь": "",
        "э": "e",
        "ю": "yu",
        "я": "ya",
        " ": " ",
        "-": "-",
        ".": ".",
        ",": ",",
        "!": "!",
        "?": "?",
        ":": ":",
    }

    name = name.lower()
    translit = []
    for letter in name:
        translit.append(slovar.get(letter, letter))

    return "".join(translit)


def password_check(password: str) -> bool:
    return (
        True
        if re.match(
            r"^(?=.*?[A-Z])(?=.*?[a-z])(?=.*?[0-9])(?=.*?[#?!@$%^&*-]).{8,}$", password
        )
        is not None
        else False
    )


def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0].strip()
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


def get_user_timezone(request):
    user_timezone = request.session.get("timezone")
    if not user_timezone:
        user_timezone = settings.TIME_ZONE
    return pytz.timezone(user_timezone)


def send_password_reset_email(user, request):
    reset_link = f"{request.scheme}://{request.get_host()}{reverse('password_reset_confirm', args=[models.PasswordResetToken.generate_token(user)])}"

    subject = "Инструкция по сбросу пароля"
    html_message = format_html(
        """
        <!DOCTYPE html>
        <html lang="ru">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Сброс пароля</title>
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700&display=swap');
                
                body, table, td, a {{ font-family: 'Montserrat', 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif; }}
                
                @media only screen and (max-width: 620px) {{
                    .email-container {{ width: 100% !important; }}
                    .button {{ width: 100% !important; }}
                }}
            </style>
        </head>
        <body style="margin: 0; padding: 0; background-color: #f7f7f7; color: #333333;">
            <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color: #f7f7f7;">
                <tr>
                    <td style="padding: 20px 0;">
                        <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="600" align="center" class="email-container" style="border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
                            <!-- Header -->
                            <tr>
                                <td style="background-color: #7C3AED; padding: 30px 40px; text-align: center;">
                                    <h1 style="margin: 0; font-size: 28px; color: white; font-weight: 600;">Восстановление пароля</h1>
                                </td>
                            </tr>
                            
                            <!-- Content -->
                            <tr>
                                <td style="background-color: #ffffff; padding: 40px;">
                                    <h2 style="margin-top: 0; margin-bottom: 20px; font-size: 22px; color: #333333;">Здравствуйте, {username}!</h2>
                                    
                                    <p style="margin: 0 0 25px; font-size: 16px; line-height: 1.6; color: #4B5563;">
                                        Мы получили запрос на сброс пароля для вашего аккаунта. Чтобы задать новый пароль, нажмите на кнопку ниже:
                                    </p>
                                    
                                    <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" style="margin-bottom: 30px;">
                                        <tr>
                                            <td align="center">
                                                <a href="{reset_link}" target="_blank" class="button" style="display: inline-block; background-color: #7C3AED; color: #ffffff; text-decoration: none; padding: 16px 32px; border-radius: 8px; font-size: 16px; font-weight: 600; transition: background-color 0.3s ease;">Сбросить пароль</a>
                                            </td>
                                        </tr>
                                    </table>
                                    
                                    <p style="margin: 0 0 15px; font-size: 16px; line-height: 1.6; color: #4B5563;">
                                        Если кнопка не работает, вы можете скопировать следующую ссылку и вставить её в адресную строку браузера:
                                    </p>
                                    
                                    <p style="margin: 0 0 30px; padding: 15px; background-color: #F3F4F6; border-radius: 8px; word-break: break-all; font-size: 14px; line-height: 1.5; color: #4B5563;">
                                        {reset_link}
                                    </p>
                                    
                                    <div style="margin: 30px 0; padding: 20px; background-color: #FEF3C7; border-left: 4px solid #F59E0B; border-radius: 4px;">
                                        <p style="margin: 0; font-size: 16px; line-height: 1.6; color: #92400E;">
                                            <strong>Важная информация:</strong><br>
                                            • Ссылка действительна в течение <strong>1 часа</strong><br>
                                            • Если вы не запрашивали сброс пароля, проигнорируйте это письмо<br>
                                            • Для безопасности не передавайте эту ссылку другим лицам
                                        </p>
                                    </div>
                                    
                                    <p style="margin: 25px 0 0; font-size: 16px; line-height: 1.6; color: #4B5563;">
                                        С уважением,<br>
                                        Команда Travel Community
                                    </p>
                                </td>
                            </tr>
                            
                            <!-- Footer -->
                            <tr>
                                <td style="background-color: #F9FAFB; padding: 30px 40px; text-align: center; border-top: 1px solid #E5E7EB;">
                                    <p style="margin: 0 0 15px; font-size: 14px; line-height: 1.6; color: #6B7280;">
                                        Если у вас возникли вопросы, вы можете связаться с нами по адресу <a href="mailto:support@example.com" style="color: #7C3AED; text-decoration: none;">support@example.com</a>
                                    </p>
                                    
                                    <p style="margin: 0; font-size: 13px; line-height: 1.6; color: #9CA3AF;">
                                        © 2025 Travel Community. Все права защищены.
                                    </p>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """,
        username=user.username,
        reset_link=reset_link,
    )

    plain_message = (
        f"Здравствуйте, {user.username}!\n\n"
        "Вы получили это письмо, потому что был запрошен сброс пароля для вашего аккаунта.\n\n"
        f"Для сброса пароля перейдите по следующей ссылке: {reset_link}\n\n"
        "Эта ссылка будет действительна в течение 1 часа. Для вашей безопасности не передавайте эту ссылку другим лицам.\n\n"
        "Если вы не запрашивали сброс пароля, проигнорируйте это письмо, и ваш пароль останется неизменным.\n\n"
        "С уважением,\n"
        "Команда Travel Community"
    )

    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        html_message=html_message,
    )
