import os
import sys
import pathlib
import subprocess

class NodeJSUtility:
    def __init__(self):
        self.path = pathlib.Path(os.path.abspath(__file__)).parent

    @staticmethod
    def get_command(cmd: list[str]) -> list[str]:
        """
        Возвращает правильную команду в зависимости от операционной системы.
        """
        if 'node' in cmd: return cmd
        if sys.platform == "win32":
            cmd[0] += ".cmd"  # Пример: "npm" -> "npm.cmd"
        return cmd

    def run_command(self, cmd: list[str], capture_output: bool = True):
        """
        Выполняет команду и возвращает результат.
        """
        try:
            result = subprocess.run(
                self.get_command(cmd),
                check=True,
                cwd=self.path,
                stdout=subprocess.PIPE if capture_output else None,
                stderr=subprocess.PIPE if capture_output else None,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            if capture_output and result.stdout:
                print(result.stdout.strip())
            return True
        except subprocess.CalledProcessError as e:
            if capture_output and e.stderr:
                print(f"Ошибка при выполнении команды {' '.join(cmd)}:\n{e.stderr.strip()}")
            return False
        except FileNotFoundError:
            print(f"Команда {' '.join(cmd)} не найдена.")
            return False

    def is_node_installed(self) -> bool:
        """
        Проверяет, установлен ли Node.js, выполняя команду `node -v`.
        """
        print("Проверка установки Node.js...")
        if self.run_command(["node", "-v"]):
            return True
        return False

    def is_npm_installed(self) -> bool:
        """
        Проверяет, установлен ли npm, выполняя команду `npm -v`.
        """
        print("Проверка установки npm...")
        if self.run_command(["npm", "-v"]):
            return True
        return False

    def check_package_json(self) -> bool:
        """
        Проверяет наличие файла package.json в директории проекта.
        """
        package_json = self.path / "package.json"
        if package_json.is_file():
            return True
        print("Файл package.json не найден в указанной директории.")
        return False

    def update_dependencies(self):
        """
        Обновляет зависимости в указанной директории.
        Выполняет `npm install` и `npm update`.
        """
        print(f"Работаем в директории: {self.path}")
        if not self.check_package_json():
            return False

        print("Устанавливаем зависимости с помощью `npm install`...")
        if not self.run_command(["npm", "install"]):
            return False
        print("Зависимости успешно установлены.")

        print("Обновляем зависимости с помощью `npm update`...")
        if not self.run_command(["npm", "update"]):
            return False
        print("Зависимости успешно обновлены.")
        return True

    def upgrade_to_latest(self):
        """
        Обновляет package.json до последних версий зависимостей с помощью npm-check-updates.
        Затем выполняет `npm install` для установки обновленных зависимостей.
        """
        print("Проверка установки npm-check-updates...")
        if not self.run_command(["ncu", "-v"]):
            print("npm-check-updates не установлен. Устанавливаем глобально...")
            if not self.run_command(["npm", "install", "-g", "npm-check-updates"]):
                return False
            print("npm-check-updates успешно установлен.")

        print("Обновляем package.json до последних версий зависимостей с помощью `ncu -u`...")
        if not self.run_command(["ncu", "-u"]):
            return False
        print("package.json успешно обновлен.")

        print("Устанавливаем обновленные зависимости с помощью `npm install`...")
        if not self.run_command(["npm", "install"]):
            return False
        print("Обновленные зависимости успешно установлены.")

    def start_install(self):
        """
        Основной метод, который выполняет проверку установки Node.js и npm,
        а затем обновляет зависимости.
        """
        print("Начало процесса обновления зависимостей...")
        if not self.is_node_installed():
            print("Node.js не установлен. Пожалуйста, установите Node.js с официального сайта: https://nodejs.org/")
            return False

        if not self.is_npm_installed():
            print("npm не установлен. Обычно npm устанавливается вместе с Node.js. Проверьте установку Node.js.")
            return False

        print("Node.js и npm установлены.")
        return self.update_dependencies()

    def start_upgrade(self):
        """
        Метод для обновления зависимостей до последних доступных версий.
        """
        print("Начало процесса обновления зависимостей до последних версий...")
        if not self.is_node_installed():
            print("Node.js не установлен. Пожалуйста, установите Node.js с официального сайта: https://nodejs.org/")
            return False

        if not self.is_npm_installed():
            print("npm не установлен. Обычно npm устанавливается вместе с Node.js. Проверьте установку Node.js.")
            return False

        print("Node.js и npm установлены.")
        self.upgrade_to_latest()


note_js_utility = NodeJSUtility()
