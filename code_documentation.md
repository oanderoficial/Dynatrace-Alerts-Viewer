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

## DynatraceApp

```python
class DynatraceApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dynatrace Alerts Viewer")
        self.setGeometry(200, 200, 800, 600)

        # Layout principal
        main_layout = QVBoxLayout()

        # Campos de data/hora
        date_layout = QHBoxLayout()

        self.start_date_label = QLabel("Data de Início:")
        self.start_date_input = QDateTimeEdit()
        self.start_date_input.setDisplayFormat("yyyy-MM-dd HH:mm")
        self.start_date_input.setDateTime(
            datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        )

        self.end_date_label = QLabel("Data de Término:")
        self.end_date_input = QDateTimeEdit()
        self.end_date_input.setDisplayFormat("yyyy-MM-dd HH:mm")
        self.end_date_input.setDateTime(datetime.now())

        date_layout.addWidget(self.start_date_label)
        date_layout.addWidget(self.start_date_input)
        date_layout.addWidget(self.end_date_label)
        date_layout.addWidget(self.end_date_input)

        main_layout.addLayout(date_layout)

        # Botões
        button_layout = QHBoxLayout()
        self.load_button = QPushButton("Carregar Dados")
        self.load_button.clicked.connect(self.load_data)
        self.save_button = QPushButton("Salvar em Excel")
        self.save_button.clicked.connect(self.save_to_excel)
        button_layout.addWidget(self.load_button)
        button_layout.addWidget(self.save_button)

        main_layout.addLayout(button_layout)

        # Tabela para exibir dados
        self.table = QTableWidget()
        main_layout.addWidget(self.table)

        # Widget principal
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    def get_problems(self, start_time, end_time):
        headers = {"Authorization": f"Api-Token {API_TOKEN}"}

        # Converter datas para UTC
        start_time_utc = start_time.astimezone(utc)
        end_time_utc = end_time.astimezone(utc)

        # Formatar as datas corretamente para ISO 8601 com milissegundos
        start_time_str = start_time_utc.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        end_time_str = end_time_utc.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

        params = {"pageSize": 400, "from": start_time_str, "to": end_time_str}

        # Desativar a verificação SSL
        response = requests.get(
            DYNATRACE_BASE_URL, headers=headers, params=params, verify=False
        )
        response.raise_for_status()

        problems = response.json().get("problems", [])

        return problems

    def load_data(self):
        # Obter datas de entrada e converter para UTC
        local_tz = timezone(
            "America/Sao_Paulo"
        )  # Substitua pelo fuso horário correto, se necessário
        start_time = (
            self.start_date_input.dateTime().toPyDateTime().replace(tzinfo=local_tz)
        )
        end_time = (
            self.end_date_input.dateTime().toPyDateTime().replace(tzinfo=local_tz)
        )

        try:
            problems = self.get_problems(start_time, end_time)
            data = self.process_data(problems)
            if not data:
                QMessageBox.information(
                    self,
                    "Informação",
                    "Nenhum alerta encontrado no intervalo de tempo selecionado.",
                )
            self.populate_table(data)
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar dados: {e}")

    def process_data(self, problems):
        data = []
        for problem in problems:
            # Extrair apenas os nomes das entidades afetadas, garantindo que cada item seja um dicionário
            affected_entities = problem.get("affectedEntities", [])
            affected_names = [
                entity.get("name", "N/A")
                for entity in affected_entities
                if isinstance(entity, dict)
            ]

            # Verificar se "rootCauseEntity" existe e é um dicionário antes de tentar acessar
            root_cause_entity = problem.get("rootCauseEntity", {})
            root_cause_name = (
                root_cause_entity.get("name", "N/A")
                if isinstance(root_cause_entity, dict)
                else "N/A"
            )

            # Calcular a duração em minutos, se ambos "startTime" e "endTime" estiverem presentes
            start_time = problem.get("startTime")
            end_time = problem.get("endTime")
            if start_time and end_time:
                duration = (
                    end_time - start_time
                ) // 60000  # Converte de milissegundos para minutos
                duration = f"{duration} min"
            else:
                duration = "N/A"

            data.append(
                {
                    "Problem": problem.get(
                        "title", "N/A"
                    ),  # Usar "title" em vez de "displayName"
                    "Impacted": problem.get("impactLevel", "N/A"),
                    "Affected": ", ".join(affected_names),
                    "Root Cause": root_cause_name,
                    "Start Date": (
                        datetime.fromtimestamp(start_time / 1000).strftime(
                            "%Y-%m-%d %H:%M:%S"
                        )
                        if start_time
                        else "N/A"
                    ),
                    "Duration (min)": duration,
                }
            )
        return data

    def populate_table(self, data):
        self.table.setRowCount(len(data))
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            [
                "Problem",
                "Impacted",
                "Affected",
                "Root Cause",
                "Start Date",
                "Duration (min)",
            ]
        )

        for row, item in enumerate(data):
            self.table.setItem(row, 0, QTableWidgetItem(item["Problem"]))
            self.table.setItem(row, 1, QTableWidgetItem(item["Impacted"]))
            self.table.setItem(row, 2, QTableWidgetItem(item["Affected"]))
            self.table.setItem(row, 3, QTableWidgetItem(item["Root Cause"]))
            self.table.setItem(row, 4, QTableWidgetItem(item["Start Date"]))
            self.table.setItem(row, 5, QTableWidgetItem(str(item["Duration (min)"])))

    def save_to_excel(self):
        row_count = self.table.rowCount()
        if row_count == 0:
            QMessageBox.warning(self, "Aviso", "Não há dados para salvar.")
            return

        data = []
        for row in range(row_count):
            data.append(
                {
                    "Problem": self.table.item(row, 0).text(),
                    "Impacted": self.table.item(row, 1).text(),
                    "Affected": self.table.item(row, 2).text(),
                    "Root Cause": self.table.item(row, 3).text(),
                    "Start Date": self.table.item(row, 4).text(),
                    "Duration (min)": self.table.item(row, 5).text(),
                }
            )

        df = pd.DataFrame(data)
        filename = "dynatrace_problems.xlsx"
        df.to_excel(filename, index=False)
        QMessageBox.information(self, "Sucesso", f"Dados salvos em {filename}")
```
