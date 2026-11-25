# Вместе в школу

Интерактивный дашборд на Python и Dash для варианта № 17 «Процесс управления социальными проектами». Он показывает взносы по СБП, закупки фонда, выдачу школьных вещей и отправку отчётов. Графики и таблица обновляются при выборе периода, категории и способа помощи.

- [Код и инструкция по использованию](https://github.com/art1162/DashBoard/tree/release)
- [Пример CSV для загрузки](https://github.com/art1162/DashBoard/blob/release/data/example.csv)
- [Коммиты разработки](https://github.com/art1162/DashBoard/commits/test/)

## Быстрый запуск на Windows

Для запуска нужен Python 3.12 или совместимая версия.

```powershell
git clone --branch release https://github.com/art1162/DashBoard.git
cd DashBoard
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

Откройте [дашборд](http://127.0.0.1:8050/). Нажмите **Загрузить CSV** и выберите `data/example.csv`. В файле 537 синтетических операций по пяти категориям школьных вещей.
