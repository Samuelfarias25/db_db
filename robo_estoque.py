import oracledb
import csv
import os
import time
from datetime import datetime

# --- 1. CONFIGURAÇÕES DO BANCO ---
DB_USER = 'system'
DB_PASS = '0064'  # <--- Atualiza a senha!
DB_DSN = 'localhost:1521/FREEPDB1'

# Variável para guardar a memória do robô
ultimo_estoque = []

# Cria a pasta de backups se não existir
if not os.path.exists('backups'):
    os.makedirs('backups')

def pegar_conexao():
    return oracledb.connect(user=DB_USER, password=DB_PASS, dsn=DB_DSN)

def gerar_csv(dados):
    """Gera o arquivo físico no computador"""
    nome_arquivo = datetime.now().strftime("backups/estoque_%Y-%m-%d_%H-%M-%S.csv")
    
    try:
        with open(nome_arquivo, mode='w', newline='', encoding='utf-8') as arquivo:
            escritor = csv.writer(arquivo, delimiter=';')
            escritor.writerow(['ID', 'SKU', 'NOME', 'ESTOQUE']) # Cabeçalho
            
            # Escreve os dados (transforma tuplas em lista se necessário)
            escritor.writerows(dados)
            
        print(f"✅ [SUCESSO] Novo arquivo gerado: {nome_arquivo}")
    except Exception as e:
        print(f"❌ Erro ao salvar arquivo: {e}")

def iniciar_robo():
    global ultimo_estoque
    print("🤖 Robô de Monitoramento Iniciado...")
    print(f"📂 Os arquivos serão salvos na pasta: {os.path.abspath('backups')}")
    print("Pressioine CTRL+C para parar o robô.\n")

    while True:
        conexao = None
        cursor = None
        try:
            # 1. Conecta ao Banco
            conexao = pegar_conexao()
            cursor = conexao.cursor()
            
            # 2. Busca os dados atuais
            sql = "SELECT id, sku, nome, estoque FROM sku ORDER BY id ASC"
            cursor.execute(sql)
            estoque_atual = cursor.fetchall() # Retorna uma lista de tuplas
            
            # 3. Compara com a memória
            # Se a memória não estiver vazia E for diferente do atual...
            if ultimo_estoque and estoque_atual != ultimo_estoque:
                print(f"🚨 [{datetime.now().strftime('%H:%M:%S')}] Alteração detectada no DBeaver!")
                gerar_csv(estoque_atual)
            
            elif not ultimo_estoque:
                print(f"ℹ️  [{datetime.now().strftime('%H:%M:%S')}] Carga inicial carregada. Aguardando alterações...")

            # Atualiza a memória
            ultimo_estoque = estoque_atual

        except oracledb.DatabaseError as e:
            print(f"❌ Erro de conexão com Oracle: {e}")
        except Exception as e:
            print(f"❌ Erro inesperado: {e}")
        finally:
            if cursor: cursor.close()
            if conexao: conexao.close()
        
        # 4. Dorme por 5 segundos antes de checar de novo
        time.sleep(5)

if __name__ == '__main__':
    iniciar_robo()