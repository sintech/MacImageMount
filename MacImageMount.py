""" GUI tool for easy mounting of RAW hard drive, cdrom, floppy images under macOS.
    Copyright (C) 2022  Konstantin Fedorov

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>."""

import os.path
import platform

from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import *
from PySide6.QtCore import Qt

import glob, subprocess


def convert_bytes(num):
    """
    this function will convert bytes to MB.... GB... etc
    """
    for x in ['b', 'KB', 'MB', 'GB', 'TB']:
        if num < 1024.0:
            return "%3.1f %s" % (num, x)
        num /= 1024.0


class CreateWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__()
        
        self.parent = parent
        self.setWindowTitle("Create image")
        
        l1 = QLabel("Size:")
        self.size = QLineEdit("10")
        self.size.setFixedWidth(60)
        l2 = QLabel("MB")
        create = QPushButton("Save")
        create.clicked.connect(self.create_image)
        
        layout = QHBoxLayout()
        layout.addWidget(l1)
        layout.addWidget(self.size)
        layout.addWidget(l2)
        layout.addWidget(create)
        
        vlay = QVBoxLayout()
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        vlay.addLayout(layout)
        vlay.addWidget(self.progress)
        
        self.setLayout(vlay)
    
    def create_image(self):
        filename = QFileDialog.getSaveFileName(self, "Save image", "", "Image files (*.img *.hda)")[0]
        
        if not filename:
            # self.close()
            return
        
        size = int(self.size.text())
        data = bytes([0] * 1024 * 1024)
        # f.seek(size*1024*1024)
        # f.write(b'0')
        self.progress.setMaximum(size - 1)
        
        with open(filename, "w+b") as f:
            for i in range(size):
                f.write(data)
                self.progress.setValue(i)
        
        self.parent.open_path([filename])
        self.close()


class Main(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("MacImageMount")
        
        if platform.system() == "Darwin":
            about_action = QAction(QIcon(), "About", self)
            about_action.triggered.connect(lambda: QMessageBox.information(self, "About", "Made by: SinTech\nVer: 1.0"))
            menubar = self.menuBar()
            menu = menubar.addMenu("Help")
            menu.addAction(about_action)
        
        self.create = QPushButton("Create")
        self.create.clicked.connect(self.create_image)
        self.image_list = [{}]
        self.dir = "Path"
        self.path = QLineEdit(self.dir)
        self.open = QPushButton("Open dir", )
        self.open.clicked.connect(self.open_path)
        
        addr_lay = QHBoxLayout()
        addr_lay.addWidget(self.create)
        addr_lay.addWidget(self.path)
        addr_lay.addWidget(self.open)
        
        self.table = QTableWidget()
        self.table.setRowCount(0)
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Image", "Size", ""])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        
        self.layout = QVBoxLayout()
        self.layout.addLayout(addr_lay)
        self.layout.addWidget(self.table)
        
        container = QWidget()
        container.setLayout(self.layout)
        self.setCentralWidget(container)
    
    def create_image(self):
        self.create_window = CreateWindow(self)
        self.create_window.setModal(True)
        self.create_window.show()
    
    def mount_image(self):
        button = self.sender()
        index = self.table.indexAt(button.pos())
        if not index.isValid():
            return
        table_row = index.row()
        
        if button.text() == "mount":
            proc = subprocess.run(["hdiutil", "attach", "-noverify", "-imagekey", "diskimage-class=CRawDiskImage",
                                   self.image_list[table_row]["image"]], capture_output=True, timeout=10,
                                  universal_newlines=True)
            if proc.returncode > 0:
                msgBox = QMessageBox()
                msgBox.setText("Image mounting error")
                msgBox.setIcon(QMessageBox.Critical)
                msgBox.setDetailedText(" ".join(proc.args) + "\n\n" + proc.stderr)
                hs = QSpacerItem(500, 0, QSizePolicy.Minimum, QSizePolicy.Expanding)
                layout = msgBox.layout()  # .setSizeConstraint(QLayout.SetMinimumSize)
                layout.addItem(hs, layout.rowCount(), 0, 1, layout.columnCount())
                msgBox.exec()
            else:
                print(proc.stdout)
                disk = proc.stdout.split("\n")[0].split(" ")[0]
                if "disk" not in disk:
                    QMessageBox.warning(self, "Warning", "Something went wrong")
                    return
                
                self.image_list[table_row]["mounted"] = disk
                self.table.item(table_row, 0).setText(
                    self.image_list[table_row]["image"].replace(self.dir + os.sep, "") + " (" + disk + ")"
                )
                self.table.item(table_row, 0).setBackground(Qt.green)
                self.table.cellWidget(table_row, 2).setText("unmount")

        elif button.text() == "unmount":
            if not self.image_list[table_row]["mounted"]:
                QMessageBox.warning(self, "Warning", "Something went wrong (mount point is empty)")
                return
            
            proc = subprocess.run(["hdiutil", "detach", self.image_list[table_row]["mounted"]], capture_output=True,
                                  timeout=10,
                                  universal_newlines=True)
            if proc.returncode > 0:
                msgBox = QMessageBox()
                msgBox.setText("Image un-mounting error")
                msgBox.setIcon(QMessageBox.Critical)
                msgBox.setDetailedText(" ".join(proc.args) + "\n\n" + proc.stderr)
                hs = QSpacerItem(400, 0, QSizePolicy.Minimum, QSizePolicy.Expanding)
                layout = msgBox.layout()  # .setSizeConstraint(QLayout.SetMinimumSize)
                layout.addItem(hs, layout.rowCount(), 0, 1, layout.columnCount())
                msgBox.exec()
            else:
                self.image_list[table_row]["mounted"] = None
                self.table.item(table_row, 0).setText(
                    self.image_list[table_row]["image"].replace(self.dir + os.sep, "")
                )
                self.table.item(table_row, 0).setBackground(Qt.white)
                self.table.cellWidget(table_row, 2).setText("mount")
    
    def open_path(self, ext_list=[]):
        
        if ext_list:
            self.dir = os.path.dirname(ext_list[0])
            file_list = ext_list
        else:
            self.dir = QFileDialog.getExistingDirectory(self, "Open Directory",
                                                        "",
                                                        QFileDialog.ShowDirsOnly)
            
            if not self.dir:
                return
            
            file_list = []
            file_list.extend(glob.glob(self.dir + os.path.sep + '**/*.img', recursive=True))
            file_list.extend(glob.glob(self.dir + os.path.sep + '**/*.hda', recursive=True))
            file_list.extend(glob.glob(self.dir + os.path.sep + '**/*.iso', recursive=True))
        
        self.path.setText(self.dir)
        self.image_list = []
        # self.table.clear()
        self.table.setRowCount(0)
        
        for file in sorted(file_list):
            self.image_list.append({"image": file, "mounted": None})
        
        for i, img_info in enumerate(self.image_list):
            file = img_info["image"]
            item_name = QTableWidgetItem(file.replace(self.dir + "/", ""))
            item_size = QTableWidgetItem(convert_bytes(os.path.getsize(file)))
            item_button = QPushButton("mount")
            item_button.clicked.connect(self.mount_image)
            self.table.insertRow(i)
            self.table.setItem(i, 0, item_name)
            self.table.setItem(i, 1, item_size)
            self.table.setCellWidget(i, 2, item_button)


if __name__ == "__main__":
    app = QApplication()
    
    widget = Main()
    widget.resize(800, 600)
    widget.show()
    
    app.exec()
