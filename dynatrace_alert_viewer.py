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
 
# Parâmetros Dynatrace
DYNATRACE_URL  = "https://dynatrace.acesso.net/e/6hty5y-45d8-5698-86f4-658gjje8f8D/api/v2/problems"
API_TOKEN = "SEU_TOKEN_DE_ACESSO"  # Insira seu token de API

class DynatraceApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dynatrace Alerts Viewer")
        self.setGeometry(200, 200, 800, 600)

        meu_layout = QVBoxLayout()

        date_layout = QHBoxLayout()
        
        # Campo de data de início
        self.start_date_label = QLabel('data de Início:')
        self.start_date_input = QDateTimeEdit()
        self.start_date_input.setDisplayFormat("dd-MM-yyyy HH:mm")
        self.start_date_input.setDateTime(
            datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        )

        # Campo de data de término
        self.end_date_label = QLabel('data de Término:')
        self.end_date_input = QDateTimeEdit()
        self.end_date_input.setDisplayFormat("dd-MM-yyyy HH:mm")
        self.end_date_input.setDateTime(datetime.now())

        # Adicionar os widgets de data/hora ao layout

        date_layout.addWidget(self.start_date_label)
        date_layout.addWidget(self.start_date_input)
        date_layout.addWidget(self.end_date_label)
        date_layout.addWidget(self.end_date_input)
        meu_layout.addLayout(date_layout)  # Adiciona ao layout principal

        # Botões para ações principais
        button_layout = QHBoxLayout()  # Layout horizontal para os botões
        self.load_button = QPushButton("Carregar Dados")  # Botão para carregar dados
        self.load_button.clicked.connect(self.load_data)  # Conecta o clique à função
        self.save_button = QPushButton("Salvar em Excel")  # Botão para salvar em Excel
        self.save_button.clicked.connect(self.save_to_excel)  # Conecta o clique à função
        button_layout.addWidget(self.load_button)
        button_layout.addWidget(self.save_button)
        meu_layout.addLayout(button_layout)  # Adiciona os botões ao layout principal

        # Tabela para exibir os dados carregados
        self.table = QTableWidget()  # Widget de tabela
        meu_layout.addWidget(self.table)  # Adiciona ao layout principal

        # Container principal da interface
        container = QWidget()  # Widget principal
        container.setLayout(meu_layout)  # Define o layout principal no container
        self.setCentralWidget(container)  # Define o container como o widget central

        # Função para buscar problemas na API Dynatrace dentro do intervalo de tempo fornecido
    def get_problems(self, start_time, end_time):
        headers = {"Authorization": f"Api-Token {API_TOKEN}"}  # Cabeçalhos da requisição

        # Conversão de datas para UTC
        start_time_utc = start_time.astimezone(utc)
        end_time_utc = end_time.astimezone(utc)

        # Formatação de datas para ISO 8601
        start_time_str = start_time_utc.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        end_time_str = end_time_utc.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

        params = {"pageSize": 400, "from": start_time_str, "to": end_time_str}  # Parâmetros da API

        # Envia a requisição GET para a API e desativa a verificação SSL
        response = requests.get(
            DYNATRACE_URL, headers=headers, params=params, verify=False
        )
        response.raise_for_status()  # Lança uma exceção em caso de erro na requisição

        problems = response.json().get("problems", [])  # Extrai os problemas da resposta
        return problems  # Retorna a lista de problemas

    # Função para carregar dados da API e exibi-los na tabela
    def load_data(self):
        # Obter datas de entrada no fuso horário local
        local_tz = timezone("America/Sao_Paulo")  # Fuso horário local
        start_time = self.start_date_input.dateTime().toPyDateTime().replace(tzinfo=local_tz)
        end_time = self.end_date_input.dateTime().toPyDateTime().replace(tzinfo=local_tz)

        try:
            # Buscar problemas e processar os dados
            problems = self.get_problems(start_time, end_time)
            data = self.process_data(problems)
            if not data:
                QMessageBox.information(
                    self, "Informação", "Nenhum alerta encontrado no intervalo de tempo selecionado."
                )
            self.populate_table(data)  # Preenche a tabela com os dados processados
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar dados: {e}")

    # Função para processar os problemas retornados pela API e estruturar os dados
    def process_data(self, problems):
        data = []
        for problem in problems:
            affected_entities = problem.get("affectedEntities", [])
            affected_names = [entity.get("name", "N/A") for entity in affected_entities if isinstance(entity, dict)]

            root_cause_entity = problem.get("rootCauseEntity", {})
            root_cause_name = root_cause_entity.get("name", "N/A") if isinstance(root_cause_entity, dict) else "N/A"

            start_time = problem.get("startTime")
            end_time = problem.get("endTime")
            if start_time and end_time:
                duration = (end_time - start_time) // 60000
                duration = f"{duration} min"
            else:
                duration = "N/A"

            data.append(
                {
                    "Problem": problem.get("title", "N/A"),
                    "Impacted": problem.get("impactLevel", "N/A"),
                    "Affected": ", ".join(affected_names),
                    "Root Cause": root_cause_name,
                    "Start Date": (
                        datetime.fromtimestamp(start_time / 1000).strftime("%Y-%m-%d %H:%M:%S")
                        if start_time
                        else "N/A"
                    ),
                    "Duration (min)": duration,
                }
            )
        return data  # Retorna os dados processados

    # Função para preencher a tabela da interface com os dados processados
    def populate_table(self, data):
        self.table.setRowCount(len(data))  # Define o número de linhas na tabela
        self.table.setColumnCount(6)  # Define o número de colunas
        self.table.setHorizontalHeaderLabels(
            ["Problem", "Impacted", "Affected", "Root Cause", "Start Date", "Duration (min)"]
        )  # Define os cabeçalhos das colunas

        for row, item in enumerate(data):
            # Insere os dados processados nas células da tabela
            self.table.setItem(row, 0, QTableWidgetItem(item["Problem"]))
            self.table.setItem(row, 1, QTableWidgetItem(item["Impacted"]))
            self.table.setItem(row, 2, QTableWidgetItem(item["Affected"]))
            self.table.setItem(row, 3, QTableWidgetItem(item["Root Cause"]))
            self.table.setItem(row, 4, QTableWidgetItem(item["Start Date"]))
            self.table.setItem(row, 5, QTableWidgetItem(str(item["Duration (min)"])))

    # Função para salvar os dados exibidos na tabela em um arquivo Excel
    def save_to_excel(self):
        row_count = self.table.rowCount()
        if row_count == 0:  # Verifica se há dados para salvar
            QMessageBox.warning(self, "Aviso", "Não há dados para salvar.")
            return

        # Extrai os dados da tabela para um DataFrame do Pandas
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

        df = pd.DataFrame(data)  # Cria um DataFrame
        filename = "dynatrace_problems.xlsx"  # Nome do arquivo
        df.to_excel(filename, index=False)  # Salva o arquivo Excel
        QMessageBox.information(self, "Sucesso", f"Dados salvos em {filename}")  

# Execução principal do programa
if __name__ == "__main__":
    requests.packages.urllib3.disable_warnings(
        requests.packages.urllib3.exceptions.InsecureRequestWarning
    )  # Suprime avisos de SSL inseguros

    app = QApplication(sys.argv)  # Cria a aplicação PyQt5
    window = DynatraceApp()  # Cria a janela principal
    window.show()  # Exibe a janela
    sys.exit(app.exec_())  # Executa o loop principal do PyQt5
