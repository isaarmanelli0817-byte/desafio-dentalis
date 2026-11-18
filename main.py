import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from app.ai_service import processar_mensagem_rh
from app.evaluator import executar_avaliacao_completa
from app.pdf_filler import preencher_ficha_pdf

HOST = "127.0.0.1"
PORT = 8000
PDF_SAIDA_ATUAL = os.path.join("resultados_exemplo", "ficha_implantacao_gerada.pdf")


class DentalisHandler(BaseHTTPRequestHandler):
    def _enviar_json(self, dados: dict | list, status: int = 200):
        corpo = json.dumps(dados, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def _enviar_arquivo(self, caminho: str, content_type: str, download_nome: str | None = None):
        if not os.path.exists(caminho):
            self._enviar_json({"erro": "Arquivo não encontrado"}, status=404)
            return

        with open(caminho, "rb") as f:
            conteudo = f.read()

        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(conteudo)))
        if download_nome:
            self.send_header("Content-Disposition", f'attachment; filename="{download_nome}"')
        self.end_headers()
        self.wfile.write(conteudo)

    def do_GET(self):
        rota = urlparse(self.path).path

        if rota == "/":
            self._enviar_arquivo("static/index.html", "text/html; charset=utf-8")
        elif rota == "/static/style.css":
            self._enviar_arquivo("static/style.css", "text/css; charset=utf-8")
        elif rota == "/static/script.js":
            self._enviar_arquivo("static/script.js", "application/javascript; charset=utf-8")
        elif rota == "/api/exemplos":
            with open("data/mensagens_exemplo.json", "r", encoding="utf-8") as f:
                self._enviar_json(json.load(f))
        elif rota == "/api/avaliacao":
            relatorio_path = "resultados_exemplo/relatorio_avaliacao.json"
            if os.path.exists(relatorio_path):
                with open(relatorio_path, "r", encoding="utf-8") as f:
                    self._enviar_json(json.load(f))
            else:
                self._enviar_json(executar_avaliacao_completa(salvar_arquivos=True))
        elif rota == "/api/download-pdf":
            self._enviar_arquivo(
                PDF_SAIDA_ATUAL,
                "application/pdf",
                download_nome="ficha_implantacao_dentalis.pdf",
            )
        else:
            self._enviar_json({"erro": "Rota não encontrada"}, status=404)

    def do_POST(self):
        rota = urlparse(self.path).path
        tamanho = int(self.headers.get("Content-Length", 0))
        corpo_raw = self.rfile.read(tamanho).decode("utf-8") if tamanho else "{}"

        try:
            payload = json.loads(corpo_raw)
        except json.JSONDecodeError:
            self._enviar_json({"erro": "JSON inválido"}, status=400)
            return

        if rota == "/api/processar":
            mensagem = (payload.get("mensagem") or "").strip()
            data_recebimento = (payload.get("data_recebimento") or "05/11/2026").strip()

            if not mensagem:
                self._enviar_json({"erro": "Informe a mensagem do RH."}, status=400)
                return

            try:
                resultado = processar_mensagem_rh(mensagem, data_recebimento)
                os.makedirs("resultados_exemplo", exist_ok=True)
                preencher_ficha_pdf(
                    resultado["ficha"],
                    "ficha_implantacao_dental.pdf",
                    PDF_SAIDA_ATUAL,
                )
                resultado["pdf_url"] = "/api/download-pdf"
                self._enviar_json(resultado)
            except Exception as e:
                self._enviar_json({"erro": str(e)}, status=500)

        elif rota == "/api/avaliar":
            try:
                resumo = executar_avaliacao_completa(salvar_arquivos=True)
                self._enviar_json(resumo)
            except Exception as e:
                self._enviar_json({"erro": str(e)}, status=500)
        else:
            self._enviar_json({"erro": "Rota não encontrada"}, status=404)


if __name__ == "__main__":
    servidor = ThreadingHTTPServer((HOST, PORT), DentalisHandler)
    print(f"Servidor Dentalis rodando em http://{HOST}:{PORT}")
    print("Pressione Ctrl+C para encerrar.")
    servidor.serve_forever()