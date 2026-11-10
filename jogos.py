"""
🎮 Fliperama Streamlit — vários jogos em um único arquivo.
Rodar localmente:  streamlit run jogos.py
"""
import random

import chess
import requests
import streamlit as st

st.set_page_config(page_title="Fliperama Streamlit", page_icon="🎮", layout="centered")
S = st.session_state


def css_botoes(altura_px: int, fonte_rem: float):
    """Deixa os botões do jogo atual largos e no tamanho certo."""
    st.markdown(
        f"""<style>
        div.stButton > button {{
            width: 100%; min-height: {altura_px}px; font-size: {fonte_rem}rem;
        }}
        </style>""",
        unsafe_allow_html=True,
    )


# =====================================================================
# 1) ADIVINHE O NÚMERO
# =====================================================================
NIVEIS_ADV = {"Fácil (1–50)": 50, "Médio (1–100)": 100, "Difícil (1–500)": 500}


def adv_novo(limite):
    S.adv_limite = limite
    S.adv_alvo = random.randint(1, limite)
    S.adv_tentativas = []
    S.adv_fim = False


def jogo_adivinha():
    st.header("🔢 Adivinhe o Número")
    nivel = st.radio("Dificuldade", list(NIVEIS_ADV), horizontal=True, key="adv_nivel")
    limite = NIVEIS_ADV[nivel]
    if S.get("adv_limite") != limite:
        adv_novo(limite)

    st.write(f"Pensei em um número entre **1 e {limite}**. Consegue descobrir?")

    if not S.adv_fim:
        with st.form("adv_form", clear_on_submit=True):
            palpite = st.number_input("Seu palpite", 1, limite, step=1)
            if st.form_submit_button("Chutar 🎯"):
                palpite = int(palpite)
                S.adv_tentativas.append(palpite)
                if palpite == S.adv_alvo:
                    S.adv_fim = True

    if S.adv_tentativas:
        ultimo = S.adv_tentativas[-1]
        if S.adv_fim:
            st.success(f"🎉 Acertou! Era **{S.adv_alvo}** — em {len(S.adv_tentativas)} tentativa(s).")
            st.balloons()
        elif ultimo < S.adv_alvo:
            st.info(f"⬆️ {ultimo} é **baixo**. Tente um número maior.")
        else:
            st.info(f"⬇️ {ultimo} é **alto**. Tente um número menor.")
        st.caption("Palpites: " + ", ".join(map(str, S.adv_tentativas)))

    if st.button("🔄 Novo jogo", key="adv_reset"):
        adv_novo(limite)
        st.rerun()


# =====================================================================
# 2) JOGO DA VELHA (contra o computador)
# =====================================================================
LINHAS = [(0, 1, 2), (3, 4, 5), (6, 7, 8), (0, 3, 6),
          (1, 4, 7), (2, 5, 8), (0, 4, 8), (2, 4, 6)]


def velha_vencedor(b):
    for a, m, c in LINHAS:
        if b[a] and b[a] == b[m] == b[c]:
            return b[a]
    return "Empate" if all(b) else None


def minimax(b, jogador):
    v = velha_vencedor(b)
    if v == "O":
        return 1, None
    if v == "X":
        return -1, None
    if v == "Empate":
        return 0, None
    melhor = (-2, None) if jogador == "O" else (2, None)
    for i in range(9):
        if not b[i]:
            b[i] = jogador
            nota, _ = minimax(b, "X" if jogador == "O" else "O")
            b[i] = ""
            if (jogador == "O" and nota > melhor[0]) or (jogador == "X" and nota < melhor[0]):
                melhor = (nota, i)
    return melhor


def velha_jogada_pc(b, nivel):
    livres = [i for i in range(9) if not b[i]]
    chance_esperta = {"Fácil": 0.0, "Médio": 0.6, "Impossível": 1.0}[nivel]
    if random.random() < chance_esperta:
        return minimax(b, "O")[1]
    return random.choice(livres)


def velha_novo():
    S.velha_tab = [""] * 9
    S.velha_fim = None


