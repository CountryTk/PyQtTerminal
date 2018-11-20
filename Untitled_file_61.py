import sys
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import os
import getpass
import socket
from pathlib import Path
from PyQt5.QtWidgets import QWidget, QLineEdit
from PyQt5.QtGui import QPainter, QColor, QSyntaxHighlighter, QTextCharFormat, QColor
from PyQt5.QtCore import QRect, Qt, pyqtSignal, QRegExp

lineBarColor = QColor(53, 53, 53)


class PlainTextEdit(QPlainTextEdit):
    commandSignal = pyqtSignal(str)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.name = "[" + str(getpass.getuser()) + "@" + str(socket.gethostname()) + "]" + "  ~" + str(os.getcwd()) + " >$ "
        self.appendPlainText(self.name)
        self.parent = parent
        
    def keyPressEvent(self, e):
        cursor = self.textCursor()
        
        if self.parent:
            
            if (e.modifiers() == Qt.ControlModifier and e.key() == Qt.Key_A):
                return
        
            if e.key() == 16777220:
                text = self.textCursor().block().text()
                #command_list = command.split()
                #print(command)
                self.commandSignal.emit(text)
                self.appendPlainText(self.name)
               
                return
                
            if e.key() == 16777219:
                
                if cursor.positionInBlock() <= len(self.name):
                    return
                    
                else:
                    cursor.deleteChar()    
                # self.parent.keyPressEvent(e)
                            
            super().keyPressEvent(e)

        e.accept()


class Terminal(QWidget):
    errorSignal = pyqtSignal(str)
    outputSignal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.process = QProcess(self)
        self.editor = PlainTextEdit(self)
        self.layout = QHBoxLayout()
        self.name = None
        self.highlighter = name_highlighter(self.editor.document(), self.editor.name)
        self.layout.addWidget(self.editor)
        self.editor.commandSignal.connect(self.handle)
        self.process.readyReadStandardError.connect(self.onReadyReadStandardError)
        self.process.readyReadStandardOutput.connect(self.onReadyReadStandardOutput)
        self.setLayout(self.layout)
        self.show()

    def onReadyReadStandardError(self):
        self.error = self.process.readAllStandardError().data().decode()
        self.editor.appendPlainText(self.error.strip('\n'))
        self.errorSignal.emit(self.error)
        
        if self.error == "":
            pass
        else:
            try:
                self.error = self.error.split(os.linesep)[-2]
            except IndexError as E:
                print(E)

    def onReadyReadStandardOutput(self):
        self.result = self.process.readAllStandardOutput().data().decode()
        self.editor.appendPlainText(self.result.strip('\n'))
        self.state = self.process.state()
        self.outputSignal.emit(self.result)

    def run(self, command):
        """Executes a system command."""

        self.process.start(command)
        
    def handle(self, command):
        
        """Split a command into list so command `echo hi` would appear as ['echo', 'hi']"""
        real_command = command.replace(self.editor.name, "")
        if real_command != "":
            command_list = real_command.split()
        else:
            command_list = None 
        # print(real_command)
        """Now we start implementing some commands"""
        if real_command == "clear":
            self.editor.clear()
            
        elif command_list is not None and command_list[0] == "echo":
            self.editor.appendPlainText(" ".join(command_list[1:]))
            
        elif real_command == "exit":
            qApp.exit()
        
        elif command_list is not None and command_list[0] == "cd" and len(command_list) > 1:
            try:
                os.chdir(" ".join(command_list[1:]))
                self.editor.name = "[" + str(getpass.getuser()) + "@" + str( socket.gethostname()) + "]" + "  ~" + str(os.getcwd()) + " >$ "
                
            except FileNotFoundError as E:
                self.editor.appendPlainText(str(E))
        
        elif len(command_list) == 1 and command_list[0] == "cd":
            os.chdir(str(Path.home()))
            self.editor.name = "[" + str(getpass.getuser()) + "@" + str( socket.gethostname()) + "]" + "  ~" + str(os.getcwd()) + " >$ "
            
        elif command == self.editor.name + real_command:
            print(self.editor.name+real_command)
            self.run(real_command)
        
        else:
            pass # When the user does a command like ls and then presses enter then it wont read the line where the cursor is on as a command
      
class name_highlighter(QSyntaxHighlighter):
    
    def __init__(self, parent=None, name=None):
        super().__init__(parent)
        self.highlightingRules = []
        self.name = name
        nameFormat = QTextCharFormat()
        nameFormat.setForeground(QColor("#00ff00"))
        nameFormat.setFontItalic(True)
        print(self.name)
        self.highlightingRules.append((QRegExp("\\b" + self.name + "\\b"), nameFormat))
        
    def highlightBlock(self, text):
        
        for pattern, format in self.highlightingRules:
            expression = QRegExp(pattern)
            index = expression.indexIn(text)
            while index >= 0:
                length = expression.matchedLength()
                self.setFormat(index, length, format)
                index = expression.indexIn(text, index + length)

    
if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = Terminal()
    sys.exit(app.exec_())
