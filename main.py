# filename: github_gui.py

import sys
import os
import json
import requests
import subprocess
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QListWidget, QListWidgetItem, QMessageBox, QHBoxLayout
)
from PyQt5.QtCore import Qt

CONFIG_PATH = os.path.expanduser("~/.config/github_gui_auth.json")

class GitHubApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GitHub Repo Viewer")
        self.setGeometry(100, 100, 600, 400)

        self.token = None
        self.repos = []
        self.page = 1

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.login_label = QLabel("GitHub Personal Access Token (Needs repo and read:user permissions):")
        self.token_input = QLineEdit()
        self.token_input.setEchoMode(QLineEdit.Password)
        self.login_button = QPushButton("Login")
        self.login_button.clicked.connect(self.login)

        self.repo_list = QListWidget()

        self.prev_button = QPushButton("Prev Page")
        self.next_button = QPushButton("Next Page")
        self.prev_button.clicked.connect(self.prev_page)
        self.next_button.clicked.connect(self.next_page)

        self.layout.addWidget(self.login_label)
        self.layout.addWidget(self.token_input)
        self.layout.addWidget(self.login_button)
        self.layout.addWidget(self.repo_list)
        self.layout.addWidget(self.prev_button)
        self.layout.addWidget(self.next_button)

        self.load_token()

    def login(self):
        self.token = self.token_input.text().strip()
        if not self.token:
            QMessageBox.warning(self, "No Token", "Please enter a token.")
            return
        self.save_token()
        self.fetch_repos()

    def save_token(self):
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, "w") as f:
            json.dump({"token": self.token}, f)

    def load_token(self):
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH) as f:
                self.token = json.load(f).get("token")
                self.token_input.setText(self.token)
                self.fetch_repos()

    def fetch_repos(self):
        headers = {"Authorization": f"token {self.token}"}
        url = f"https://api.github.com/user/repos?per_page=10&page={self.page}"
        resp = requests.get(url, headers=headers)

        if resp.status_code != 200:
            QMessageBox.critical(self, "Error", f"Failed to fetch repos:\n{resp.text}")
            return

        self.repos = resp.json()
        self.display_repos()

    def display_repos(self):
        self.repo_list.clear()
        for repo in self.repos:
            name = repo["full_name"]
            url = repo["clone_url"]

            item = QListWidgetItem(name)
            self.repo_list.addItem(item)

            btn_layout = QHBoxLayout()
            clone_button = QPushButton("Clone")
            clone_button.clicked.connect(lambda _, u=url: self.clone_repo(u))
            info_button = QPushButton("Info")
            info_button.clicked.connect(lambda _, r=repo: self.show_info(r))

            container = QWidget()
            btn_layout.addWidget(clone_button)
            btn_layout.addWidget(info_button)
            container.setLayout(btn_layout)
            item.setSizeHint(container.sizeHint())
            self.repo_list.setItemWidget(item, container)

    def clone_repo(self, url):
        dest = os.path.join(os.path.expanduser("~"), os.path.basename(url).replace(".git", ""))
        try:
            subprocess.run(["git", "clone", url, dest], check=True)
            QMessageBox.information(self, "Cloned", f"Repo cloned to {dest}")
        except subprocess.CalledProcessError:
            QMessageBox.critical(self, "Error", "Failed to clone repo.")

    def show_info(self, repo):
        info = f"""
Name: {repo['name']}
Full Name: {repo['full_name']}
Private: {repo['private']}
Stars: {repo['stargazers_count']}
Forks: {repo['forks_count']}
URL: {repo['html_url']}
"""
        QMessageBox.information(self, "Repo Info", info.strip())

    def next_page(self):
        self.page += 1
        self.fetch_repos()

    def prev_page(self):
        if self.page > 1:
            self.page -= 1
            self.fetch_repos()

def main():
    app = QApplication(sys.argv)
    win = GitHubApp()
    win.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()