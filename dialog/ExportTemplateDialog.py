from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon


class ExportTemplateDialog(QDialog):
    def __init__(self, export_type_list, type_mask_dict):
        super().__init__()
        self.export_type_set = export_type_list
        self.type_mask_dict = type_mask_dict

        # 设置对话框属性
        self.setWindowTitle('编辑导出模板')

        self.template_table = QTableWidget()
        self.createTemplateTable()

        self.check_button = QPushButton('检查')
        self.export_button = QPushButton('导出')

        self.initUI()

    def initUI(self):
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.check_button)
        button_layout.addStretch()
        button_layout.addWidget(self.export_button)
        button_layout.addStretch()

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.template_table)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

    def createTemplateTable(self):
        self.template_table.setColumnCount(4)
        self.template_table.setRowCount(len(self.export_type_set))
        self.template_table.setHorizontalHeaderLabels(['装置指纹', '站控层GOOSE模板', '过程层SV模板', '过程层GOOSE模板'])
        for index, ied_type in enumerate(self.export_type_set):
            self.template_table.setItem(index, 0, QTableWidgetItem(ied_type))
            unzip_type_mask = tuple(map(lambda x: self.type_mask_dict[ied_type] & x, [0x04, 0x02, 0x01]))
            for column_index, editable_flag in enumerate(unzip_type_mask):
                item_flag = self.template_table.item(index, column_index + 1).flags() & (editable_flag << 2)
                self.template_table.item(index, column_index + 1).setFlags()