"""
🎮 Fliperama Streamlit — vários jogos em um único arquivo.
Rodar localmente:  streamlit run jogos.py
"""
import json
import math
import random
import unicodedata

import chess
import requests
import streamlit as st
import streamlit.components.v1 as components

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


def css_grade(chave: str, fonte: str, espaco: str = "3px"):
    """CSS de um tabuleiro de botões que não quebra linha no celular."""
    return f"""
    .st-key-{chave} {{ max-width: 520px; margin: 0 auto; }}
    .st-key-{chave} [data-testid="stVerticalBlock"] {{ gap: {espaco} !important; }}
    .st-key-{chave} [data-testid="stHorizontalBlock"] {{ flex-wrap: nowrap !important; gap: {espaco} !important; }}
    .st-key-{chave} [data-testid="stColumn"], .st-key-{chave} [data-testid="column"] {{
        min-width: 0 !important; width: auto !important; flex: 1 1 0 !important; }}
    .st-key-{chave} .stButton, .st-key-{chave} .stButton > button {{ width: 100% !important; }}
    .st-key-{chave} button {{
        aspect-ratio: 1 / 1; min-height: 0 !important; padding: 0 !important;
        border-radius: 5px !important; line-height: 1 !important; font-weight: 800;
        font-size: {fonte} !important; }}
    .st-key-{chave} button p {{ font-size: inherit !important; line-height: 1 !important; font-weight: inherit; }}
    """


# =====================================================================
# 7) TERMO (adivinhe a palavra de 5 letras)
# =====================================================================
PALAVRAS_TERMO = [
    "AMIGO", "BOLSA", "CARRO", "DENTE", "FESTA", "GENTE", "HOTEL", "JOGOS", "LIVRO", "MUNDO",
    "NOITE", "OUTRO", "PRAIA", "PRATO", "RISCO", "SALTO", "TEMPO", "VERDE", "ZEBRA", "AVIAO",
    "BANCO", "CAMPO", "DISCO", "FORNO", "GARFO", "LIMAO", "MANGA", "NUVEM", "PASTA", "POLVO",
    "RAIVA", "SONHO", "TIGRE", "VIDRO", "BRAVO", "CHUVA", "PEDRA", "PORTA", "LAPIS", "MOLHO",
    "PLANO", "SORTE", "TARDE", "VENTO", "CANTO", "CORPO", "FOLHA", "GRUPO", "LEITE", "NAVIO",
    "PAPEL", "QUEDA", "SABOR", "TRIGO", "VIOLA", "CALOR", "FLUXO", "GOLPE", "JUSTO", "MAGIA",
]
CORES_TERMO = {"verde": "#3aa35b", "amarelo": "#d4a72c", "cinza": "#6b6f76", "vazio": "transparent"}


