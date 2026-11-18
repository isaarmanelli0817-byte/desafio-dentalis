from app.evaluator import executar_avaliacao_completa

res = executar_avaliacao_completa(salvar_arquivos=True)

print(f"\nMédia Geral: {res['media_geral']}%")
for r in res["resultados"]:
    print(f"- {r['titulo']}: {r['percentual']}% ({r['acertos']}/{r['total']}) | Marca OK: {r['marca_aprovada']}")