def velha_click(i):
    b = S.velha_tab
    if b[i] or S.velha_fim:
        return
    b[i] = "X"
    S.velha_fim = velha_vencedor(b)
    if not S.velha_fim:
        b[velha_jogada_pc(b, S.velha_nivel)] = "O"
        S.velha_fim = velha_vencedor(b)
    if S.velha_fim:
        chave = {"X": "voce", "O": "pc", "Empate": "empate"}[S.velha_fim]
        S.velha_placar[chave] += 1


def jogo_velha():
    st.header("❌⭕ Jogo da Velha")
    if "velha_tab" not in S:
        velha_novo()
        S.velha_placar = {"voce": 0, "pc": 0, "empate": 0}
    st.radio("Nível do computador", ["Fácil", "Médio", "Impossível"],
             index=1, horizontal=True, key="velha_nivel")

    p = S.velha_placar
    c1, c2, c3 = st.columns(3)
    c1.metric("Você (❌)", p["voce"])
    c2.metric("Empates", p["empate"])
    c3.metric("Computador (⭕)", p["pc"])

    css_botoes(90, 2.2)
    simbolo = {"X": "❌", "O": "⭕", "": "·"}
    for r in range(3):
        cols = st.columns(3)
        for c in range(3):
            i = r * 3 + c
            cols[c].button(simbolo[S.velha_tab[i]], key=f"velha_{i}",
                           on_click=velha_click, args=(i,),
                           disabled=bool(S.velha_tab[i] or S.velha_fim))

    fim = S.velha_fim
    if fim == "X":
        st.success("🎉 Você venceu!")
    elif fim == "O":
        st.error("🤖 O computador venceu!")
    elif fim == "Empate":
        st.warning("🤝 Deu velha!")

    if st.button("🔄 Nova partida", key="velha_reset"):
        velha_novo()
        st.rerun()


# =====================================================================
# 3) FORCA
# =====================================================================
PALAVRAS = {
    "Animais": ["ELEFANTE", "GIRAFA", "TUCANO", "CAPIVARA", "JACARE", "ONCA", "TAMANDUA", "PINGUIM"],
    "Frutas": ["ABACAXI", "JABUTICABA", "MANGA", "GOIABA", "MARACUJA", "ACEROLA", "PITANGA"],
    "Países": ["BRASIL", "ARGENTINA", "PORTUGAL", "JAPAO", "CANADA", "MEXICO", "AUSTRALIA"],
    "Tecnologia": ["PYTHON", "STREAMLIT", "GITHUB", "TECLADO", "INTERNET", "ALGORITMO"],
}
DESENHOS = [
    "  +---+\n      |\n      |\n      |\n     ===",
    "  +---+\n  O   |\n      |\n      |\n     ===",
    "  +---+\n  O   |\n  |   |\n      |\n     ===",
    "  +---+\n  O   |\n /|   |\n      |\n     ===",
    "  +---+\n  O   |\n /|\\  |\n      |\n     ===",
    "  +---+\n  O   |\n /|\\  |\n /    |\n     ===",
    "  +---+\n  O   |\n /|\\  |\n / \\  |\n     ===",
]
MAX_ERROS = len(DESENHOS) - 1


def forca_novo():
    S.forca_cat = random.choice(list(PALAVRAS))
    S.forca_palavra = random.choice(PALAVRAS[S.forca_cat])
    S.forca_letras = set()
    S.forca_erros = 0


def forca_chute(letra):
    if letra in S.forca_letras:
        return
    S.forca_letras.add(letra)
    if letra not in S.forca_palavra:
        S.forca_erros += 1


def jogo_forca():
    st.header("🪢 Forca")
    if "forca_palavra" not in S:
        forca_novo()

    palavra = S.forca_palavra
    venceu = all(l in S.forca_letras for l in palavra)
    perdeu = S.forca_erros >= MAX_ERROS

    col_desenho, col_info = st.columns([1, 2])
    col_desenho.code(DESENHOS[S.forca_erros], language=None)
    with col_info:
        st.write(f"**Dica:** {S.forca_cat}")
        mostra = " ".join(l if (l in S.forca_letras or perdeu) else "_" for l in palavra)
        st.markdown(f"### `{mostra}`")
        st.write(f"Erros: **{S.forca_erros}/{MAX_ERROS}**")

    if venceu:
        st.success("🎉 Você salvou o boneco!")
    elif perdeu:
        st.error(f"💀 Enforcado! A palavra era **{palavra}**.")
    else:
        css_botoes(42, 1.0)
        alfabeto = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        por_linha = 9
        for inicio in range(0, len(alfabeto), por_linha):
            cols = st.columns(por_linha)
            for j, letra in enumerate(alfabeto[inicio:inicio + por_linha]):
                cols[j].button(letra, key=f"forca_{letra}", on_click=forca_chute,
                               args=(letra,), disabled=letra in S.forca_letras)

    if st.button("🔄 Nova palavra", key="forca_reset"):
        forca_novo()
        st.rerun()


