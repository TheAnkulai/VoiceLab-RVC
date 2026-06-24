# VoiceLab-RVC

VoiceLab-RVC — это очищенная локальная сборка RVC inference с собственным PySide6-интерфейсом.  
Проект предназначен для запуска готовых RVC `.pth` моделей на Windows CPU без оригинального Gradio WebUI, обучения, UVR и ONNX-экспорта.

## Возможности

- запуск готовых RVC-моделей через desktop GUI;
- запуск inference через CLI-скрипт;
- поддержка F0-методов `pm`, `harvest`, `rmvpe`;
- вывод процесса в консоль внутри GUI;
- работа без `.env` файла за счёт fallback-путей в `rvc_infer_cli.py`;
- CPU-сборка на `torch==2.1.2+cpu`.

## Структура проекта

```text
VoiceLab-RVC/
  assets/
    hubert/
      hubert_base.pt
    rmvpe/
      rmvpe.pt
    weights/
      *.pth

  configs/
  infer/
  logs/
    *.index

  inputs/
  outputs/
  TEMP/

  rvc_gui.py
  rvc_infer_cli.py
  download_models.py
  run_gui.bat
  requirements_base_no_torch.txt
```

## Требования

- Windows 10/11;
- Python 3.10;
- установленный FFmpeg и доступный из PATH;
- Microsoft C++ Build Tools, если `fairseq` или некоторые зависимости придётся собирать из исходников.

Проверить Python:

```powershell
py -3.10 --version
```

Проверить FFmpeg:

```powershell
ffmpeg -version
```

## Подготовка окружения

Перейти в папку проекта:

```powershell
F:
cd F:\VoiceLab\VoiceLab-RVC
```

Создать виртуальное окружение:

```powershell
py -3.10 -m venv .venv
.venv\Scripts\activate
```

Понизить `pip` до версии 24.0. Это важно для старых зависимостей RVC, особенно `omegaconf` / `fairseq`.

```powershell
python -m pip install pip==24.0
python -m pip install setuptools wheel
```

## Установка зависимостей

Сначала ставятся базовые зависимости без PyTorch, `fairseq` и пакетов, которые могут подтянуть неправильную версию `torch`:

```powershell
python -m pip install -r requirements_cpu.txt
```

Затем отдельно ставится CPU-версия PyTorch:

```powershell
python -m pip install torch==2.1.2+cpu torchvision==0.16.2+cpu torchaudio==2.1.2+cpu --index-url https://download.pytorch.org/whl/cpu
```

Затем `fairseq` ставится без зависимостей, чтобы он не подтянул свежий `torch`:

```powershell
python -m pip install fairseq==0.12.2 --no-deps
```

Затем `torchcrepe` ставится без зависимостей, потому что RVC `pipeline.py` импортирует его на верхнем уровне, даже если метод `crepe` не используется:

```powershell
python -m pip install torchcrepe==0.0.20 --no-deps
```

Важно: не устанавливать `fairseq` и `torchcrepe` обычной командой без `--no-deps`, иначе pip может подтянуть несовместимую версию `torch`.

## Проверка окружения

После установки проверить версии и импорты:

```powershell
python -c "import torch; print(torch.__version__)"
python -c "import torchaudio; print(torchaudio.__version__)"
python -c "import torchvision; print(torchvision.__version__)"
python -c "import fairseq; print('fairseq OK')"
python -c "import faiss; print('faiss OK')"
python -c "import pyworld; print('pyworld OK')"
python -c "import torchcrepe; print('torchcrepe OK')"
python -c "import PySide6; print('PySide6 OK')"
```

Ожидаемые версии:

```text
torch:       2.1.2+cpu
torchaudio:  2.1.2+cpu
torchvision: 0.16.2+cpu
```

## Загрузка базовых моделей

Перед первым запуском нужно скачать:

- `assets/hubert/hubert_base.pt`;
- `assets/rmvpe/rmvpe.pt`.

Для этого используется скрипт:

```powershell
python download_models.py
```

Принудительно перекачать файлы:

```powershell
python download_models.py --force
```

Скачать только HuBERT без RMVPE:

```powershell
python download_models.py --no-rmvpe
```

После загрузки должны существовать файлы:

```text
assets/hubert/hubert_base.pt
assets/rmvpe/rmvpe.pt
```

## Добавление RVC-моделей

Готовые модели `.pth` нужно положить в:

```text
assets/weights/
```

