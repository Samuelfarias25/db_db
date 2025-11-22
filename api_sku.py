from flask import Flask, jsonify
import oracledb
import csv
import os
import time
import threading
from datetime import datetime

app = Flask(__name__)

# --- CONFIGURAÇÕES ---
DB_USER = 'system'
DB_PASS = '0064'  # Tua senha mantida
DB_DSN = 'localhost:1521/FREEPDB1'

# Variável global para guardar a memória do robô
ultimo_estado_conhecido = []

# --- CRIAR PASTA DE BACKUP ---
if not os.path.exists('backups'):
    os.makedirs('backups')

def pegar_conexao():
    return oracledb.connect(user=DB_USER, password=DB_PASS, dsn=DB_DSN)

# --- FUNÇÃO DO MONITOR (RODA EM SEGUNDO PLANO) ---
def monitorar_banco():
    global ultimo_estado_conhecido
    print("👀 Monitor de banco iniciado (Automático)...")
    
    while True:
        try:
            conexao = pegar_conexao()
            cursor = conexao.cursor()
            
            # Pega os dados atuais
            cursor.execute("SELECT id, sku, nome, estoque FROM sku ORDER BY id ASC")
            estado_atual = cursor.fetchall()
            
            # LÓGICA DE COMPARAÇÃO
            if estado_atual != ultimo_estado_conhecido:
                # Se não for a primeira execução, gera backup
                if ultimo_estado_conhecido: 
                    print(f"🚨 [{datetime.now().strftime('%H:%M:%S')}] Alteração no DBeaver detectada! Gerando CSV...")
                    salvar_csv(estado_atual)
                else:
                    print("ℹ️ Carga inicial de dados concluída.")
                
                # Atualiza a memória
                ultimo_estado_conhecido = estado_atual
            
            cursor.close()
            conexao.close()
            
        except Exception as e:
            print(f"❌ Erro no monitor: {e}")
        
        time.sleep(5) # Verifica a cada 5 segundos

def salvar_csv(dados):
    nome_arquivo = datetime.now().strftime("backups/backup_%Y-%m-%d_%H-%M-%S.csv")
    
    try:
        with open(nome_arquivo, mode='w', newline='', encoding='utf-8') as arquivo:
            escritor = csv.writer(arquivo, delimiter=';')
            escritor.writerow(['ID', 'SKU', 'NOME', 'ESTOQUE'])
            escritor.writerows(dados)
        print(f"✅ Arquivo salvo: {nome_arquivo}")
    except Exception as e:
        print(f"❌ Erro ao salvar CSV: {e}")

# --- ROTA DA API (JSON) ---
@app.route('/skus', methods=['GET'])
def listar_skus():
    global ultimo_estado_conhecido
    
    colunas = ['ID', 'SKU', 'NOME', 'ESTOQUE']
    
    # Se a memória estiver vazia (ex: acabou de ligar e o monitor ainda não rodou)
    if not ultimo_estado_conhecido:
        conexao = None
        cursor = None
        try:
            conexao = pegar_conexao()
            cursor = conexao.cursor()
            cursor.execute("SELECT id, sku, nome, estoque FROM sku ORDER BY id ASC")
            ultimo_estado_conhecido = cursor.fetchall()
        except Exception as e:
            return jsonify({"erro": str(e)}), 500
        finally:
            if cursor: cursor.close()
            if conexao: conexao.close()

    # Transforma em JSON
    resultados = []
    for linha in ultimo_estado_conhecido:
        resultados.append(dict(zip(colunas, linha)))
        
    return jsonify(resultados)

# --- INICIAR TUDO ---
if __name__ == '__main__':
    # Inicia o Robô em paralelo
    thread_monitor = threading.Thread(target=monitorar_banco)
    thread_monitor.daemon = True 
    thread_monitor.start()
    
    print("🚀 API Online em: http://localhost:5000/skus")
    # use_reloader=False é obrigatório aqui para não duplicar o robô
    app.run(debug=True, port=5000, use_reloader=False)