# =====================================================================
# 4) PEDRA, PAPEL E TESOURA
# =====================================================================
OPCOES = {"Pedra": "🪨", "Papel": "📄", "Tesoura": "✂️"}
GANHA_DE = {"Pedra": "Tesoura", "Papel": "Pedra", "Tesoura": "Papel"}


def ppt_jogar(escolha):
    pc = random.choice(list(OPCOES))
    if escolha == pc:
        res = "empate"
    elif GANHA_DE[escolha] == pc:
        res = "voce"
    else:
        res = "pc"
    S.ppt_placar[res] += 1
    S.ppt_ultimo = (escolha, pc, res)


def jogo_ppt():
    st.header("🪨📄✂️ Pedra, Papel e Tesoura")
    if "ppt_placar" not in S:
        S.ppt_placar = {"voce": 0, "pc": 0, "empate": 0}
        S.ppt_ultimo = None

    p = S.ppt_placar
    c1, c2, c3 = st.columns(3)
    c1.metric("Você", p["voce"])
    c2.metric("Empates", p["empate"])
    c3.metric("Computador", p["pc"])

    css_botoes(80, 1.4)
    cols = st.columns(3)
    for col, (nome, emoji) in zip(cols, OPCOES.items()):
        col.button(f"{emoji} {nome}", key=f"ppt_{nome}", on_click=ppt_jogar, args=(nome,))

    if S.ppt_ultimo:
        voce, pc, res = S.ppt_ultimo
        st.markdown(f"## {OPCOES[voce]} &nbsp; vs &nbsp; {OPCOES[pc]}")
        msg = {"voce": st.success, "pc": st.error, "empate": st.warning}[res]
        texto = {"voce": f"Você venceu! {voce} ganha de {pc}.",
                 "pc": f"Você perdeu! {pc} ganha de {voce}.",
                 "empate": "Empate!"}[res]
        msg(texto)

    if st.button("🔄 Zerar placar", key="ppt_reset"):
        del S["ppt_placar"]
        st.rerun()


# =====================================================================
# 5) JOGO DA MEMÓRIA
# =====================================================================
EMOJIS = ["🐶", "🐱", "🦊", "🐸", "🐵", "🦁", "🐼", "🐙"]


def mem_novo():
    cartas = EMOJIS * 2
    random.shuffle(cartas)
    S.mem_cartas = cartas
    S.mem_achados = set()
    S.mem_virados = []
    S.mem_jogadas = 0


def mem_click(i):
    if i in S.mem_achados or i in S.mem_virados:
        return
    if len(S.mem_virados) == 2:  # par errado ainda à mostra: esconde e segue
        S.mem_virados = []
    S.mem_virados.append(i)
    if len(S.mem_virados) == 2:
        S.mem_jogadas += 1
        a, b = S.mem_virados
        if S.mem_cartas[a] == S.mem_cartas[b]:
            S.mem_achados.update((a, b))
            S.mem_virados = []


def jogo_memoria():
    st.header("🧠 Jogo da Memória")
    if "mem_cartas" not in S:
        mem_novo()

    st.write(f"Jogadas: **{S.mem_jogadas}** · Pares: **{len(S.mem_achados) // 2}/{len(EMOJIS)}**")
    css_botoes(75, 2.0)
    for r in range(4):
        cols = st.columns(4)
        for c in range(4):
            i = r * 4 + c
            visivel = i in S.mem_achados or i in S.mem_virados
            cols[c].button(S.mem_cartas[i] if visivel else "❓", key=f"mem_{i}",
                           on_click=mem_click, args=(i,), disabled=i in S.mem_achados)

    if len(S.mem_achados) == len(S.mem_cartas):
        st.success(f"🎉 Parabéns! Você terminou em {S.mem_jogadas} jogadas.")
        st.balloons()

    if st.button("🔄 Embaralhar de novo", key="mem_reset"):
        mem_novo()
        st.rerun()


