# 📚 Library MCP Server

A modern **Model Context Protocol (MCP) Server** for library management, built with **Python** and **Streamlit**. This project enables AI assistants and MCP-compatible clients to interact with a library system through standardized tools for searching, retrieving, and managing book information.

---

## ✨ Features

* 📖 Search books by title, author, or keyword
* 📚 Retrieve detailed book information
* 🤖 MCP-compatible server for AI applications
* 🌐 Interactive Streamlit web interface
* ⚡ Fast, lightweight, and easy to extend
* 🐍 Built entirely with Python

---

## 🛠️ Tech Stack

* **Python 3.12+**
* **Model Context Protocol (MCP)**
* **Streamlit**
* **Pydantic**
* **FastMCP** (if applicable)
* **uv / pip** for dependency management

---

## 📂 Project Structure

```text
Library_mcp_server/
│
├── app.py                 # Main MCP server
├── client.py              # Example MCP client
├── streamlit_app.py       # Streamlit interface
├── requirements.txt       # Project dependencies
├── README.md              # Documentation
├── .gitignore
└── ...
```

---

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/Tchalz/Library_mcp_server.git
cd Library_mcp_server
```

### 2. Create a Virtual Environment

Windows

```bash
python -m venv .venv
```

Activate it:

```bash
.venv\Scripts\activate
```

macOS/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## ▶️ Running the MCP Server

```bash
python app.py
```

---

## 🌐 Running the Streamlit Interface

```bash
streamlit run streamlit_app.py
```

Then open the URL displayed in your terminal (typically `http://localhost:8501`).

---

## 🔌 MCP Integration

This server exposes tools through the **Model Context Protocol**, making it easy for compatible AI assistants and applications to connect and use its capabilities.

Example workflow:

1. Start the MCP server.
2. Connect with an MCP client.
3. Call the available tools.
4. Receive structured responses.

---

## 📦 Installation Requirements

* Python 3.12 or newer
* Git
* pip

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## 🤝 Contributing

Contributions are welcome.

To contribute:

1. Fork the repository.
2. Create a feature branch.
3. Commit your changes.
4. Open a Pull Request.

---

## 📄 License

This project is licensed under the MIT License. Feel free to use, modify, and distribute it in accordance with the license terms.

---

## 👨‍💻 Author

**Chibuzor Nwozuzu**

GitHub: https://github.com/Tchalz

---

## ⭐ Support

If you find this project useful:

* ⭐ Star the repository
* 🍴 Fork it
* 🐛 Report issues
* 💡 Suggest new features

Your support helps improve the project and makes it more useful for the community.
