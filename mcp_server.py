import json
import os
import sys

from app.ai_service import processar_mensagem_rh
from app.evaluator import executar_avaliacao_completa
from app.pdf_filler import preencher_ficha_pdf

TOOLS = [
    {
        "name": "processar_implantacao_dentalis",
        "description": (
            "Extrai dados cadastrais e de beneficiÃ¡rios de uma mensagem de RH, "
            "preenche a Ficha de ImplantaÃ§Ã£o PDF oficial da Dentalis e gera 2 opÃ§Ãµes "
            "de comunicado HTML validadas contra o Guia de Marca."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "mensagem": {
                    "type": "string",
                    "description": "Texto completo da mensagem enviada pelo RH (e-mail, WhatsApp ou Slack).",
                },
                "data_recebimento": {
                    "type": "string",
                    "description": "Data de recebimento no formato DD/MM/AAAA (padrÃ£o: 05/11/2026).",
                },
            },
            "required": ["mensagem"],
        },
    },
    {
        "name": "executar_benchmark_dentalis",
        "description": (
            "Executa o harness de avaliaÃ§Ã£o nas 5 mensagens de exemplo da Dentalis "
            "e retorna a taxa de acerto por cenÃ¡rio e conformidade com o Guia de Marca."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
]


def responder(req_id, result=None, error=None):
    payload = {"jsonrpc": "2.0", "id": req_id}
    if error is not None:
        payload["error"] = error
    else:
        payload["result"] = result
    sys.stdout.write(json.dumps(payload, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def executar_tool(nome: str, argumentos: dict):
    if nome == "processar_implantacao_dentalis":
        mensagem = (argumentos.get("mensagem") or "").strip()
        if not mensagem:
            raise ValueError("O parÃ¢metro 'mensagem' Ã© obrigatÃ³rio.")
        data_recebimento = (argumentos.get("data_recebimento") or "05/11/2026").strip()

        resultado = processar_mensagem_rh(mensagem, data_recebimento)
        os.makedirs("resultados_exemplo", exist_ok=True)
        caminho_pdf = os.path.join("resultados_exemplo", "ficha_mcp_gerada.pdf")
        preencher_ficha_pdf(resultado["ficha"], "ficha_implantacao_dental.pdf", caminho_pdf)
        resultado["pdf_gerado"] = caminho_pdf
        return resultado

    if nome == "executar_benchmark_dentalis":
        return executar_avaliacao_completa(salvar_arquivos=False)

    raise ValueError(f"Ferramenta desconhecida: {nome}")


def main():
    for linha in sys.stdin:
        linha = linha.strip()
        if not linha:
            continue

        try:
            req = json.loads(linha)
        except json.JSONDecodeError:
            continue

        req_id = req.get("id")
        metodo = req.get("method")
        params = req.get("params") or {}

        # NotificaÃ§Ãµes JSON-RPC nÃ£o possuem 'id' e nÃ£o devem receber resposta
        if req_id is None:
            continue

        if metodo == "initialize":
            responder(
                req_id,
                result={
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "dentalis-implantacao-mcp", "version": "1.0.0"},
                },
            )
        elif metodo == "ping":
            responder(req_id, result={})
        elif metodo == "tools/list":
            responder(req_id, result={"tools": TOOLS})
        elif metodo == "tools/call":
            nome_tool = params.get("name")
            argumentos = params.get("arguments") or {}
            try:
                saida = executar_tool(nome_tool, argumentos)
                responder(
                    req_id,
                    result={
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(saida, ensure_ascii=False, indent=2),
                            }
                        ]
                    },
                )
            except Exception as exc:
                responder(
                    req_id,
                    result={
                        "isError": True,
                        "content": [{"type": "text", "text": f"Erro ao executar ferramenta: {exc}"}],
                    },
                )
        else:
            responder(req_id, error={"code": -32601, "message": f"MÃ©todo nÃ£o suportado: {metodo}"})


if __name__ == "__main__":
    main()