# =====================================================================
# 6) XADREZ (contra o computador)
# =====================================================================
SIMBOLO_XQ = {chess.KING: "♚", chess.QUEEN: "♛", chess.ROOK: "♜",
              chess.BISHOP: "♝", chess.KNIGHT: "♞", chess.PAWN: "♟︎"}
VALOR = {chess.PAWN: 100, chess.KNIGHT: 320, chess.BISHOP: 330,
         chess.ROOK: 500, chess.QUEEN: 900, chess.KING: 0}
# Tabelas de posição (visão das brancas, linha 8 no topo)
PST = {
    chess.PAWN: [0, 0, 0, 0, 0, 0, 0, 0,
                 50, 50, 50, 50, 50, 50, 50, 50,
                 10, 10, 20, 30, 30, 20, 10, 10,
                 5, 5, 10, 25, 25, 10, 5, 5,
                 0, 0, 0, 20, 20, 0, 0, 0,
                 5, -5, -10, 0, 0, -10, -5, 5,
                 5, 10, 10, -20, -20, 10, 10, 5,
                 0, 0, 0, 0, 0, 0, 0, 0],
    chess.KNIGHT: [-50, -40, -30, -30, -30, -30, -40, -50,
                   -40, -20, 0, 0, 0, 0, -20, -40,
                   -30, 0, 10, 15, 15, 10, 0, -30,
                   -30, 5, 15, 20, 20, 15, 5, -30,
                   -30, 0, 15, 20, 20, 15, 0, -30,
                   -30, 5, 10, 15, 15, 10, 5, -30,
                   -40, -20, 0, 5, 5, 0, -20, -40,
                   -50, -40, -30, -30, -30, -30, -40, -50],
    chess.BISHOP: [-20, -10, -10, -10, -10, -10, -10, -20,
                   -10, 0, 0, 0, 0, 0, 0, -10,
                   -10, 0, 5, 10, 10, 5, 0, -10,
                   -10, 5, 5, 10, 10, 5, 5, -10,
                   -10, 0, 10, 10, 10, 10, 0, -10,
                   -10, 10, 10, 10, 10, 10, 10, -10,
                   -10, 5, 0, 0, 0, 0, 5, -10,
                   -20, -10, -10, -10, -10, -10, -10, -20],
    chess.ROOK: [0, 0, 0, 0, 0, 0, 0, 0,
                 5, 10, 10, 10, 10, 10, 10, 5,
                 -5, 0, 0, 0, 0, 0, 0, -5,
                 -5, 0, 0, 0, 0, 0, 0, -5,
                 -5, 0, 0, 0, 0, 0, 0, -5,
                 -5, 0, 0, 0, 0, 0, 0, -5,
                 -5, 0, 0, 0, 0, 0, 0, -5,
                 0, 0, 0, 5, 5, 0, 0, 0],
    chess.QUEEN: [-20, -10, -10, -5, -5, -10, -10, -20,
                  -10, 0, 0, 0, 0, 0, 0, -10,
                  -10, 0, 5, 5, 5, 5, 0, -10,
                  -5, 0, 5, 5, 5, 5, 0, -5,
                  0, 0, 5, 5, 5, 5, 0, -5,
                  -10, 5, 5, 5, 5, 5, 0, -10,
                  -10, 0, 5, 0, 0, 0, 0, -10,
                  -20, -10, -10, -5, -5, -10, -10, -20],
    chess.KING: [-30, -40, -40, -50, -50, -40, -40, -30,
                 -30, -40, -40, -50, -50, -40, -40, -30,
                 -30, -40, -40, -50, -50, -40, -40, -30,
                 -30, -40, -40, -50, -50, -40, -40, -30,
                 -20, -30, -30, -40, -40, -30, -30, -20,
                 -10, -20, -20, -20, -20, -20, -20, -10,
                 20, 20, 0, 0, 0, 0, 20, 20,
                 20, 30, 10, 0, 0, 10, 30, 20],
}
MATE = 100_000
NIVEIS_XQ = {"Fácil": 1, "Médio": 2, "Difícil": 3}
PROMOCAO = {"Dama": chess.QUEEN, "Torre": chess.ROOK, "Bispo": chess.BISHOP, "Cavalo": chess.KNIGHT}
FIM_PT = {
    chess.Termination.CHECKMATE: "xeque-mate",
    chess.Termination.STALEMATE: "afogamento (empate)",
    chess.Termination.INSUFFICIENT_MATERIAL: "material insuficiente (empate)",
    chess.Termination.SEVENTYFIVE_MOVES: "regra dos 75 lances (empate)",
    chess.Termination.FIVEFOLD_REPETITION: "repetição (empate)",
    chess.Termination.FIFTY_MOVES: "regra dos 50 lances (empate)",
    chess.Termination.THREEFOLD_REPETITION: "tripla repetição (empate)",
}


