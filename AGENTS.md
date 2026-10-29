# Instruções para agentes

Após qualquer alteração no código, documentação, configuração ou testes, siga
obrigatoriamente este ciclo antes de concluir a tarefa:

1. Faça code review das alterações com `git diff` e `git diff --check`.
2. Execute toda a suíte de testes com
   `./venv/bin/python -m unittest discover -s tests -v`.
3. Se o code review ou qualquer teste identificar um problema, corrija-o e
   repita os dois passos até que ambos terminem sem falhas.

Não considere uma alteração concluída enquanto revisão e testes não tiverem
passado.
