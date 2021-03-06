import re
import json
import os
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from pyscl.SCL import SCL
from exportmethods import *
import xlsxwriter
from functools import reduce
from .ExportTemplateDialog import ExportTemplateDialog
from .ClassificationDialog import ClassificationDialog
from GlobalConfig import GlobalConfig


class IedSelectDialog(QDialog):
    def __init__(self, ied_list, scd_file_path, ied_count):
        super().__init__()
        self.ied_list = ied_list
        self.scd_file_path = scd_file_path
        self.ied_count = ied_count
        self.ied_table = QTableWidget()
        self.ied_table.itemClicked.connect(self.editRegularCombobox)
        self.ied_table.itemChanged.connect(self.checkIedSelected)

        self.filter_item_label = QLabel("过滤选项")
        self.filter_item_combobox = QComboBox()
        self.filter_item_combobox.addItem("装置名称")
        self.filter_item_combobox.addItem("装置描述")
        self.filter_item_combobox.addItem("装置型号")
        self.filter_item_combobox.addItem("生产厂商")
        self.filter_item_combobox.currentIndexChanged.connect(self.refreshFilter)
        self.filter_item_label.setBuddy(self.filter_item_combobox)
        self.filter_lineedit = QLineEdit()
        self.filter_lineedit.setPlaceholderText("过滤器")
        self.filter_lineedit.textChanged.connect(self.refreshFilter)

        self.process_unchecked_item_btn = QPushButton("隐藏非选中项")
        self.process_unchecked_item_btn.clicked.connect(self.processUncheckedRow)
        self.select_all_btn = QPushButton("全选")
        self.select_all_btn.clicked.connect(self.selectAllVisibleRow)
        self.cancel_select_all_btn = QPushButton("取消全选")
        self.cancel_select_all_btn.clicked.connect(self.cancelSelectAllVisibleRow)
        self.export_btn = QPushButton("导出")
        self.export_btn.clicked.connect(self.exportLinkTable)
        self.quit_btn = QPushButton("退出")
        self.quit_btn.clicked.connect(self.close)

        self.statusBar = QStatusBar()
        self.checked_item_count_label = QLabel("当前选中项目个数: ")
        self.checked_item_count_label.setFrameShape(QFrame.WinPanel)
        self.checked_item_count_label.setFrameShadow(QFrame.Sunken)
        self.statusBar.addWidget(self.checked_item_count_label)
        self.checked_item_count = QLabel("0")
        self.checked_item_count.setFixedWidth(40)
        self.checked_item_count.setAlignment(Qt.AlignCenter)
        self.checked_item_count.setFrameShape(QFrame.WinPanel)
        self.checked_item_count.setFrameShadow(QFrame.Sunken)
        self.statusBar.addWidget(self.checked_item_count)
        self.visible_item_count_label = QLabel("当前显示项目个数：")
        self.visible_item_count_label.setFrameShape(QFrame.WinPanel)
        self.visible_item_count_label.setFrameShadow(QFrame.Sunken)
        self.statusBar.addWidget(self.visible_item_count_label)
        self.visible_item_count = QLabel("0")
        self.visible_item_count.setFixedWidth(40)
        self.visible_item_count.setAlignment(Qt.AlignCenter)
        self.visible_item_count.setFrameShape(QFrame.WinPanel)
        self.visible_item_count.setFrameShadow(QFrame.Sunken)
        self.statusBar.addWidget(self.visible_item_count)
        self.operate_str = QLabel("等待")
        self.operate_str.setFrameShape(QFrame.WinPanel)
        self.operate_str.setFrameShadow(QFrame.Sunken)
        self.statusBar.addWidget(self.operate_str, 1)
        self.operate_progress = QProgressBar()
        self.operate_progress.setTextVisible(False)
        operate_progress_style = """
        QProgressBar::chunk {
            background-color: #3333FF;
            width: 10px;
            margin: 1px;
        }
        """
        self.operate_progress.setStyleSheet(operate_progress_style)
        self.operate_progress.setFixedWidth(200)
        self.statusBar.addWidget(self.operate_progress)

        self.pop_menu = QMenu()
        self.select_current_row_action = QAction('选中该装置')
        self.select_current_row_action.setIcon(QIcon('./img/add.png'))
        self.select_current_row_action.triggered.connect(self.selectCurrentRow)
        self.deselect_current_row_action = QAction('取消选中该装置')
        self.deselect_current_row_action.setIcon(QIcon('./img/delete.png'))
        self.deselect_current_row_action.triggered.connect(self.deselectCurrentRow)
        self.adjust_same_type_action = QAction('同步同型号规则')
        self.adjust_same_type_action.setIcon(QIcon('./img/sync.png'))
        self.adjust_same_type_action.triggered.connect(self.adjustSameTypeRegular)
        self.select_all_item_below_action = QAction('选中下方所有装置')
        self.select_all_item_below_action.setIcon(QIcon('./img/down.png'))
        self.select_all_item_below_action.triggered.connect(self.selectAllItemBelow)
        self.fast_configure_regular_action = QAction('快速配置规则')
        self.fast_configure_regular_action.setIcon(QIcon('./img/fast_configure.png'))
        self.fast_configure_regular_action.triggered.connect(self.fastConfigureRegular)
        self.pop_menu.addActions([self.select_current_row_action, self.deselect_current_row_action,
                                  self.adjust_same_type_action, self.select_all_item_below_action,
                                  self.fast_configure_regular_action])
        self.ied_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ied_table.customContextMenuRequested.connect(self.popContextMenu)

        self.initUI()
        if GlobalConfig.config_dict['isRelateClassRegular']:
            self.ied_table.itemChanged.connect(self.adjustSameTypeRegular)

        self.refreshVisibleItemCount()

    def initUI(self):
        self.createIedTable()

        # 设置UI布局
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(self.filter_item_label)
        filter_layout.addWidget(self.filter_item_combobox)
        filter_layout.addWidget(self.filter_lineedit)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.process_unchecked_item_btn)
        button_layout.addWidget(self.select_all_btn)
        button_layout.addWidget(self.cancel_select_all_btn)
        button_layout.addWidget(self.export_btn)
        button_layout.addWidget(self.quit_btn)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.ied_table)
        main_layout.addLayout(filter_layout)
        main_layout.addLayout(button_layout)
        main_layout.addWidget(self.statusBar)

        self.setLayout(main_layout)

        # 设置对话框的一些属性
        self.setWindowTitle('导出断链表-[%s]' % self.scd_file_path)
        self.setWindowIcon(QIcon('./img/export.png'))
        self.setMinimumSize(1000, 700)

    def createIedTable(self):
        self.ied_table.setColumnCount(6)
        self.ied_table.setRowCount(len(self.ied_list))
        self.ied_table.setHorizontalHeaderLabels(['', '装置名称', '装置描述', '装置型号', '生产厂商', '排序规则'])
        self.ied_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.ied_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.ied_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.ied_table.horizontalHeader().setStretchLastSection(True)
        self.ied_table.setColumnWidth(0, 20)
        self.ied_table.setColumnWidth(2, 300)
        self.ied_table.setColumnWidth(3, 240)

        row_num = 0
        export_method_desc_dict = {export_method_class.__name__: export_method_class.desc for export_method_class in
                                   ExportMethod.__subclasses__()}
        for ied in self.ied_list:
            check = QTableWidgetItem()
            check.setCheckState(Qt.Unchecked)
            self.ied_table.setItem(row_num, 0, check)
            self.ied_table.setItem(row_num, 1, QTableWidgetItem(ied['name']))
            self.ied_table.setItem(row_num, 2, QTableWidgetItem(ied['desc']))
            self.ied_table.setItem(row_num, 3, QTableWidgetItem(ied['type']))
            self.ied_table.setItem(row_num, 4, QTableWidgetItem(ied.get('manufacturer', '')))
            self.ied_table.setItem(row_num, 5, QTableWidgetItem(export_method_desc_dict[ied['regular']]))
            row_num += 1

        self.loadRegularCache()
        self.refreshCheckedItemCount()
        self.ied_table.cellChanged.connect(self.refreshCheckedItemCount)

    def editRegularCombobox(self, item):
        for row_index in range(self.ied_table.rowCount()):
            self.ied_table.removeCellWidget(row_index, 5)
        current_row = item.row()
        current_column = item.column()
        current_regular_desc = item.text()
        regular_combobox_items = [export_method_class.desc for export_method_class in ExportMethod.__subclasses__()]
        self.regular_combobox = QComboBox()
        self.regular_combobox.addItems(regular_combobox_items)
        self.regular_combobox.activated.connect(self.editRegularText)
        for export_method_class in ExportMethod.__subclasses__():
            if current_regular_desc == export_method_class.desc:
                self.regular_combobox.setCurrentIndex(export_method_class.index)
        if current_column == 5:
            self.ied_table.setCellWidget(current_row, current_column, self.regular_combobox)

    def editRegularText(self):
        current_row = self.ied_table.currentRow()
        current_column = self.ied_table.currentColumn()
        self.ied_table.removeCellWidget(current_row, current_column)
        self.ied_table.setItem(current_row, current_column, QTableWidgetItem(self.regular_combobox.currentText()))
        self.adjustSameTypeRegular()

    def popContextMenu(self, pos):
        screen_pos = self.ied_table.mapToGlobal(pos)
        current_row = self.ied_table.currentRow()
        self.select_current_row_action.setVisible(not self.ied_table.item(current_row, 0).checkState())
        self.deselect_current_row_action.setVisible(self.ied_table.item(current_row, 0).checkState())
        self.adjust_same_type_action.setVisible(not GlobalConfig.config_dict['isRelateClassRegular'])
        self.fast_configure_regular_action.setVisible(GlobalConfig.config_dict['isRelateClassRegular'])
        self.pop_menu.popup(screen_pos)

    # 同步调整所有通类型装置的导出规则
    def adjustSameTypeRegular(self):
        current_row = self.ied_table.currentRow()
        current_ied_fingerprint = '[%s]-[%s]' % tuple(map(lambda x: self.ied_table.item(current_row, x).text(), [4, 3]))
        current_ied_regular = self.ied_table.item(current_row, 5).text()
        row_count = self.ied_table.rowCount()
        for row in range(0, row_count):
            ied_fingerprint = '[%s]-[%s]' % tuple(map(lambda x: self.ied_table.item(row, x).text(), [4, 3]))
            if ied_fingerprint == current_ied_fingerprint and row != current_row:
                self.ied_table.item(row, 5).setText(current_ied_regular)

    def processUncheckedRow(self):
        if self.process_unchecked_item_btn.text() == "隐藏非选中项":
            for row_num in range(self.ied_table.rowCount()):
                if not self.ied_table.item(row_num, 0).checkState():
                    self.ied_table.setRowHidden(row_num, True)
            self.process_unchecked_item_btn.setText("展开非选中项")
        else:
            for row_num in range(self.ied_table.rowCount()):
                if not self.ied_table.item(row_num, 0).checkState():
                    self.ied_table.setRowHidden(row_num, False)
            self.refreshFilter()
            self.process_unchecked_item_btn.setText("隐藏非选中项")
        self.refreshVisibleItemCount()

    def refreshFilter(self):
        column_num = self.filter_item_combobox.currentIndex() + 1
        filter_word = self.filter_lineedit.text()
        for row_num in range(self.ied_table.rowCount()):
            if filter_word != '':
                if self.ied_table.item(row_num, column_num).text().find(filter_word):
                    self.ied_table.setRowHidden(row_num, True)
                else:
                    self.ied_table.setRowHidden(row_num, False)
            else:
                self.ied_table.setRowHidden(row_num, False)
        self.refreshVisibleItemCount()

    def selectAllVisibleRow(self):
        for row_num in range(self.ied_table.rowCount()):
            if not self.ied_table.isRowHidden(row_num):
                self.ied_table.item(row_num, 0).setCheckState(Qt.Checked)
        self.refreshCheckedItemCount()

    def cancelSelectAllVisibleRow(self):
        for row_num in range(self.ied_table.rowCount()):
            if not self.ied_table.isRowHidden(row_num):
                self.ied_table.item(row_num, 0).setCheckState(Qt.Unchecked)
        self.refreshCheckedItemCount()

    def exportLinkTable(self):
        self.saveRegularCache()

        # 选择导出位置
        scd_file_name = self.scd_file_path.split('/')[-1]
        scd_file_dir = self.scd_file_path.replace(scd_file_name, '')
        default_table_file_name = scd_file_name.replace('.scd', '断链信息表.xlsx')
        default_table_file_name = default_table_file_name.replace('.SCD', '断链信息表.xlsx')
        table_filepath = QFileDialog.getSaveFileName(None, "请选择导出路径", default_table_file_name,
                                                     "Microsoft Excel文件(*.xlsx)", scd_file_dir)[0]
        if table_filepath != '':
            # 解析整个个SCD获取必要的信息
            def runtime_function(ied_info):
                progress_percent = int(ied_info['index'] / self.ied_count * 80)
                progress_description = '正在解析%s...' % ied_info['name']
                self.operate_progress.setValue(progress_percent)
                self.operate_str.setText(progress_description)
                QApplication.processEvents()

            scl = SCL(self.scd_file_path, runtime_function)
            # 所需要导出的IED列表
            export_result = dict()
            for row_num in range(self.ied_table.rowCount()):
                if self.ied_table.item(row_num, 0).checkState():
                    iedname = self.ied_table.item(row_num, 1).text()
                    export_method_desc = self.ied_table.item(row_num, 5).text()
                    for export_method_class in ExportMethod.__subclasses__():
                        if export_method_class.desc == export_method_desc:
                            export_result[iedname] = export_method_class.generateLinkTable(iedname, scl)

            self.operate_str.setText("导出至%s..." % table_filepath)
            self.operate_progress.setValue(95)

            # 编辑厂家分类信息
            manufacturer_list = list()
            for row in range(self.ied_table.rowCount()):
                if self.ied_table.item(row, 0).checkState():
                    if not self.ied_table.item(row, 4).text():
                        manufacturer_str = self.ied_table.item(row, 3).text()
                    else:
                        manufacturer_str = self.ied_table.item(row, 4).text()
                    if manufacturer_str not in manufacturer_list:
                        manufacturer_list.append(manufacturer_str)

            source_template_dict = None

            # 编辑模型内部描述模板
            if GlobalConfig.config_dict['isExportSourceDesc']:
                export_type_list = []
                type_mask_dict = {}
                ied_fingerprint_dict = {}
                ied_example_dict = {}
                for row in range(self.ied_table.rowCount()):
                    if self.ied_table.item(row, 0).checkState():
                        ied_fingerprint = '[%s]-[%s]' % tuple(map(lambda x: self.ied_table.item(row, x).text(), [4, 3]))
                        ied_fingerprint_dict[self.ied_table.item(row, 1).text()] = ied_fingerprint
                        if ied_fingerprint not in export_type_list:
                            export_type_list.append(ied_fingerprint)
                            type_mask_dict[ied_fingerprint] = 0
                            ied_example_dict[ied_fingerprint] = self.ied_table.item(row, 1).text()

                for ied_name in export_result.keys():
                    ied_result = export_result.get(ied_name)
                    ied_mask = reduce(lambda x, y: (x << 1) + y, list(map(lambda x: 1 if len(x) else 0, ied_result)))
                    ied_fingerprint = ied_fingerprint_dict[ied_name]
                    type_mask_dict[ied_fingerprint] = type_mask_dict[ied_fingerprint] | ied_mask

                export_template_dialog = ExportTemplateDialog(export_type_list, type_mask_dict, ied_example_dict,
                                                              self.scd_file_path)
                if not export_template_dialog.exec():
                    self.operate_str.setText("等待")
                    self.operate_progress.setValue(0)
                    return

                source_template_dict = export_template_dialog.getTemplateDict()

            # 导出至Excel表格
            workbook = xlsxwriter.Workbook(table_filepath)

            def writeToWorksheet(export_result, mode, work_sheet_title="全站断链表"):
                # 单元格样式
                ied_header_format = workbook.add_format({
                    'align': 'center',
                    'bold': 'true',
                    'fg_color': '#D1D1D1'
                })
                if mode == 0:
                    header_format = workbook.add_format({
                        'align': 'center',
                        'bold': 'true',
                        'fg_color': '#D1D1D1'
                    })
                elif mode == 2:
                    header_format = workbook.add_format({
                        'align': 'center'
                    })
                field_format = workbook.add_format({
                    'align': 'center'
                })

                if mode == 2:
                    worksheet = workbook.add_worksheet(work_sheet_title)
                    row = 0

                row = 0
                for ied_name in export_result.keys():
                    ied_result = export_result.get(ied_name)
                    ied = scl.getObjectByReference(ied_name)
                    if mode == 0:
                        worksheet = workbook.add_worksheet(ied_name)
                        row = 0
                    elif mode == 2:
                        ied_title = '%s:%s断链信息表' % (ied_name, ied.desc)
                        worksheet.merge_range('A%s:B%s' % (row + 1, row + 1), ied_title, ied_header_format)
                        row += 1
                    worksheet.set_column(0, 0, width=30)
                    worksheet.set_column(1, 1, width=60)
                    for index, ap_result in list(enumerate(ied_result)):
                        header_dict = {0: '站控层GOOSE断链表', 1: '过程层SV断链表', 2: '过程层GOOSE断链表'}
                        link_type_dict = {0: 'GOOSE', 1: 'SV', 2: 'GOOSE'}
                        if len(ap_result):
                            worksheet.merge_range('A%s:B%s' % (row + 1, row + 1), header_dict[index], header_format)
                            worksheet.write(row + 1, 0, '模型源描述', field_format)
                            worksheet.write(row + 1, 1, '断链信息描述', field_format)
                            row += 2
                            for dataset_index, dataset_reference in enumerate(ap_result):
                                if source_template_dict:
                                    ied_fingerprint = '[%s]-[%s]' % (ied.manufacturer, ied.type)
                                    source_desc_template = source_template_dict.get(ied_fingerprint, '')[index]
                                    replace_pattern = re.compile(r"\[num,[01],[1-2]\]")
                                    replace_str_list = replace_pattern.findall(source_desc_template)
                                    source_desc = source_desc_template
                                    for replace_str in replace_str_list:
                                        replace_str_elements = replace_str.lstrip('[').rstrip(']').split(',')
                                        offset = int(replace_str_elements[1])
                                        padding = int(replace_str_elements[2])
                                        if padding == 1:
                                            number_str = "%d" % (dataset_index + offset)
                                        else:
                                            number_str = f"%0{padding}d" % (dataset_index + offset)
                                        source_desc = source_desc.replace(replace_str, number_str)
                                    worksheet.write(row, 0, source_desc)
                                external_ied_name = dataset_reference.split('+')[0]
                                external_ied_desc = scl.queryDescriptionByReference(external_ied_name)
                                appid_string = '%04X' % scl.getAppidByDatasetReference(dataset_reference)
                                replace_tuple_list = [GlobalConfig.config_dict['linkDescTemplate'],
                                                      ('[InIedname]', ied_name),
                                                      ('[InIedDesc]', ied.desc),
                                                      ('[ExIedname]', external_ied_name),
                                                      ('[ExIedDesc]', external_ied_desc),
                                                      ('[LinkType]',  link_type_dict[index]),
                                                      ('[Appid]', appid_string)]
                                link_desc = reduce(lambda x, y: x.replace(y[0], y[1]), replace_tuple_list)
                                worksheet.write(row, 1, link_desc)
                                row += 1
                            if mode == 0:
                                row += 1
                    if mode == 2:
                        row += 3

            if GlobalConfig.config_dict['exportMode'] == 1:
                classification_dialog = ClassificationDialog(manufacturer_list, self.scd_file_path)
                if not classification_dialog.exec():
                    self.operate_str.setText("等待")
                    self.operate_progress.setValue(0)
                    return

                manufacturer_list, manufacturer_data = classification_dialog.getManufacturerData()
                export_result_list = dict.fromkeys(manufacturer_list)
                for ied_name in export_result.keys():
                    ied = scl.getObjectByReference(ied_name)
                    ied_manufacturer = manufacturer_data[ied.manufacturer if ied.manufacturer else ied.type]
                    if export_result_list[ied_manufacturer] is None:
                        export_result_list[ied_manufacturer] = {}
                    export_result_list[ied_manufacturer][ied_name] = export_result[ied_name]
                for work_sheet_title in export_result_list.keys():
                    writeToWorksheet(export_result_list[work_sheet_title], mode=2, work_sheet_title=work_sheet_title)
            else:
                writeToWorksheet(export_result, mode=GlobalConfig.config_dict['exportMode'])
            try:
                workbook.close()
            except Exception as e:
                self.refreshOperateStatus("导出失败", 95)
                QMessageBox.critical(None, "导出失败", "断链表导出至 %s 失败" % table_filepath)
                self.operate_str.setText("等待")
                self.operate_progress.setValue(0)
                return

            QMessageBox.information(None, "导出成功", "断链表导出至 %s 成功" % table_filepath)
            self.operate_str.setText("等待")
            self.operate_progress.setValue(0)

    def refreshCheckedItemCount(self):
        checked_item_count = 0
        for row_num in range(self.ied_table.rowCount()):
            if self.ied_table.item(row_num, 0).checkState() == 2:
                checked_item_count += 1
        self.checked_item_count.setText(str(checked_item_count))

    def refreshVisibleItemCount(self):
        visible_item_count = 0
        for row_num in range(self.ied_table.rowCount()):
            if not self.ied_table.isRowHidden(row_num):
                visible_item_count += 1
        self.visible_item_count.setText(str(visible_item_count))

    def refreshOperateStatus(self, operate_str="等待", operate_percent=0.0):
        self.operate_str.setText(operate_str)
        self.operate_progress.setValue(int(operate_percent))

    # 选中该行
    def selectCurrentRow(self):
        current_row = self.ied_table.currentRow()
        self.ied_table.item(current_row, 0).setCheckState(Qt.Checked)

    # 取消选中该行
    def deselectCurrentRow(self):
        current_row = self.ied_table.currentRow()
        self.ied_table.item(current_row, 0).setCheckState(Qt.Unchecked)

    # 选中该行下方所有装置
    def selectAllItemBelow(self):
        current_row = self.ied_table.currentRow()
        row_count = self.ied_table.rowCount()
        for row in range(current_row, row_count):
            if not self.ied_table.isRowHidden(row):
                self.ied_table.item(row, 0).setCheckState(Qt.Checked)

    # 快速规则配置
    def fastConfigureRegular(self):
        ied_fingerprint_list = list()
        row_count = self.ied_table.rowCount()
        for row in range(row_count):
            ied_fingerprint = '[%s]-[%s]' % tuple(map(lambda x: self.ied_table.item(row, x).text(), [4, 3]))
            if ied_fingerprint not in ied_fingerprint_list:
                ied_fingerprint_list.append(ied_fingerprint)
            else:
                self.ied_table.setRowHidden(row, True)
        self.refreshVisibleItemCount()

    # 检查是否有 ied 被选择
    def checkIedSelected(self):
        for row_index in range(self.ied_table.rowCount()):
            check_state_item = self.ied_table.item(row_index, 0)
            if check_state_item is not None and check_state_item.checkState() == 2:
                self.export_btn.setEnabled(True)
                return
        self.export_btn.setEnabled(False)

    # 保存规则缓存
    def saveRegularCache(self):
        regular_dict = {}
        for row_index in range(self.ied_table.rowCount()):
            ied_name = self.ied_table.item(row_index, 1).text()
            check_state = self.ied_table.item(row_index, 0).checkState()
            regular_str = self.ied_table.item(row_index, 5).text()
            regular_dict[ied_name] = (check_state, regular_str)
        scd_file_name = os.path.basename(self.scd_file_path)
        with open('scd_cache/%s_regular.json' % scd_file_name, 'w', encoding='utf8') as regular_cache:
            json.dump(regular_dict, regular_cache, indent=True, ensure_ascii=False)

    # 加载规则缓存
    def loadRegularCache(self):
        scd_file_name = os.path.basename(self.scd_file_path)
        cache_file_path = "scd_cache/%s_regular.json" % scd_file_name
        if os.path.exists(cache_file_path):
            with open(cache_file_path, 'r', encoding='utf8') as regular_cache:
                regular_dict = json.load(regular_cache)
            for row_index in range(self.ied_table.rowCount()):
                ied_name = self.ied_table.item(row_index, 1).text()
                if ied_name in regular_dict.keys():
                    self.ied_table.item(row_index, 0).setCheckState(regular_dict[ied_name][0])
                    self.ied_table.item(row_index, 5).setText(regular_dict[ied_name][1])