def xq_avaliar(b):
    """Material + posição, do ponto de vista de quem joga."""
    s = 0
    for sq, p in b.piece_map().items():
        v = VALOR[p.piece_type] + PST[p.piece_type][sq ^ 56 if p.color else sq]
        s += v if p.color == chess.WHITE else -v
    return s if b.turn == chess.WHITE else -s


def xq_ordenar(b, lances):
    def nota(m):
        n = 0
        if b.is_capture(m):
            vitima = b.piece_at(m.to_square)
            n = 10 * (VALOR[vitima.piece_type] if vitima else 100) - VALOR[b.piece_at(m.from_square).piece_type]
        if m.promotion:
            n += 8000
        return -n
    return sorted(lances, key=nota)


def xq_quiescencia(b, alfa, beta, prof):
    parado = xq_avaliar(b)
    if parado >= beta:
        return beta
    alfa = max(alfa, parado)
    if prof == 0:
        return alfa
    for m in xq_ordenar(b, [m for m in b.legal_moves if b.is_capture(m)]):
        b.push(m)
        s = -xq_quiescencia(b, -beta, -alfa, prof - 1)
        b.pop()
        if s >= beta:
            return beta
        alfa = max(alfa, s)
    return alfa


def xq_negamax(b, prof, alfa, beta, ply):
    lances = list(b.legal_moves)
    if not lances:
        return -MATE + ply if b.is_check() else 0
    if b.is_insufficient_material() or b.halfmove_clock >= 100:
        return 0
    if prof == 0:
        return xq_quiescencia(b, alfa, beta, 4)
    melhor = -MATE * 2
    for m in xq_ordenar(b, lances):
        b.push(m)
        s = -xq_negamax(b, prof - 1, -beta, -alfa, ply + 1)
        b.pop()
        melhor = max(melhor, s)
        alfa = max(alfa, s)
        if alfa >= beta:
            break
    return melhor


def xq_melhor_lance(b, nivel):
    prof = NIVEIS_XQ[nivel]
    ruido = {"Fácil": 120, "Médio": 25, "Difícil": 0}[nivel]
    lances = list(b.legal_moves)
    random.shuffle(lances)
    melhor, melhor_nota = lances[0], -MATE * 3
    alfa = -MATE * 2
    for m in xq_ordenar(b, lances):
        b.push(m)
        s = -xq_negamax(b, prof - 1, -MATE * 2, -alfa + ruido, 1) + random.randint(-ruido, ruido)
        b.pop()
        if s > melhor_nota:
            melhor, melhor_nota = m, s
        if ruido == 0:
            alfa = max(alfa, s)
    return melhor


def xq_novo():
    S.xq_board = chess.Board()
    S.xq_sel = None
    S.xq_cor = chess.WHITE if S.get("xq_lado", "Brancas") == "Brancas" else chess.BLACK


def xq_click(sq):
    b = S.xq_board
    if b.outcome(claim_draw=True) or b.turn != S.xq_cor:
        return
    p = b.piece_at(sq)
    if p and p.color == S.xq_cor:
        S.xq_sel = None if S.xq_sel == sq else sq
        return
    if S.xq_sel is None:
        return
    m = chess.Move(S.xq_sel, sq)
    if b.piece_at(S.xq_sel).piece_type == chess.PAWN and chess.square_rank(sq) in (0, 7):
        m.promotion = PROMOCAO[S.xq_promo]
    if m in b.legal_moves:
        b.push(m)
    S.xq_sel = None


