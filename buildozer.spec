[app]

# Название приложения на рабочем столе
title = HADS Tracker

# Системное имя пакета
package.name = hadstracker

# Домен пакета
package.domain = org.health

# Исходный каталог с файлами
source.dir = .

# Расширения файлов для включения в сборку
source.include_exts = py,png,jpg,kv,atlas

# Версия приложения
version = 1.0.0

# Список зависимостей (только чистый Python и Kivy, fpdf без C-модулей)
requirements = python3,kivy,fpdf

# Ориентация экрана
orientation = portrait

# Системные разрешения Android (сеть для синхронизации и доступ к диску для сохранения PDF/CSV)
android.permissions = WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,INTERNET

# Настройки целевого Android SDK и NDK
android.api = 33
android.minapi = 21
android.ndk = 25b

# Сборка строго под современную 64-битную архитектуру
android.archs = arm64-v8a

# Автоматическое принятие лицензионных соглашений SDK
android.accept_sdk_license = True

# Использование стабильной ветки python-for-android
p4a.branch = master

[buildozer]

# Уровень подробности логов
log_level = 2

# Отключение блокирующего запроса root-прав
warn_on_root = 0
