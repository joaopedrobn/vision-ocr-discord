# Conteúdo do arquivo main.py (Versão Final com aiohttp)

import os
import discord
import aiohttp # <-- MUDANÇA: Importa a nova biblioteca
from dotenv import load_dotenv
from flask import Flask
from threading import Thread

# Bloco do Servidor Web (Flask)
app = Flask('')
@app.route('/')
def home():
    return "Servidor do Bot está no ar!"
def run_app():
  app.run(host='0.0.0.0', port=8080)
def start_web_server():
    t = Thread(target=run_app)
    t.start()

# Carregar variáveis de ambiente
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
OCR_API_KEY = os.getenv('OCR_API_KEY')

# Configurar Intents
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'Bot conectado como {client.user}')
    print('Pronto para ler imagens com o comando !ocr')
    print('------')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.lower().startswith('!ocr'):
        if not message.attachments:
            await message.reply("⚠️ Ops! Você precisa anexar uma imagem junto com o comando `!ocr`.")
            return

        attachment = message.attachments[0]
        if not attachment.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.webp')):
            await message.reply("⚠️ Por favor, envie um arquivo de imagem válido (`.png`, `.jpg`, etc.).")
            return
            
        try:
            temp_msg = await message.reply("🔎 Processando sua imagem...")

            payload = {
                'apikey': OCR_API_KEY,
                'url': attachment.url,
                'language': 'por',
            }
            
            # --- MUDANÇA PRINCIPAL: Usando aiohttp em vez de requests ---
            async with aiohttp.ClientSession() as session:
                async with session.post('https://api.ocr.space/parse/image', data=payload) as response:
                    # Verifica se a requisição foi bem sucedida
                    if response.status != 200:
                        await temp_msg.delete()
                        await message.reply("❌ Ocorreu um erro ao contatar a API de OCR.")
                        return
                    
                    result = await response.json()
            # --- FIM DA MUDANÇA ---

            await temp_msg.delete()

            if result['IsErroredOnProcessing']:
                error_message = result.get('ErrorMessage', ['Erro desconhecido.'])[0]
                await message.reply(f"❌ Erro ao processar a imagem: {error_message}")
                return

            parsed_results = result.get('ParsedResults')
            if not parsed_results or not parsed_results[0]['ParsedText'].strip():
                await message.reply("❌ Não consegui extrair nenhum texto da imagem.")
                return

            extracted_text = parsed_results[0]['ParsedText']

            if len(extracted_text) > 4000:
                extracted_text = extracted_text[:4000] + "\n\n... (texto cortado por ser muito longo)"

            embed = discord.Embed(
                title="📝 OCR",
                description=f"```{extracted_text}```",
                color=discord.Color.blue()
            )
            embed.set_footer(text=f"Imagem enviada por {message.author.display_name}")
            await message.reply(embed=embed)

        except Exception as e:
            # Se a mensagem temporária ainda existir, tente deletá-la
            if 'temp_msg' in locals() and temp_msg:
                await temp_msg.delete()
            print(f"Ocorreu um erro inesperado: {e}")
            await message.reply("🤖 Desculpe, ocorreu um erro inesperado ao tentar processar sua imagem.")

# Iniciar o bot e o servidor
if not DISCORD_TOKEN or not OCR_API_KEY:
    print("ERRO: Token do Discord ou chave da API do OCR não encontrados.")
else:
    start_web_server()
    client.run(DISCORD_TOKEN)