def xq_desfazer():
    b = S.xq_board
    if b.move_stack:
        b.pop()
    while b.move_stack and b.turn != S.xq_cor:
        b.pop()
    S.xq_sel = None


def xq_css(b):
    claro, escuro = "#f0d9b5", "#b58863"
    ultimo = b.move_stack[-1] if b.move_stack else None
    alvos = {m.to_square for m in b.legal_moves if m.from_square == S.xq_sel}
    rei_xeque = b.king(b.turn) if b.is_check() else None
    regras = ["""
    .st-key-xq_tab { max-width: 560px; margin: 0 auto; border: 6px solid #5c3d22; border-radius: 4px; }
    .st-key-xq_tab [data-testid="stVerticalBlock"] { gap: 0 !important; }
    .st-key-xq_tab [data-testid="stHorizontalBlock"] { flex-wrap: nowrap !important; gap: 0 !important; }
    .st-key-xq_tab [data-testid="stColumn"], .st-key-xq_tab [data-testid="column"] {
        min-width: 0 !important; width: auto !important; flex: 1 1 0 !important; }
    .st-key-xq_tab .stButton, .st-key-xq_tab .stButton > button { width: 100% !important; }
    .st-key-xq_tab button {
        aspect-ratio: 1 / 1; min-height: 0 !important; padding: 0 !important;
        border: none !important; border-radius: 0 !important; line-height: 1 !important;
        font-size: clamp(1.4rem, 6vw, 2.7rem) !important; font-variant-emoji: text; }
    .st-key-xq_tab button p { font-size: inherit !important; line-height: 1 !important; }
    .st-key-xq_tab button:focus { box-shadow: none !important; }
    """]
    for sq in chess.SQUARES:
        e_claro = (chess.square_file(sq) + chess.square_rank(sq)) % 2 == 1
        cor = claro if e_claro else escuro
        if ultimo and sq in (ultimo.from_square, ultimo.to_square):
            cor = "#cdd26a" if e_claro else "#aaa23a"
        if sq == S.xq_sel:
            cor = "#f6f669" if e_claro else "#dac34b"
        fundo = cor
        if sq == rei_xeque:
            fundo = f"radial-gradient(circle, #ff3b3b 25%, {cor} 80%)"
        elif sq in alvos:
            fundo = (f"radial-gradient(circle, transparent 58%, rgba(0,0,0,.28) 60%) , {cor}"
                     if b.piece_at(sq) else
                     f"radial-gradient(circle, rgba(0,0,0,.28) 16%, transparent 18%), {cor}")
        p = b.piece_at(sq)
        if p and p.color == chess.WHITE:
            texto = "color:#fff !important; text-shadow:0 0 2px #000,0 0 2px #000,0 0 1px #000;"
        else:
            texto = "color:#111 !important; text-shadow:none;"
        regras.append(f".st-key-xq_{sq} button{{background:{fundo} !important;{texto}}}")
    st.markdown("<style>" + "\n".join(regras) + "</style>", unsafe_allow_html=True)


