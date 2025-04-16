from flask import Flask, render_template, request
from groq import Groq
import os
import fitz 
import docx  
from dotenv import load_dotenv
import pandas as pd
from tabulate import tabulate

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = Groq(api_key=GROQ_API_KEY)

def extrair_texto(caminho_arquivo):
    extensao = os.path.splitext(caminho_arquivo)[1].lower()

    if extensao == ".txt":
        with open(caminho_arquivo, 'r', encoding='utf-8') as f:
            return f.read()

    elif extensao == ".pdf":
        texto_pdf = ""
        with fitz.open(caminho_arquivo) as doc:
            for pagina in doc:
                texto_pdf += pagina.get_text()
        return texto_pdf

    elif extensao == ".docx":
        doc = docx.Document(caminho_arquivo)
        return "\n".join([p.text for p in doc.paragraphs])
    
    elif extensao == ".xlsx":
        df = pd.read_excel(caminho_arquivo)
        markdown_output = tabulate(df, headers='keys', tablefmt='pipe', showindex=False)
        return markdown_output
    else:
        return "Formato de arquivo não suportado."

@app.route("/", methods=["GET", "POST"])
def index():
    response_text = ""
    user_input = ""

    if request.method == "POST":
        user_input = request.form.get("question", "")
        arquivo = request.files.get("arquivo")

        arquivo_texto = ""
        if arquivo and arquivo.filename != "":
            caminho = os.path.join(UPLOAD_FOLDER, arquivo.filename)
            arquivo.save(caminho)

            try:
                arquivo_texto = extrair_texto(caminho)
            except Exception as e:
                response_text = f"Erro ao ler o arquivo: {str(e)}"
                return render_template("index.html", response=response_text, question=user_input)

        
        prompt_final = user_input
        if arquivo_texto:
            prompt_final += f"\n\n[Conteúdo do arquivo]:\n{arquivo_texto}"

        try:
            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt_final}],
                model="llama-3.1-8b-instant",
                temperature=0.0
            )
            response_text = chat_completion.choices[0].message.content

        except Exception as e:
            response_text = f"Erro: {str(e)}"

    return render_template("index.html", response=response_text, question=user_input)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=1234,debug=True)
