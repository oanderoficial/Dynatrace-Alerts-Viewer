# Code Documentation 

## Bibliotecas utilizadas

```python
import sys
import requests
import pandas as pd
from datetime import datetime, timedelta
from pytz import timezone, utc
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QDateTimeEdit,
)
from PyQt5.QtCore import Qt

```

## Parâmetros de acesso Dynatrace 

```python
DYNATRACE_BASE_URL = "https://dynatrace.seu.ambiente.net/e/Ae54fe67-5567-46yu-86f4-56b25d5hji78/api/v2/problems"
API_TOKEN = " "  # Insira seu token de API
```
