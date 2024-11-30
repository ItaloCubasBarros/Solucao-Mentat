import os
import openai
import PyPDF2
from flask import Flask, render_template, request, redirect, url_for

# Configuração da chave da API do OpenAI
app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}

# Função para verificar se o arquivo é PDF
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Função para extrair o texto de um PDF
def extrair_texto_pdf(caminho_pdf):
    with open(caminho_pdf, 'rb') as arquivo:
        leitor = PyPDF2.PdfReader(arquivo)
        texto = ""
        for pagina in range(len(leitor.pages)):
            texto += leitor.pages[pagina].extract_text()
    return texto

# Função para gerar o resumo do texto extraído do PDF
def gerar_resumo(texto):
    try:
        resposta = openai.ChatCompletion.create(
            model="gpt-4",  
            messages=[{"role": "system", "content": "Você é um assistente de IA que cria resumos concisos."},
                      {"role": "user", "content": f"Resuma o seguinte texto:\n\n{texto}"}],
            max_tokens=200,  
            temperature=0.7
        )
        resumo = resposta['choices'][0]['message']['content'].strip()
        return resumo
    except Exception as e:
        print(f"Erro ao gerar resumo: {e}")
        return "Erro ao gerar resumo."

# Função para gerar um quiz com base no resumo
def gerar_quiz(resumo):
    try:
        prompt = f"Crie um quiz de múltipla escolha com 3 perguntas baseadas no seguinte resumo:\n\n{resumo}"

        resposta = openai.ChatCompletion.create(
            model="gpt-4", 
            messages=[{"role": "system", "content": "Você é um assistente de IA que cria quizzes."},
                      {"role": "user", "content": prompt}],
            max_tokens=250,
            temperature=0.7
        )

        quiz = resposta['choices'][0]['message']['content'].strip()
        return quiz
    except Exception as e:
        print(f"Erro ao gerar quiz: {e}")
        return "Erro ao gerar quiz."

# Função para gerar a persona e sugestões com base no feedback do aluno
# Função para gerar a persona e sugestões com base no feedback do aluno
def gerar_persona_e_sugestoes(feedback):
    try:
        prompt = f"""
        Um aluno da universidade escreveu o seguinte feedback para a aula de um professor:
        "{feedback}"
        
        Com base no feedback, defina a persona desse aluno, incluindo:
        1. O estilo de aprendizagem dele (exemplo: aprende melhor com práticas, interatividade, teoria, etc.).
        2. O que ele prefere em termos de metodologia e o que ele sugere para melhorar o aprendizado.
        3. Como o professor deve tratar esse aluno para maximizar seu engajamento e aprendizado.
        4. Faça um mapa de persona para o usuário baseado no seu feedback
        """
        
        resposta = openai.ChatCompletion.create(
            model="gpt-4",  
            messages=[{
                "role": "system", 
                "content": "Você é um assistente de IA que gera respostas detalhadas para perfis de estudantes e sugestões pedagógicas."
            },
            {
                "role": "user", 
                "content": prompt
            }],
            max_tokens=300,
            temperature=0.7
        )

        conteudo = resposta['choices'][0]['message']['content'].strip()
        persona, sugestao = conteudo.split("\n", 1)
        return persona, sugestao
    except Exception as e:
        print(f"Erro ao gerar persona e sugestões: {e}")
        return "Erro ao gerar persona", "Erro ao gerar sugestões"

# Rota para feedback do aluno
@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if request.method == 'POST':
        feedback = request.form['feedback']

        if feedback:
            try:
                persona, sugestao = gerar_persona_e_sugestoes(feedback)
                return render_template('feedback.html', feedback=feedback, persona=persona, sugestao=sugestao)
            except Exception as e:
                return render_template('feedback.html', error="Erro ao processar a solicitação. Tente novamente.")
    
    return render_template('feedback.html')

# Rota para upload de PDF e geração de quiz
@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
        arquivo = request.files['file']
        if arquivo and allowed_file(arquivo.filename):
            caminho_pdf = os.path.join(app.config['UPLOAD_FOLDER'], arquivo.filename)
            arquivo.save(caminho_pdf)
            
            texto_pdf = extrair_texto_pdf(caminho_pdf)
            resumo = gerar_resumo(texto_pdf)
            quiz = gerar_quiz(resumo)
            
            return render_template('quiz.html', resumo=resumo, quiz=quiz)
    
    return render_template('quiz.html')

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True)