def sem_acento(txt: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", txt) if unicodedata.category(c) != "Mn")


def termo_cores(chute, alvo):
    res, resto = ["cinza"] * 5, list(alvo)
    for i in range(5):
        if chute[i] == alvo[i]:
            res[i] = "verde"
            resto.remove(chute[i])
    for i in range(5):
        if res[i] != "verde" and chute[i] in resto:
            res[i] = "amarelo"
            resto.remove(chute[i])
    return res


def termo_novo():
    S.termo_alvo = random.choice(PALAVRAS_TERMO)
    S.termo_chutes = []
    S.termo_msg = ""


def termo_html(chutes, alvo):
    linhas = []
    for n in range(6):
        if n < len(chutes):
            letras, cores = chutes[n], termo_cores(chutes[n], alvo)
        else:
            letras, cores = " " * 5, ["vazio"] * 5
        celulas = "".join(
            f"<div style='width:52px;height:52px;display:flex;align-items:center;justify-content:center;"
            f"font-size:1.6rem;font-weight:800;color:#fff;border-radius:6px;background:{CORES_TERMO[c]};"
            f"border:2px solid {'#888' if c == 'vazio' else CORES_TERMO[c]}'>{l}</div>"
            for l, c in zip(letras, cores))
        linhas.append(f"<div style='display:flex;gap:6px;justify-content:center'>{celulas}</div>")
    return "<div style='display:flex;flex-direction:column;gap:6px;margin:8px 0'>" + "".join(linhas) + "</div>"


def jogo_termo():
    if "termo_alvo" not in S:
        termo_novo()
    alvo, chutes = S.termo_alvo, S.termo_chutes
    venceu = bool(chutes) and chutes[-1] == alvo
    perdeu = len(chutes) >= 6 and not venceu

    st.markdown(termo_html(chutes, alvo), unsafe_allow_html=True)

    if venceu:
        st.success(f"🎉 Acertou em {len(chutes)} tentativa(s)!")
        st.balloons()
    elif perdeu:
        st.error(f"😢 Acabaram as tentativas. A palavra era **{alvo}**.")
    else:
        with st.form("termo_form", clear_on_submit=True):
            chute = st.text_input("Sua palavra (5 letras)", max_chars=5)
            if st.form_submit_button("Enviar ✅"):
                chute = sem_acento(chute.strip().upper())
                if len(chute) != 5 or not chute.isalpha():
                    S.termo_msg = "Digite exatamente 5 letras."
                else:
                    S.termo_msg = ""
                    S.termo_chutes.append(chute)
                st.rerun()
        if S.termo_msg:
            st.warning(S.termo_msg)

        # Teclado com as letras já testadas
        estado = {}
        prioridade = {"verde": 3, "amarelo": 2, "cinza": 1}
        for c in chutes:
            for l, cor in zip(c, termo_cores(c, alvo)):
                if prioridade[cor] > prioridade.get(estado.get(l), 0):
                    estado[l] = cor
        teclas = []
        for linha in ("QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM"):
            teclas.append("<div style='display:flex;gap:4px;justify-content:center;margin:3px 0'>" + "".join(
                f"<span style='min-width:26px;padding:6px 4px;text-align:center;border-radius:4px;font-weight:700;"
                f"color:{'#fff' if l in estado else 'inherit'};"
                f"background:{CORES_TERMO[estado[l]] if l in estado else 'rgba(128,128,128,.18)'}'>{l}</span>"
                for l in linha) + "</div>")
        st.markdown("".join(teclas), unsafe_allow_html=True)

    if st.button("🔄 Nova palavra", key="termo_reset"):
        termo_novo()
        st.rerun()


# =====================================================================
# 8) 2048
# =====================================================================
CORES_2048 = {0: ("#cdc1b4", "#776e65"), 2: ("#eee4da", "#776e65"), 4: ("#ede0c8", "#776e65"),
              8: ("#f2b179", "#fff"), 16: ("#f59563", "#fff"), 32: ("#f67c5f", "#fff"),
              64: ("#f65e3b", "#fff"), 128: ("#edcf72", "#fff"), 256: ("#edcc61", "#fff"),
              512: ("#edc850", "#fff"), 1024: ("#edc53f", "#fff"), 2048: ("#edc22e", "#fff")}


def g2048_juntar(linha):
    v = [x for x in linha if x]
    saida, pontos, i = [], 0, 0
    while i < len(v):
        if i + 1 < len(v) and v[i] == v[i + 1]:
            saida.append(v[i] * 2)
            pontos += v[i] * 2
            i += 2
        else:
            saida.append(v[i])
            i += 1
    return saida + [0] * (4 - len(saida)), pontos


def g2048_mover(grade, direcao):
    """Retorna (nova_grade, pontos, mudou)."""
    nova = [[0] * 4 for _ in range(4)]
    pontos = 0
    for k in range(4):
        if direcao == "esq":
            idx = [(k, c) for c in range(4)]
        elif direcao == "dir":
            idx = [(k, c) for c in range(3, -1, -1)]
        elif direcao == "cima":
            idx = [(r, k) for r in range(4)]
        else:
            idx = [(r, k) for r in range(3, -1, -1)]
        linha, p = g2048_juntar([grade[r][c] for r, c in idx])
        pontos += p
        for (r, c), val in zip(idx, linha):
            nova[r][c] = val
    return nova, pontos, nova != grade


def g2048_nova_peca(grade):
    vazias = [(r, c) for r in range(4) for c in range(4) if not grade[r][c]]
    if vazias:
        r, c = random.choice(vazias)
        grade[r][c] = 4 if random.random() < 0.1 else 2


def g2048_novo():
    S.g2048_grade = [[0] * 4 for _ in range(4)]
    g2048_nova_peca(S.g2048_grade)
    g2048_nova_peca(S.g2048_grade)
    S.g2048_pontos = 0
    S.g2048_continuar = False


def g2048_jogar(direcao):
    nova, pontos, mudou = g2048_mover(S.g2048_grade, direcao)
    if mudou:
        g2048_nova_peca(nova)
        S.g2048_grade = nova
        S.g2048_pontos += pontos
        S.g2048_recorde = max(S.get("g2048_recorde", 0), S.g2048_pontos)


def jogo_2048():
    if "g2048_grade" not in S:
        g2048_novo()
    grade = S.g2048_grade
    c1, c2 = st.columns(2)
    c1.metric("Pontos", S.g2048_pontos)
    c2.metric("Recorde", S.get("g2048_recorde", 0))

    celulas = ""
    for linha in grade:
        for v in linha:
            fundo, cor = CORES_2048.get(v, ("#3c3a32", "#fff"))
            tam = "2rem" if v < 100 else "1.6rem" if v < 1000 else "1.3rem"
            celulas += (f"<div style='aspect-ratio:1;display:flex;align-items:center;justify-content:center;"
                        f"border-radius:6px;background:{fundo};color:{cor};font-weight:800;font-size:{tam}'>"
                        f"{v or ''}</div>")
    st.markdown("<div style='display:grid;grid-template-columns:repeat(4,1fr);gap:8px;padding:8px;"
                "background:#bbada0;border-radius:8px;max-width:380px;margin:0 auto 12px'>"
                + celulas + "</div>", unsafe_allow_html=True)

    tem_2048 = any(v >= 2048 for linha in grade for v in linha)
    sem_lances = not any(g2048_mover(grade, d)[2] for d in ("esq", "dir", "cima", "baixo"))
    if tem_2048 and not S.g2048_continuar:
        st.success("🏆 Você fez 2048! Pode continuar jogando para aumentar os pontos.")
        if st.button("Continuar jogando", key="g2048_cont"):
            S.g2048_continuar = True
            st.rerun()
    if sem_lances:
        st.error(f"Fim de jogo! Você fez {S.g2048_pontos} pontos.")
    else:
        css_botoes(56, 1.5)
        _, cima, _ = st.columns(3)
        cima.button("⬆️", key="g2048_cima", on_click=g2048_jogar, args=("cima",))
        esq, baixo, dir_ = st.columns(3)
        esq.button("⬅️", key="g2048_esq", on_click=g2048_jogar, args=("esq",))
        baixo.button("⬇️", key="g2048_baixo", on_click=g2048_jogar, args=("baixo",))
        dir_.button("➡️", key="g2048_dir", on_click=g2048_jogar, args=("dir",))

    if st.button("🔄 Novo jogo", key="g2048_reset"):
        g2048_novo()
        st.rerun()


# =====================================================================
# 9) CAMPO MINADO
# =====================================================================
CM_TAM = {"Fácil (8×8, 10 minas)": (8, 10), "Médio (10×10, 18 minas)": (10, 18)}
CORES_NUM = {1: "#1e63d6", 2: "#2e8b3a", 3: "#d32f2f", 4: "#283593",
             5: "#8d1c1c", 6: "#00838f", 7: "#222", 8: "#666"}


def cm_vizinhos(i, n):
    r, c = divmod(i, n)
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if (dr or dc) and 0 <= r + dr < n and 0 <= c + dc < n:
                yield (r + dr) * n + c + dc


def cm_novo():
    S.cm_n, S.cm_qtd = CM_TAM[S.get("cm_nivel", list(CM_TAM)[0])]
    S.cm_minas = None
    S.cm_abertas = set()
    S.cm_bandeiras = set()
    S.cm_fim = None
    S.cm_explodiu = None


def cm_numero(i):
    return sum(j in S.cm_minas for j in cm_vizinhos(i, S.cm_n))


def cm_click(i):
    if S.cm_fim or i in S.cm_abertas:
        return
    if S.cm_modo == "🚩 Bandeira":
        S.cm_bandeiras.symmetric_difference_update({i})
        return
    if i in S.cm_bandeiras:
        return
    n = S.cm_n
    if S.cm_minas is None:  # 1º clique nunca é mina
        proibidas = {i, *cm_vizinhos(i, n)}
        S.cm_minas = set(random.sample([j for j in range(n * n) if j not in proibidas], S.cm_qtd))
    if i in S.cm_minas:
        S.cm_fim, S.cm_explodiu = "perdeu", i
        return
    pilha = [i]
    while pilha:
        j = pilha.pop()
        if j in S.cm_abertas:
            continue
        S.cm_abertas.add(j)
        S.cm_bandeiras.discard(j)
        if cm_numero(j) == 0:
            pilha.extend(k for k in cm_vizinhos(j, n) if k not in S.cm_abertas)
    if len(S.cm_abertas) == n * n - S.cm_qtd:
        S.cm_fim = "venceu"


def jogo_campo_minado():
    c1, c2 = st.columns(2)
    c1.radio("Tamanho", list(CM_TAM), key="cm_nivel", help="Vale a partir do próximo jogo.")
    c2.radio("Ao clicar:", ["⛏️ Abrir", "🚩 Bandeira"], key="cm_modo", horizontal=True)
    if "cm_abertas" not in S:
        cm_novo()
    n = S.cm_n
    st.write(f"💣 Minas: **{S.cm_qtd}** · 🚩 Bandeiras: **{len(S.cm_bandeiras)}**")

    regras = [css_grade("cm_tab", "clamp(.9rem, 4vw, 1.4rem)", "2px")]
    for i in range(n * n):
        if i in S.cm_abertas:
            num = cm_numero(i)
            estilo = f"background:#e9e9e9 !important; color:{CORES_NUM.get(num, '#222')} !important; border:1px solid #cfcfcf !important;"
        elif i == S.cm_explodiu:
            estilo = "background:#ff5252 !important; border:none !important;"
        else:
            estilo = "background:#8fa3b8 !important; color:#fff !important; border:2px outset #b9c8d8 !important;"
        regras.append(f".st-key-cm_{i} button{{{estilo}}}")
    st.markdown("<style>" + "\n".join(regras) + "</style>", unsafe_allow_html=True)

    with st.container(key="cm_tab"):
        for r in range(n):
            cols = st.columns(n)
            for c in range(n):
                i = r * n + c
                if i in S.cm_abertas:
                    num = cm_numero(i)
                    rotulo = str(num) if num else "⠀"
                elif S.cm_fim and S.cm_minas and i in S.cm_minas:
                    rotulo = "💣"
                elif i in S.cm_bandeiras:
                    rotulo = "🚩"
                else:
                    rotulo = "⠀"
                cols[c].button(rotulo, key=f"cm_{i}", on_click=cm_click, args=(i,))

    if S.cm_fim == "venceu":
        st.success("🎉 Você limpou o campo!")
        st.balloons()
    elif S.cm_fim == "perdeu":
        st.error("💥 Boom! Você pisou numa mina.")

    if st.button("🔄 Novo campo", key="cm_reset"):
        cm_novo()
        st.rerun()


# =====================================================================
# 10) LIGUE 4 (contra o computador)
# =====================================================================
L4_LIN, L4_COL = 6, 7


def l4_vence(t, p):
    for r in range(L4_LIN):
        for c in range(L4_COL):
            for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
                if all(0 <= r + k * dr < L4_LIN and 0 <= c + k * dc < L4_COL
                       and t[r + k * dr][c + k * dc] == p for k in range(4)):
                    return True
    return False


def l4_validas(t):
    return [c for c in range(L4_COL) if not t[0][c]]


def l4_soltar(t, c, p):
    for r in range(L4_LIN - 1, -1, -1):
        if not t[r][c]:
            t[r][c] = p
            return r
    return None


def l4_simular(t, c, p):
    novo = [linha[:] for linha in t]
    l4_soltar(novo, c, p)
    return novo


def l4_jogada_pc(t):
    validas = l4_validas(t)
    for p in ("O", "X"):  # 1º tenta vencer, depois bloqueia
        for c in validas:
            if l4_vence(l4_simular(t, c, p), p):
                return c
    seguras = [c for c in validas
               if not any(l4_vence(l4_simular(l4_simular(t, c, "O"), c2, "X"), "X")
                          for c2 in l4_validas(l4_simular(t, c, "O")))]
    opcoes = seguras or validas
    return min(opcoes, key=lambda c: abs(3 - c) + random.random() * 1.8)


def l4_novo():
    S.l4_tab = [[""] * L4_COL for _ in range(L4_LIN)]
    S.l4_fim = None


def l4_click(c):
    t = S.l4_tab
    if S.l4_fim or c not in l4_validas(t):
        return
    l4_soltar(t, c, "X")
    if l4_vence(t, "X"):
        S.l4_fim = "X"
    elif not l4_validas(t):
        S.l4_fim = "Empate"
    else:
        l4_soltar(t, l4_jogada_pc(t), "O")
        if l4_vence(t, "O"):
            S.l4_fim = "O"
        elif not l4_validas(t):
            S.l4_fim = "Empate"
    if S.l4_fim:
        chave = {"X": "voce", "O": "pc", "Empate": "empate"}[S.l4_fim]
        S.l4_placar[chave] += 1


def jogo_ligue4():
    if "l4_tab" not in S:
        l4_novo()
        S.l4_placar = {"voce": 0, "pc": 0, "empate": 0}
    p = S.l4_placar
    c1, c2, c3 = st.columns(3)
    c1.metric("Você (🔴)", p["voce"])
    c2.metric("Empates", p["empate"])
    c3.metric("Computador (🟡)", p["pc"])

    st.markdown("<style>" + css_grade("l4_tab", "clamp(1.2rem, 5.5vw, 2.2rem)", "4px") +
                ".st-key-l4_tab{background:#1f4fbf;padding:8px;border-radius:10px}"
                ".st-key-l4_tab button{background:#163a8f !important;border:none !important;"
                "border-radius:50% !important;}</style>", unsafe_allow_html=True)
    peca = {"X": "🔴", "O": "🟡", "": "⠀"}
    with st.container(key="l4_tab"):
        for r in range(L4_LIN):
            cols = st.columns(L4_COL)
            for c in range(L4_COL):
                cols[c].button(peca[S.l4_tab[r][c]], key=f"l4_{r}_{c}", on_click=l4_click, args=(c,))

    fim = S.l4_fim
    if fim == "X":
        st.success("🎉 Você ligou 4!")
    elif fim == "O":
        st.error("🤖 O computador ligou 4!")
    elif fim == "Empate":
        st.warning("🤝 Tabuleiro cheio, empate!")
    else:
        st.caption("Clique em qualquer casa de uma coluna para soltar sua peça nela.")

    if st.button("🔄 Nova partida", key="l4_reset"):
        l4_novo()
        st.rerun()


# =====================================================================
# 11) QUIZ COM IA (usa a chave Groq)
# =====================================================================
def groq_chat(mensagens, json_mode=False):
    corpo = {"model": S.groq_modelo, "messages": mensagens, "temperature": 0.9}
    if json_mode:
        corpo["response_format"] = {"type": "json_object"}
    r = requests.post("https://api.groq.com/openai/v1/chat/completions",
                      headers={"Authorization": f"Bearer {S.groq_key}"}, json=corpo, timeout=90)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


def quiz_gerar(tema, nivel, qtd):
    prompt = (
        f"Crie um quiz em português do Brasil com {qtd} perguntas de múltipla escolha sobre o tema: "
        f"\"{tema}\". Nível de dificuldade: {nivel}. Cada pergunta deve ter exatamente 4 opções e "
        "apenas uma correta. Varie a posição da resposta correta. Responda SOMENTE com JSON no formato: "
        '{"perguntas": [{"pergunta": "...", "opcoes": ["...", "...", "...", "..."], '
        '"correta": 0, "explicacao": "..."}]} onde "correta" é o índice (0 a 3) da opção certa.'
    )
    texto = groq_chat([{"role": "system", "content": "Você cria quizzes educativos, corretos e divertidos."},
                       {"role": "user", "content": prompt}], json_mode=True)
    dados = json.loads(texto)
    perguntas = []
    for q in dados.get("perguntas", []):
        ops = q.get("opcoes", [])
        if (isinstance(ops, list) and len(ops) == 4 and isinstance(q.get("correta"), int)
                and 0 <= q["correta"] < 4 and q.get("pergunta")):
            perguntas.append(q)
    return perguntas


def jogo_quiz_ia():
    if not S.get("quiz_perguntas"):
        st.write("A IA cria um quiz novinho sobre **qualquer tema** que você escolher.")
        with st.form("quiz_form"):
            tema = st.text_input("Tema do quiz", placeholder="Ex.: Copa do Mundo, dinossauros, Brasil Colônia, Harry Potter...")
            c1, c2 = st.columns(2)
            nivel = c1.select_slider("Dificuldade", ["Fácil", "Médio", "Difícil"], value="Médio")
            qtd = c2.select_slider("Perguntas", [5, 10, 15], value=5)
            if st.form_submit_button("✨ Gerar quiz", type="primary"):
                if not tema.strip():
                    st.error("Escreva um tema.")
                else:
                    with st.spinner("A IA está preparando as perguntas..."):
                        try:
                            perguntas = quiz_gerar(tema.strip(), nivel, qtd)
                        except requests.HTTPError as e:
                            perguntas = None
                            st.error(f"A Groq recusou o pedido (erro {e.response.status_code}). Tente de novo.")
                        except (requests.RequestException, ValueError, KeyError):
                            perguntas = None
                            st.error("Não consegui gerar o quiz agora. Tente de novo.")
                    if perguntas:
                        S.quiz_perguntas, S.quiz_tema = perguntas, tema.strip()
                        S.quiz_i, S.quiz_pontos, S.quiz_respondida = 0, 0, None
                        st.rerun()
                    elif perguntas is not None:
                        st.error("A IA não mandou perguntas válidas. Tente de novo ou mude o tema.")
        return

    perguntas, i = S.quiz_perguntas, S.quiz_i
    if i >= len(perguntas):
        total = len(perguntas)
        st.subheader(f"Resultado: {S.quiz_pontos} de {total} 🎯")
        st.progress(S.quiz_pontos / total)
        if S.quiz_pontos == total:
            st.balloons()
            st.success("Gabaritou! 🏆")
        elif S.quiz_pontos >= total * 0.6:
            st.success("Mandou bem! 👏")
        else:
            st.info("Dá para melhorar, tente outro! 💪")
        if st.button("✨ Novo quiz", key="quiz_novo"):
            S.quiz_perguntas = None
            st.rerun()
        return

    q = perguntas[i]
    st.caption(f"Tema: {S.quiz_tema} · Pergunta {i + 1} de {len(perguntas)} · Pontos: {S.quiz_pontos}")
    st.progress(i / len(perguntas))
    st.subheader(q["pergunta"])
    escolha = st.radio("Escolha uma opção", q["opcoes"], index=None, key=f"quiz_r_{i}",
                       disabled=S.quiz_respondida is not None, label_visibility="collapsed")

    if S.quiz_respondida is None:
        if st.button("Responder ✅", key=f"quiz_ok_{i}", disabled=escolha is None):
            S.quiz_respondida = q["opcoes"].index(escolha)
            if S.quiz_respondida == q["correta"]:
                S.quiz_pontos += 1
            st.rerun()
    else:
        certa = q["opcoes"][q["correta"]]
        if S.quiz_respondida == q["correta"]:
            st.success("✅ Certa resposta!")
        else:
            st.error(f"❌ Errou. A resposta certa era: **{certa}**")
        if q.get("explicacao"):
            st.info(q["explicacao"])
        if st.button("Próxima ➡️", key=f"quiz_prox_{i}"):
            S.quiz_i += 1
            S.quiz_respondida = None
            st.rerun()

    if st.button("🛑 Encerrar quiz", key="quiz_sair"):
        S.quiz_perguntas = None
        st.rerun()


# =====================================================================
# JOGOS ANIMADOS (HTML5 canvas embutido)
# =====================================================================
BASE_JS = r"""
const cv = document.getElementById('c'), ctx = cv.getContext('2d');
const keys = {};
const MAPA = {ArrowLeft:'esq', KeyA:'esq', KeyZ:'esq', ArrowRight:'dir', KeyD:'dir', KeyM:'dir', Slash:'dir',
              ArrowUp:'cima', KeyW:'cima', ArrowDown:'baixo', KeyS:'baixo', Space:'acao', Enter:'acao', KeyP:'pausa'};
function apertar(k){ if (!keys[k]) { keys[k] = true; aoApertar(k); } }
function soltar(k){ if (keys[k]) { keys[k] = false; aoSoltar(k); } }
addEventListener('keydown', e => { const k = MAPA[e.code]; if (k) { e.preventDefault(); apertar(k); } });
addEventListener('keyup', e => { const k = MAPA[e.code]; if (k) { e.preventDefault(); soltar(k); } });
document.querySelectorAll('[data-k]').forEach(b => {
  const k = b.dataset.k;
  b.addEventListener('pointerdown', e => { e.preventDefault(); b.setPointerCapture(e.pointerId); apertar(k); });
  ['pointerup', 'pointercancel', 'lostpointercapture'].forEach(t => b.addEventListener(t, e => { e.preventDefault(); soltar(k); }));
  b.addEventListener('contextmenu', e => e.preventDefault());
});
function lerRecorde(n){ try { return +localStorage.getItem(n) || 0; } catch (e) { return 0; } }
function salvarRecorde(n, v){ const r = lerRecorde(n); if (v > r) { try { localStorage.setItem(n, v); } catch (e) {} return v; } return r; }
function texto(t, x, y, tam, cor, alinh){ ctx.font = `bold ${tam}px system-ui, sans-serif`; ctx.fillStyle = cor || '#fff';
  ctx.textAlign = alinh || 'center'; ctx.textBaseline = 'middle'; ctx.fillText(t, x, y); }
function painel(titulo, linhas){ ctx.fillStyle = 'rgba(5,8,20,.72)'; ctx.fillRect(0, 0, cv.width, cv.height);
  texto(titulo, cv.width/2, cv.height/2 - 30 - linhas.length*12, 34, '#ffd34d');
  linhas.forEach((l, i) => texto(l, cv.width/2, cv.height/2 + 10 + i*28 - linhas.length*12, 17, '#fff')); }
function rr(x, y, w, h, r){ ctx.beginPath(); ctx.moveTo(x+r, y); ctx.arcTo(x+w, y, x+w, y+h, r); ctx.arcTo(x+w, y+h, x, y+h, r);
  ctx.arcTo(x, y+h, x, y, r); ctx.arcTo(x, y, x+w, y, r); ctx.closePath(); }
function ajudaInicio(){ return matchMedia('(pointer: coarse)').matches ? 'Toque na tela para começar' : 'Clique aqui e aperte ESPAÇO'; }
let ultimoT = performance.now();
function loop(t){ const dt = Math.min(0.04, (t - ultimoT) / 1000); ultimoT = t; atualizar(dt); desenhar(); requestAnimationFrame(loop); }
"""


def pagina_canvas(js_jogo: str, largura: int, botoes: str) -> str:
    return f"""<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<style>
html,body{{margin:0;background:transparent;font-family:system-ui,sans-serif;user-select:none;-webkit-user-select:none;
  -webkit-touch-callout:none;overflow:hidden}}
#wrap{{display:flex;flex-direction:column;align-items:center;gap:10px;padding:4px}}
canvas{{width:min(100%,{largura}px);height:auto;border-radius:14px;box-shadow:0 8px 28px rgba(0,0,0,.4);
  touch-action:none;display:block;outline:none}}
.ctl{{display:flex;gap:8px;width:min(100%,{largura}px)}}
.ctl button{{flex:1;padding:14px 0;font-size:20px;font-weight:700;border:none;border-radius:12px;background:#283044;
  color:#fff;touch-action:none;cursor:pointer}}
.ctl button:active{{background:#46526e;transform:translateY(1px)}}
</style></head><body><div id="wrap"><canvas id="c" tabindex="0"></canvas><div class="ctl">{botoes}</div></div>
<script>{BASE_JS}
{js_jogo}
requestAnimationFrame(loop);
</script></body></html>"""


# ---------------------------------------------------------------- CORRIDA
CORRIDA_JS = r"""
const W = 360, H = 600; cv.width = W; cv.height = H;
const RX = 50, RW = 260;                       // estrada
const CORES = ['#3d8bff', '#ffb02e', '#a259ff', '#2ec4b6', '#f2f2f2', '#ff6fb5'];
let estado = 'inicio', carro, inimigos, moedas, part, arvores, vel, pontos, vidas, invul, spawnT, moedaT, faixa, recorde = lerRecorde('rec_corrida');
function reiniciar(){
  carro = {x: W/2, y: H - 95, w: 36, h: 62}; inimigos = []; moedas = []; part = [];
  vel = 280; pontos = 0; vidas = 3; invul = 0; spawnT = 1; moedaT = 2; faixa = 0;
  arvores = []; for (let i = 0; i < 10; i++) arvores.push({x: i % 2 ? RX + RW + 12 + Math.random()*24 : 8 + Math.random()*26, y: i * 65, r: 12 + Math.random()*7});
}
reiniciar();
function aoApertar(k){
  if (k === 'acao') { if (estado === 'inicio' || estado === 'fim') { reiniciar(); estado = 'jogando'; } else if (estado === 'pausa') estado = 'jogando'; }
  if (k === 'pausa') estado = estado === 'jogando' ? 'pausa' : estado === 'pausa' ? 'jogando' : estado;
}
function aoSoltar(k){}
const toques = {};
cv.addEventListener('pointerdown', e => {
  cv.focus();
  if (estado !== 'jogando') { aoApertar('acao'); return; }
  const r = cv.getBoundingClientRect(); const lado = (e.clientX - r.left) < r.width/2 ? 'esq' : 'dir';
  toques[e.pointerId] = lado; keys[lado] = true;
});
['pointerup', 'pointercancel', 'pointerleave'].forEach(t => cv.addEventListener(t, e => {
  const l = toques[e.pointerId]; if (l) { delete toques[e.pointerId]; if (!Object.values(toques).includes(l)) keys[l] = false; }
}));
function bate(a, b){ return Math.abs(a.x - b.x) < (a.w + b.w)/2 - 5 && Math.abs(a.y - b.y) < (a.h + b.h)/2 - 6; }
function explodir(x, y, cor, n){ for (let i = 0; i < n; i++) { const a = Math.random()*6.28, s = 60 + Math.random()*260;
  part.push({x, y, vx: Math.cos(a)*s, vy: Math.sin(a)*s, t: 0.6 + Math.random()*0.5, cor}); } }
function atualizar(dt){
  for (const p of part) { p.x += p.vx*dt; p.y += p.vy*dt; p.t -= dt; }
  part = part.filter(p => p.t > 0);
  if (estado !== 'jogando') return;
  vel = Math.min(760, vel + dt*8);
  pontos += vel*dt/10; faixa = (faixa + vel*dt) % 60;
  for (const a of arvores) { a.y += vel*dt; if (a.y > H + 30) a.y -= 650; }
  const lateral = 300 + vel*0.15;
  if (keys.esq) carro.x -= lateral*dt;
  if (keys.dir) carro.x += lateral*dt;
  carro.x = Math.max(RX + carro.w/2 + 4, Math.min(RX + RW - carro.w/2 - 4, carro.x));
  spawnT -= dt;
  if (spawnT <= 0) {
    spawnT = Math.max(0.38, 1.15 - vel/900) + Math.random()*0.45;
    const f = Math.floor(Math.random()*3), x = RX + RW/6*(1 + 2*f);
    if (!inimigos.some(e => Math.abs(e.x - x) < 5 && e.y < 90))
      inimigos.push({x, y: -70, w: 36, h: 62, v: vel*(0.3 + Math.random()*0.3), cor: CORES[Math.floor(Math.random()*CORES.length)]});
  }
  moedaT -= dt;
  if (moedaT <= 0) { moedaT = 1.2 + Math.random()*1.8; const f = Math.floor(Math.random()*3);
    moedas.push({x: RX + RW/6*(1 + 2*f), y: -30, w: 22, h: 22, giro: 0}); }
  for (const e of inimigos) e.y += (vel - e.v)*dt;
  for (const m of moedas) { m.y += vel*dt; m.giro += dt*6; }
  invul = Math.max(0, invul - dt);
  for (const e of inimigos) if (!e.morto && invul <= 0 && bate(carro, e)) {
    e.morto = true; vidas--; invul = 2; explodir((carro.x + e.x)/2, (carro.y + e.y)/2, '#ff8a3d', 40); vel *= 0.7;
    if (vidas <= 0) { estado = 'fim'; recorde = salvarRecorde('rec_corrida', Math.floor(pontos)); }
  }
  for (const m of moedas) if (!m.pega && bate(carro, m)) { m.pega = true; pontos += 50; explodir(m.x, m.y, '#ffe066', 12); }
  inimigos = inimigos.filter(e => !e.morto && e.y < H + 80);
  moedas = moedas.filter(m => !m.pega && m.y < H + 40);
}
function desenhaCarro(x, y, w, h, cor, jogador){
  ctx.save(); ctx.translate(x, y);
  ctx.fillStyle = '#111'; [[-w/2-4, -h/2+8], [w/2-3, -h/2+8], [-w/2-4, h/2-20], [w/2-3, h/2-20]].forEach(([a, b]) => { rr(a, b, 7, 14, 3); ctx.fill(); });
  ctx.fillStyle = cor; rr(-w/2, -h/2, w, h, 9); ctx.fill();
  ctx.fillStyle = 'rgba(255,255,255,.25)'; rr(-w/2 + 4, -h/2 + 3, w - 8, 6, 3); ctx.fill();
  ctx.fillStyle = '#1b2433'; rr(-w/2 + 5, jogador ? -h/2 + 14 : h/2 - 26, w - 10, 12, 4); ctx.fill();
  rr(-w/2 + 6, jogador ? h/2 - 20 : -h/2 + 12, w - 12, 8, 3); ctx.fill();
  if (jogador) { ctx.fillStyle = '#fff'; ctx.fillRect(-3, -h/2 + 28, 6, 22); }
  ctx.fillStyle = jogador ? '#fff7b0' : '#ff4d4d';
  ctx.fillRect(-w/2 + 4, jogador ? -h/2 : h/2 - 4, 8, 4); ctx.fillRect(w/2 - 12, jogador ? -h/2 : h/2 - 4, 8, 4);
  ctx.restore();
}
function desenhar(){
  ctx.fillStyle = '#2f8f3a'; ctx.fillRect(0, 0, W, H);
  for (const a of arvores) { ctx.fillStyle = '#1f6b2b'; ctx.beginPath(); ctx.arc(a.x + 3, a.y + 3, a.r, 0, 7); ctx.fill();
    ctx.fillStyle = '#3fae4f'; ctx.beginPath(); ctx.arc(a.x, a.y, a.r, 0, 7); ctx.fill(); }
  ctx.fillStyle = '#3a3d46'; ctx.fillRect(RX, 0, RW, H);
  for (let y = -40 + faixa % 40; y < H; y += 40) {
    ctx.fillStyle = (Math.floor((y - faixa)/40) % 2) ? '#e53935' : '#fff';
    ctx.fillRect(RX - 8, y, 8, 20); ctx.fillRect(RX + RW, y, 8, 20);
    ctx.fillStyle = (Math.floor((y - faixa)/40) % 2) ? '#fff' : '#e53935';
    ctx.fillRect(RX - 8, y + 20, 8, 20); ctx.fillRect(RX + RW, y + 20, 8, 20);
  }
  ctx.fillStyle = 'rgba(255,255,255,.75)';
  for (let y = -60 + faixa; y < H; y += 60) { ctx.fillRect(RX + RW/3 - 3, y, 6, 30); ctx.fillRect(RX + 2*RW/3 - 3, y, 6, 30); }
  for (const m of moedas) { const s = Math.abs(Math.cos(m.giro));
    ctx.fillStyle = '#f5b700'; ctx.beginPath(); ctx.ellipse(m.x, m.y, 11*s + 1, 11, 0, 0, 7); ctx.fill();
    ctx.fillStyle = '#ffe066'; ctx.beginPath(); ctx.ellipse(m.x, m.y, 7*s + 0.5, 7, 0, 0, 7); ctx.fill(); }
  for (const e of inimigos) desenhaCarro(e.x, e.y, e.w, e.h, e.cor, false);
  if (estado !== 'fim' && !(invul > 0 && Math.floor(invul*10) % 2)) desenhaCarro(carro.x, carro.y, carro.w, carro.h, '#e53935', true);
  for (const p of part) { ctx.globalAlpha = Math.max(0, p.t); ctx.fillStyle = p.cor; ctx.fillRect(p.x - 3, p.y - 3, 6, 6); }
  ctx.globalAlpha = 1;
  ctx.fillStyle = 'rgba(0,0,0,.45)'; rr(8, 8, 150, 52, 10); ctx.fill(); rr(W - 118, 8, 110, 52, 10); ctx.fill();
  texto('🏁 ' + Math.floor(pontos), 18, 24, 18, '#fff', 'left');
  texto(Math.round(vel/3) + ' km/h', 18, 46, 14, '#9fe6ff', 'left');
  texto('❤️'.repeat(Math.max(0, vidas)), W - 63, 24, 16);
  texto('Recorde ' + recorde, W - 63, 46, 13, '#ffd34d');
  if (estado === 'inicio') painel('🏎️ Corrida', ['Desvie dos carros e pegue as moedas!', '← → ou toque nos lados da tela', ajudaInicio()]);
  if (estado === 'pausa') painel('⏸️ Pausado', ['ESPAÇO ou toque para continuar']);
  if (estado === 'fim') painel('💥 Fim de corrida!', ['Pontos: ' + Math.floor(pontos), 'Recorde: ' + recorde, 'ESPAÇO ou toque para jogar de novo']);
}
"""

# ---------------------------------------------------------------- COME-COME
COMECOME_JS = r"""
const MAPA_TXT = [
 '###################',
 '#........#........#',
 '#o##.###.#.###.##o#',
 '#.................#',
 '#.##.#.#####.#.##.#',
 '#....#...#...#....#',
 '####.###.#.###.####',
 '####.#.......#.####',
 '####.#.##-##.#.####',
 '.......#EEE#.......',
 '####.#.#####.#.####',
 '####.#.......#.####',
 '####.#.#####.#.####',
 '#........#........#',
 '#.##.###.#.###.##.#',
 '#o.#.....P.....#.o#',
 '##.#.#.#####.#.#.##',
 '#....#...#...#....#',
 '#.######.#.######.#',
 '#.................#',
 '###################'];
const C = 19, L = 21, T = 24, TOPO = 34;
cv.width = C*T; cv.height = L*T + TOPO;
const DIRS = {esq: [-1, 0], dir: [1, 0], cima: [0, -1], baixo: [0, 1]};
const CORES_INI = ['#ff4d6d', '#ff9f1c', '#c77dff'];
let grade, resta, jog, inis, estado = 'inicio', pontos = 0, vidas = 3, nivel = 1, poderT = 0, combo = 0, timer = 0, relogio = 0,
    flutuantes = [], recorde = lerRecorde('rec_come');
function carregarMapa(){ grade = MAPA_TXT.map(l => l.replace(/[PE]/g, ' ').split('')); resta = 0;
  grade.forEach(l => l.forEach(c => { if (c === '.' || c === 'o') resta++; })); }
function posicionar(){
  jog = {x: 9, y: 15, dx: 0, dy: 0, p: 0, q: null, vel: Math.min(8.2, 6.6 + nivel*0.2)};
  const vi = Math.min(7.6, 5.0 + nivel*0.4);
  inis = [{x: 9, y: 7, modo: 'caca', espera: 0}, {x: 8, y: 9, modo: 'casa', espera: 2.5}, {x: 10, y: 9, modo: 'casa', espera: 6}]
    .map((e, i) => Object.assign(e, {dx: 0, dy: 0, p: 0, vel: vi, tipo: i, cor: CORES_INI[i]}));
  inis[0].dx = -1; poderT = 0;
}
function novoJogo(){ pontos = 0; vidas = 3; nivel = 1; carregarMapa(); posicionar(); }
novoJogo();
function celula(x, y){ x = ((x % C) + C) % C; if (y < 0 || y >= L) return '#'; return grade[y][x]; }
function passa(x, y, e){ const c = celula(x, y); if (c === '#') return false;
  if (c === '-') return !!e && (e.modo === 'saindo' || e.modo === 'voltando'); return true; }
function enrolar(e){ e.x = ((e.x % C) + C) % C; }
function aoApertar(k){
  if (DIRS[k] && jog) jog.q = DIRS[k];
  if (k === 'acao') { if (estado === 'inicio' || estado === 'fim') { novoJogo(); estado = 'pronto'; timer = 1.2; } else if (estado === 'pausa') estado = 'jogando'; }
  if (k === 'pausa') estado = estado === 'jogando' ? 'pausa' : estado === 'pausa' ? 'jogando' : estado;
}
function aoSoltar(k){}
let toqueIni = null;
cv.addEventListener('pointerdown', e => { cv.focus(); if (estado === 'inicio' || estado === 'fim' || estado === 'pausa') { aoApertar('acao'); return; }
  toqueIni = {x: e.clientX, y: e.clientY}; });
cv.addEventListener('pointermove', e => { if (!toqueIni) return; const dx = e.clientX - toqueIni.x, dy = e.clientY - toqueIni.y;
  if (Math.hypot(dx, dy) > 18) { jog.q = Math.abs(dx) > Math.abs(dy) ? (dx > 0 ? DIRS.dir : DIRS.esq) : (dy > 0 ? DIRS.baixo : DIRS.cima); toqueIni = {x: e.clientX, y: e.clientY}; } });
['pointerup', 'pointercancel'].forEach(t => cv.addEventListener(t, () => toqueIni = null));
function comer(x, y){
  const c = grade[y][x];
  if (c === '.') { grade[y][x] = ' '; pontos += 10; resta--; }
  else if (c === 'o') { grade[y][x] = ' '; pontos += 50; resta--; poderT = Math.max(3, 8 - nivel*0.6); combo = 0;
    for (const e of inis) if (e.modo === 'caca') { e.modo = 'medo'; if (e.dx || e.dy) { e.x += e.dx; e.y += e.dy; enrolar(e); e.dx = -e.dx; e.dy = -e.dy; e.p = 1 - e.p; } } }
  if (resta === 0) { estado = 'nivel'; timer = 2; }
}
function moverJog(dt){
  const j = jog;
  if (j.q && (j.dx || j.dy) && j.q[0] === -j.dx && j.q[1] === -j.dy) { j.x += j.dx; j.y += j.dy; enrolar(j); j.dx = -j.dx; j.dy = -j.dy; j.p = 1 - j.p; }
  if (!j.dx && !j.dy) { if (j.q && passa(j.x + j.q[0], j.y + j.q[1])) { j.dx = j.q[0]; j.dy = j.q[1]; } else return; }
  j.p += j.vel*dt;
  while (j.p >= 1) {
    j.p -= 1; j.x += j.dx; j.y += j.dy; enrolar(j); comer(j.x, j.y);
    if (j.q && passa(j.x + j.q[0], j.y + j.q[1])) { j.dx = j.q[0]; j.dy = j.q[1]; }
    else if (!passa(j.x + j.dx, j.y + j.dy)) { j.dx = 0; j.dy = 0; j.p = 0; break; }
  }
}
function alvo(e){
  if (e.modo === 'saindo') return [9, 7];
  if (e.modo === 'voltando') return [9, 9];
  if (e.modo === 'medo') return null;
  if (e.tipo === 0) return [jog.x, jog.y];
  if (e.tipo === 1) return [jog.x + jog.dx*4, jog.y + jog.dy*4];
  return Math.hypot(e.x - jog.x, e.y - jog.y) > 7 ? [jog.x, jog.y] : [1, 19];
}
function escolherDir(e){
  const opc = [];
  for (const [dx, dy] of Object.values(DIRS)) {
    if ((e.dx || e.dy) && dx === -e.dx && dy === -e.dy) continue;
    if (passa(e.x + dx, e.y + dy, e)) opc.push([dx, dy]);
  }
  if (!opc.length) { e.dx = -e.dx; e.dy = -e.dy; return; }
  const a = alvo(e); let esc;
  if (e.modo === 'medo') {
    esc = Math.random() < 0.35 ? opc[Math.floor(Math.random()*opc.length)]
        : opc.reduce((m, o) => { const d = Math.hypot(e.x + o[0] - jog.x, e.y + o[1] - jog.y); return d > m.d ? {o, d} : m; }, {o: opc[0], d: -1}).o;
  } else if (e.modo === 'caca' && Math.random() < 0.1) esc = opc[Math.floor(Math.random()*opc.length)];
  else esc = opc.reduce((m, o) => { const d = Math.hypot(e.x + o[0] - a[0], e.y + o[1] - a[1]); return d < m.d ? {o, d} : m; }, {o: opc[0], d: 1e9}).o;
  e.dx = esc[0]; e.dy = esc[1];
}
function moverIni(e, dt){
  if (e.modo === 'casa') { e.espera -= dt; if (e.espera <= 0) { e.modo = 'saindo'; escolherDir(e); } return; }
  const v = e.modo === 'medo' ? 3.4 : e.modo === 'voltando' ? 13 : e.modo === 'saindo' ? 4 : e.vel;
  if (!e.dx && !e.dy) escolherDir(e);
  e.p += v*dt;
  while (e.p >= 1) {
    e.p -= 1; e.x += e.dx; e.y += e.dy; enrolar(e);
    if (e.modo === 'saindo' && e.x === 9 && e.y === 7) e.modo = 'caca';
    if (e.modo === 'voltando' && e.x === 9 && e.y === 9) e.modo = 'saindo';
    escolherDir(e);
  }
}
function pos(e){ return [e.x + e.dx*e.p, e.y + e.dy*e.p]; }
function atualizar(dt){
  relogio += dt;
  flutuantes.forEach(f => { f.t -= dt; f.y -= 20*dt; }); flutuantes = flutuantes.filter(f => f.t > 0);
  if (estado === 'pronto') { timer -= dt; if (timer <= 0) estado = 'jogando'; return; }
  if (estado === 'morte') { timer -= dt; if (timer <= 0) { if (vidas > 0) { posicionar(); estado = 'pronto'; timer = 1.2; }
    else { estado = 'fim'; recorde = salvarRecorde('rec_come', pontos); } } return; }
  if (estado === 'nivel') { timer -= dt; if (timer <= 0) { nivel++; carregarMapa(); posicionar(); estado = 'pronto'; timer = 1.5; } return; }
  if (estado !== 'jogando') return;
  for (const k of ['esq', 'dir', 'cima', 'baixo']) if (keys[k]) jog.q = DIRS[k];
  if (poderT > 0) { poderT -= dt; if (poderT <= 0) inis.forEach(e => { if (e.modo === 'medo') e.modo = 'caca'; }); }
  moverJog(dt);
  if (estado !== 'jogando') return;
  for (const e of inis) moverIni(e, dt);
  const [jx, jy] = pos(jog);
  for (const e of inis) {
    const [ex, ey] = pos(e);
    if (Math.hypot(jx - ex, jy - ey) < 0.7) {
      if (e.modo === 'medo') { const pts = 200 * 2 ** combo; combo = Math.min(combo + 1, 3); pontos += pts;
        flutuantes.push({x: ex, y: ey, t: 1, txt: pts}); e.modo = 'voltando'; }
      else if (e.modo === 'caca' || e.modo === 'saindo') { vidas--; estado = 'morte'; timer = 1.6; return; }
    }
  }
}
function desenharMapa(){
  ctx.fillStyle = '#060a1f'; ctx.fillRect(0, 0, cv.width, cv.height);
  for (let y = 0; y < L; y++) for (let x = 0; x < C; x++) {
    const c = grade[y][x], px = x*T, py = y*T + TOPO;
    if (c === '#') {
      ctx.fillStyle = '#121c55'; ctx.fillRect(px, py, T, T);
      ctx.strokeStyle = '#5b8cff'; ctx.lineWidth = 2; ctx.beginPath();
      if (y > 0 && grade[y-1][x] !== '#') { ctx.moveTo(px, py + 1); ctx.lineTo(px + T, py + 1); }
      if (y < L-1 && grade[y+1][x] !== '#') { ctx.moveTo(px, py + T - 1); ctx.lineTo(px + T, py + T - 1); }
      if (x > 0 && grade[y][x-1] !== '#') { ctx.moveTo(px + 1, py); ctx.lineTo(px + 1, py + T); }
      if (x < C-1 && grade[y][x+1] !== '#') { ctx.moveTo(px + T - 1, py); ctx.lineTo(px + T - 1, py + T); }
      ctx.stroke();
    } else if (c === '.') { ctx.fillStyle = '#ffd9a0'; ctx.beginPath(); ctx.arc(px + T/2, py + T/2, 3, 0, 7); ctx.fill(); }
    else if (c === 'o') { ctx.fillStyle = '#fff'; ctx.beginPath(); ctx.arc(px + T/2, py + T/2, 6 + Math.sin(relogio*8)*1.5, 0, 7); ctx.fill(); }
    else if (c === '-') { ctx.fillStyle = '#ff8fd1'; ctx.fillRect(px, py + T/2 - 2, T, 4); }
  }
}
function desenharSlime(x, y){
  const s = 1 + Math.sin(relogio*14)*0.06, olhar = jog.dx || jog.dy ? [jog.dx, jog.dy] : [0, 0];
  ctx.save(); ctx.translate(x, y); ctx.scale(1/s, s);
  ctx.fillStyle = '#39d353'; ctx.beginPath(); ctx.arc(0, 0, 10.5, 0, 7); ctx.fill();
  ctx.fillStyle = 'rgba(255,255,255,.35)'; ctx.beginPath(); ctx.arc(-4, -5, 3.5, 0, 7); ctx.fill();
  for (const ox of [-4, 4]) { ctx.fillStyle = '#fff'; ctx.beginPath(); ctx.arc(ox, -2, 3.6, 0, 7); ctx.fill();
    ctx.fillStyle = '#111'; ctx.beginPath(); ctx.arc(ox + olhar[0]*1.6, -2 + olhar[1]*1.6, 1.8, 0, 7); ctx.fill(); }
  ctx.strokeStyle = '#145a22'; ctx.lineWidth = 1.6; ctx.beginPath(); ctx.arc(0, 3, 3.5, 0.2, Math.PI - 0.2); ctx.stroke();
  ctx.restore();
}
function desenharVirus(e, x, y){
  const piscar = e.modo === 'medo' && poderT < 2 && Math.floor(relogio*8) % 2;
  const cor = e.modo === 'medo' ? (piscar ? '#fff' : '#2f6bff') : e.cor;
  ctx.save(); ctx.translate(x, y);
  if (e.modo !== 'voltando') {
    ctx.strokeStyle = cor; ctx.fillStyle = cor; ctx.lineWidth = 2;
    for (let i = 0; i < 8; i++) { const a = i*Math.PI/4 + relogio*2;
      ctx.beginPath(); ctx.moveTo(Math.cos(a)*8, Math.sin(a)*8); ctx.lineTo(Math.cos(a)*12, Math.sin(a)*12); ctx.stroke();
      ctx.beginPath(); ctx.arc(Math.cos(a)*12, Math.sin(a)*12, 2, 0, 7); ctx.fill(); }
    ctx.beginPath(); ctx.arc(0, 0, 9, 0, 7); ctx.fill();
  }
  if (e.modo === 'medo') { ctx.strokeStyle = '#fff'; ctx.lineWidth = 1.5; ctx.beginPath();
    for (let i = 0; i <= 4; i++) ctx.lineTo(-5 + i*2.5, 3 + (i % 2 ? -1.5 : 1.5)); ctx.stroke();
    ctx.fillStyle = '#fff'; ctx.fillRect(-4, -3, 2, 2); ctx.fillRect(2, -3, 2, 2); }
  else { for (const ox of [-3.5, 3.5]) { ctx.fillStyle = '#fff'; ctx.beginPath(); ctx.arc(ox, -1.5, 3, 0, 7); ctx.fill();
      ctx.fillStyle = '#111'; ctx.beginPath(); ctx.arc(ox + e.dx*1.3, -1.5 + e.dy*1.3, 1.6, 0, 7); ctx.fill(); }
    if (e.modo !== 'voltando') { ctx.strokeStyle = '#111'; ctx.lineWidth = 1.5; ctx.beginPath();
      ctx.moveTo(-6, -6); ctx.lineTo(-1.5, -4); ctx.moveTo(6, -6); ctx.lineTo(1.5, -4); ctx.stroke(); } }
  ctx.restore();
}
function desenhar(){
  desenharMapa();
  for (const e of inis) { const [x, y] = pos(e); desenharVirus(e, x*T + T/2, y*T + T/2 + TOPO); }
  const [jx, jy] = pos(jog);
  if (estado === 'morte') { const s = Math.max(0, timer/1.6); ctx.globalAlpha = s; desenharSlime(jx*T + T/2, jy*T + T/2 + TOPO); ctx.globalAlpha = 1; }
  else desenharSlime(jx*T + T/2, jy*T + T/2 + TOPO);
  for (const f of flutuantes) texto(f.txt, f.x*T + T/2, f.y*T + TOPO, 14, '#7df9ff');
  ctx.fillStyle = '#060a1f'; ctx.fillRect(0, 0, cv.width, TOPO);
  texto('Pontos ' + pontos, 10, TOPO/2, 16, '#fff', 'left');
  texto('Nível ' + nivel, cv.width/2, TOPO/2, 16, '#9fe6ff');
  for (let i = 0; i < vidas; i++) { ctx.fillStyle = '#39d353'; ctx.beginPath(); ctx.arc(cv.width - 16 - i*22, TOPO/2, 8, 0, 7); ctx.fill(); }
  if (estado === 'pronto') texto('PREPARE-SE!', cv.width/2, (11.5)*T + TOPO, 22, '#ffd34d');
  if (estado === 'nivel') texto('NÍVEL ' + nivel + ' COMPLETO! 🎉', cv.width/2, (11.5)*T + TOPO, 20, '#ffd34d');
  if (estado === 'inicio') painel('🟢 Come-Come', ['Coma todas as bolinhas sem ser pego', 'pelos vírus! Bolona = vírus com medo', 'Setas, arrastar o dedo ou botões', ajudaInicio()]);
  if (estado === 'pausa') painel('⏸️ Pausado', ['ESPAÇO ou toque para continuar']);
  if (estado === 'fim') painel('Fim de jogo!', ['Pontos: ' + pontos + '   ·   Nível ' + nivel, 'Recorde: ' + recorde, 'ESPAÇO ou toque para jogar de novo']);
}
"""

# ---------------------------------------------------------------- PINBALL
PINBALL_JS = r"""
const W = 400, H = 640; cv.width = W; cv.height = H;
const G = 760, R = 9;
const segs = [];
function seg(ax, ay, bx, by, o = {}){ const s = {ax, ay, bx, by, rest: o.rest ?? 0.45, kick: o.kick || 0, cor: o.cor || '#6f8cff', lw: o.lw || 5, flash: 0, gate: !!o.gate};
  segs.push(s); return s; }
function linha(pts, o){ for (let i = 0; i < pts.length - 1; i++) seg(pts[i][0], pts[i][1], pts[i+1][0], pts[i+1][1], o); }
linha([[125, 592], [10, 500], [10, 90], [28, 42], [65, 16], [110, 8], [290, 8], [335, 16], [372, 40], [395, 90], [395, 628]]);
seg(360, 628, 395, 628);                                   // fundo da canaleta
seg(360, 628, 360, 175);                                   // parede da canaleta
linha([[360, 500], [275, 592]]);
const portao = seg(360, 175, 395, 140, {gate: true, cor: '#ffd34d', lw: 3});
linha([[55, 420], [55, 492], [104, 538]], {cor: '#6f8cff'});
const estilingues = [seg(55, 420, 104, 538, {kick: 520, rest: 0.2, cor: '#ff5ea8', lw: 6}),
                     seg(305, 420, 256, 538, {kick: 520, rest: 0.2, cor: '#ff5ea8', lw: 6})];
linha([[305, 420], [305, 492], [256, 538]], {cor: '#6f8cff'});
linha([[96, 60], [96, 100]], {cor: '#6f8cff', lw: 4}); linha([[304, 60], [304, 100]], {cor: '#6f8cff', lw: 4});
const bumpers = [{x: 140, y: 190, r: 24, cor: '#ff4d6d', flash: 0}, {x: 260, y: 190, r: 24, cor: '#2ec4b6', flash: 0},
                 {x: 200, y: 280, r: 24, cor: '#ffb02e', flash: 0}];
const postes = [{x: 200, y: 120, r: 7}, {x: 30, y: 280, r: 6}, {x: 330, y: 280, r: 6}];
const luzes = [{x: 150, y: 72}, {x: 200, y: 72}, {x: 250, y: 72}];
const flippers = [{px: 125, py: 592, len: 64, lado: 1, a: 0.5, tecla: 'esq'}, {px: 275, py: 592, len: 64, lado: -1, a: 0.5, tecla: 'dir'}];
const REPOUSO = 0.5, CIMA = -0.48;
let bola, antes = 'jogando', estado = 'inicio', pontos = 0, bolas = 3, mult = 1, forca = 0, carregando = false, msg = '', msgT = 0,
    recorde = lerRecorde('rec_pinball');
function pontaFlipper(f){ return [f.px + f.lado*f.len*Math.cos(f.a), f.py + f.len*Math.sin(f.a)]; }
function novaBola(){ bola = {x: 377.5, y: 616, vx: 0, vy: 0}; bola.naMesa = false; forca = 0; carregando = false; estado = 'lancar'; }
function novoJogo(){ pontos = 0; bolas = 3; mult = 1; luzes.forEach(l => l.on = false); novaBola(); }
function aviso(t){ msg = t; msgT = 1.6; }
function aoApertar(k){
  if (k === 'acao') {
    if (estado === 'inicio' || estado === 'fim') { novoJogo(); return; }
    if (estado === 'pausa') { estado = antes; return; }
    if (estado === 'lancar') carregando = true;
  }
  if (k === 'pausa') { if (estado === 'jogando' || estado === 'lancar') { antes = estado; carregando = false; estado = 'pausa'; } else if (estado === 'pausa') estado = antes; }
}
function aoSoltar(k){
  if (k === 'acao' && estado === 'lancar' && carregando) { bola.vy = -(980 + 760*forca); carregando = false; forca = 0; estado = 'jogando'; }
}
const toques = {};
cv.addEventListener('pointerdown', e => {
  cv.focus();
  if (estado === 'inicio' || estado === 'fim' || estado === 'pausa') { aoApertar('acao'); return; }
  const r = cv.getBoundingClientRect(), x = (e.clientX - r.left)/r.width*W;
  if (estado === 'lancar' && x > 340) { toques[e.pointerId] = 'acao'; apertar('acao'); return; }
  const lado = x < W/2 ? 'esq' : 'dir'; toques[e.pointerId] = lado; apertar(lado);
});
['pointerup', 'pointercancel', 'pointerleave'].forEach(t => cv.addEventListener(t, e => {
  const l = toques[e.pointerId]; if (l) { delete toques[e.pointerId]; if (!Object.values(toques).includes(l)) soltar(l); } }));
function marcar(p){ pontos += p*mult; }
function colideSeg(ax, ay, bx, by, raio, rest, vSup){
  const dx = bx - ax, dy = by - ay; let t = ((bola.x - ax)*dx + (bola.y - ay)*dy)/(dx*dx + dy*dy);
  t = Math.max(0, Math.min(1, t));
  const px = ax + t*dx, py = ay + t*dy; let nx = bola.x - px, ny = bola.y - py; const d = Math.hypot(nx, ny);
  if (d >= raio || d === 0) return null;
  nx /= d; ny /= d; bola.x = px + nx*raio; bola.y = py + ny*raio;
  const sx = vSup ? vSup[0]*t : 0, sy = vSup ? vSup[1]*t : 0;
  const rvx = bola.vx - sx, rvy = bola.vy - sy, vn = rvx*nx + rvy*ny;
  if (vn < 0) { bola.vx = rvx - (1 + rest)*vn*nx + sx; bola.vy = rvy - (1 + rest)*vn*ny + sy; }
  return {nx, ny, vn};
}
function colideCirculo(c, rest, impulso){
  const dx = bola.x - c.x, dy = bola.y - c.y, d = Math.hypot(dx, dy), m = c.r + R;
  if (d >= m || d === 0) return false;
  const nx = dx/d, ny = dy/d; bola.x = c.x + nx*m; bola.y = c.y + ny*m;
  const vn = bola.vx*nx + bola.vy*ny;
  if (vn < 0) { bola.vx -= (1 + rest)*vn*nx; bola.vy -= (1 + rest)*vn*ny; }
  if (impulso) { const v = Math.hypot(bola.vx, bola.vy); if (v < impulso) { bola.vx += nx*(impulso - v); bola.vy += ny*(impulso - v); } }
  return true;
}
function passo(h){
  for (const f of flippers) { f.ponta0 = pontaFlipper(f); const alvo = keys[f.tecla] && estado !== 'pausa' ? CIMA : REPOUSO;
    const vel = alvo < f.a ? 24 : 12; f.a = alvo < f.a ? Math.max(alvo, f.a - vel*h) : Math.min(alvo, f.a + vel*h); }
  if (estado === 'lancar') { bola.x = 377.5; bola.y = 616; bola.vx = bola.vy = 0; return; }
  bola.vy += G*h; bola.x += bola.vx*h; bola.y += bola.vy*h;
  const v = Math.hypot(bola.vx, bola.vy); if (v > 1900) { bola.vx *= 1900/v; bola.vy *= 1900/v; }
  if (!bola.naMesa && bola.x < 350) bola.naMesa = true;
  for (const s of segs) {
    if (s.gate && !bola.naMesa) continue;
    const c = colideSeg(s.ax, s.ay, s.bx, s.by, R + s.lw/2, s.rest);
    if (c && s.kick && c.vn < -60) { bola.vx += c.nx*s.kick; bola.vy += c.ny*s.kick; s.flash = 0.15; marcar(10); }
  }
  for (const b of bumpers) if (colideCirculo(b, 0.6, 720)) { if (b.flash <= 0.05) marcar(100); b.flash = 0.18; }
  for (const p of postes) colideCirculo(p, 0.5, 0);
  for (const f of flippers) { const p = pontaFlipper(f);
    const vs = [(p[0] - f.ponta0[0])/h, (p[1] - f.ponta0[1])/h];
    colideSeg(f.px, f.py, p[0], p[1], R + 7, 0.25, vs); }
  for (const l of luzes) if (!l.on && Math.hypot(bola.x - l.x, bola.y - l.y) < 16) { l.on = true; marcar(50);
    if (luzes.every(x => x.on)) { mult = Math.min(5, mult + 1); aviso('MULTIPLICADOR x' + mult + '!'); marcar(500); setTimeout(() => luzes.forEach(x => x.on = false), 700); } }
  if (bola.y > H + 30) {
    bolas--;
    if (bolas > 0) { aviso('Bola perdida! Restam ' + bolas); novaBola(); }
    else { estado = 'fim'; recorde = salvarRecorde('rec_pinball', pontos); }
  }
}
function atualizar(dt){
  msgT -= dt; for (const b of bumpers) b.flash -= dt; for (const s of segs) s.flash -= dt;
  if (estado === 'lancar' && carregando) forca = Math.min(1, forca + dt*0.9);
  if (estado !== 'jogando' && estado !== 'lancar') return;
  const n = 10; for (let i = 0; i < n; i++) passo(dt/n);
}
function desenhar(){
  const g = ctx.createLinearGradient(0, 0, 0, H); g.addColorStop(0, '#1a0f3d'); g.addColorStop(1, '#090616');
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  ctx.globalAlpha = 0.13; texto(pontos, 200, 400, 64, '#fff'); ctx.globalAlpha = 1;
  texto('x' + mult, 200, 445, 18, '#ffd34d');
  for (const l of luzes) { ctx.fillStyle = l.on ? '#ffe066' : '#3a2f66'; ctx.beginPath(); ctx.arc(l.x, l.y, 9, 0, 7); ctx.fill();
    if (l.on) { ctx.strokeStyle = 'rgba(255,224,102,.5)'; ctx.lineWidth = 4; ctx.stroke(); } }
  ctx.lineCap = 'round';
  for (const s of segs) { if (s.gate && !bola.naMesa) continue; ctx.strokeStyle = s.flash > 0 ? '#fff' : s.cor; ctx.lineWidth = s.lw;
    ctx.beginPath(); ctx.moveTo(s.ax, s.ay); ctx.lineTo(s.bx, s.by); ctx.stroke(); }
  for (const b of bumpers) { const f = b.flash > 0;
    ctx.fillStyle = f ? '#fff' : b.cor; ctx.beginPath(); ctx.arc(b.x, b.y, b.r + (f ? 3 : 0), 0, 7); ctx.fill();
    ctx.fillStyle = '#1a0f3d'; ctx.beginPath(); ctx.arc(b.x, b.y, b.r*0.55, 0, 7); ctx.fill();
    ctx.fillStyle = f ? b.cor : '#fff'; ctx.beginPath(); ctx.arc(b.x, b.y, b.r*0.3, 0, 7); ctx.fill(); }
  for (const p of postes) { ctx.fillStyle = '#9fb3ff'; ctx.beginPath(); ctx.arc(p.x, p.y, p.r, 0, 7); ctx.fill(); }
  for (const f of flippers) { const p = pontaFlipper(f);
    ctx.strokeStyle = '#ffd34d'; ctx.lineWidth = 15; ctx.beginPath(); ctx.moveTo(f.px, f.py); ctx.lineTo(p[0], p[1]); ctx.stroke();
    ctx.fillStyle = '#b8860b'; ctx.beginPath(); ctx.arc(f.px, f.py, 4, 0, 7); ctx.fill(); }
  ctx.fillStyle = '#2b2350'; ctx.fillRect(363, 628, 30, 10);
  if (estado === 'lancar') { ctx.fillStyle = 'rgba(255,94,168,.25)'; ctx.fillRect(366, 550, 24, 80);
    ctx.fillStyle = '#ff5ea8'; ctx.fillRect(366, 630 - forca*80, 24, forca*80); }
  const bg = ctx.createRadialGradient(bola.x - 3, bola.y - 3, 1, bola.x, bola.y, R);
  bg.addColorStop(0, '#fff'); bg.addColorStop(1, '#8a93a8');
  ctx.fillStyle = bg; ctx.beginPath(); ctx.arc(bola.x, bola.y, R, 0, 7); ctx.fill();
  texto('Bolas: ' + '⚪'.repeat(Math.max(0, bolas)), 20, 628, 13, '#cfd6ff', 'left');
  if (msgT > 0) texto(msg, 200, 340, 20, '#ffd34d');
  if (estado === 'lancar' && msgT <= 0) texto(matchMedia('(pointer: coarse)').matches ? 'Segure 🚀 e solte' : 'Segure ESPAÇO e solte', 200, 340, 17, '#ff9fd0');
  if (estado === 'inicio') painel('🪩 Pinball', ['Não deixe a bola cair entre as palhetas!', '← → (ou toque nos lados) mexem as palhetas', 'ESPAÇO / 🚀 segura e solta para lançar', ajudaInicio()]);
  if (estado === 'pausa') painel('⏸️ Pausado', ['ESPAÇO ou toque para continuar']);
  if (estado === 'fim') painel('Fim de jogo!', ['Pontos: ' + pontos, 'Recorde: ' + recorde, 'ESPAÇO ou toque para jogar de novo']);
}
novaBola(); estado = 'inicio';
"""

BOTOES_CORRIDA = '<button data-k="esq">◀ Esquerda</button><button data-k="dir">Direita ▶</button>'
BOTOES_COME = ('<button data-k="esq">◀</button><button data-k="cima">▲</button>'
               '<button data-k="baixo">▼</button><button data-k="dir">▶</button>')
BOTOES_PINBALL = '<button data-k="esq">◀ Palheta</button><button data-k="acao">🚀</button><button data-k="dir">Palheta ▶</button>'


def jogo_animado(js, largura, altura_iframe, botoes):
    pagina = pagina_canvas(js, largura, botoes)
    if hasattr(st, "iframe"):  # Streamlit novo
        st.iframe(pagina, height=altura_iframe)
    else:  # Streamlit antigo
        components.html(pagina, height=altura_iframe, scrolling=False)
    st.caption("🖱️ No computador, clique no jogo antes de usar o teclado. 📱 No celular, use os botões ou toque na tela.")


def jogo_pinball():
    jogo_animado(PINBALL_JS, 400, 730, BOTOES_PINBALL)


def jogo_comecome():
    jogo_animado(COMECOME_JS, 456, 640, BOTOES_COME)


def jogo_corrida():
    jogo_animado(CORRIDA_JS, 360, 690, BOTOES_CORRIDA)


# =====================================================================
# 👑 A VIDA É UM JOGO — Do Zero ao Império  (motor da simulação)
# =====================================================================
RAMOS = {
    "🏗️ Construção civil": dict(mercado=4500, cap0=7000, capf=14000, margem=.35, fixo=400, salario=2800, vol=.35,
        desc="Contratos grandes e lucrativos, mas o dinheiro oscila muito e a burocracia pesa."),
    "🤖 Tecnologia e IA": dict(mercado=2200, cap0=5000, capf=11000, margem=.70, fixo=300, salario=5000, vol=.25,
        desc="Margem altíssima e crescimento rápido. A equipe é cara e conhecimento vale ouro."),
    "🍔 Alimentação": dict(mercado=5000, cap0=6500, capf=9000, margem=.38, fixo=800, salario=2000, vol=.12,
        desc="Cliente todo dia e faturamento estável, porém margem apertada."),
    "🛒 Comércio": dict(mercado=6000, cap0=8000, capf=11000, margem=.30, fixo=700, salario=1900, vol=.15,
        desc="Gira bem e escala fácil, mas a guerra de preços é feroz."),
    "🧰 Prestação de serviços": dict(mercado=2500, cap0=4500, capf=6000, margem=.62, fixo=400, salario=2300, vol=.18,
        desc="Começa barato e com boa margem, mas depende muito de você e da sua reputação."),
    "🏠 Mercado imobiliário": dict(mercado=2200, cap0=7000, capf=9000, margem=.75, fixo=400, salario=3200, vol=.45,
        desc="Comissões enormes, mas meses de vacas magras. Para quem aguenta o sobe-e-desce."),
}
FASES = [  # nome, faturamento médio mensal mínimo, patrimônio mínimo
    ("🌱 Sonhador", 0, -1e12),
    ("🛠️ Autônomo", 4000, 0),
    ("🏪 Pequeno Negócio", 15000, 30000),
    ("🏢 Empresa em Crescimento", 50000, 250000),
    ("🏙️ Empresa Consolidada", 250000, 2000000),
    ("🏰 Império", 1000000, 10000000),
]
ESTRUTURAS = [("Cantinho em casa", 1), ("Salinha alugada", 4), ("Loja / escritório", 12),
              ("Andar comercial", 35), ("Sede própria", 90), ("Complexo empresarial", 250)]
CUSTO_VIDA = 1200
IND = ["rep", "rel", "saude", "felic", "conhec", "integ"]
NOME_IND = {"rep": "⭐ Reputação", "rel": "🤝 Relacionamentos", "saude": "💚 Saúde emocional",
            "felic": "😊 Felicidade", "conhec": "📚 Conhecimento", "integ": "⚖️ Integridade"}

NOMES_M = ["Roberto", "Carlos", "Marcos", "Eduardo", "Fábio", "Rafael", "Thiago", "Leandro", "Gustavo",
           "Paulo", "Henrique", "Sérgio", "Diego", "Vinícius", "Rodrigo", "André"]
NOMES_F = ["Juliana", "Patrícia", "Camila", "Fernanda", "Renata", "Larissa", "Beatriz", "Vanessa",
           "Aline", "Marina", "Cláudia", "Débora", "Bianca", "Letícia", "Priscila", "Tatiane"]
PAPEIS = {
    "socio": dict(titulo="🤝 Sócio(a) em potencial", bom=.4,
                  b="empresário(a) honesto(a) e experiente, cauteloso(a) com promessas, faz questão de contrato bem feito",
                  r="oportunista que quer o capital do jogador e fugir das responsabilidades; exagera contatos, apressa decisões, evita falar de contrato"),
    "amigo": dict(titulo="🫂 Amigo(a) de longa data", bom=.65,
                  b="amigo(a) leal de verdade, sincero(a), às vezes diz verdades duras porque se importa",
                  r="falso(a) amigo(a): bajula quando há dinheiro, pede favores, some nas horas difíceis e fala mal dos outros"),
    "novo_amigo": dict(titulo="🥂 Amigo(a) novo(a) do sucesso", bom=.3,
                       b="pessoa bem-sucedida que admira o jogador de verdade e gosta de ajudar sem interesse",
                       r="aproveitador(a) que surgiu quando o jogador prosperou, vive de aparências e de 'negócios garantidos'"),
    "consultor": dict(titulo="📊 Consultor(a)", bom=.65,
                      b="consultor(a) competente, faz perguntas difíceis, mostra números, cobra caro mas entrega",
                      r="consultor(a) de palco: frases de efeito, slides bonitos, nenhum plano concreto"),
    "advogado": dict(titulo="⚖️ Advogado(a)", bom=.85,
                     b="advogado(a) cuidadoso(a) e ético(a), aponta riscos em contratos e recomenda prudência",
                     r="advogado(a) que só pensa em honorários e incentiva brigas judiciais desnecessárias"),
    "investidor": dict(titulo="💼 Investidor(a)", bom=.6,
                       b="investidor(a) sério(a), quer crescer junto, respeita a cultura da empresa",
                       r="investidor(a) predador(a): quer controle total, cortar custos a qualquer preço e vender a empresa"),
    "concorrente": dict(titulo="🦈 Concorrente", bom=.15,
                        b="concorrente duro(a) mas leal, compete com qualidade e respeita regras",
                        r="concorrente desleal: espalha boatos, rouba funcionários e clientes, blefa o tempo todo"),
    "amor": dict(titulo="❤️ Interesse amoroso", bom=.5,
                 b="pessoa genuína, gosta do jogador independentemente do dinheiro, pergunta sobre sentimentos, sonhos e família",
                 r="pessoa interesseira: muito carinhosa, mas sempre puxa assunto sobre patrimônio, presentes, viagens caras e conta conjunta"),
    "mentor": dict(titulo="🧓 Mentor(a)", bom=.85,
                   b="empresário(a) veterano(a) generoso(a) que ensina com histórias reais de erros e acertos",
                   r="empresário(a) vaidoso(a) que dá conselhos para se promover e cobra favores depois"),
}
PISTAS = {
    True: ["Ex-parceiros falam muito bem de {n}.", "{n} tem nome limpo, sem processos na Justiça.",
           "Gente próxima diz que {n} sempre cumpre o que promete.", "{n} ajudou um conhecido seu de graça no ano passado."],
    False: ["Há processos por calote no nome de {n}.", "Um antigo colega diz que {n} 'some quando a coisa aperta'.",
            "{n} já abriu e fechou quatro empresas em cinco anos.", "Uma pessoa confidenciou que {n} vive pedindo dinheiro emprestado."],
}

CONQUISTAS = {
    "primeiro_lucro": ("💵 Primeiro Lucro", "Feche um mês no azul."),
    "primeiro_func": ("👥 Agora Somos Dois", "Contrate seu primeiro funcionário."),
    "colchao": ("🛟 Colchão de Segurança", "Tenha R$ 20 mil em caixa."),
    "fase2": ("🏪 Pequeno Negócio", "Chegue à fase Pequeno Negócio."),
    "fase3": ("🏢 Em Crescimento", "Chegue à fase Empresa em Crescimento."),
    "fase4": ("🏙️ Consolidado", "Chegue à fase Empresa Consolidada."),
    "fase5": ("🏰 IMPÉRIO", "Chegue à fase Império."),
    "milhao": ("💎 Primeiro Milhão", "Tenha patrimônio de R$ 1 milhão."),
    "sequencia": ("🔥 Máquina de Lucro", "Lucre 6 meses seguidos."),
    "sem_divida": ("🕊️ Livre de Dívidas", "Quite totalmente uma dívida."),
    "detetive": ("🕵️ Detetive", "Desmascare alguém antes de sair no prejuízo."),
    "licao": ("🩹 Lição Cara", "Caia num golpe (acontece com os melhores)."),
    "maos_limpas": ("🧼 Mãos Limpas", "Chegue ao mês 24 com integridade 90 ou mais."),
    "familia": ("🏡 Coração em Primeiro Lugar", "Tenha relacionamentos 90 ou mais."),
    "amor": ("💍 Amor Verdadeiro", "Case com uma pessoa genuína."),
    "empregos": ("🏭 Gerador de Empregos", "Tenha 10 funcionários."),
    "sobrevivente": ("🎂 5 Anos de Estrada", "Sobreviva 60 meses."),
    "familia_formada": ("👶 Família Formada", "Tenha um filho."),
    "amor_que_dura": ("💞 Amor que Dura", "Chegue ao mês 60 casado(a) e com atenção ao relacionamento acima de 70."),
    "superacao": ("🌅 Superação", "Recupere a saúde emocional (70+) depois de uma traição."),
    "vida_plena": ("🌈 Vida Plena", "Tenha as 5 dimensões da vida em 70 ou mais."),
}


def brl(v):
    return ("-R$ " if v < 0 else "R$ ") + f"{abs(v):,.0f}".replace(",", ".")


def ele(p):
    return "ele" if p["sexo"] == "M" else "ela"


def oa(p):
    return "o" if p["sexo"] == "M" else "a"


def mudar(e, **kw):
    for k, v in kw.items():
        if k in ("caixa", "divida"):
            e[k] += v
        elif k == "mercado":  # multiplicador
            e["mercado"] = max(300, e["mercado"] * v)
        else:
            e[k] = max(0, min(100, e[k] + v))


def log(e, texto, pid=None):
    e["diario"].append((e["mes"], texto, pid))


def agendar(e, meses, fn):
    e["pend"].append({"mes": e["mes"] + meses, "fn": fn})


def forcar(e, meses, ev_id):
    e["forcados"].append({"mes": e["mes"] + meses, "ev": ev_id})


def conquistar(e, cid):
    if cid not in e["conquistas"]:
        e["conquistas"].add(cid)
        e["novas_conq"].append(cid)


def media(lista, n=3):
    ult = lista[-n:]
    return sum(ult) / len(ult) if ult else 0


def receita_media(e):
    return media(e["hist_receita"]) if e["hist_receita"] else e["r"]["mercado"]


def valor_empresa(e):
    """Lucro líquido médio × um múltiplo que cresce com o tamanho da empresa."""
    liquido = media(e["hist_lucro_op"]) - CUSTO_VIDA
    return max(0, liquido) * (6 + min(30, 2 * e["func"] + 4 * e["estrutura"]))


def patrimonio(e):
    return e["caixa"] - e["divida"] + valor_empresa(e) * e["part"]


def limite_credito(e):
    return max(0, 5000 + receita_media(e) * 3 + e["rep"] * 100 - e["divida"])


def sat(e):
    """Quanto maior o negócio, mais difícil crescer (saturação de mercado)."""
    return 1 / (1 + e["mercado"] / 40000)


def capacidade(e):
    cap = e["r"]["cap0"] + e["func"] * e["r"]["capf"]
    return cap * (0.7 if e["saude"] < 20 else 1)


def margem(e):
    return min(0.92, e["r"]["margem"] + e["conhec"] / 1000 + e["bonus_margem"])


def custo_fixo(e):
    return e["r"]["fixo"] * (1.8 ** e["estrutura"])


def folha(e):
    return e["func"] * e["r"]["salario"] * (1 + e["extra_salario"])


def fase_atual(e):
    rm, pat, f = receita_media(e), patrimonio(e), 0
    for i, (_, fat, pmin) in enumerate(FASES):
        if rm >= fat and pat >= pmin:
            f = i
    return f


def dimensoes(e):
    pat = patrimonio(e)
    pros = 0 if pat <= 1000 else min(100, 20 * math.log10(pat / 1000))
    return {
        "💰 Prosperidade": round(pros),
        "🏢 Empresa": round(min(100, e["fase_max"] * 16 + e["rep"] * 0.2)),
        "🌿 Qualidade de vida": round((e["saude"] + e["felic"]) / 2),
        "🤝 Relacionamentos": round(e["rel"]),
        "⚖️ Integridade": round(e["integ"]),
    }


def pontuacao(e):
    return int(sum(dimensoes(e).values()) * 2)


def titulo_vida(pts):
    for lim, t in [(200, "Sobrevivente em Apuros"), (400, "Batalhador(a)"), (550, "Empreendedor(a) de Verdade"),
                   (700, "Referência no Mercado"), (850, "Lenda dos Negócios")]:
        if pts < lim:
            return t
    return "👑 Mestre da Vida"


def nova_pessoa(e, papel, forcar_bom=None):
    usados = {p["nome"] for p in e["pessoas"].values()}
    sexo = random.choice("MF")
    nomes = [n for n in (NOMES_M if sexo == "M" else NOMES_F) if n not in usados] or ["Alex"]
    pid = f"p{len(e['pessoas'])}"
    bom = forcar_bom if forcar_bom is not None else random.random() < PAPEIS[papel]["bom"]
    p = dict(id=pid, nome=random.choice(nomes), sexo=sexo, idade=random.randint(26, 62), papel=papel,
             bom=bom, pistas=[], ativo=True, revelado=False, conheceu=e["mes"])
    e["pessoas"][pid] = p
    e["chats"][pid] = []
    log(e, f"Você conheceu {p['nome']} ({PAPEIS[papel]['titulo']}).", pid)
    return p


def pessoa(e, papel, criar=True):
    for p in e["pessoas"].values():
        if p["papel"] == papel and p["ativo"]:
            return p
    return nova_pessoa(e, papel) if criar else None


def investigar(e, p):
    verdade = p["bom"] if random.random() < 0.8 else not p["bom"]
    pista = random.choice(PISTAS[verdade]).format(n=p["nome"])
    if pista not in p["pistas"]:
        p["pistas"].append(pista)
    return pista


def revelar(e, p):
    p["revelado"] = True
    if not p["bom"]:
        log(e, f"🚩 Você descobriu quem {p['nome']} realmente é.", p["id"])


def novo_jogo_vida(jogador, empresa, ramo, legado=0):
    r = dict(RAMOS[ramo])
    e = dict(jogador=jogador, empresa=empresa, ramo=ramo, r=r, mes=1, caixa=3000.0, divida=0.0, taxa=0.0,
             mercado=float(r["mercado"]), func=0, estrutura=0, part=1.0, bonus_margem=0.0, extra_salario=0.0,
             vida_mult=1.0, rep=40, rel=60, saude=80, felic=65, conhec=15 + legado, integ=70,
             hist_receita=[], hist_lucro_op=[], hist_resultado=[], pessoas={}, chats={}, diario=[], pend=[], forcados=[],
             conquistas=set(), novas_conq=[], usados=[], ja=set(), flags=set(), fase_max=0, seq_lucro=0,
             etapa="acao", ev=None, resultados=[], noticias=[], relatorio=None, fim=None, teve_divida=False,
             parceiro=None, socio=None, avaliacao5=False, atencao=60, regime=None, filhos=0,
             namoro_desde=None)
    nova_pessoa(e, "amigo")
    log(e, f"Você abriu \"{empresa}\" no ramo {ramo} com {brl(3000)} no bolso e um computador velho. Começa a jornada!")
    e["prox"] = escolher_evento(e)
    return e


# ---------------------------------------------------------------- AÇÕES DO MÊS
def acoes_disponiveis(e):
    rm = receita_media(e)
    mkt = max(500, round(rm * 0.3, -2))
    estudo = 400 + 300 * e["fase_max"]
    inov = round(1000 + rm * 0.4, -2)
    amp = round(2500 * 2.6 ** e["estrutura"], -2)
    lista = [
        ("💼 Vender e prospectar", "Bater de porta em porta atrás de clientes. Mercado +12%, mas cansa.", 0, "vender"),
        (f"📣 Marketing ({brl(mkt)})", "Anúncios e redes sociais. Traz bastante cliente novo.", mkt, "marketing"),
        (f"📚 Estudar e se capacitar ({brl(estudo)})", "Cursos e livros. Conhecimento melhora margem e decisões.", estudo, "estudar"),
        ("🍻 Networking em eventos (R$ 300)", "Conhecer gente nova. Rende contatos e oportunidades.", 300, "network"),
        ("🧘 Cuidar de você e da família", "Recarregar as energias. O negócio cresce um pouco menos.", 0, "descansar"),
        (f"💡 Inovar o produto ({brl(inov)})", "Melhorar o que você vende. Margem e clientes sobem.", inov, "inovar"),
    ]
    if e["estrutura"] < len(ESTRUTURAS) - 1:
        prox = ESTRUTURAS[e["estrutura"] + 1]
        lista.append((f"🏗️ Mudar para: {prox[0]} ({brl(amp)})",
                      f"Comporta até {prox[1]} funcionários. Aumenta reputação e custo fixo.", amp, "ampliar"))
    return lista


def fazer_acao(e, chave, custo):
    e["caixa"] -= custo
    txt = ""
    if chave == "vender":
        e["mercado"] += e["mercado"] * 0.12 * sat(e) + 600
        mudar(e, saude=-5, rep=+1)
        txt = "Você rodou a cidade oferecendo seu trabalho e fechou novos clientes."
    elif chave == "marketing":
        e["mercado"] += custo * 1.6 * sat(e)
        mudar(e, rep=+2)
        txt = "A campanha viralizou um pouco, e o telefone não parou de tocar."
    elif chave == "estudar":
        mudar(e, conhec=+8, saude=-2, felic=+2)
        txt = "Você estudou finanças, vendas e gestão. Está enxergando coisas que antes passavam batido."
    elif chave == "network":
        e["mercado"] *= 1.03
        mudar(e, rel=+6, rep=+2, saude=-2)
        txt = "Você trocou muitos cartões e fez contatos interessantes."
        if random.random() < 0.55:
            forcar(e, 1, random.choice(["consultor", "mentor", "amor_conhecer", "investidor"]))
            txt += " Alguém em especial ficou com seu contato…"
    elif chave == "descansar":
        e["mercado"] *= 0.96
        mudar(e, saude=+16, felic=+10, rel=+6)
        e["atencao"] = min(100, e.get("atencao", 60) + 35)
        txt = "Você desligou o celular, dormiu bem e jantou com quem ama. Voltou outra pessoa."
    elif chave == "inovar":
        e["bonus_margem"] = min(0.15, e["bonus_margem"] + 0.02)
        e["mercado"] *= 1.06
        mudar(e, conhec=+3, rep=+2)
        txt = "O produto ficou melhor e mais lucrativo. Os clientes perceberam."
    elif chave == "ampliar":
        e["estrutura"] += 1
        mudar(e, rep=+5, felic=+5)
        txt = f"Você mudou para: {ESTRUTURAS[e['estrutura']][0]}! Mais espaço, mais custo, mais respeito."
    log(e, txt)
    return txt


def contratar(e, n):
    custo = n * e["r"]["salario"] * 0.5
    e["caixa"] -= custo
    e["func"] += n
    conquistar(e, "primeiro_func")
    if e["func"] >= 10:
        conquistar(e, "empregos")
    log(e, f"Você contratou {n} pessoa(s). Custo de recrutamento: {brl(custo)}.")


def demitir(e, n):
    custo = n * e["r"]["salario"] * 1.2
    e["caixa"] -= custo
    e["func"] -= n
    mudar(e, rel=-2 * n, felic=-2)
    log(e, f"Você demitiu {n} pessoa(s) e pagou {brl(custo)} de rescisão.")


def pegar_emprestimo(e, valor, taxa=0.035):
    e["taxa"] = (e["divida"] * e["taxa"] + valor * taxa) / (e["divida"] + valor)
    e["divida"] += valor
    e["caixa"] += valor
    e["teve_divida"] = True
    log(e, f"🏦 Empréstimo de {brl(valor)} a {taxa * 100:.1f}% ao mês.")


def amortizar(e, valor):
    valor = min(valor, e["divida"], max(0, e["caixa"]))
    e["caixa"] -= valor
    e["divida"] -= valor
    if e["divida"] < 1:
        e["divida"], e["taxa"] = 0, 0
        if e["teve_divida"]:
            conquistar(e, "sem_divida")
    log(e, f"🏦 Você pagou {brl(valor)} da dívida.")


# ---------------------------------------------------------------- FECHAMENTO DO MÊS
def fechar_mes(e):
    antes = {k: e[k] for k in IND + ["caixa", "divida", "func"]}
    antes["patrimonio"] = patrimonio(e)
    fase_antes = e["fase_max"]
    cap = capacidade(e)
    vendido = min(e["mercado"], cap) * random.uniform(1 - e["r"]["vol"] / 2, 1 + e["r"]["vol"] / 2)
    receita = max(0.0, vendido)
    lucro_bruto = receita * margem(e)
    fixo, salarios = custo_fixo(e), folha(e)
    juros = e["divida"] * e["taxa"]
    vida = (CUSTO_VIDA * e["vida_mult"] * (1 + 0.15 * e["fase_max"]) * (1.25 if "casado" in e["flags"] else 1)
            * (1 + 0.35 * e.get("filhos", 0)))
    lucro_op = lucro_bruto - fixo - salarios
    resultado = lucro_op - juros - vida
    e["caixa"] += resultado
    e["hist_receita"].append(receita)
    e["hist_lucro_op"].append(lucro_op)
    e["hist_resultado"].append(resultado)
    noticias = e["noticias"] = []

    # mercado e desgaste
    if e["mercado"] > cap * 1.3:
        mudar(e, rep=-2, felic=-1)
        noticias.append("😤 Tem mais cliente do que você consegue atender. Gente reclamando da demora: contrate!")
    saturacao = sat(e)
    e["mercado"] = max(300.0, e["mercado"] * (1 + (0.006 + (e["rep"] - 50) / 1200) * saturacao))
    mudar(e, saude=-(3 + (1 if e["func"] == 0 else 0)) + (2 if e["func"] >= 5 else 0))
    if resultado > 0:
        e["seq_lucro"] += 1
        mudar(e, felic=+1)
        conquistar(e, "primeiro_lucro")
        if e["seq_lucro"] >= 6:
            conquistar(e, "sequencia")
    else:
        e["seq_lucro"] = 0
        mudar(e, felic=-2)
    if e["divida"] > receita_media(e) * 6 and e["divida"] > 10000:
        mudar(e, saude=-3, felic=-2)
        noticias.append("😰 A dívida está tirando seu sono.")

    # consequências que chegaram
    vencidos = [p for p in e["pend"] if p["mes"] <= e["mes"]]
    e["pend"] = [p for p in e["pend"] if p["mes"] > e["mes"]]
    for p in vencidos:
        msg = p["fn"](e)
        if msg:
            noticias.append(msg)
            log(e, msg)

    if e["saude"] <= 0:
        e["caixa"] -= 3000
        e["mercado"] *= 0.7
        e["saude"] = 35
        msg = "🚑 Você teve um esgotamento (burnout) e ficou internado(a). Conta do hospital: R$ 3.000, e clientes sumiram."
        noticias.append(msg)
        log(e, msg)

    # caixa negativo → cheque especial ou falência
    if e["caixa"] < 0:
        falta = -e["caixa"] + 500
        if limite_credito(e) >= falta:
            pegar_emprestimo(e, falta, taxa=0.08)
            mudar(e, saude=-3)
            noticias.append(f"⚠️ O caixa ficou negativo e o banco cobriu com cheque especial: {brl(falta)} a 8% ao mês!")
        else:
            e["fim"] = "falencia"

    # fase e conquistas
    f = fase_atual(e)
    if f > e["fase_max"]:
        e["fase_max"] = f
        for i in range(2, f + 1):
            conquistar(e, f"fase{i}")
        log(e, f"🚀 Sua empresa chegou à fase {FASES[f][0]}!")
    if e["caixa"] >= 20000:
        conquistar(e, "colchao")
    if patrimonio(e) >= 1_000_000:
        conquistar(e, "milhao")
    if e["mes"] >= 24 and e["integ"] >= 90:
        conquistar(e, "maos_limpas")
    if e["rel"] >= 90:
        conquistar(e, "familia")
    if e["mes"] >= 60:
        conquistar(e, "sobrevivente")
    vida_afetiva_mes(e, noticias)
    if "traido" in e["flags"] and e["saude"] >= 70:
        conquistar(e, "superacao")
    if min(dimensoes(e).values()) >= 70:
        conquistar(e, "vida_plena")

    e["relatorio"] = dict(mes=e["mes"], receita=receita, lucro_bruto=lucro_bruto, fixo=fixo, salarios=salarios,
                          juros=juros, vida=vida, resultado=resultado, antes=antes, fase_antes=fase_antes,
                          cap=cap, demanda=e["mercado"])
    e["mes"] += 1
    if not e["fim"]:
        e["prox"] = escolher_evento(e)
    e["etapa"] = "fim" if e["fim"] else "relatorio"


# ---------------------------------------------------------------- EVENTOS
EVENTOS = {}


def evento(eid, titulo, teaser, cond=lambda e: True, peso=1.0, unico=False, cooldown=6):
    def reg(fn):
        EVENTOS[eid] = dict(id=eid, titulo=titulo, teaser=teaser, cond=cond, peso=peso, unico=unico,
                            cooldown=cooldown, montar=fn)
        return fn
    return reg


def escolher_evento(e):
    due = [f for f in e["forcados"] if f["mes"] <= e["mes"] and EVENTOS[f["ev"]]["cond"](e)
           and not (EVENTOS[f["ev"]]["unico"] and f["ev"] in e["ja"])]
    if e["saude"] < 30 and "saude_alerta" not in e["usados"][-3:]:
        return "saude_alerta"
    if due:
        e["forcados"].remove(due[0])
        return due[0]["ev"]
    e["forcados"] = [f for f in e["forcados"] if f["mes"] >= e["mes"] - 6]
    cands = []
    for ev in EVENTOS.values():
        if ev["peso"] <= 0 or not ev["cond"](e):
            continue
        if ev["unico"] and ev["id"] in e["ja"]:
            continue
        if ev["id"] in e["usados"][-ev["cooldown"]:]:
            continue
        cands.append(ev)
    if not cands:
        return "mes_tranquilo"
    return random.choices(cands, weights=[c["peso"] for c in cands])[0]["id"]


def montar_evento(e, eid):
    e["usados"].append(eid)
    e["ja"].add(eid)
    texto, opcoes = EVENTOS[eid]["montar"](e)
    return dict(id=eid, titulo=EVENTOS[eid]["titulo"], texto=texto, opcoes=opcoes)


# --- 1. Burocracia
@evento("burocracia", "📄 A papelada chegou", "Um envelope pardo da prefeitura está na sua mesa…",
        cond=lambda e: e["fase_max"] <= 2, peso=1.2, unico=False, cooldown=14)
def _(e):
    custo = 600 + 400 * e["fase_max"]

    def desp(e):
        mudar(e, caixa=-custo, saude=+2)
        return f"O despachante resolveu tudo em uma semana. Custou {brl(custo)}, mas você dormiu tranquilo."

    def sozinho(e):
        mudar(e, saude=-8, conhec=+5)
        if random.random() < 0.4:
            multa = custo * 2

            def cobra(e):
                mudar(e, caixa=-multa, rep=-3)
                return f"📄 Um erro na papelada que você fez sozinho virou multa de {brl(multa)}."
            agendar(e, 2, cobra)
        return "Você perdeu noites em filas e sites do governo, mas aprendeu como a burocracia funciona."
    return ("Alvará, licença, inscrição municipal… uma pilha de documentos com prazo curto. Errar pode custar caro.",
            [(f"🧾 Contratar despachante (−{brl(custo)})", desp), ("💪 Resolver sozinho", sozinho)])


# --- 2. Falta de dinheiro
@evento("sem_caixa", "💸 O dinheiro está acabando", "Você abriu o app do banco e prendeu a respiração…",
        cond=lambda e: e["caixa"] < CUSTO_VIDA * 2, peso=3, cooldown=4)
def _(e):
    valor = round(max(8000, receita_media(e) * 2), -3)

    def banco(e):
        pegar_emprestimo(e, valor, 0.04)
        return f"O gerente liberou {brl(valor)} a 4% ao mês. Fôlego agora, conta depois."

    def socio(e):
        e["seguinte"] = "socio_proposta"
        return "Você espalhou que procura um sócio. No dia seguinte, alguém ligou…"

    def cinto(e):
        e["vida_mult"] = 0.6
        mudar(e, felic=-10, rel=-5, integ=+2)

        def volta(e):
            e["vida_mult"] = 1.0
            return "🍽️ O aperto de cinto acabou. Dá para voltar a viver um pouco."
        agendar(e, 3, volta)
        return "Sem restaurante, sem lazer, arroz e ovo por 3 meses. Dói, mas sem juros."
    return (f"O caixa está em {brl(e['caixa'])}. As contas do mês que vem não fecham. O que fazer?",
            [(f"🏦 Pegar empréstimo de {brl(valor)} (4% a.m.)", banco), ("🤝 Procurar um sócio", socio),
             ("✂️ Cortar gastos pessoais por 3 meses", cinto)])


# --- 3. Concorrência
@evento("concorrencia", "🏪 Abriu um concorrente na esquina", "Tem uma faixa de 'INAUGURAÇÃO' do outro lado da rua…",
        cond=lambda e: e["mes"] > 3, peso=1, cooldown=12)
def _(e):
    custo = round(1500 + receita_media(e) * 0.3, -2)

    def preco(e):
        e["mercado"] *= 1.12
        e["bonus_margem"] -= 0.05

        def volta(e):
            e["bonus_margem"] += 0.05
            return "🏷️ A guerra de preços esfriou e você voltou a cobrar o preço normal."
        agendar(e, 6, volta)
        return "Você baixou o preço. Segurou os clientes, mas está trabalhando mais para ganhar menos."

    def inovar(e):
        e["caixa"] -= custo
        if random.random() < 0.45 + e["conhec"] / 200:
            e["mercado"] *= 1.3
            e["bonus_margem"] = min(0.15, e["bonus_margem"] + 0.03)
            mudar(e, rep=+5)
            return "Sua novidade virou assunto na cidade! O concorrente é que ficou preocupado."
        mudar(e, conhec=+5)
        return "A inovação não pegou. Você gastou, mas aprendeu o que o cliente NÃO quer."

    def ignorar(e):
        e["mercado"] *= 0.88
        return "Você fingiu que não viu. Alguns clientes foram experimentar o concorrente."
    return ("Um concorrente bem financiado abriu perto de você com preços agressivos.",
            [("🏷️ Baixar o preço", preco), (f"💡 Inovar e se diferenciar (−{brl(custo)})", inovar),
             ("🙈 Ignorar", ignorar)])


# --- 4. Cliente inadimplente
@evento("inadimplente", "🧾 O cliente não pagou", "Um cliente grande parou de responder suas mensagens…",
        cond=lambda e: receita_media(e) > 2500, peso=1, cooldown=10)
def _(e):
    v = round(receita_media(e) * 0.6, -2)

    def negociar(e):
        e["caixa"] += v * 0.6
        return f"Você aceitou receber {brl(v * 0.6)} à vista. Não é tudo, mas está no bolso."

    def justica(e):
        e["caixa"] -= 600
        adv = pessoa(e, "advogado")
        chance = 0.55 + (0.3 if adv["bom"] else 0)

        def sentenca(e):
            if random.random() < chance:
                e["caixa"] += v * 1.1
                return f"⚖️ Você ganhou o processo contra o cliente caloteiro! Entraram {brl(v * 1.1)} com correção."
            return "⚖️ Você perdeu o processo do cliente caloteiro. O dinheiro não volta."
        agendar(e, 4, sentenca)
        return f"{adv['nome']}, advogad{oa(adv)}, entrou com a ação. Resultado em uns 4 meses."

    def esquecer(e):
        mudar(e, felic=-4, rel=+2)
        return "Você deixou para lá. Raiva engolida, mas sem perder mais tempo."
    return (f"Um cliente deve {brl(v)} e sumiu.",
            [(f"🤝 Negociar e receber 60% agora", negociar), ("⚖️ Entrar na Justiça (−R$ 600)", justica),
             ("🕊️ Deixar para lá", esquecer)])


# --- 5. Funcionário desonesto
@evento("func_desonesto", "🕳️ Sumiu dinheiro do caixa", "Os números do caixa não estão batendo…",
        cond=lambda e: e["func"] >= 1, peso=1, cooldown=12)
def _(e):
    culpado = random.random() < 0.55
    perda = round(max(800, receita_media(e) * 0.4), -2)

    def investigar_f(e):
        e["caixa"] -= 500
        if culpado:
            e["func"] -= 1
            mudar(e, rep=+2, integ=+3)
            conquistar(e, "detetive")
            return "As câmeras mostraram tudo. Você demitiu o funcionário por justa causa. A equipe respeitou."
        mudar(e, rel=+4)
        e["mercado"] *= 1.04
        return "Era um erro do sistema de pagamento! O funcionário ficou grato por você não ter acusado sem provas."

    def confiar(e):
        if culpado:
            def rombo(e):
                e["caixa"] -= perda * 2
                mudar(e, felic=-6)
                conquistar(e, "licao")
                return f"🕳️ O desvio continuou e virou um rombo de {brl(perda * 2)}. Confiança sem verificação custa caro."
            agendar(e, 2, rombo)
            return "Você decidiu confiar na equipe e não fez nada."
        mudar(e, rel=+3)
        return "Você confiou, e estava certo: era um erro de troco. A equipe gosta de trabalhar com você."

    def demitir_f(e):
        e["func"] -= 1
        mudar(e, integ=-8, rep=-4)
        if not culpado:
            def processo(e):
                e["caixa"] -= e["r"]["salario"] * 3
                mudar(e, rep=-4)
                return f"⚖️ O funcionário demitido sem provas era inocente e te processou: {brl(e['r']['salario'] * 3)}."
            agendar(e, 3, processo)
        return "Você demitiu o principal suspeito sem provas. O clima na equipe ficou pesado."
    return (f"Faltam {brl(perda)} no caixa e há um funcionário suspeito.",
            [("🔎 Investigar com câmeras e auditoria (−R$ 500)", investigar_f), ("🙏 Confiar na equipe", confiar),
             ("🚪 Demitir o suspeito na hora", demitir_f)])


# --- 6. Impostos
@evento("impostos", "🏛️ Impostos atrasados", "Uma carta da Receita Federal com letras vermelhas…",
        cond=lambda e: receita_media(e) > 3000, peso=1, cooldown=12)
def _(e):
    v = round(receita_media(e) * 0.4, -2)

    def parcelar(e):
        e["divida"] += v
        e["taxa"] = (e["taxa"] * (e["divida"] - v) + v * 0.015) / e["divida"]
        e["teve_divida"] = True
        return f"Você parcelou {brl(v)} com juros baixos (1,5% a.m.). Dívida organizada."

    def pagar(e):
        e["caixa"] -= v
        mudar(e, rep=+2, integ=+3)
        return f"Pago à vista: {brl(v)}. Nome limpo e consciência tranquila."

    def arriscar(e):
        mudar(e, integ=-6)
        e["flags"].add("sonegou")
        if random.random() < 0.45:
            def multa(e):
                e["caixa"] -= v * 2
                mudar(e, rep=-8)
                return f"🏛️ A Receita voltou com multa e juros: {brl(v * 2)}. E a notícia se espalhou."
            agendar(e, 3, multa)
        return "Você deixou para depois e torceu para ninguém lembrar…"
    return (f"Você tem {brl(v)} de impostos em atraso.",
            [("📑 Parcelar", parcelar), (f"💳 Pagar à vista (−{brl(v)})", pagar), ("🎲 Deixar quieto e arriscar", arriscar)])


# --- 7. Grande oportunidade
@evento("oportunidade", "🎯 Uma oportunidade de ouro?", "Um fornecedor ligou com uma proposta 'imperdível'…",
        cond=lambda e: e["mes"] > 2, peso=1.2, cooldown=6)
def _(e):
    v = round(max(2000, receita_media(e) * 1.5), -2)
    chance = min(0.85, 0.45 + e["conhec"] / 250)

    def investir(e):
        e["caixa"] -= v
        sucesso = random.random() < chance

        def retorno(e):
            if sucesso:
                e["caixa"] += v * 2.6
                mudar(e, rep=+3, felic=+5)
                return f"🎯 A aposta deu certo! Retorno de {brl(v * 2.6)}."
            e["caixa"] += v * 0.3
            mudar(e, felic=-5)
            return f"🎯 A 'oportunidade de ouro' micou. Você recuperou só {brl(v * 0.3)}."
        agendar(e, 3, retorno)
        return f"Você investiu {brl(v)}. O resultado sai em 3 meses. (Pelo seu conhecimento, a chance parece de {chance:.0%}.)"

    def preservar(e):
        mudar(e, saude=+2)
        return "Você preservou o caixa. Talvez tenha perdido algo, talvez tenha se livrado de uma furada."
    return (f"Um lote de mercadoria/serviço com potencial de quase triplicar em 3 meses. Precisa de {brl(v)} agora.",
            [(f"💰 Investir {brl(v)}", investir), ("🛡️ Preservar o caixa", preservar)])


# --- 8. Sócio
@evento("socio_proposta", "🤝 Proposta de sociedade", "Alguém de terno pediu uma reunião 'urgente e confidencial'…",
        cond=lambda e: e["socio"] is None, peso=0.8, cooldown=18)
def _(e):
    p = pessoa(e, "socio")
    v = round(max(3000, e["caixa"] * 0.6), -2)
    e["socio_valor"] = v
    fala = random.choice([
        "Tenho contatos importantes e consigo dobrar seu faturamento em seis meses. Só preciso que você entre com o capital.",
        "Seu negócio tem potencial, mas falta gente grande. Eu trago os clientes, você entra com o dinheiro.",
        "Eu já fiz isso antes. Juntos a gente cresce rápido, mas tem que decidir logo, tenho outros interessados."])

    def inv(e):
        e["caixa"] -= 300
        pista = investigar(e, p)
        e["seguinte"] = "socio_decisao"
        return f"🔎 Você pesquisou sobre {p['nome']}: \"{pista}\""

    def adv(e):
        e["caixa"] -= 1200
        a = pessoa(e, "advogado")
        e["seguinte"] = "socio_decisao"
        if not p["bom"]:
            p["pistas"].append(f"O contrato de {p['nome']} deixava TODAS as dívidas no seu nome.")
            return f"⚖️ {a['nome']} leu o contrato e ficou pálid{oa(a)}: as dívidas ficariam só com você!"
        p["pistas"].append(f"O contrato proposto por {p['nome']} é justo e equilibrado.")
        return f"⚖️ {a['nome']} analisou: contrato equilibrado, sem pegadinhas."
    return (f"**{p['nome']}, {p['idade']} anos**, quer ser seu sócio. *\"{fala}\"* Quer {brl(v)} seus.",
            [("🔎 Investigar o histórico (−R$ 300)", inv), ("⚖️ Advogado analisa a proposta (−R$ 1.200)", adv)]
            + _opcoes_socio(e, p, v))


def _opcoes_socio(e, p, v):
    def aceitar(e):
        e["caixa"] -= v
        e["socio"] = p["id"]
        e["part"] *= 0.75
        log(e, f"Você virou sócio(a) de {p['nome']} com {brl(v)}.", p["id"])
        if p["bom"]:
            def contatos(e):
                e["mercado"] *= 1.4
                mudar(e, rep=+5, rel=+3)
                revelar(e, p)
                return f"🤝 Os contatos de {p['nome']} trouxeram clientes grandes! Mercado +40%."
            agendar(e, 2, contatos)
            agendar(e, 6, contatos)
        else:
            p["bomba"] = e["mes"] + 5
            forcar(e, 2, "segredo_socio")

            def fuga(e):
                if e["socio"] != p["id"]:
                    return None
                perda = v * 0.5
                e["caixa"] -= perda
                e["divida"] += v
                e["taxa"] = max(e["taxa"], 0.03)
                e["socio"] = None
                e["part"] = min(1.0, e["part"] / 0.75)
                p["ativo"] = False
                revelar(e, p)
                mudar(e, rep=-6, felic=-12, saude=-8)
                conquistar(e, "licao")
                return f"🚨 {p['nome']} SUMIU! Sacou {brl(perda)} da conta da empresa e deixou {brl(v)} em dívidas no seu nome."
            agendar(e, 5, fuga)
        return f"Vocês apertaram as mãos. {p['nome']} agora é sócio(a) com 25% da empresa."

    def recusar(e):
        if not p["bom"]:
            def soube(e):
                revelar(e, p)
                p["ativo"] = False
                conquistar(e, "detetive")
                return f"📰 Você soube que {p['nome']} aplicou um golpe em outro empresário. Escapou por pouco!"
            agendar(e, 3, soube)
        else:
            def foi(e):
                mudar(e, felic=-2)
                return f"📰 {p['nome']} se associou a outra empresa, que está crescendo rápido. Será que você perdeu uma chance?"
            agendar(e, 4, foi)
        return f"Você agradeceu e recusou. {p['nome']} saiu meio contrariad{oa(p)}."
    return [(f"✅ Aceitar e investir {brl(v)}", aceitar), ("❌ Recusar", recusar)]


@evento("socio_decisao", "🤝 Hora de decidir sobre a sociedade", "", peso=0, cooldown=0)
def _(e):
    p = pessoa(e, "socio")
    return (f"Com o que você descobriu, vai entrar na sociedade com {p['nome']}?",
            _opcoes_socio(e, p, e.get("socio_valor", 3000)))


@evento("segredo_socio", "🤫 Um segredo sobre seu sócio", "Uma ex-funcionária do seu sócio quer falar com você…",
        cond=lambda e: e["socio"] is not None, peso=0.4, cooldown=12)
def _(e):
    p = e["pessoas"][e["socio"]]
    real = (not p["bom"]) == (random.random() < 0.8)

    def inv(e):
        e["caixa"] -= 800
        if not p["bom"]:
            e["seguinte"] = "desfazer_sociedade"
            conquistar(e, "detetive")
            return f"🔎 Auditoria confirmou: {p['nome']} estava desviando dinheiro aos poucos e planejava sumir!"
        return f"🔎 A auditoria não encontrou nada. {p['nome']} está limp{oa(p)}. Era fofoca."

    def confrontar(e):
        if not p["bom"]:
            if random.random() < 0.5:
                e["seguinte"] = "desfazer_sociedade"
                return f"{p['nome']} gaguejou, ficou vermelh{oa(p)}… e acabou admitindo que estava com problemas."
            p["bomba"] = e["mes"]
            return f"{p['nome']} jurou inocência, ofendid{oa(p)}. Mas ficou estranh{oa(p)} desde então…"
        mudar(e, rel=-3)
        return f"{p['nome']} ficou magoad{oa(p)} com a desconfiança, mas mostrou todos os extratos."

    def ignorar(e):
        return "Você preferiu acreditar no seu sócio e não tocou mais no assunto."
    boato = "está escondendo dívidas e já fez isso com outros sócios" if real or random.random() < .5 else "tem um passado complicado"
    return (f"Uma pessoa que trabalhou com **{p['nome']}** diz que ele(a) {boato}. Pode ser verdade… ou inveja.",
            [("🔎 Contratar auditoria (−R$ 800)", inv), ("🗣️ Confrontar cara a cara", confrontar), ("🙈 Ignorar", ignorar)])


@evento("desfazer_sociedade", "✂️ Desfazer a sociedade", "", peso=0, cooldown=0)
def _(e):
    p = e["pessoas"][e["socio"]]
    v = e.get("socio_valor", 3000)

    def sair(e):
        e["caixa"] += v * 0.5
        e["socio"] = None
        e["part"] = min(1.0, e["part"] / 0.75)
        p["ativo"] = False
        revelar(e, p)
        mudar(e, felic=+5, integ=+2)
        return f"Com provas na mão, você desfez a sociedade e recuperou {brl(v * 0.5)}. Ufa!"
    return (f"Você tem provas contra {p['nome']}. Vai desfazer a sociedade agora?",
            [("✂️ Desfazer e recuperar parte do dinheiro", sair)])


# --- 9. Amigo pede dinheiro
@evento("amigo_dinheiro", "🫂 Um amigo precisa de ajuda", "Seu celular toca. É um amigo antigo, com a voz embargada…",
        cond=lambda e: e["caixa"] > 2500, peso=1, cooldown=10)
def _(e):
    p = pessoa(e, "amigo")
    v = round(random.uniform(0.15, 0.35) * max(e["caixa"], 4000), -2)
    motivo = random.choice(["o aluguel atrasado", "uma cirurgia da mãe", "uma dívida que apertou", "pagar a faculdade do filho"])

    def emprestar(e, fr=1.0):
        val = v * fr
        e["caixa"] -= val
        if p["bom"]:
            e["flags"].add("ajudou_amigo")

            def paga(e):
                e["caixa"] += val * 1.1
                mudar(e, rel=+6, felic=+4)
                revelar(e, p)
                forcar(e, 4, "retribuicao")
                return f"🫂 {p['nome']} devolveu os {brl(val)} com um extra e um abraço apertado. Amizade de verdade."
            agendar(e, 4, paga)
        else:
            def some(e):
                revelar(e, p)
                mudar(e, rel=-6, felic=-6)
                conquistar(e, "licao")
                return f"📵 {p['nome']} não pagou, te bloqueou e foi visto(a) postando foto em viagem."
            agendar(e, 4, some)
        mudar(e, rel=+3, integ=+2)
        return f"Você emprestou {brl(val)} para {p['nome']}. Prometeu pagar em 4 meses."

    def recusar(e):
        if p["bom"]:
            mudar(e, rel=-3)
            return f"{p['nome']} entendeu, mas ficou chatead{oa(p)}."
        revelar(e, p)
        mudar(e, rep=-2, rel=-2)
        return f"{p['nome']} ficou furios{oa(p)} e começou a falar mal de você pela cidade. Mostrou quem era."
    return (f"**{p['nome']}** pede {brl(v)} emprestado para {motivo}. Promete devolver em 4 meses.",
            [(f"💵 Emprestar {brl(v)}", emprestar), (f"🤏 Emprestar metade", lambda e: emprestar(e, 0.5)),
             ("🙅 Recusar com jeito", recusar)])


@evento("retribuicao", "🌟 Quem planta, colhe", "Aquele amigo que você ajudou quer te apresentar alguém…",
        cond=lambda e: "ajudou_amigo" in e["flags"], peso=0, unico=True, cooldown=0)
def _(e):
    p = pessoa(e, "amigo")

    def aceitar(e):
        e["mercado"] *= 1.35
        mudar(e, rep=+5, rel=+5, felic=+5)
        return f"O cliente indicado por {p['nome']} fechou um contrato enorme! Mercado +35%."
    return (f"**{p['nome']}** não esqueceu sua ajuda e te indicou para o diretor de uma empresa grande.",
            [("🙏 Agradecer e aproveitar", aceitar)])


# --- 10. Amigo novo do sucesso
@evento("falso_amigo", "🥂 Os novos amigos do sucesso", "Você foi convidado para uma festa VIP numa cobertura…",
        cond=lambda e: e["fase_max"] >= 2, peso=1, unico=True)
def _(e):
    p = pessoa(e, "novo_amigo")
    v = round(max(5000, e["caixa"] * 0.3), -3)

    def investir(e):
        e["caixa"] -= v
        if p["bom"]:
            def ganha(e):
                e["caixa"] += v * 1.4
                return f"📈 O investimento indicado por {p['nome']} rendeu 40%. Nem todo mundo é golpista!"
            agendar(e, 4, ganha)
        else:
            def golpe(e):
                revelar(e, p)
                p["ativo"] = False
                mudar(e, felic=-8)
                conquistar(e, "licao")
                return f"📉 A 'cripto garantida' de {p['nome']} era pirâmide. Os {brl(v)} viraram pó, e {ele(p)} sumiu."
            agendar(e, 3, golpe)
        return f"Você colocou {brl(v)} no negócio de {p['nome']}."

    def recusar(e):
        if not p["bom"]:
            def soube(e):
                revelar(e, p)
                conquistar(e, "detetive")
                return f"📰 Saiu no jornal: o 'negócio garantido' de {p['nome']} era pirâmide financeira. Escapou!"
            agendar(e, 3, soube)
        mudar(e, saude=+2)
        return f"Você recusou com elegância. {p['nome']} continuou simpátic{oa(p)}… por enquanto."
    return (f"Na festa, **{p['nome']}** (que você nunca tinha visto até ficar bem de vida) jura que tem um investimento "
            f"em cripto que 'rende 10% ao mês, garantido'. Sugere você colocar {brl(v)}.",
            [(f"💸 Investir {brl(v)}", investir), ("🙅 Recusar", recusar)])


# --- 11–13. Amor
@evento("amor_conhecer", "💘 Um encontro inesperado", "Alguém sorriu para você no evento de ontem…",
        cond=lambda e: e["parceiro"] is None and "casado" not in e["flags"], peso=0.5, cooldown=18)
def _(e):
    p = pessoa(e, "amor")

    def sair(e):
        iniciar_namoro(e, p)
        forcar(e, 3, "amor_pedido")
        return f"Vocês saíram, riram a noite inteira… Começou um namoro com {p['nome']}! 💕"

    def foco(e):
        mudar(e, felic=-3)
        return "Você disse que agora o foco é a empresa. Será que perdeu alguém especial?"
    return (f"No evento, você conheceu **{p['nome']}, {p['idade']} anos**. Inteligente, engraçad{oa(p)}, "
            f"e parece muito interessad{oa(p)} em você… e no que você faz.",
            [("💌 Chamar para sair", sair), ("💼 Focar no trabalho", foco)])


@evento("amor_pedido", "💔 Uma conversa séria no jantar", "Seu amor quer conversar sobre 'o futuro de vocês'…",
        cond=lambda e: e["parceiro"] is not None, peso=0, cooldown=0)
def _(e):
    p = e["pessoas"][e["parceiro"]]
    v = round(max(4000, e["caixa"] * 0.35), -3)

    def dar(e):
        e["caixa"] -= v
        if p["bom"]:
            def ok(e):
                e["caixa"] += v
                mudar(e, felic=+8, rel=+5)
                revelar(e, p)
                forcar(e, 1, "casamento")
                return f"🌷 A loja de {p['nome']} deu certo, e {ele(p)} devolveu cada centavo. Que orgulho!"
            agendar(e, 5, ok)
        else:
            def fim(e):
                e["parceiro"] = None
                p["ativo"] = False
                revelar(e, p)
                mudar(e, felic=-15, saude=-10)
                conquistar(e, "licao")
                return f"💔 A 'loja' de {p['nome']} nunca existiu. Quando o dinheiro acabou, o amor também."
            agendar(e, 3, fim)
        mudar(e, felic=+5)
        return f"Você transferiu {brl(v)}. {p['nome']} te abraçou forte."

    def recusar(e):
        if p["bom"]:
            mudar(e, rel=+5, felic=+3)
            revelar(e, p)
            forcar(e, 2, "casamento")
            return f"{p['nome']} disse: 'Você tem razão, vou juntar aos poucos.' Vocês ficaram ainda mais próximos."
        e["parceiro"] = None
        p["ativo"] = False
        revelar(e, p)
        conquistar(e, "detetive")
        mudar(e, felic=-8)
        return f"{p['nome']} ficou fri{oa(p)}, sumiu por uma semana e terminou por mensagem. Doeu… mas foi melhor assim."

    def plano(e):
        mudar(e, saude=-3)
        if p["bom"]:
            mudar(e, rel=+8, conhec=+3)
            forcar(e, 2, "casamento")
            return f"Vocês montaram o plano juntos. {p['nome']} adorou sua ajuda: 'Você é a melhor coisa da minha vida.'"
        p["pistas"].append(f"{p['nome']} se irritou quando você pediu um plano de negócios.")
        forcar(e, 2, "amor_pedido")
        return f"{p['nome']} se irritou: 'Pra que tanta pergunta? Você não confia em mim?' Hmm…"
    return (f"**{p['nome']}** diz que quer abrir uma lojinha e pede {brl(v)} emprestado. *\"A gente é um time, né?\"*",
            [(f"💝 Dar o dinheiro", dar), ("🙅 Recusar com carinho", recusar),
             ("📝 Propor fazer um plano de negócios juntos", plano)])


@evento("casamento", "💍 O pedido!", "Você está com uma caixinha de veludo no bolso…",
        cond=lambda e: e["parceiro"] is not None and "casado" not in e["flags"], peso=0, cooldown=0)
def _(e):
    p = e["pessoas"][e["parceiro"]]

    def casar(e, separacao):
        e["flags"].add("casado")
        e["regime"] = "separacao" if separacao else "comunhao"
        e["atencao"] = min(100, e.get("atencao", 60) + 25)
        mudar(e, felic=+15, rel=+10, saude=+5)
        if p["bom"]:
            conquistar(e, "amor")
            return f"💍 Vocês se casaram! {p['nome']} é sua parceira de vida de verdade." if p["sexo"] == "F" else \
                   f"💍 Vocês se casaram! {p['nome']} é seu parceiro de vida de verdade."
        if not separacao:
            def divorcio(e):
                if e["parceiro"] != p["id"]:
                    return None
                perda = max(0, e["caixa"]) * 0.5
                e["caixa"] -= perda
                e["parceiro"] = None
                p["ativo"] = False
                e["flags"].discard("casado")
                revelar(e, p)
                mudar(e, felic=-20, saude=-15)
                return f"💔 {p['nome']} pediu o divórcio e levou {brl(perda)} na partilha. O interesse era o dinheiro."
            agendar(e, 6, divorcio)
        else:
            def sai(e):
                if e["parceiro"] != p["id"]:
                    return None
                e["parceiro"] = None
                p["ativo"] = False
                e["flags"].discard("casado")
                revelar(e, p)
                mudar(e, felic=-12)
                return f"💔 {p['nome']} pediu o divórcio, mas a separação de bens protegeu seu patrimônio."
            agendar(e, 6, sai)
        return f"💍 Vocês se casaram numa festa linda com {p['nome']}!"

    def esperar(e):
        mudar(e, felic=-2)
        return "Você guardou a caixinha. Ainda não é a hora."
    return (f"Depois de tudo, você pensa em pedir **{p['nome']}** em casamento. Seu advogado lembra: o regime de bens importa.",
            [("💍 Casar (comunhão parcial de bens)", lambda e: casar(e, False)),
             ("💍 Casar (separação total de bens)", lambda e: casar(e, True)), ("⏳ Esperar mais", esperar)])


# --- 14. Consultor
@evento("consultor", "📊 Um consultor bate à porta", "Recebeu um e-mail: 'Posso triplicar sua margem'…",
        cond=lambda e: e["mes"] > 4, peso=0.8, cooldown=14)
def _(e):
    p = pessoa(e, "consultor")
    v = round(1500 + receita_media(e) * 0.5, -2)

    def contratar_c(e):
        e["caixa"] -= v
        if p["bom"]:
            e["bonus_margem"] = min(0.15, e["bonus_margem"] + 0.04)
            e["mercado"] *= 1.15
            mudar(e, conhec=+10)
            revelar(e, p)
            return f"{p['nome']} reorganizou preços e processos. Margem +4%, clientes +15%. Valeu cada centavo!"
        mudar(e, conhec=+2)
        p["pistas"].append(f"O relatório de {p['nome']} parecia copiado da internet.")
        return f"{p['nome']} entregou 80 slides bonitos… e nenhuma ação prática."

    def inv(e):
        pista = investigar(e, p)
        e["seguinte"] = "consultor_decisao"
        return f"🔎 Você ligou para ex-clientes: \"{pista}\""
    e["consultor_v"] = v
    return (f"**{p['nome']}** oferece uma consultoria completa por {brl(v)}.",
            [(f"✅ Contratar (−{brl(v)})", contratar_c), ("🔎 Ligar para ex-clientes primeiro", inv),
             ("❌ Recusar", lambda e: "Você agradeceu e seguiu do seu jeito.")])


@evento("consultor_decisao", "📊 E a consultoria?", "", peso=0, cooldown=0)
def _(e):
    texto, opc = EVENTOS["consultor"]["montar"](e)
    return ("Agora que você sabe mais, contrata a consultoria?", [opc[0], opc[2]])


# --- 15. Investidor
@evento("investidor", "💼 Um investidor quer entrar", "Um fundo de investimento pediu seus números…",
        cond=lambda e: receita_media(e) > 8000 and e["part"] > 0.5, peso=0.8, cooldown=14)
def _(e):
    p = pessoa(e, "investidor")
    oferta = round(receita_media(e) * 10, -3)

    def aceitar(e, fatia=0.25):
        e["caixa"] += oferta
        e["part"] *= (1 - fatia)
        if p["bom"]:
            def rede(e):
                e["mercado"] *= 1.25
                mudar(e, rep=+5, conhec=+5)
                revelar(e, p)
                return f"💼 A rede de contatos de {p['nome']} abriu portas enormes. Mercado +25%."
            agendar(e, 3, rede)
        else:
            def pressao(e):
                revelar(e, p)
                mudar(e, felic=-10, saude=-8, rel=-5)
                e["mercado"] *= 0.9
                return f"💼 {p['nome']} exige cortes, demissões e metas absurdas. Você virou funcionário(a) da própria empresa."
            agendar(e, 4, pressao)
        return f"Entraram {brl(oferta)} no caixa. {p['nome']} agora tem {fatia:.0%} da empresa."

    def negociar(e):
        if random.random() < 0.5:
            return aceitar(e, 0.18)
        p["ativo"] = False
        return f"{p['nome']} achou sua contraproposta ousada demais e desistiu."
    return (f"**{p['nome']}** oferece {brl(oferta)} por 25% da sua empresa.",
            [("🤝 Aceitar", aceitar), ("🗣️ Negociar por 18%", negociar), ("❌ Recusar", lambda e: "Você preferiu crescer com as próprias pernas.")])


# --- 16. Concorrente desleal
@evento("concorrente", "🦈 Jogo sujo do concorrente", "Seu celular vibra sem parar: avaliações de 1 estrela…",
        cond=lambda e: e["mes"] > 5, peso=0.8, cooldown=12)
def _(e):
    p = pessoa(e, "concorrente")

    def transparencia(e):
        mudar(e, saude=-3, rep=+3 if e["integ"] >= 60 else 0, integ=+2)
        return "Você respondeu cada avaliação com educação e provas. Muitos clientes te defenderam."

    def falsas(e):
        mudar(e, integ=-15)
        e["mercado"] *= 1.1
        if random.random() < 0.35:
            def descoberta(e):
                mudar(e, rep=-20)
                e["mercado"] *= 0.8
                return "📰 Descobriram que você comprou avaliações falsas. Virou meme na cidade. Reputação despencou."
            agendar(e, 2, descoberta)
        return "Você comprou 200 avaliações 5 estrelas. Funcionou… por enquanto."

    def processar(e):
        e["caixa"] -= 2000
        if random.random() < (0.7 if not p["bom"] else 0.3):
            def ganha(e):
                e["caixa"] += 6000
                mudar(e, rep=+6)
                revelar(e, p)
                return f"⚖️ A Justiça provou que {p['nome']} estava por trás dos ataques. Indenização de R$ 6.000!"
            agendar(e, 3, ganha)
        return "Seu advogado entrou com uma ação por concorrência desleal."
    return (f"Alguém está espalhando avaliações falsas sobre você. Tudo indica que é **{p['nome']}**, seu concorrente.",
            [("🧾 Responder com transparência", transparencia), ("🤫 Comprar avaliações falsas também", falsas),
             ("⚖️ Processar (−R$ 2.000)", processar)])


# --- 17. Fiscalização
@evento("fiscalizacao", "👮 Fiscalização surpresa!", "Dois fiscais estão na porta pedindo para entrar…",
        cond=lambda e: e["mes"] > 6, peso=0.8, cooldown=14)
def _(e):
    sujo = "sonegou" in e["flags"] or e["integ"] < 50
    multa = round(max(2000, receita_media(e) * 0.8), -2)

    def docs(e):
        if sujo:
            e["caixa"] -= multa
            mudar(e, rep=-5)
            e["flags"].discard("sonegou")
            return f"Encontraram irregularidades. Multa de {brl(multa)}. Pelo menos agora está tudo regularizado."
        mudar(e, rep=+3, integ=+2)
        return "Tudo em ordem! Os fiscais até elogiaram sua organização."

    def jeitinho(e):
        mudar(e, integ=-25)
        e["caixa"] -= multa * 0.3
        if random.random() < 0.3:
            def escandalo(e):
                e["caixa"] -= multa * 3
                mudar(e, rep=-25)
                e["mercado"] *= 0.75
                return f"🚨 ESCÂNDALO! O fiscal foi preso e entregou quem pagou propina. Multa de {brl(multa * 3)} e sua imagem destruída."
            agendar(e, 2, escandalo)
        return f"Você 'deu um jeitinho' de {brl(multa * 0.3)}. Os fiscais foram embora sorrindo."
    return ("Os fiscais querem ver notas, alvarás e a contabilidade.",
            [("📂 Apresentar todos os documentos", docs), (f"🤝 'Dar um jeitinho' (propina)", jeitinho)])


# --- 18. Crise econômica
@evento("crise", "📉 Crise econômica!", "O noticiário só fala em juros altos e desemprego…",
        cond=lambda e: e["mes"] > 10, peso=0.5, cooldown=24)
def _(e):
    e["mercado"] *= 0.75

    def demitir_c(e):
        if e["func"] > 0:
            demitir(e, max(1, e["func"] // 3))
        mudar(e, integ=-3)
        return "Você cortou parte da equipe. Doeu, mas a empresa respira."

    def manter(e):
        e["vida_mult"] = 0.7
        mudar(e, felic=-6, rep=+6, rel=+4, integ=+4)

        def volta(e):
            e["vida_mult"] = 1.0
            e["mercado"] *= 1.15
            return "🌤️ A crise passou. Sua equipe, que você protegeu, está mais leal do que nunca."
        agendar(e, 4, volta)
        return "Você cortou o próprio salário para não demitir ninguém. A equipe nunca vai esquecer."

    def diversificar(e):
        custo = round(1000 + receita_media(e) * 0.3, -2)
        e["caixa"] -= custo
        if random.random() < 0.4 + e["conhec"] / 200:
            e["mercado"] *= 1.3
            return "Você encontrou um nicho que cresce na crise! Mercado se recuperou."
        return f"A diversificação custou {brl(custo)} e não decolou."
    return ("A economia afundou. Seus clientes estão comprando 25% menos.",
            [("✂️ Demitir parte da equipe", demitir_c), ("🛡️ Manter todos e cortar seu salário", manter),
             ("🧭 Diversificar para um novo nicho", diversificar)])


# --- 19. Golpe do Pix
@evento("golpe_pix", "📱 Mensagem urgente", "Chegou um áudio do 'seu fornecedor' com tom desesperado…",
        cond=lambda e: e["mes"] > 2, peso=0.7, unico=True)
def _(e):
    v = round(max(1500, receita_media(e) * 0.5), -2)

    def ligar(e):
        conquistar(e, "detetive")
        mudar(e, conhec=+5)
        return "Você ligou no número antigo do fornecedor: ele nunca mandou essa mensagem. Era golpe!"

    def pagar(e):
        e["caixa"] -= v
        mudar(e, felic=-5, conhec=+5)
        conquistar(e, "licao")
        return f"Você mandou {brl(v)}. Duas horas depois, o fornecedor de verdade ligou perguntando do pagamento… Era golpe."
    return (f"Seu 'fornecedor' manda mensagem de um número novo: 'Mudei de banco, paga os {brl(v)} nessa chave Pix nova, "
            "é urgente senão perco o desconto!'", [("📞 Ligar para o número antigo e confirmar", ligar), ("💸 Pagar logo", pagar)])


# --- 20. Mentor
@evento("mentor", "🧓 Um mentor aparece", "Um empresário famoso comentou no seu post…",
        cond=lambda e: e["conhec"] < 85, peso=0.6, cooldown=18)
def _(e):
    p = pessoa(e, "mentor")

    def aceitar(e):
        if p["bom"]:
            mudar(e, conhec=+15, rep=+4, saude=-3)
            revelar(e, p)
            return f"{p['nome']} te ensinou em um mês o que levaria anos. Conhecimento +15."
        mudar(e, conhec=+5, saude=-6, felic=-3)
        p["pistas"].append(f"{p['nome']} cobrou favores pessoais em troca dos conselhos.")
        return f"{p['nome']} ensinou umas coisas, mas cobrou favores e usou seu nome para se promover."
    return (f"**{p['nome']}**, dono(a) de um grupo de empresas, oferece mentoria gratuita em troca de você ajudar num projeto social.",
            [("🙏 Aceitar", aceitar), ("❌ Recusar", lambda e: "Você agradeceu. Agora não dá.")])


# --- 21. Pedido de aumento
@evento("aumento", "💬 Pedido de aumento", "Seu melhor funcionário pediu 'cinco minutinhos'…",
        cond=lambda e: e["func"] >= 2, peso=0.8, cooldown=10)
def _(e):
    def dar(e):
        e["extra_salario"] += 0.05
        e["mercado"] *= 1.05
        mudar(e, rep=+2, rel=+3)
        return "Aumento dado. A equipe ficou motivada e a produtividade subiu."

    def negar(e):
        if random.random() < 0.45:
            e["func"] -= 1
            e["mercado"] *= 0.95
            return "Ele pediu demissão e foi trabalhar para o concorrente, levando alguns clientes."
        mudar(e, felic=-2)
        return "Ele ficou, mas sem o mesmo brilho no olho."
    return ("O funcionário que mais vende pede 15% de aumento, dizendo que recebeu proposta do concorrente.",
            [("💰 Dar aumento", dar), ("🙅 Negar", negar)])


# --- 22. Viagem
@evento("viagem", "✈️ Convite para uma viagem", "Um convite dourado chegou pelo correio…",
        cond=lambda e: e["fase_max"] >= 2, peso=0.6, cooldown=14)
def _(e):
    v = round(4000 + receita_media(e) * 0.2, -3)

    def ir(e):
        e["caixa"] -= v
        mudar(e, felic=+15, saude=+12, rel=+5)
        if random.random() < 0.5:
            forcar(e, 1, "investidor")
            return "Viagem incrível! E na piscina você conheceu um investidor que pediu seu cartão…"
        return "Viagem incrível. Você voltou renovado(a)."
    return (f"Amigos ricos te chamaram para 10 dias em Fernando de Noronha. Sua parte: {brl(v)}.",
            [(f"🏝️ Ir (−{brl(v)})", ir), ("🏢 Ficar trabalhando", lambda e: (e.__setitem__("mercado", e["mercado"] * 1.05), "Você ficou e fechou uns negócios. Mas viu as fotos com inveja.")[1])])


# --- 23. Família
@evento("familia", "🎂 Família ou reunião?", "Dois compromissos marcados no mesmo dia…",
        cond=lambda e: e["rel"] < 95, peso=0.9, cooldown=8)
def _(e):
    quem = random.choice(["do seu filho", "da sua mãe", "do seu melhor amigo", "do seu pai"])

    def fam(e):
        e["mercado"] *= 0.96
        mudar(e, rel=+10, felic=+6, saude=+3)
        return "Você foi à festa. As risadas e o abraço valeram mais que qualquer contrato."

    def reuniao(e):
        e["mercado"] *= 1.1
        mudar(e, rel=-10, felic=-4)
        return "A reunião foi ótima e rendeu clientes. Mas alguém ficou te esperando…"
    return (f"O aniversário {quem} cai no mesmo horário da reunião com um cliente importante.",
            [("🎂 Ir ao aniversário", fam), ("💼 Ir à reunião", reuniao)])


# --- 24. Saúde
@evento("saude_alerta", "🩺 Seu corpo está pedindo socorro", "Você acordou com o coração disparado…", peso=0, cooldown=3)
def _(e):
    def ferias(e):
        e["mercado"] *= 0.9
        mudar(e, saude=+30, felic=+10, rel=+4)
        return "Duas semanas de descanso de verdade. Voltou com energia."

    def ignorar(e):
        if random.random() < 0.5:
            def internacao(e):
                e["caixa"] -= 3000
                e["mercado"] *= 0.8
                e["saude"] = 40
                return "🚑 Você desmaiou no escritório e ficou 1 semana internado(a). Hospital: R$ 3.000. Clientes sumiram."
            agendar(e, 1, internacao)
        mudar(e, saude=-5)
        return "Você tomou um remédio e voltou ao trabalho. Até quando?"
    return ("Insônia, ansiedade, dor no peito. O médico foi direto: 'Ou você para, ou o corpo vai te parar.'",
            [("🌴 Tirar 2 semanas de férias", ferias), ("💊 Ignorar e seguir", ignorar)])


# --- 25. Fornecedor sem nota
@evento("sem_nota", "📦 Fornecedor 'sem nota'", "Um fornecedor chegou com uma proposta 'por fora'…",
        cond=lambda e: e["mes"] > 3, peso=0.7, cooldown=14)
def _(e):
    def aceitar(e):
        e["bonus_margem"] = min(0.15, e["bonus_margem"] + 0.05)
        mudar(e, integ=-10)
        e["flags"].add("sonegou")
        return "Margem +5%… e um esqueleto no armário."
    return ("Ele oferece mercadoria 30% mais barata, mas sem nota fiscal.",
            [("🤫 Aceitar", aceitar), ("🧾 Recusar", lambda e: (mudar(e, integ=+3), "Você recusou. Seu contador te deu os parabéns.")[1])])


# --- 26. Contrato grande
@evento("contrato", "📜 Contrato milionário na mesa", "Uma multinacional quer marcar uma reunião…",
        cond=lambda e: e["fase_max"] >= 3, peso=0.8, cooldown=12)
def _(e):
    total = round(receita_media(e) * 4, -3)
    contratar_n = 3

    def aceitar(e):
        contratar(e, contratar_n)
        quebra = random.random() < 0.25
        for m in range(1, 7):
            def parcela(e, m=m):
                if quebra and m >= 3:
                    if m == 3:
                        mudar(e, felic=-8)
                        return "📜 O cliente do contrato milionário entrou em recuperação judicial e parou de pagar!"
                    return None
                e["caixa"] += total / 6 * 0.5
                return f"📜 Parcela {m}/6 do contrato grande: +{brl(total / 6 * 0.5)} de lucro." if m in (1, 6) else None
            agendar(e, m, parcela)
        mudar(e, rep=+6)
        return f"Contrato assinado! Você contratou {contratar_n} pessoas para dar conta."
    return (f"Contrato de {brl(total)} em 6 meses. Mas você precisa contratar {contratar_n} pessoas já.",
            [("✍️ Assinar", aceitar), ("❌ Recusar (risco alto)", lambda e: "Você preferiu não depender de um cliente só.")])


# --- 27. Proposta de compra
@evento("compra", "🏦 Querem comprar sua empresa", "Um grupo grande mandou um e-mail com o assunto 'Proposta'…",
        cond=lambda e: e["fase_max"] >= 3 and valor_empresa(e) > 100000, peso=0.5, cooldown=24)
def _(e):
    oferta = round(valor_empresa(e) * e["part"] * 1.3, -3)

    def vender(e):
        e["caixa"] += oferta
        e["fim"] = "venda"
        return f"Você vendeu tudo por {brl(oferta)}!"

    def recusar(e):
        mudar(e, rep=+4, felic=+3)
        return "Você recusou. 'Meu negócio não está à venda.' O mercado inteiro ficou sabendo."
    return (f"Um grupo oferece {brl(oferta)} pela sua parte na empresa. Se aceitar, sua jornada termina aqui com o dinheiro no bolso.",
            [(f"💰 Vender e se aposentar", vender), ("👑 Recusar e seguir rumo ao Império", recusar)])


# --- 28. Doação
@evento("doacao", "🎗️ Um pedido do coração", "Uma ONG do bairro pediu para falar com você…",
        cond=lambda e: e["caixa"] > 5000, peso=0.6, cooldown=12)
def _(e):
    v = round(max(1000, e["caixa"] * 0.05), -2)

    def doar(e):
        e["caixa"] -= v
        mudar(e, rep=+5, integ=+5, felic=+6, rel=+3)
        return "As crianças fizeram um cartaz de agradecimento com o nome da sua empresa. Você chorou um pouco."
    return (f"Uma ONG que ensina crianças precisa de {brl(v)} para não fechar.",
            [(f"💛 Doar {brl(v)}", doar), ("🙅 Agora não dá", lambda e: "Você explicou que o momento está difícil.")])



# ---------------------------------------------------------------- VIDA AFETIVA
def iniciar_namoro(e, p):
    e["parceiro"] = p["id"]
    e["namoro_desde"] = e["mes"]
    e["atencao"] = 70
    mudar(e, felic=+10, rel=+5)


def terminar_relacao(e, motivo, felic=-15, saude=-10):
    p = e["pessoas"].get(e["parceiro"]) if e["parceiro"] else None
    if not p:
        return ""
    txt = ""
    if "casado" in e["flags"]:
        if e.get("regime") == "comunhao":
            perda = max(0, e["caixa"]) * 0.3
            e["caixa"] -= perda
            txt = f" Na partilha de bens, foram {brl(perda)}."
        else:
            txt = " A separação de bens protegeu seu patrimônio."
        e["flags"].discard("casado")
    e["parceiro"] = None
    e["namoro_desde"] = None
    p["ativo"] = False
    mudar(e, felic=felic, saude=saude)
    log(e, f"💔 Fim do relacionamento com {p['nome']}: {motivo}.{txt}", p["id"])
    return f"💔 {p['nome']} e você terminaram: {motivo}.{txt}"


def vida_afetiva_mes(e, noticias):
    """Relacionamento precisa de atenção todo mês; casamento e filhos dão alegria mas exigem presença."""
    if not e["parceiro"]:
        return
    casado = "casado" in e["flags"]
    e["atencao"] = max(0, e.get("atencao", 60) - (10 if casado else 7) - (3 if e.get("filhos") else 0))
    if e["atencao"] >= 55:
        mudar(e, felic=+(3 if casado else 2), saude=+1)
        if casado and e["mes"] >= 60 and e["atencao"] > 70:
            conquistar(e, "amor_que_dura")
    elif e["atencao"] < 30:
        mudar(e, felic=-2)
        if not any(f["ev"] == "amor_atencao" for f in e["forcados"]) and "amor_atencao" not in e["usados"][-3:]:
            forcar(e, 1, "amor_atencao")
    if e["atencao"] <= 0:
        noticias.append(terminar_relacao(e, "você simplesmente não estava mais presente", felic=-18, saude=-12))
    if e.get("filhos"):
        mudar(e, felic=+2, saude=-1)


@evento("amor_atencao", "🥀 Seu relacionamento está esfriando", "Uma mensagem no celular: 'Precisamos conversar.'",
        cond=lambda e: e["parceiro"] is not None, peso=0, cooldown=2)
def _(e):
    p = e["pessoas"][e["parceiro"]]
    frase = random.choice(["Você casou com a empresa, não comigo.", "Eu me sinto sozinh{a} mesmo com você do lado.",
                           "Quando foi a última vez que a gente conversou sem você olhar o celular?"]).format(a=oa(p))

    def jantar(e):
        custo = round(300 + receita_media(e) * 0.03, -2)
        e["caixa"] -= custo
        e["atencao"] = min(100, e["atencao"] + 45)
        mudar(e, felic=+6, rel=+4)
        return f"Jantar especial, celular desligado ({brl(custo)}). Vocês riram como no começo. ❤️"

    def prometer(e):
        e["atencao"] = min(100, e["atencao"] + 15)
        e["mercado"] *= 0.97
        return "Você prometeu chegar mais cedo. Agora precisa cumprir: lembre de cuidar da família nos próximos meses."

    def ignorar(e):
        e["atencao"] = max(0, e["atencao"] - 15)
        mudar(e, rel=-5)
        if random.random() < 0.45:
            forcar(e, 2, "traicao")
        return "Você respondeu 'depois a gente fala' e voltou para a planilha."
    return (f"**{p['nome']}** desabafa: *\"{frase}\"*",
            [("🍷 Jantar especial, só vocês dois", jantar), ("🤞 Prometer mudar", prometer), ("💼 'Agora não dá'", ignorar)])


@evento("traicao", "💔 Uma descoberta que dói", "Uma notificação acendeu no celular errado, na hora errada…",
        cond=lambda e: e["parceiro"] is not None and (e.get("atencao", 60) < 40 or not e["pessoas"][e["parceiro"]]["bom"])
        and e["mes"] - (e.get("namoro_desde") or e["mes"]) >= 4, peso=0.5, cooldown=24)
def _(e):
    p = e["pessoas"][e["parceiro"]]
    e["flags"].add("traido")
    mudar(e, saude=-22, felic=-18)
    carente = p["bom"]  # pessoa boa que se afastou por solidão x pessoa interesseira

    def perdoar(e):
        if carente:
            e["atencao"] = 55
            mudar(e, felic=+5, rel=+3)
            revelar(e, p)
            return (f"Vocês conversaram a noite inteira. {p['nome']} se arrependeu de verdade: se sentia invisível. "
                    "A confiança vai demorar, mas vocês decidiram recomeçar.")
        e["atencao"] = 40
        forcar(e, 4, "traicao")
        return f"Você perdoou. {p['nome']} jurou que nunca mais… e pediu um presente caro para 'selar a paz'."

    def terminar(e):
        if not carente:
            revelar(e, p)
            conquistar(e, "detetive")
        return terminar_relacao(e, "traição", felic=-5, saude=-3)

    def terapia(e):
        e["caixa"] -= 600
        mudar(e, saude=+15, felic=+5, conhec=+3)
        p["pistas"].append(f"Na terapia você percebeu: {p['nome']} " +
                           ("se afastou porque você também se afastou." if carente else "sempre esteve mais perto do seu dinheiro do que de você."))
        e["seguinte"] = "traicao_decisao"
        return "A terapeuta te ajudou a enxergar com mais clareza o que aconteceu."
    origem = "com alguém do trabalho, nas suas longas ausências" if carente else "com outra pessoa, enquanto pedia presentes caros a você"
    return (f"Você descobriu que **{p['nome']}** estava se envolvendo {origem}. O chão sumiu. (Saúde emocional −22)",
            [("🤝 Perdoar e tentar de novo", perdoar), ("🚪 Terminar", terminar), ("🛋️ Fazer terapia antes de decidir (−R$ 600)", terapia)])


@evento("traicao_decisao", "💔 E agora?", "", peso=0, cooldown=0)
def _(e):
    _, opc = EVENTOS["traicao"]["montar"](e)
    e["flags"].add("traido")
    mudar(e, saude=+22, felic=+18)  # a dor já foi contada no evento anterior
    return ("Com a cabeça mais no lugar, o que você decide?", opc[:2])


@evento("bebe", "👶 Uma notícia que muda tudo", "Seu amor está com um sorriso diferente hoje…",
        cond=lambda e: e["parceiro"] is not None and e.get("filhos", 0) < 3 and e.get("atencao", 60) >= 40
        and e["mes"] - (e.get("namoro_desde") or e["mes"]) >= 8, peso=0.5, cooldown=18)
def _(e):
    p = e["pessoas"][e["parceiro"]]

    def ter(e):
        e["filhos"] = e.get("filhos", 0) + 1
        e["atencao"] = min(100, e["atencao"] + 20)
        mudar(e, felic=+20, rel=+12, saude=-8)
        conquistar(e, "familia_formada")
        if p["bom"]:
            revelar(e, p)
        log(e, f"👶 Nasceu seu {'primeiro filho' if e['filhos'] == 1 else str(e['filhos']) + 'º filho'}!", p["id"])
        return ("👶 Daqui a alguns meses chega um bebê! Noites sem dormir, custo de vida maior, "
                "e um amor que você nem sabia que existia.")

    def esperar(e):
        if p["bom"]:
            mudar(e, rel=-3)
            return f"Vocês conversaram e decidiram esperar a empresa se estabilizar. {p['nome']} entendeu, mas ficou pensativ{oa(p)}."
        e["atencao"] = max(0, e["atencao"] - 20)
        return f"{p['nome']} ficou fri{oa(p)}: 'Então eu não sou prioridade, né?'"
    return (f"**{p['nome']}** diz que quer ter um filho com você. Isso vai mudar suas prioridades para sempre.",
            [("👶 Vamos ter um filho!", ter), ("⏳ Ainda não é a hora", esperar)])


@evento("filho_momento", "🧸 Coisas de pai e mãe", "Tem um desenho colado na geladeira com seu nome…",
        cond=lambda e: e.get("filhos", 0) > 0, peso=1.1, cooldown=5)
def _(e):
    cena = random.choice([
        ("Hoje é a apresentação de dança na escola, no mesmo horário da reunião com o maior cliente do ano.",
         "🎭 Ir à apresentação", "💼 Ir à reunião"),
        ("Seu filho acordou com febre de 39 °C na madrugada, e amanhã cedo você tem uma visita importante.",
         "🌡️ Ficar em casa cuidando", "📅 Manter a visita e pedir ajuda"),
        ("No jantar, seu filho pergunta: 'Por que você nunca está em casa?'",
         "🤗 Tirar o fim de semana inteiro para ele", "📱 Explicar que é pelo futuro dele"),
        ("A escola chamou: as notas caíram e o professor quer conversar com os pais.",
         "🏫 Ir à reunião da escola", "📧 Responder por e-mail"),
    ])
    texto, sim, nao = cena

    def presente(e):
        e["mercado"] *= 0.96
        e["atencao"] = min(100, e.get("atencao", 60) + 15)
        mudar(e, rel=+10, felic=+8, saude=+3)
        return "Você estava lá. O olhar dele ao te ver vai ficar na sua memória para sempre."

    def ausente(e):
        e["mercado"] *= 1.06
        mudar(e, rel=-8, felic=-6)
        e["atencao"] = max(0, e.get("atencao", 60) - 10)
        return "O trabalho rendeu. Mas à noite ele já estava dormindo quando você chegou."
    return (texto, [(sim, presente), (nao, ausente)])


@evento("pretendente", "🎩 Um(a) pretendente encantador(a)", "Chegou um buquê sem cartão no seu escritório…",
        cond=lambda e: e["parceiro"] is None and e["fase_max"] >= 3, peso=0.6, cooldown=24)
def _(e):
    p = nova_pessoa(e, "amor", forcar_bom=random.random() < 0.25)
    pergunta = random.choice(["quanto sua empresa fatura", "se você tem imóveis no seu nome",
                              "se você pensa em viajar para Dubai em breve"])

    def sair(e):
        iniciar_namoro(e, p)
        forcar(e, 3, "amor_pedido")
        return f"Vocês começaram a sair. {p['nome']} é encantador{'a' if p['sexo'] == 'F' else ''}… e caro{'a' if p['sexo'] == 'F' else ''}."

    def devagar(e):
        p["pistas"].append(f"Logo no 1º encontro, {p['nome']} perguntou {pergunta}.")
        mudar(e, saude=+2)
        return f"Você preferiu ir devagar e observar. Anotou que {p['nome']} perguntou {pergunta} logo de cara."
    return (f"Desde que você ficou famoso(a) na cidade, **{p['nome']}, {p['idade']} anos**, "
            f"apareceu do nada: presentes, elogios, convites. No primeiro café, perguntou {pergunta}.",
            [("💘 Se deixar levar", sair), ("🧐 Ir devagar e observar", devagar)])


@evento("amigo_dificil", "🫂 Um amigo no fundo do poço", "Faz tempo que seu amigo não posta nada…",
        cond=lambda e: e["mes"] > 6, peso=0.7, cooldown=16)
def _(e):
    p = pessoa(e, "amigo")
    drama = random.choice(["perdeu o emprego e está em depressão", "se separou e não consegue sair da cama",
                           "perdeu o pai e está sem chão"])

    def presente(e):
        e["mercado"] *= 0.95
        mudar(e, rel=+12, integ=+4, felic=+4, saude=-3)
        if p["bom"]:
            revelar(e, p)
            e["flags"].add("ajudou_amigo")
            forcar(e, 6, "retribuicao")
        return f"Você passou dias ao lado de {p['nome']}. Não resolveu tudo, mas {ele(p)} disse: 'Você salvou minha vida.'"

    def mensagem(e):
        mudar(e, rel=-6)
        return f"Você mandou um 'força, amigo!' e voltou ao trabalho. {p['nome']} visualizou e não respondeu."
    return (f"**{p['nome']}** {drama}. Não pediu dinheiro, só precisa de alguém por perto. Mas este mês a empresa está a mil.",
            [("🫂 Estar presente de verdade", presente), ("📱 Mandar uma mensagem de apoio", mensagem)])


# --- 29. Mês tranquilo
@evento("mes_tranquilo", "☕ Um mês tranquilo", "Parece que vem aí um mês calmo… será?", peso=0.7, cooldown=3)
def _(e):
    return ("Pela primeira vez em muito tempo, sobrou uma tarde livre. O que fazer?",
            [("📖 Ler um livro de negócios", lambda e: (mudar(e, conhec=+4), "Você anotou três ideias que vai testar.")[1]),
             ("🍝 Jantar com amigos", lambda e: (mudar(e, rel=+5, felic=+3), "Boas conversas, boa comida. Recarregou.")[1]),
             ("🧮 Revisar as contas", lambda e: (e.__setitem__("caixa", e["caixa"] + receita_media(e) * 0.05),
                                               f"Você achou assinaturas esquecidas e economizou {brl(receita_media(e) * 0.05)}.")[1])])


# ---------------------------------------------------------------- INTERFACE
CSS_VIDA = """<style>
.vida-hero{background:linear-gradient(135deg,#1b1240 0%,#3b1d6e 50%,#b8860b 130%);color:#fff;border-radius:18px;
  padding:22px 24px;margin-bottom:14px;box-shadow:0 8px 30px rgba(59,29,110,.35)}
.vida-hero h2{margin:0;font-size:1.7rem;color:#ffd34d}.vida-hero p{margin:.3rem 0 0;opacity:.9}
.vida-top{display:flex;flex-wrap:wrap;gap:8px;align-items:center;justify-content:space-between;
  background:linear-gradient(90deg,#1b1240,#3b1d6e);color:#fff;border-radius:14px;padding:12px 16px;margin-bottom:10px}
.vida-top b{color:#ffd34d}.vida-chip{display:inline-block;padding:3px 10px;border-radius:999px;margin:2px;font-size:.85rem;
  background:rgba(128,128,128,.15)}
.vida-chip.up{background:rgba(46,160,67,.18);color:#2ea043}.vida-chip.down{background:rgba(218,54,51,.16);color:#da3633}
.vida-ev{border:2px solid #b8860b;border-radius:16px;padding:18px 20px;margin:8px 0 12px;
  background:linear-gradient(180deg,rgba(184,134,11,.10),rgba(184,134,11,.02))}
.vida-ev h3{margin:0 0 .4rem;color:#b8860b}
.vida-teaser{border-left:4px solid #8a5cf6;padding:8px 12px;border-radius:6px;background:rgba(138,92,246,.10);margin:8px 0}
.vida-conq{border-radius:12px;padding:10px;text-align:center;min-height:92px}
.vida-conq.on{background:linear-gradient(135deg,#ffd34d33,#b8860b33);border:1px solid #b8860b}
.vida-conq.off{background:rgba(128,128,128,.08);border:1px dashed rgba(128,128,128,.4);opacity:.7}
</style>"""


def vida_hall():
    hall = S.get("vida_hall", [])
    if not hall:
        return
    st.markdown("#### 🏛️ Hall da Fama")
    for i, h in enumerate(sorted(hall, key=lambda h: -h["pts"])[:10], 1):
        medalha = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f"{i}º")
        st.markdown(f"{medalha} **{h['pts']} pts**: {h['empresa']} ({h['ramo']}) · {h['fase']} · "
                    f"{h['meses']} meses · *{h['titulo']}* · {h['fim']}")


def vida_setup():
    st.markdown(CSS_VIDA, unsafe_allow_html=True)
    st.markdown("""<div class="vida-hero"><h2>👑 A VIDA É UM JOGO</h2>
    <p><b>Do Zero ao Império.</b> Construa seu império. Descubra em quem confiar. Escolha quem você quer ser.</p>
    <p style="font-size:.9rem;opacity:.8">Você começa com R$ 3.000, um computador velho e muita coragem.</p></div>""",
                unsafe_allow_html=True)
    legado = S.get("vida_legado", 0)
    if legado:
        st.success(f"🧬 **Experiência de vidas passadas:** você começa com **+{legado} de conhecimento**.")
    with st.form("vida_setup"):
        empresa = st.text_input("Nome da sua empresa", placeholder="Ex.: Silva Soluções, Sabor da Vila, NovaTech…", max_chars=40)
        ramo = st.radio("Em que ramo você vai empreender?", list(RAMOS),
                        captions=[RAMOS[r]["desc"] for r in RAMOS])
        if st.form_submit_button("🚀 Começar minha vida", type="primary"):
            S.vida = novo_jogo_vida(S.get("usuario", "Você"), empresa.strip() or "Minha Empresa", ramo, legado)
            st.rerun()
    vida_hall()


def vida_topo(e):
    ano, mes = (e["mes"] - 1) // 12 + 1, (e["mes"] - 1) % 12 + 1
    fogo = f" · 🔥 {e['seq_lucro']} meses no lucro" if e["seq_lucro"] >= 2 else ""
    st.markdown(f"""<div class="vida-top"><span>🏢 <b>{e['empresa']}</b> · {e['ramo']}</span>
      <span>📅 Ano {ano}, mês {mes}{fogo}</span><span>{FASES[e['fase_max']][0]}</span></div>""", unsafe_allow_html=True)
    c = st.columns(4)
    c[0].metric("💵 Caixa", brl(e["caixa"]))
    c[1].metric("🏦 Dívida", brl(e["divida"]), f"{e['taxa'] * 100:.1f}% a.m." if e["divida"] else None,
                delta_color="off")
    c[2].metric("📈 Faturamento/mês", brl(e["hist_receita"][-1] if e["hist_receita"] else 0))
    c[3].metric("💎 Patrimônio", brl(patrimonio(e)))
    cols = st.columns(3)
    for i, k in enumerate(IND):
        cols[i % 3].progress(e[k] / 100, text=f"{NOME_IND[k]}: **{e[k]:.0f}**")
    if e["parceiro"]:
        p = e["pessoas"][e["parceiro"]]
        a = e.get("atencao", 60)
        estado = "💍 Casamento" if "casado" in e["flags"] else "❤️ Namoro"
        filhos = f" · 👶 {e['filhos']} filho(s)" if e.get("filhos") else ""
        alerta = " ⚠️ precisa de você!" if a < 30 else ""
        st.progress(a / 100, text=f"{estado} com {p['nome']}{filhos} · atenção ao relacionamento: **{a:.0f}**{alerta}")
    elif e.get("filhos"):
        st.caption(f"👶 {e['filhos']} filho(s)")
    if e["fase_max"] < len(FASES) - 1:
        nome, fat, pat = FASES[e["fase_max"] + 1]
        rm, pt = receita_media(e), patrimonio(e)
        st.caption(f"🎯 **Próxima fase: {nome}**. Precisa de faturamento médio de {brl(fat)} e patrimônio de {brl(max(pat, 0))}.")
        a, b = st.columns(2)
        a.progress(min(1.0, max(0.0, rm / fat)), text=f"Faturamento {rm / fat:.0%}")
        b.progress(min(1.0, max(0.0, pt / pat)) if pat > 0 else 1.0, text=f"Patrimônio {max(0, pt) / pat:.0%}" if pat > 0 else "Patrimônio ✔")
    else:
        st.caption("🏰 **Você construiu um IMPÉRIO.** Agora é cuidar do que importa: vida plena e legado.")


def vida_acao(e):
    ev = EVENTOS[e["prox"]]
    if ev["teaser"]:
        st.markdown(f"<div class='vida-teaser'>🔮 <b>Neste mês:</b> {ev['teaser']}</div>", unsafe_allow_html=True)
    st.markdown(f"### 📅 Mês {e['mes']}: onde você vai colocar sua energia?")
    acoes = acoes_disponiveis(e)
    cols = st.columns(2)
    for i, (rot, desc, custo, chave) in enumerate(acoes):
        with cols[i % 2]:
            if st.button(rot, key=f"vida_a_{chave}_{e['mes']}", width="stretch",
                         type="primary" if chave in ("vender", "marketing") else "secondary"):
                e["acao_txt"] = fazer_acao(e, chave, custo)
                e["ev"] = montar_evento(e, e["prox"])
                e["resultados"] = []
                e["etapa"] = "evento"
                st.rerun()
            st.caption(desc)

    lim = ESTRUTURAS[e["estrutura"]][1]
    with st.expander(f"👥 Equipe: {e['func']} de {lim} funcionário(s) · {ESTRUTURAS[e['estrutura']][0]}"):
        cap = capacidade(e)
        st.write(f"Capacidade de atendimento: **{brl(cap)}/mês** · Demanda de clientes: **{brl(e['mercado'])}/mês**")
        if e["mercado"] > cap * 1.05:
            st.warning("Tem mais cliente do que você dá conta! Contrate para não perder reputação.")
        st.caption(f"Cada funcionário custa {brl(e['r']['salario'] * (1 + e['extra_salario']))}/mês e aumenta a "
                   f"capacidade em {brl(e['r']['capf'])}. Contratar custa meio salário; demitir custa 1,2 salário.")
        c1, c2 = st.columns(2)
        livre = lim - e["func"]
        if livre > 0:
            n = c1.number_input("Quantos contratar?", 1, livre, 1, key=f"vida_nc_{e['mes']}")
            if c1.button("➕ Contratar", key=f"vida_c_{e['mes']}"):
                contratar(e, int(n))
                st.rerun()
        else:
            c1.info("Sem espaço. Mude para uma estrutura maior.")
        if e["func"] > 0:
            n2 = c2.number_input("Quantos demitir?", 1, e["func"], 1, key=f"vida_nd_{e['mes']}")
            if c2.button("➖ Demitir", key=f"vida_d_{e['mes']}"):
                demitir(e, int(n2))
                st.rerun()

    with st.expander(f"🏦 Banco: limite disponível {brl(limite_credito(e))}"):
        c1, c2 = st.columns(2)
        lim_c = int(limite_credito(e) // 500 * 500)
        if lim_c >= 500:
            v = c1.number_input("Pegar empréstimo (3,5% a.m.)", 500, lim_c, min(5000, lim_c), 500, key=f"vida_emp_{e['mes']}")
            if c1.button("💳 Pegar", key=f"vida_pe_{e['mes']}"):
                pegar_emprestimo(e, float(v))
                st.rerun()
        else:
            c1.info("O banco não libera mais crédito para você agora.")
        if e["divida"] > 0 and e["caixa"] > 0:
            maxp = int(min(e["divida"], e["caixa"]))
            v2 = c2.number_input("Pagar dívida", 1, max(1, maxp), max(1, maxp), key=f"vida_am_{e['mes']}")
            if c2.button("✅ Pagar", key=f"vida_pa_{e['mes']}"):
                amortizar(e, float(v2))
                st.rerun()


def vida_evento(e):
    if e.get("acao_txt"):
        st.info(f"✔️ {e['acao_txt']}")
    for r in e["resultados"]:
        st.success(r)
    ev = e["ev"]
    st.markdown(f"<div class='vida-ev'><h3>{ev['titulo']}</h3></div>", unsafe_allow_html=True)
    st.markdown(ev["texto"])
    for i, (rot, fn) in enumerate(ev["opcoes"]):
        if st.button(rot, key=f"vida_o_{ev['id']}_{i}_{e['mes']}_{len(e['resultados'])}", width="stretch"):
            res = fn(e)
            if res:
                e["resultados"].append(res)
                log(e, f"{ev['titulo']}: {res}")
            nxt = e.pop("seguinte", None)
            if nxt and not e["fim"]:
                e["ev"] = montar_evento(e, nxt)
            elif e["fim"]:
                e["etapa"] = "fim"
            else:
                fechar_mes(e)
            st.rerun()
    st.caption("Não existe resposta certa. Toda escolha tem vantagens, riscos e consequências, e algumas só aparecem meses depois.")


def chips_variacao(e, antes):
    chips = []
    for k in IND:
        d = e[k] - antes[k]
        if abs(d) >= 1:
            chips.append(f"<span class='vida-chip {'up' if d > 0 else 'down'}'>{NOME_IND[k]} {d:+.0f}</span>")
    d = patrimonio(e) - antes["patrimonio"]
    chips.append(f"<span class='vida-chip {'up' if d >= 0 else 'down'}'>💎 Patrimônio {'+' if d >= 0 else ''}{brl(d)}</span>")
    return "".join(chips)


def vida_relatorio(e):
    r = e["relatorio"]
    for cid in e["novas_conq"]:
        st.toast(f"🏆 Conquista: {CONQUISTAS[cid][0]}", icon="🏆")
    if e["fase_max"] > r["fase_antes"]:
        st.balloons()
        st.success(f"## 🚀 NOVA FASE: {FASES[e['fase_max']][0]}!")
    if e["resultados"]:
        for res in e["resultados"]:
            st.info(res)
    st.markdown(f"### 📊 Fechamento do mês {r['mes']}")
    cor = "#2ea043" if r["resultado"] >= 0 else "#da3633"
    st.markdown(f"<div style='font-size:1.9rem;font-weight:800;color:{cor}'>"
                f"{'Lucro' if r['resultado'] >= 0 else 'Prejuízo'} de {brl(abs(r['resultado']))}</div>", unsafe_allow_html=True)
    st.markdown(f"""
| Mês {r['mes']} | Valor |
|---|---|
| 📈 Faturamento | **{brl(r['receita'])}** |
| ➖ Custos do produto/serviço | {brl(r['receita'] - r['lucro_bruto'])} |
| 🏢 Custo fixo (aluguel, contas) | {brl(r['fixo'])} |
| 👥 Salários | {brl(r['salarios'])} |
| 🏦 Juros | {brl(r['juros'])} |
| 🏠 Seu custo de vida | {brl(r['vida'])} |
""")
    st.markdown(chips_variacao(e, r["antes"]), unsafe_allow_html=True)
    if e["noticias"]:
        st.markdown("#### 📰 Aconteceu neste mês")
        for n in e["noticias"]:
            st.markdown(f"- {n}")
    if e["novas_conq"]:
        st.markdown("#### 🏆 Conquistas desbloqueadas")
        for cid in e["novas_conq"]:
            st.markdown(f"**{CONQUISTAS[cid][0]}**: {CONQUISTAS[cid][1]}")

    if e["mes"] > 60 and not e["avaliacao5"]:
        e["avaliacao5"] = True
        pts = pontuacao(e)
        st.markdown("---\n## 🎂 Avaliação dos seus 5 anos")
        cols = st.columns(5)
        for c, (k, v) in zip(cols, dimensoes(e).items()):
            c.metric(k, v)
        st.success(f"Pontuação de vida: **{pts}/1000**: *{titulo_vida(pts)}*. A jornada continua rumo ao Império!")

    ev = EVENTOS[e["prox"]]
    if ev["teaser"]:
        st.markdown(f"<div class='vida-teaser'>🔮 <b>Próximo mês:</b> {ev['teaser']}</div>", unsafe_allow_html=True)
    if st.button(f"▶️ Viver o mês {e['mes']}", type="primary", key=f"vida_prox_{e['mes']}", width="stretch"):
        e["novas_conq"] = []
        e["resultados"] = []
        e["acao_txt"] = ""
        e["etapa"] = "acao"
        st.rerun()


def vida_registrar_fim(e):
    if e.get("registrado"):
        return
    e["registrado"] = True
    pts = pontuacao(e)
    fim = {"falencia": "💥 Faliu", "venda": "💰 Vendeu a empresa", "aposentou": "🌅 Aposentou"}.get(e["fim"], e["fim"])
    S.setdefault("vida_hall", []).append(dict(pts=pts, empresa=e["empresa"], ramo=e["ramo"], fase=FASES[e["fase_max"]][0],
                                              meses=e["mes"] - 1, titulo=titulo_vida(pts), fim=fim))
    S.vida_legado = min(30, S.get("vida_legado", 0) + max(2, (e["mes"] - 1) // 6))


def vida_fim(e):
    vida_registrar_fim(e)
    pts = pontuacao(e)
    if e["fim"] == "falencia":
        st.error(f"## 💥 Falência no mês {e['mes'] - 1}\nO caixa acabou e o banco não empresta mais. "
                 "Mas todo grande empreendedor já quebrou pelo menos uma vez.")
    elif e["fim"] == "venda":
        st.balloons()
        st.success(f"## 💰 Você vendeu a empresa e saiu com {brl(e['caixa'] - e['divida'])}!")
    else:
        st.success("## 🌅 Você encerrou essa vida e deixou seu legado.")
    st.markdown(f"### Pontuação de vida: {pts}/1000: *{titulo_vida(pts)}*")
    cols = st.columns(5)
    for c, (k, v) in zip(cols, dimensoes(e).items()):
        c.metric(k, v)
    piores = sorted(dimensoes(e).items(), key=lambda x: x[1])[:2]
    st.info("📚 **Lição desta vida:** " + " e ".join(f"{k} ficou em {v}" for k, v in piores) +
            ". Dinheiro sozinho não é sucesso; o jogo mede a vida inteira.")
    st.success(f"🧬 Na próxima vida você começa com **+{S.get('vida_legado', 0)} de conhecimento** pela experiência acumulada.")
    if st.button("🔄 Viver uma nova vida", type="primary", key="vida_nova"):
        S.vida = None
        st.rerun()
    vida_hall()


def persona_prompt(e, p):
    pap = PAPEIS[p["papel"]]
    hist = [t for (_, t, pid) in e["diario"] if pid == p["id"]][-6:]
    return (f"Você é {p['nome']}, {p['idade']} anos, personagem do jogo de simulação 'A Vida É um Jogo'. "
            f"Seu papel na vida do jogador: {pap['titulo']}.\n"
            f"SUA VERDADEIRA PERSONALIDADE (segredo, nunca revele diretamente): {pap['b'] if p['bom'] else pap['r']}.\n"
            f"O jogador se chama {e['jogador']}, dono(a) da empresa '{e['empresa']}' ({e['ramo']}). Mês {e['mes']} da jornada. "
            f"Caixa da empresa: {brl(e['caixa'])}. Fase: {FASES[e['fase_max']][0]}.\n"
            f"O que já aconteceu entre vocês: {' | '.join(hist) or 'vocês se conheceram há pouco.'}\n"
            "REGRAS: responda em português do Brasil, no máximo 3 frases curtas, como uma pessoa real conversando por "
            "mensagem. Nunca saia do personagem e nunca diga que é uma IA. Se você é desonesto(a), deixe pistas SUTIS "
            "(pressa, promessas exageradas, fugir de perguntas sobre documentos, desviar para dinheiro), mas nunca confesse. "
            "Se é honesto(a), seja transparente, admita riscos e limites, e às vezes diga verdades desconfortáveis.")


def vida_pessoas(e):
    if not e["pessoas"]:
        st.info("Você ainda não conheceu ninguém.")
        return
    st.caption("💬 Converse com as pessoas (a IA dá vida a cada uma) e observe as atitudes. "
               "Ninguém é totalmente previsível. Descubra em quem confiar!")
    pessoas = sorted(e["pessoas"].values(), key=lambda p: (not p["ativo"], -p["conheceu"]))
    for p in pessoas:
        if p["revelado"]:
            status = "✅ Provou ser confiável" if p["bom"] else "🚩 Mostrou quem realmente é"
        else:
            status = "❔ Confiabilidade desconhecida"
        ativo = "" if p["ativo"] else " · 🚪 saiu da sua vida"
        with st.expander(f"{p['nome']}, {p['idade']} anos · {PAPEIS[p['papel']]['titulo']} · {status}{ativo}"):
            if p["pistas"]:
                st.markdown("**🔎 O que você descobriu:**\n" + "\n".join(f"- {x}" for x in p["pistas"]))
            for papel_msg, txt in e["chats"][p["id"]]:
                with st.chat_message("user" if papel_msg == "user" else "assistant",
                                     avatar=None if papel_msg == "user" else "🧑"):
                    st.write(txt)
            if not p["ativo"]:
                continue
            if not S.get("groq_key"):
                st.caption("Entre com uma chave Groq para conversar.")
                continue
            with st.form(f"vida_chat_{p['id']}", clear_on_submit=True):
                msg = st.text_input(f"Mensagem para {p['nome']}", placeholder="Pergunte algo, negocie, observe…")
                if st.form_submit_button("💬 Enviar") and msg.strip():
                    hist = [{"role": "system", "content": persona_prompt(e, p)}]
                    for papel_msg, txt in e["chats"][p["id"]][-10:]:
                        hist.append({"role": papel_msg, "content": txt})
                    hist.append({"role": "user", "content": msg.strip()})
                    try:
                        with st.spinner(f"{p['nome']} está digitando…"):
                            resp = groq_chat(hist)
                        e["chats"][p["id"]] += [("user", msg.strip()), ("assistant", resp.strip())]
                    except Exception:
                        st.error("Não consegui falar com a IA agora. Tente de novo.")
                    st.rerun()


def vida_diario(e):
    for mes, txt, _ in reversed(e["diario"][-80:]):
        st.markdown(f"**Mês {mes}** · {txt}")


def vida_conquistas(e):
    cols = st.columns(3)
    for i, (cid, (nome, desc)) in enumerate(CONQUISTAS.items()):
        on = cid in e["conquistas"]
        cols[i % 3].markdown(f"<div class='vida-conq {'on' if on else 'off'}'><b>{nome if on else '🔒 ' + nome.split(' ', 1)[1]}</b>"
                             f"<br><small>{desc}</small></div>", unsafe_allow_html=True)
        cols[i % 3].write("")


def jogo_vida():
    if not S.get("vida"):
        vida_setup()
        return
    e = S.vida
    st.markdown(CSS_VIDA, unsafe_allow_html=True)
    if e["etapa"] == "fim":
        vida_fim(e)
        return
    vida_topo(e)
    n_conq = len(e["conquistas"])
    abas = st.tabs(["🎮 Jogar", f"👥 Pessoas ({sum(p['ativo'] for p in e['pessoas'].values())})", "📜 Diário",
                    f"🏆 Conquistas ({n_conq}/{len(CONQUISTAS)})"])
    with abas[0]:
        {"acao": vida_acao, "evento": vida_evento, "relatorio": vida_relatorio}[e["etapa"]](e)
    with abas[1]:
        vida_pessoas(e)
    with abas[2]:
        vida_diario(e)
    with abas[3]:
        vida_conquistas(e)
        st.write("")
        if st.button("🌅 Encerrar esta vida e entrar no Hall da Fama", key="vida_aposentar"):
            e["fim"] = "aposentou"
            e["etapa"] = "fim"
            st.rerun()


# =====================================================================
# COMO JOGAR (instruções de cada jogo)
# =====================================================================
COMO_XADREZ = """
**🎯 Objetivo:** dar **xeque-mate** no rei adversário, ou seja, atacar o rei de um jeito que ele não tenha como escapar.

**🖱️ Como mexer aqui:** clique numa peça sua (a casa fica amarela). As **bolinhas** mostram para onde ela pode ir, e os **anéis** mostram peças que ela pode capturar. Depois clique na casa de destino. O computador responde sozinho. As brancas sempre começam.

**♟️ Como cada peça anda:**
- **♟ Peão:** anda **1 casa para frente** (no primeiro movimento pode andar 2). Captura **na diagonal**, 1 casa para frente. Nunca anda para trás.
- **♜ Torre:** quantas casas quiser em **linha reta** (para frente, para trás e para os lados).
- **♝ Bispo:** quantas casas quiser na **diagonal**. Cada bispo fica sempre na mesma cor de casa.
- **♞ Cavalo:** anda em **"L"** (2 casas numa direção e 1 para o lado). É a única peça que **pula** as outras.
- **♛ Dama (rainha):** a peça mais forte. Anda como a torre **e** como o bispo juntos.
- **♚ Rei:** anda **1 casa** em qualquer direção e nunca pode ir para uma casa atacada.

Você **captura** uma peça inimiga parando na casa dela. Não dá para pular em cima das suas próprias peças.

**📏 Regras importantes:**
- **Xeque:** seu rei está sendo atacado (a casa dele fica vermelha). Você é **obrigado** a se livrar do xeque: fugir com o rei, colocar uma peça na frente ou capturar quem está atacando.
- **Xeque-mate:** é um xeque sem saída, e quem levou perde a partida.
- **Afogamento:** quem tem a vez não está em xeque, mas não tem nenhum lance permitido. Isso dá **empate**.
- **Roque:** o rei anda **2 casas** em direção a uma torre, e a torre pula para o outro lado dele. Só vale se o rei e a torre nunca se mexeram, se não houver peças entre eles e se o rei não estiver em xeque nem passar por casa atacada. Aqui, clique no rei e depois na casa 2 para o lado.
- **Promoção:** o peão que chega à última fileira vira outra peça, que você escolhe em *"Promover peão a"* (quase sempre a Dama).
- **En passant:** se um peão inimigo andar 2 casas e parar **ao lado** do seu peão, você pode capturá-lo como se ele tivesse andado só 1. Isso só vale no lance logo em seguida.

**💰 Valor das peças (para pensar nas trocas):** peão = 1 · cavalo = 3 · bispo = 3 · torre = 5 · dama = 9.

**💡 Dicas para começar:**
1. Ocupe o **centro** com peões (casas e4, d4, e5, d5).
2. Tire **cavalos e bispos** de casa logo no começo.
3. Faça o **roque** cedo para proteger o rei.
4. Antes de jogar, pergunte: *"essa peça vai ficar desprotegida?"* e *"o que o adversário está ameaçando?"*
5. Não saia com a dama muito cedo, porque ela vira alvo.
6. Travou num lance? Use o **↩️ Desfazer lance** e tente outro. Comece no nível **Fácil**.
"""

INSTRUCOES = {
    "👑 A Vida É um Jogo": """
**🎯 Objetivo:** sair do zero (R$ 3.000 e um computador velho) e construir um **império**, sem perder o que mais importa no caminho. A vitória não é só dinheiro. Sua **pontuação de vida** (0 a 1000) mede **5 dimensões**: 💰 Prosperidade · 🏢 Empresa · 🌿 Qualidade de vida · 🤝 Relacionamentos · ⚖️ Integridade.

**Como cada mês funciona:**
1. **Escolha onde colocar sua energia:** vender, marketing, estudar, networking, descansar, inovar ou mudar para uma estrutura maior.
2. **Viva um acontecimento:** sócios, amigos, amores, fiscais, golpes, crises, propostas milionárias… Escolha o que fazer.
3. **Veja o fechamento do mês:** lucro ou prejuízo, notícias e conquistas. A 🔮 prévia mostra o que vem no próximo mês.

**⚠️ Consequências demoram:** muitas decisões só mostram o resultado **meses depois**. Confiar em quem não devia pode custar caro lá na frente.

**👥 Pessoas:** cada pessoa tem um **caráter secreto** (pode ser confiável ou não). Investigue, observe as atitudes e **converse com elas** na aba *Pessoas*. A IA dá vida a cada personagem, e os desonestos deixam pistas sutis.

**💼 Gestão:**
- **Equipe:** quando a demanda passa da sua capacidade, contrate. Cliente sem atendimento derruba a reputação.
- **Estrutura:** limita quantos funcionários cabem. Mude para um espaço maior para crescer.
- **Banco:** empréstimo a 3,5% ao mês. Se o caixa ficar negativo, o banco cobre com **cheque especial a 8%**. Se nem isso der, é **falência**.
- **Saúde emocional:** se zerar, você tem um *burnout*. Descanse!

**❤️ Vida afetiva:** namoro e casamento trazem felicidade **se você estiver presente**. A *atenção ao relacionamento* cai todo mês (mais rápido depois do casamento) e sobe quando você escolhe **🧘 Cuidar de você e da família**. Abandonado, o amor esfria, e pode vir até uma traição 💔. Um 👶 **filho** muda suas prioridades: mais alegria, mais custo e dilemas entre a família e o trabalho.

**🏆 Fases:** 🌱 Sonhador → 🛠️ Autônomo → 🏪 Pequeno Negócio → 🏢 Em Crescimento → 🏙️ Consolidada → 🏰 **Império**. São 21 conquistas para desbloquear, e no mês 60 tem uma avaliação dos seus 5 anos.

**🧬 Legado:** cada vida que termina vai para o **Hall da Fama** e te dá **conhecimento extra** na próxima. Quanto mais você joga, mais longe vai.

**💡 Dicas:** comece no ramo de **serviços** ou **imobiliário** (os mais fáceis). Não gaste todo o caixa de uma vez. Contrate quando faltar capacidade. E desconfie de quem promete demais e tem pressa.
""",
    "🪩 Pinball": """
**🎯 Objetivo:** fazer o máximo de pontos **sem deixar a bola cair** no buraco entre as duas palhetas amarelas. Você tem **3 bolas**.

**Controles:**
- **Lançar a bola:** segure **ESPAÇO** (ou o botão 🚀) para puxar a mola e solte. Quanto mais tempo segurar, mais forte vai.
- **Palheta esquerda:** **←** ou **A** (no celular, toque no lado esquerdo da tela ou em "◀ Palheta").
- **Palheta direita:** **→** ou **D** (no celular, toque no lado direito ou em "Palheta ▶").
- **P** pausa o jogo.

**Pontos:**
- 🔴🟢🟠 **Bumpers** (círculos coloridos) arremessam a bola e valem **100**.
- 🩷 **Estilingues** (linhas rosa acima das palhetas) chutam a bola e valem **10**.
- 💡 Acenda as **3 luzes do topo** passando por elas para ganhar **+500** e aumentar o **multiplicador** (até x5). Ele multiplica todos os pontos!

**💡 Dica:** não fique apertando sem parar. Espere a bola chegar perto da palheta e bata no momento certo, porque a ponta da palheta joga a bola mais longe.
""",
    "🟢 Come-Come": """
**🎯 Objetivo:** você é o **slime verde 🟢**. Coma **todas as bolinhas** do labirinto sem ser pego pelos **vírus**. Ao limpar o labirinto, você passa de nível, e a cada nível os vírus ficam mais rápidos. Você tem **3 vidas**.

**Controles:** **setas** ou **W A S D** no teclado. No celular, **arraste o dedo** na direção que quer ir ou use os botões ◀ ▲ ▼ ▶. Dá para apertar a direção **antes** de chegar na curva, e o slime vira assim que der. **P** pausa.

**Pontos:**
- Bolinha pequena: **10**
- ⚪ **Bolona** (nos cantos): **50**, e os vírus ficam **azuis e com medo** por alguns segundos. Nesse tempo **você pode comê-los**! Eles valem 200, 400, 800... em sequência. Quando começam a **piscar**, o efeito está acabando.

**💡 Dicas:**
- Os corredores das laterais do meio são um **túnel**: sai de um lado e aparece do outro.
- Guarde as bolonas para quando os vírus estiverem perto de você.
- Cada vírus tem um jeito: o vermelho persegue você direto, o laranja tenta cortar sua frente e o roxo às vezes desiste e vai para o canto.
""",
    "🏎️ Corrida": """
**🎯 Objetivo:** dirigir o carro vermelho o **mais longe possível**, desviando dos outros carros. A velocidade vai **aumentando** com o tempo!

**Controles:** **←** e **→** (ou **A** e **D**). No celular, **segure o dedo** no lado esquerdo ou direito da tela, ou use os botões. **P** pausa.

**Pontos e vidas:**
- Os pontos sobem conforme a distância percorrida.
- 🪙 **Moeda** dourada vale **+50**.
- Você tem **3 vidas ❤️**. A cada batida perde uma, e o carro fica piscando por 2 segundos (nesse tempo não bate de novo).

**💡 Dica:** não fique colado num lado da pista. Fique perto do meio para conseguir fugir para qualquer lado, e olhe sempre lá na frente.
""",
    "♟️ Xadrez": COMO_XADREZ,
    "🔢 Adivinhe o Número": """
**🎯 Objetivo:** descobrir o número secreto que o computador pensou usando o **menor número de chutes**.

**Como jogar:** escolha a dificuldade, digite um número e clique em **Chutar**. O jogo diz se o número secreto é **maior ⬆️** ou **menor ⬇️** que o seu chute.

**💡 Dica:** chute sempre **no meio** do intervalo que sobrou. Por exemplo, de 1 a 100 chute 50; se for maior, chute 75; e assim por diante. Com essa estratégia você acerta qualquer número de 1 a 100 em no máximo 7 chutes!
""",
    "❌⭕ Jogo da Velha": """
**🎯 Objetivo:** fazer uma **linha de 3** com o seu símbolo, na horizontal, na vertical ou na diagonal.

**Como jogar:** você é o **❌** e sempre começa. Clique numa casa vazia, e o computador (**⭕**) joga logo depois. Se as 9 casas encherem sem ninguém fazer linha, **deu velha** (empate).

**Níveis:** *Fácil* joga aleatório, *Médio* às vezes erra e *Impossível* nunca perde (o melhor que dá é empatar).

**💡 Dicas:** comece pelo **centro** ou por um **canto**. Sempre bloqueie quando o adversário tiver 2 em linha. Tente criar duas ameaças ao mesmo tempo para ele não conseguir bloquear as duas.
""",
    "🪢 Forca": """
**🎯 Objetivo:** descobrir a palavra secreta **antes que o boneco seja enforcado**.

**Como jogar:** veja a **dica** (a categoria da palavra) e clique nas letras. Se a letra existir na palavra, ela aparece em todos os lugares onde estiver. Se não existir, uma parte do boneco é desenhada. Com **6 erros**, você perde.

**💡 Dicas:** comece pelas **vogais** (A, E, O, I) e depois tente as consoantes mais comuns em português: R, S, M, N, T, C. As palavras não têm acento.
""",
    "🪨 Pedra, Papel e Tesoura": """
**🎯 Objetivo:** escolher o objeto que **ganha** do objeto do computador.

**Quem ganha de quem:**
- 🪨 **Pedra** quebra a ✂️ **Tesoura**
- ✂️ **Tesoura** corta o 📄 **Papel**
- 📄 **Papel** embrulha a 🪨 **Pedra**

Se os dois escolherem a mesma coisa, é **empate**. Clique na sua escolha, e o computador escolhe ao mesmo tempo, sem trapaça. O placar vai somando.
""",
    "🧠 Jogo da Memória": """
**🎯 Objetivo:** encontrar todos os **8 pares** de bichinhos usando o menor número de jogadas.

**Como jogar:** clique em uma carta ❓ para virá-la e depois em outra.
- Se as duas forem **iguais**, elas ficam abertas. ✅
- Se forem **diferentes**, elas ficam à mostra até você clicar na próxima carta e depois se escondem de novo. Tente **lembrar onde estava cada bicho**!

Cada par de cartas viradas conta como **1 jogada**. O mínimo possível é 8.
""",
    "🟩 Termo": """
**🎯 Objetivo:** adivinhar a **palavra secreta de 5 letras** em até **6 tentativas**.

**Como jogar:** digite qualquer palavra de 5 letras e clique em **Enviar**. Cada letra muda de cor:
- 🟩 **Verde:** a letra está na palavra e **no lugar certo**.
- 🟨 **Amarelo:** a letra está na palavra, mas **em outro lugar**.
- ⬛ **Cinza:** a letra **não está** na palavra.

O teclado embaixo mostra as letras que você já testou. Não precisa usar acento (AVIÃO = AVIAO).

**💡 Dica:** no primeiro chute use uma palavra com várias vogais diferentes, como **AUDIO** ou **TEIAS**.
""",
    "🔢 2048": """
**🎯 Objetivo:** juntar os números até formar um bloco com **2048**.

**Como jogar:** use as setas ⬅️ ⬆️ ⬇️ ➡️. **Todos** os blocos deslizam para aquele lado ao mesmo tempo. Quando dois blocos com o **mesmo número** se encostam, eles se **somam** e viram um só (2+2=4, 4+4=8, 8+8=16...). A cada movimento aparece um bloco novo (2 ou 4) num espaço vazio.

O jogo acaba quando o tabuleiro enche e não há mais nenhuma soma possível. Cada soma vale pontos.

**💡 Dicas:** escolha um **canto** para guardar o maior número e não tire ele de lá. Use quase sempre só 2 ou 3 direções (por exemplo ⬇️ e ⬅️, e às vezes ➡️) e evite a direção que tira o bloco grande do canto.
""",
    "💣 Campo Minado": """
**🎯 Objetivo:** abrir **todas as casas sem mina**, sem pisar em nenhuma bomba.

**Como jogar:**
- Com o modo **⛏️ Abrir** selecionado, clique numa casa para abri-la. O **primeiro clique nunca é mina**.
- O **número** numa casa aberta diz **quantas minas existem nas 8 casas em volta** dela (lados e diagonais).
- Casa vazia significa zero minas em volta, e o jogo abre a região sozinho.
- Troque para **🚩 Bandeira** para marcar onde você acha que tem mina. Clique de novo para tirar a marcação. Casas com bandeira não abrem por acidente.

**💡 Dica:** se uma casa com **1** só tem **uma** casa fechada em volta, essa casa é mina. Marque com bandeira. Se um número já tem todas as suas minas marcadas, as outras casas em volta dele são **seguras**.
""",
    "🔴 Ligue 4": """
**🎯 Objetivo:** ser o primeiro a **alinhar 4 peças** da sua cor na horizontal, na vertical ou na diagonal.

**Como jogar:** você é o **🔴** e começa. Clique em **qualquer casa de uma coluna** e sua peça **cai** até o fundo dessa coluna, parando na primeira casa livre. Depois o computador (**🟡**) joga. Se o tabuleiro encher sem ninguém fazer 4, é empate.

**💡 Dicas:** jogue pelo **meio**, porque a coluna central participa de mais linhas. Sempre olhe se o computador tem **3 em linha** e bloqueie. Tente montar duas ameaças ao mesmo tempo.
""",
    "🤖 Quiz com IA": """
**🎯 Objetivo:** acertar o máximo de perguntas de um quiz **criado na hora pela inteligência artificial** (usando a sua chave Groq).

**Como jogar:**
1. Escreva **qualquer tema** (futebol, história, filmes, ciências, sua série favorita...).
2. Escolha a dificuldade e quantas perguntas quer, e clique em **✨ Gerar quiz**.
3. Para cada pergunta, marque uma opção e clique em **Responder**. Você vê na hora se acertou e uma explicação.
4. No final aparece a sua pontuação.

⚠️ A IA pode errar de vez em quando. Se uma resposta parecer estranha, confira em outra fonte.
""",
}


# =====================================================================
# MENU
# =====================================================================
JOGOS = {
    "👑 A Vida É um Jogo": jogo_vida,
    "🪩 Pinball": jogo_pinball,
    "🟢 Come-Come": jogo_comecome,
    "🏎️ Corrida": jogo_corrida,
    "♟️ Xadrez": jogo_xadrez,
    "🤖 Quiz com IA": jogo_quiz_ia,
    "🟩 Termo": jogo_termo,
    "🔢 2048": jogo_2048,
    "💣 Campo Minado": jogo_campo_minado,
    "🔴 Ligue 4": jogo_ligue4,
    "❌⭕ Jogo da Velha": jogo_velha,
    "🧠 Jogo da Memória": jogo_memoria,
    "🪢 Forca": jogo_forca,
    "🔢 Adivinhe o Número": jogo_adivinha,
    "🪨 Pedra, Papel e Tesoura": jogo_ppt,
}


# =====================================================================
# TELA DE ENTRADA (nome + chave Groq)
# =====================================================================
MODELOS_PREFERIDOS = ["llama-3.3-70b-versatile", "openai/gpt-oss-120b", "openai/gpt-oss-20b",
                      "llama-3.1-8b-instant"]


def escolher_modelo(ids):
    for m in MODELOS_PREFERIDOS:
        if m in ids:
            return m
    texto = [m for m in ids if not any(x in m for x in ("whisper", "tts", "guard", "playai", "vision"))]
    return (texto or ids or ["llama-3.3-70b-versatile"])[0]


def validar_chave_groq(chave: str):
    """Retorna (ok, mensagem, lista_de_modelos)."""
    try:
        r = requests.get("https://api.groq.com/openai/v1/models",
                         headers={"Authorization": f"Bearer {chave}"}, timeout=10)
    except requests.RequestException:
        return False, "Não consegui falar com a Groq agora. Tente de novo em instantes.", []
    if r.status_code == 200:
        return True, "", [m.get("id", "") for m in r.json().get("data", [])]
    if r.status_code in (401, 403):
        return False, "Chave Groq inválida. Confira e tente de novo.", []
    return False, f"A Groq respondeu com erro {r.status_code}. Tente de novo.", []


def tela_entrada():
    st.markdown("<h1 style='text-align:center'>🎮 Fliperama</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align:center'>{len(JOGOS)} jogos para você se divertir. "
                "Digite seu nome e sua chave Groq para entrar.</p>", unsafe_allow_html=True)
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
                    ok, erro, modelos = validar_chave_groq(chave)
                if ok:
                    S.usuario, S.groq_key, S.groq_modelo = nome, chave, escolher_modelo(modelos)
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

st.header(escolhido)
abrir = ((escolhido == "♟️ Xadrez" and not S.get("xq_board", chess.Board()).move_stack)
         or (escolhido == "👑 A Vida É um Jogo" and not S.get("vida")))
with st.expander("📖 Como jogar", expanded=abrir):
    st.markdown(INSTRUCOES[escolhido])

JOGOS[escolhido]()