Пример:

```text
assets/weights/NecoArcRu.pth
```

После запуска GUI модели появятся в списке. Если модель была добавлена во время работы приложения, нажать кнопку обновления списка моделей и индексов.

## Добавление индексов

Файлы `.index` нужно положить в:

```text
logs/
```

Пример:

```text
logs/added_IVF677_Flat_nprobe_1_Neco-Arc_v2.index
```

Index необязателен. Можно запускать преобразование с пустым index и `index-rate = 0`.

## Запуск GUI

Через PowerShell:

```powershell
python rvc_gui.py
```

Или двойным кликом через:

```text
run_gui.bat
```

Содержимое `run_gui.bat`:

```bat
@echo off
cd /d "%~dp0"
call .venv\Scripts\activate
python rvc_gui.py
```

## Использование GUI

1. Выбрать модель в поле `Желаемый голос`.
2. Выбрать index, если он нужен.
3. Выбрать входной аудиофайл.
4. Указать выходной `.wav`.
5. Выбрать F0 method:
   - `pm` — быстрый вариант;
   - `harvest` — более медленный, стабильный CPU-вариант;
   - `rmvpe` — качественный вариант, использует `assets/rmvpe/rmvpe.pt`.
6. Нажать `Преобразовать`.
7. Следить за процессом в консоли снизу.

Во время преобразования основные элементы интерфейса блокируются, чтобы параметры не менялись в середине процесса.

## Запуск через CLI

Пример без index:

```powershell
python rvc_infer_cli.py `
  --model "NecoArcRu.pth" `
  --input "F:\VoiceLab\VoiceLab-RVC\inputs\input.wav" `
  --output "F:\VoiceLab\VoiceLab-RVC\outputs\output.wav" `
  --f0-method pm `
  --index-rate 0
```

Пример с index:

```powershell
python rvc_infer_cli.py `
  --model "NecoArcRu.pth" `
  --input "F:\VoiceLab\VoiceLab-RVC\inputs\input.wav" `
  --output "F:\VoiceLab\VoiceLab-RVC\outputs\output.wav" `
  --index "logs\added_IVF677_Flat_nprobe_1_Neco-Arc_v2.index" `
  --f0-method harvest `
  --index-rate 0.7
```

## Важные особенности установки

### Почему PyTorch ставится отдельно

Некоторые старые и дополнительные RVC-зависимости могут попытаться подтянуть свежий `torch`, например:

- `fairseq`;
- `torchcrepe`;
- `local-attention`;
- `hyper-connections`;
- `torchfcpe`.

Для этой сборки нужна версия:

```text
torch==2.1.2+cpu
```

Поэтому PyTorch ставится отдельной командой из CPU-индекса PyTorch, а `fairseq` и `torchcrepe` ставятся с `--no-deps`.

### Почему `pip==24.0`

Старый стек RVC использует зависимости с устаревшими metadata. Более новые версии pip могут отказываться устанавливать некоторые старые пакеты, например `omegaconf==2.0.6`.

## Минимально нужные assets

Для обычного inference нужны:

```text
assets/weights/*.pth
assets/hubert/hubert_base.pt
assets/rmvpe/rmvpe.pt
logs/*.index
```

`assets/rmvpe/rmvpe.pt` нужен только для метода `rmvpe`.

## Что было удалено из оригинального RVC

В этой сборке не используются:

- Gradio WebUI;
- обучение моделей;
- UVR;
- ONNX export;
- pretrained-модели для обучения;
- realtime RVC;
- IPEX/XPU ветки;
- лишние test/export inputs.

## Возможные проблемы

### `torch` стал версии 2.12.x

Нужно вернуть правильный стек:

```powershell
python -m pip uninstall torch torchvision torchaudio -y
python -m pip install torch==2.1.2+cpu torchvision==0.16.2+cpu torchaudio==2.1.2+cpu --index-url https://download.pytorch.org/whl/cpu
```

### `ModuleNotFoundError: torchcrepe`

Установить без зависимостей:

```powershell
python -m pip install torchcrepe==0.0.20 --no-deps
```

### `rmvpe` не находит модель

Проверить, что файл существует:

```text
assets/rmvpe/rmvpe.pt
```

## Текущий статус

- Windows CPU inference работает.
- GUI работает.
- CLI inference работает.
- `.env` файл не обязателен.
- Поддерживаются `pm`, `harvest`, `rmvpe`.