def jogo_xadrez():
    st.header("♟️ Xadrez")
    c1, c2, c3 = st.columns(3)
    c1.radio("Jogar de", ["Brancas", "Pretas"], key="xq_lado", horizontal=True,
             help="Vale a partir da próxima partida.")
    c2.radio("Nível", list(NIVEIS_XQ), index=1, key="xq_nivel", horizontal=True)
    c3.selectbox("Promover peão a", list(PROMOCAO), key="xq_promo")

    if "xq_board" not in S:
        xq_novo()
    b = S.xq_board
    fim = b.outcome(claim_draw=True)

    xq_css(b)
    fileiras = range(7, -1, -1) if S.xq_cor == chess.WHITE else range(8)
    colunas = range(8) if S.xq_cor == chess.WHITE else range(7, -1, -1)
    with st.container(key="xq_tab"):
        for r in fileiras:
            cols = st.columns(8)
            for j, f in enumerate(colunas):
                sq = chess.square(f, r)
                p = b.piece_at(sq)
                cols[j].button(SIMBOLO_XQ[p.piece_type] if p else "⠀", key=f"xq_{sq}",
                               on_click=xq_click, args=(sq,), help=chess.square_name(sq))

    # Situação da partida
    if fim:
        if fim.winner is None:
            st.warning(f"🤝 Empate por {FIM_PT.get(fim.termination, 'regra')}.")
        elif fim.winner == S.xq_cor:
            st.success("🏆 Xeque-mate! Você venceu!")
            st.balloons()
        else:
            st.error("🤖 Xeque-mate! O computador venceu.")
    elif b.turn == S.xq_cor:
        st.info(("⚠️ Você está em **xeque**! " if b.is_check() else "") +
                "Sua vez: clique numa peça e depois na casa de destino.")

    b1, b2 = st.columns(2)
    b1.button("↩️ Desfazer lance", key="xq_undo", on_click=xq_desfazer)
    if b2.button("🔄 Nova partida", key="xq_reset"):
        xq_novo()
        st.rerun()

    with st.expander("📜 Lances da partida"):
        st.write(chess.Board().variation_san(b.move_stack) if b.move_stack else "Nenhum lance ainda.")

    # Vez do computador: o tabuleiro já mostra o seu lance enquanto ele pensa
    if not fim and b.turn != S.xq_cor:
        with st.spinner("🤖 Computador pensando..."):
            lance = xq_melhor_lance(b.copy(), S.xq_nivel)
        b.push(lance)
        st.rerun()


# =====================================================================
# MENU
# =====================================================================
JOGOS = {
    "♟️ Xadrez": jogo_xadrez,
    "🔢 Adivinhe o Número": jogo_adivinha,
    "❌⭕ Jogo da Velha": jogo_velha,
    "🪢 Forca": jogo_forca,
    "🪨 Pedra, Papel e Tesoura": jogo_ppt,
    "🧠 Jogo da Memória": jogo_memoria,
}



# =====================================================================
# TELA DE ENTRADA (nome + chave Groq)
# =====================================================================
def validar_chave_groq(chave: str):
    """Retorna (ok, mensagem). Consulta a lista de modelos da Groq."""
    try:
        r = requests.get("https://api.groq.com/openai/v1/models",
                         headers={"Authorization": f"Bearer {chave}"}, timeout=10)
    except requests.RequestException:
        return False, "Não consegui falar com a Groq agora. Tente de novo em instantes."
    if r.status_code == 200:
        return True, ""
    if r.status_code in (401, 403):
        return False, "Chave Groq inválida. Confira e tente de novo."
    return False, f"A Groq respondeu com erro {r.status_code}. Tente de novo."


def tela_entrada():
    st.markdown("<h1 style='text-align:center'>🎮 Fliperama</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center'>Digite seu nome e sua chave Groq para entrar.</p>",
                unsafe_allow_html=True)
    _, meio, _ = st.columns([1, 2, 1])
    with meio, st.form("entrada"):
        nome = st.text_input("Seu nome", max_chars=30)
        chave = st.text_input("Chave Groq", type="password", placeholder="gsk_...",
                              help="Crie a sua grátis em console.groq.com/keys. "
                                   "Ela fica só nesta sessão e não é salva.")
        if st.form_submit_button("Entrar ▶️", type="primary"):
            nome, chave = nome.strip(), chave.strip()
            if not nome or not chave:
                st.error("Preencha o nome e a chave.")
            else:
                with st.spinner("Verificando a chave..."):
                    ok, erro = validar_chave_groq(chave)
                if ok:
                    S.usuario, S.groq_key = nome, chave
                    st.rerun()
                else:
                    st.error(erro)


def sair():
    for k in list(S.keys()):
        del S[k]


if "usuario" not in S:
    tela_entrada()
    st.stop()

st.sidebar.title("🎮 Fliperama")
st.sidebar.write(f"Olá, **{S.usuario}**! 👋")
escolhido = st.sidebar.radio("Escolha um jogo", list(JOGOS))
st.sidebar.button("🚪 Sair", on_click=sair)
st.sidebar.caption("Feito com Streamlit · um único arquivo .py")

JOGOS[escolhido]()
