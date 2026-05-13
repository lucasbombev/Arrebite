# Arrebite
Pequeno programa que impede o notebook de suspender ou desligar a tela automaticamente. Com interface gráfica simples e menu para terminal. Ideal para apresentações, downloads longos ou monitoramento noturno.

---
<img width="517" height="425" alt="image" src="/ligth_mode.png" />
<img width="517" height="425" alt="image" src="/dark_mode.png" />


---

```markdown
# ⚡ Arrebite – Mantenha seu notebook sempre acordado

Pequeno utilitário para **impedir que o notebook entre em suspensão automática** ou que a **tela se apague/bloqueie** sozinha.  
Perfeito para apresentações, downloads longos, monitoramento noturno ou qualquer situação em que você precisa que o computador permaneça ativo.

---

## ✨ Funcionalidades

- ✅ Desabilita a **suspensão automática** do sistema
- ✅ Desabilita o **desligamento/bloqueio automático da tela**
- ✅ Restaura as configurações originais com um clique
- ✅ Interface gráfica amigável (GUI) ou versão para terminal
- ✅ Funciona no **Linux** (GNOME, KDE, Xfce) e **Windows**
- ✅ Não precisa de reinicialização – efeito imediato e reversível

---

## 📦 Requisitos

- **Python 3.6 ou superior**
- Para Linux (opcional, mas recomendado): `xrandr`, `xset`, `gsettings` (já vêm na maioria das distribuições)
- Para Windows: nenhuma dependência extra – usa `powercfg`
- Para a interface gráfica (GUI): apenas `tkinter` (geralmente incluso no Python). Se não estiver, instale com:
  ```bash
  # Ubuntu/Debian
  sudo apt install python3-tk

  # Windows
  # já vem com o Python oficial
  ```

---

## 🚀 Instalação

1. **Clone o repositório**
   ```bash
   git clone https://github.com/seuusuario/arrebite.git
   cd arrebite
   ```

2. **Execute diretamente** (não precisa instalar)
   - Versão terminal:
     ```bash
     python3 arrebite.py
     ```
   - Versão com interface gráfica:
     ```bash
     python3 arrebite_gui.py
     ```

---

## 📖 Tutorial de uso

### 🔹 Versão Terminal (`arrebite.py`)

Ao executar, você verá um menu como este:

```
========================================
        ARREBITE - Mantenha seu PC acordado
========================================
[1] Ativar modo anti-sono (desliga suspensão + tela)
[2] Restaurar configurações padrão
[3] Sair
Escolha uma opção:
```

- **Opção 1** → Ativa imediatamente as duas proteções. O sistema não suspenderá e a tela nunca apagará/bloqueará sozinha.
- **Opção 2** → Volta às configurações originais (ex: suspensão após 15 min, tela bloqueia após 5 min).
- **Opção 3** → Sai do programa. **Atenção:** ao sair sem restaurar, as alterações permanecem ativas até você restaurar manualmente ou reiniciar o computador.

> 💡 Dica: Execute em um terminal separado. Para interromper o programa e restaurar automaticamente, basta escolher a opção 2 antes de sair.

---

### 🔹 Versão com Interface Gráfica (`arrebite_gui.py`)

1. Execute o arquivo:
   ```bash
   python3 arrebite_gui.py
   ```
   Uma janela será aberta.

2. **Janela principal** – contém:
   - Botão **🟢 ATIVAR MODO ANTI-SONO** → aplica as duas proteções.
   - Botão **🟠 RESTAURAR PADRÕES** → volta ao comportamento normal.
   - Botão **🔴 SAIR** → fecha o programa (pergunta se deseja restaurar antes).
   - Área de **log / mensagens** que mostra o que foi feito e eventuais erros.

3. **Comportamento**:
   - Clique em **ATIVAR** – o sistema fica "acordado" indefinidamente. O botão "ATIVAR" fica desabilitado (cinza) e "RESTAURAR" habilitado.
   - Clique em **RESTAURAR** – as configurações voltam ao normal. O botão "RESTAURAR" desabilita e "ATIVAR" reabilita.
   - Feche a janela com o **X** – aparece uma pergunta: *"Deseja restaurar as configurações antes de sair?"* – escolha Sim para restaurar ou Não para manter o modo ativo.

---

## ⚠️ Observações importantes

- Os comandos utilizados afetam **apenas a sessão atual** do usuário. Após reiniciar o computador, as configurações padrão voltam.
- Em alguns ambientes Linux (Wayland), pode ser necessário ajustar permissões ou usar ferramentas alternativas. O programa detecta automaticamente X11 e usa `gsettings` para GNOME.
- No Windows, o programa executa `powercfg /change ...` sem privilégios de administrador – funciona apenas para as configurações de energia do usuário atual.

---

## 🛠️ Como contribuir

Sinta-se à vontade para abrir **issues** ou **pull requests**. Sugestões de melhoria, relatos de bugs em distribuições Linux específicas ou adaptações para macOS são bem-vindos.

---

## 📄 Licença

Distribuído sob a licença **MIT**. Consulte o arquivo `LICENSE` para mais informações.

---

## 🧠 Autor

Criado por [Lucas] – [@lucasbombev](https://github.com/lucasbombev)  
⚡ *Arrebite – porque notebooks também precisam de um "café" para ficar acordados.*
```
